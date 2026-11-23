import os
from pathlib import Path
from urllib.parse import quote


def test_serve_file_supports_vietnamese_export_filename(client, app):
    upload_root = Path(app.config["UPLOAD_FOLDER"])
    exports_dir = upload_root / "proj-vi" / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    filename = "Báo cáo Q4.pptx"
    (exports_dir / filename).write_bytes(b"pptx-content")

    response = client.get(f"/files/proj-vi/exports/{quote(filename)}")

    assert response.status_code == 200
    assert response.data == b"pptx-content"
    assert "attachment" in response.headers.get("Content-Disposition", "").lower()


def test_serve_file_blocks_traversal_and_symlink_escape(client, app, tmp_path):
    upload_root = Path(app.config["UPLOAD_FOLDER"])
    pages_dir = upload_root / "proj-sec" / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    outside_file = tmp_path / "secret.txt"
    outside_file.write_text("top-secret", encoding="utf-8")

    # Block dot-dot / slash traversal via router or controller
    res_dotdot = client.get("/files/../pages/secret.txt")
    assert res_dotdot.status_code in {403, 404}

    res_encoded_slash = client.get("/files/proj-sec/pages/..%2F..%2Fsecret.txt")
    assert res_encoded_slash.status_code in {403, 404}

    # Backslash traversal reaches controller and must be rejected with 403
    res_backslash = client.get("/files/proj-sec/pages/..%5C..%5Csecret.txt")
    assert res_backslash.status_code == 403

    # Direct controller test for dot-dot segment
    res_literal_dotdot = client.get("/files/proj-sec/pages/..")
    assert res_literal_dotdot.status_code in {403, 404}

    # Block symlink escaping upload folder
    symlink_path = pages_dir / "linked.txt"
    try:
        os.symlink(outside_file, symlink_path)
    except (OSError, NotImplementedError):
        return

    res_symlink = client.get("/files/proj-sec/pages/linked.txt")
    assert res_symlink.status_code == 403


def test_serve_user_template_blocks_traversal(client, app):
    upload_root = Path(app.config["UPLOAD_FOLDER"])
    tpl_dir = upload_root / "user-templates" / "tpl-1"
    tpl_dir.mkdir(parents=True, exist_ok=True)
    (tpl_dir / "preview.png").write_bytes(b"png")

    ok = client.get("/files/user-templates/tpl-1/preview.png")
    assert ok.status_code == 200

    res_slash = client.get("/files/user-templates/..%2Fproj-sec/preview.png")
    assert res_slash.status_code in {403, 404}

    res_backslash = client.get("/files/user-templates/..%5Cproj-sec/preview.png")
    assert res_backslash.status_code == 403


def test_serve_mineru_file_blocks_sibling_prefix_escape(client, app):
    upload_root = Path(app.config["UPLOAD_FOLDER"])
    mineru_root = upload_root / "mineru_files"
    (mineru_root / "abc").mkdir(parents=True, exist_ok=True)
    (mineru_root / "abc" / "safe.txt").write_text("safe", encoding="utf-8")

    sibling_dir = mineru_root / "abc_secret"
    sibling_dir.mkdir(parents=True, exist_ok=True)
    (sibling_dir / "leak.txt").write_text("secret-sibling-data", encoding="utf-8")

    ok = client.get("/files/mineru/abc/safe.txt")
    assert ok.status_code == 200
    assert ok.data == b"safe"

    escape_res = client.get("/files/mineru/abc/../abc_secret/leak.txt")
    assert escape_res.status_code == 403
