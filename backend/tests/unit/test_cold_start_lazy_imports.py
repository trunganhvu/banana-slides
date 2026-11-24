"""Tests for backend cold-start lazy imports and Cloudflare container optimizations."""
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from flask import Flask


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = PROJECT_ROOT / "backend"


def test_importing_controllers_defers_heavy_sdks():
    """Importing Flask controllers must not eagerly load heavy AI or export SDKs."""
    script = (
        "import json, sys; "
        f"sys.path.insert(0, {str(BACKEND_DIR)!r}); "
        "import controllers; "
        "heavy = ('google.genai', 'openai', 'anthropic', 'markitdown', 'pandas', 'pptx', 'fitz'); "
        "loaded = [m for m in heavy if m in sys.modules]; "
        "print(json.dumps(loaded))"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=True,
    )
    assert proc.stdout.strip() == "[]"


def test_lazy_provider_exports_and_mock_patch_compatibility():
    """PEP 562 exports resolve classes and still support unittest.mock.patch."""
    import services
    import services.ai_providers as ai_providers
    import utils

    assert ai_providers.GenAITextProvider.__name__ == "GenAITextProvider"
    assert ai_providers.OpenAITextProvider.__name__ == "OpenAITextProvider"
    assert services.ExportService.__name__ == "ExportService"
    assert utils.PPTXBuilder.__name__ == "PPTXBuilder"

    app = Flask(__name__)
    app.config.update(
        AI_PROVIDER_FORMAT="openai",
        OPENAI_API_KEY="test-openai-key",
        OPENAI_API_BASE="https://api.example.com/v1",
    )
    with app.app_context():
        with patch("services.ai_providers.OpenAITextProvider") as provider_cls:
            provider = ai_providers.get_text_provider(model="gpt-4o-mini")

    assert provider == provider_cls.return_value
    provider_cls.assert_called_once()


def test_cloudflare_container_cold_start_optimizations():
    """Cloudflare Dockerfile, entrypoint, Worker, and wrangler.jsonc stay optimized."""
    dockerfile = (PROJECT_ROOT / "cloudflare-backend" / "Dockerfile").read_text(encoding="utf-8")
    assert "--compile-bytecode" in dockerfile
    assert "compileall" in dockerfile

    entrypoint_bytes = (PROJECT_ROOT / "cloudflare-backend" / "entrypoint.sh").read_bytes()
    assert b"\r" not in entrypoint_bytes
    entrypoint = entrypoint_bytes.decode("utf-8")
    assert "RUN_STARTUP_MIGRATE" in entrypoint
    assert "alembic upgrade head" in entrypoint

    worker_src = (PROJECT_ROOT / "cloudflare-backend" / "src" / "index.ts").read_text(encoding="utf-8")
    assert "BANANA_SKIP_AUTO_MIGRATE" in worker_src
    assert "RUN_STARTUP_MIGRATE" in worker_src

    wrangler = (PROJECT_ROOT / "cloudflare-backend" / "wrangler.jsonc").read_text(encoding="utf-8")
    assert '"BANANA_SKIP_AUTO_MIGRATE": "1"' in wrangler
    assert '"RUN_STARTUP_MIGRATE": "0"' in wrangler
