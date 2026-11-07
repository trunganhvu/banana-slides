"""Migration 019 backfill  template_image_path / template_style 

 Phase A spec §2.4 019 
-  template_image_path  ProjectTemplateAsset template_asset_id 
-  template_image_path  asset warning log
-  template_style  template_style_text = 
-  template_mode  'single'

 sqlite  alembic upgrade  018
 019 backfill 
"""

import os
import shutil
import sqlite3
import tempfile
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config


BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _make_alembic_config(db_url: str) -> Config:
    cfg = Config(str(BACKEND_ROOT / 'alembic.ini'))
    cfg.set_main_option('script_location', str(BACKEND_ROOT / 'migrations'))
    cfg.set_main_option('sqlalchemy.url', db_url)
    return cfg


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """ Test docstring """
    upload_dir = tmp_path / 'uploads'
    upload_dir.mkdir()
    monkeypatch.setenv('UPLOAD_FOLDER', str(upload_dir))

    db_path = tmp_path / 'test_019.db'
    db_url = f'sqlite:///{db_path}'
    # Test verification logic
    monkeypatch.setenv('DATABASE_URL', db_url)

    cfg = _make_alembic_config(db_url)
    command.upgrade(cfg, '018_add_project_title')

    yield db_path, db_url, upload_dir, cfg


def _seed_project(conn, *, template_image_path=None, template_style=None,
                  page_count=3):
    proj_id = str(uuid.uuid4())
    conn.execute(
        'INSERT INTO projects (id, creation_type, status, template_image_path, '
        ' template_style, image_aspect_ratio, created_at, updated_at) '
        "VALUES (?, 'idea', 'DRAFT', ?, ?, '16:9', "
        " CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
        (proj_id, template_image_path, template_style),
    )
    page_ids = []
    for i in range(page_count):
        page_id = str(uuid.uuid4())
        page_ids.append(page_id)
        conn.execute(
            'INSERT INTO pages (id, project_id, order_index, status, '
            ' created_at, updated_at) '
            "VALUES (?, ?, ?, 'DRAFT', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (page_id, proj_id, i),
        )
    conn.commit()
    return proj_id, page_ids


def _create_template_file(upload_dir: Path, project_id: str, filename='template.png') -> str:
    """ Test docstring """
    target_dir = upload_dir / project_id / 'template'
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / filename
    target.write_bytes(b'\x89PNG\r\n\x1a\n')  # PNG header is enough for "exists" check
    return f'{project_id}/template/{filename}'


def test_backfill_creates_asset_when_template_image_exists(fresh_db):
    db_path, db_url, upload_dir, cfg = fresh_db
    conn = sqlite3.connect(db_path)
    try:
        proj_id, page_ids = _seed_project(conn)
        rel_path = _create_template_file(upload_dir, proj_id)
        conn.execute(
            'UPDATE projects SET template_image_path = ?, template_style = ? '
            'WHERE id = ?',
            (rel_path, '', proj_id),
        )
        conn.commit()
    finally:
        conn.close()

    command.upgrade(cfg, '019_per_page_template')

    conn = sqlite3.connect(db_path)
    try:
        # Test verification logic
        assets = conn.execute(
            'SELECT id, project_id, image_path, source, analysis_status '
            'FROM project_template_assets WHERE project_id = ?',
            (proj_id,),
        ).fetchall()
        assert len(assets) == 1
        asset_id, _, image_path, source, status = assets[0]
        assert image_path == rel_path
        assert source == 'upload'
        assert status == 'pending'

        # Test verification logic
        rows = conn.execute(
            'SELECT template_asset_id, template_style_text, template_selection_source '
            'FROM pages WHERE project_id = ?',
            (proj_id,),
        ).fetchall()
        assert len(rows) == len(page_ids)
        for tpl_id, tpl_style, src in rows:
            assert tpl_id == asset_id
            assert tpl_style == ''
            assert src == 'batch_apply'

        # Test verification logic
        mode = conn.execute(
            'SELECT template_mode FROM projects WHERE id = ?', (proj_id,)
        ).fetchone()[0]
        assert mode == 'single'
    finally:
        conn.close()


def test_backfill_skips_asset_when_template_file_missing(fresh_db, caplog):
    db_path, db_url, upload_dir, cfg = fresh_db
    conn = sqlite3.connect(db_path)
    try:
        proj_id, page_ids = _seed_project(conn, page_count=2)
        # Test verification logic
        conn.execute(
            'UPDATE projects SET template_image_path = ? WHERE id = ?',
            (f'{proj_id}/template/missing.png', proj_id),
        )
        conn.commit()
    finally:
        conn.close()

    with caplog.at_level('WARNING'):
        command.upgrade(cfg, '019_per_page_template')

    conn = sqlite3.connect(db_path)
    try:
        assets = conn.execute(
            'SELECT COUNT(*) FROM project_template_assets WHERE project_id = ?',
            (proj_id,),
        ).fetchone()[0]
        assert assets == 0  # Test logic

        rows = conn.execute(
            'SELECT template_asset_id, template_style_text '
            'FROM pages WHERE project_id = ?',
            (proj_id,),
        ).fetchall()
        for tpl_id, tpl_style in rows:
            assert tpl_id is None
            assert tpl_style is None
    finally:
        conn.close()


def test_backfill_handles_style_only_project(fresh_db):
    db_path, db_url, upload_dir, cfg = fresh_db
    conn = sqlite3.connect(db_path)
    try:
        proj_id, page_ids = _seed_project(conn)
        conn.execute(
            'UPDATE projects SET template_style = ? WHERE id = ?',
            ('', proj_id),
        )
        conn.commit()
    finally:
        conn.close()

    command.upgrade(cfg, '019_per_page_template')

    conn = sqlite3.connect(db_path)
    try:
        assets = conn.execute(
            'SELECT COUNT(*) FROM project_template_assets WHERE project_id = ?',
            (proj_id,),
        ).fetchone()[0]
        assert assets == 0  # Test logic

        rows = conn.execute(
            'SELECT template_asset_id, template_style_text, template_selection_source '
            'FROM pages WHERE project_id = ?',
            (proj_id,),
        ).fetchall()
        for tpl_id, tpl_style, src in rows:
            assert tpl_id is None
            assert tpl_style == ''
            assert src == 'batch_apply'
    finally:
        conn.close()


def test_backfill_leaves_clean_projects_untouched(fresh_db):
    """ Test docstring """
    db_path, db_url, upload_dir, cfg = fresh_db
    conn = sqlite3.connect(db_path)
    try:
        proj_id, page_ids = _seed_project(conn)
    finally:
        conn.close()

    command.upgrade(cfg, '019_per_page_template')

    conn = sqlite3.connect(db_path)
    try:
        assets = conn.execute(
            'SELECT COUNT(*) FROM project_template_assets WHERE project_id = ?',
            (proj_id,),
        ).fetchone()[0]
        assert assets == 0

        rows = conn.execute(
            'SELECT template_asset_id, template_style_text, template_selection_source '
            'FROM pages WHERE project_id = ?',
            (proj_id,),
        ).fetchall()
        for tpl_id, tpl_style, src in rows:
            assert tpl_id is None
            assert tpl_style is None
            assert src is None  # Test logic

        mode = conn.execute(
            'SELECT template_mode FROM projects WHERE id = ?', (proj_id,)
        ).fetchone()[0]
        assert mode == 'single'  # server_default
    finally:
        conn.close()


def test_downgrade_reverts_schema(fresh_db):
    db_path, db_url, upload_dir, cfg = fresh_db
    command.upgrade(cfg, '019_per_page_template')
    command.downgrade(cfg, '018_add_project_title')

    conn = sqlite3.connect(db_path)
    try:
        # Test verification logic
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        assert 'project_template_assets' not in tables

        # Test verification logic
        cols = {r[1] for r in conn.execute("PRAGMA table_info('projects')")}
        assert 'template_mode' not in cols

        # Test verification logic
        page_cols = {r[1] for r in conn.execute("PRAGMA table_info('pages')")}
        for col in ('template_asset_id', 'template_style_text',
                    'template_selection_source', 'template_match_reason',
                    'template_match_confidence'):
            assert col not in page_cols
    finally:
        conn.close()