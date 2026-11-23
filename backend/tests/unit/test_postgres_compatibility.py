from unittest.mock import MagicMock

import psycopg2
from config import build_engine_options, normalize_database_url
from desktop_bootstrap import repair_desktop_settings_schema


def test_psycopg2_is_importable():
    assert hasattr(psycopg2, 'connect')


def test_normalize_database_url_rewrites_legacy_postgres_scheme():
    assert normalize_database_url('postgres://user:pass@host:5432/db') == 'postgresql://user:pass@host:5432/db'
    assert normalize_database_url(' postgresql://user:pass@host:5432/db ') == 'postgresql://user:pass@host:5432/db'
    assert normalize_database_url('sqlite:///tmp/test.db') == 'sqlite:///tmp/test.db'
    assert normalize_database_url(None) == ''


def test_build_engine_options_for_postgres_excludes_sqlite_connect_args():
    opts = build_engine_options('postgresql://postgres:pw@db.example.supabase.co:5432/postgres')

    assert 'check_same_thread' not in opts['connect_args']
    assert 'timeout' not in opts['connect_args']
    assert opts['connect_args']['connect_timeout'] == 15
    assert opts['pool_pre_ping'] is True
    assert opts['pool_recycle'] == 300
    assert opts['pool_size'] == 5
    assert opts['max_overflow'] == 10


def test_build_engine_options_for_sqlite_preserves_thread_and_timeout_settings():
    opts = build_engine_options('sqlite:///backend/instance/database.db')

    assert opts['connect_args']['check_same_thread'] is False
    assert opts['connect_args']['timeout'] == 30
    assert opts['pool_pre_ping'] is True
    assert opts['pool_recycle'] == 3600


def test_repair_desktop_settings_schema_skips_non_sqlite_dialects():
    fake_db = MagicMock()
    fake_db.engine.dialect.name = 'postgresql'

    repair_desktop_settings_schema(fake_db)

    fake_db.engine.begin.assert_not_called()
