"""Utilities for OpenAI-compatible and self-hosted local LLM endpoints."""

import ipaddress
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit, urlunsplit

import requests

from config import is_placeholder_api_key

LOCAL_DUMMY_API_KEY = "sk-local-no-key"
SUPPORTED_PROVIDER_FORMATS = {"gemini", "openai"}
PROVIDER_FORMAT_ALIASES = {
    "local": "openai",
    "self_hosted": "openai",
    "self-hosted": "openai",
    "openai_compatible": "openai",
    "openai-compatible": "openai",
}

_DOCKER_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
_ENDPOINT_SUFFIXES = (
    "/chat/completions",
    "/images/generations",
    "/completions",
    "/models",
)


def parse_provider_format(raw: Optional[str]) -> Optional[str]:
    """Parse provider format string into canonical 'gemini' or 'openai', or None."""
    normalized = (raw or "").strip().lower()
    if not normalized:
        return None
    mapped = PROVIDER_FORMAT_ALIASES.get(normalized, normalized)
    return mapped if mapped in SUPPORTED_PROVIDER_FORMATS else None


def normalize_provider_format(raw: Optional[str], default: str = "gemini") -> str:
    """Return canonical provider format ('gemini' or 'openai'), falling back to default."""
    parsed = parse_provider_format(raw)
    if parsed:
        return parsed
    fallback = parse_provider_format(default)
    return fallback or "gemini"


def is_running_in_docker() -> bool:
    """Return True when the backend process is running inside a Docker container."""
    return os.getenv("IN_DOCKER") == "1" or os.path.exists("/.dockerenv")


def is_local_or_private_base_url(url: Optional[str]) -> bool:
    """Return True when url points to loopback, localhost, or a private network host."""
    if not url:
        return False
    candidate = url.strip()
    if "://" not in candidate:
        candidate = f"http://{candidate}"
    try:
        host = (urlsplit(candidate).hostname or "").strip().lower()
    except ValueError:
        return False
    if not host:
        return False
    if host in _DOCKER_LOOPBACK_HOSTS or host == "host.docker.internal" or host.endswith((".local", ".internal")):
        return True
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return False


def _format_netloc(
    hostname: str,
    port: Optional[int],
    username: Optional[str],
    password: Optional[str],
) -> str:
    host_part = f"[{hostname}]" if ":" in hostname else hostname
    if port is not None:
        host_part = f"{host_part}:{port}"
    if username is not None:
        auth = f"{username}:{password}" if password is not None else username
        return f"{auth}@{host_part}"
    return host_part


def normalize_openai_base_url(
    raw_url: Optional[str],
    *,
    rewrite_docker_localhost: bool = True,
) -> str:
    """Normalize an OpenAI-compatible base URL across common local LLM runners.

    - Prepends ``http://`` when no scheme is specified.
    - Strips accidentally pasted endpoint suffixes (``/chat/completions``, etc.).
    - Appends ``/v1`` when the URL has no path component.
    - Rewrites loopback hosts to ``host.docker.internal`` inside Docker.
    """
    cleaned = (raw_url or "").strip().rstrip("/")
    if not cleaned:
        return ""
    if "://" not in cleaned:
        cleaned = f"http://{cleaned}"

    parts = urlsplit(cleaned)
    path = parts.path.rstrip("/")
    lower_path = path.lower()
    for suffix in _ENDPOINT_SUFFIXES:
        if lower_path.endswith(suffix):
            path = path[: len(path) - len(suffix)].rstrip("/")
            break

    if not path:
        path = "/v1"

    hostname = parts.hostname or ""
    netloc = parts.netloc
    if (
        rewrite_docker_localhost
        and is_running_in_docker()
        and hostname.lower() in _DOCKER_LOOPBACK_HOSTS
    ):
        target_host = os.getenv("DOCKER_HOST_GATEWAY", "host.docker.internal")
        try:
            port = parts.port
        except ValueError:
            port = None
        netloc = _format_netloc(target_host, port, parts.username, parts.password)

    return urlunsplit((parts.scheme, netloc, path, "", "")).rstrip("/")


def _dedupe_models(items: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        model_id = str(item or "").strip()
        if model_id and model_id not in seen:
            seen.add(model_id)
            result.append(model_id)
    return result


def _extract_openai_models(payload: Any) -> List[str]:
    items = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return []
    extracted: List[str] = []
    for entry in items:
        if isinstance(entry, str):
            extracted.append(entry)
        elif isinstance(entry, dict):
            model_id = entry.get("id") or entry.get("name") or entry.get("model")
            if model_id:
                extracted.append(str(model_id))
    return _dedupe_models(extracted)


def _extract_ollama_models(payload: Any) -> List[str]:
    if not isinstance(payload, dict):
        return []
    items = payload.get("models")
    if not isinstance(items, list):
        return []
    extracted: List[str] = []
    for entry in items:
        if isinstance(entry, dict):
            model_id = entry.get("name") or entry.get("model")
            if model_id:
                extracted.append(str(model_id))
    return _dedupe_models(extracted)


def _build_connection_error(effective_base: str, docker_rewritten: bool, exc: Exception) -> RuntimeError:
    msg = f"Không thể kết nối tới LLM server tại {effective_base}: {exc}"
    if docker_rewritten:
        msg += (
            " (Đang chạy trong Docker: hãy đảm bảo server local lắng nghe trên 0.0.0.0, "
            "ví dụ đặt OLLAMA_HOST=0.0.0.0)"
        )
    return RuntimeError(msg)


def discover_openai_compatible_models(
    api_base_url: str,
    api_key: Optional[str] = None,
    timeout: float = 6.0,
) -> Dict[str, Any]:
    """Query ``{base}/models`` (with Ollama ``/api/tags`` fallback) to list available models."""
    raw_normalized = normalize_openai_base_url(api_base_url, rewrite_docker_localhost=False)
    effective_base = normalize_openai_base_url(api_base_url, rewrite_docker_localhost=True)
    if not effective_base:
        raise ValueError("API Base URL không hợp lệ")

    docker_rewritten = raw_normalized != effective_base
    headers: Dict[str, str] = {}
    cleaned_key = (api_key or "").strip()
    if cleaned_key and not is_placeholder_api_key(cleaned_key):
        headers["Authorization"] = f"Bearer {cleaned_key}"

    models_url = f"{effective_base}/models"
    try:
        resp = requests.get(models_url, headers=headers, timeout=timeout)
    except requests.exceptions.RequestException as exc:
        raise _build_connection_error(effective_base, docker_rewritten, exc) from exc

    models: List[str] = []
    source = "openai_models"

    if resp.ok:
        try:
            models = _extract_openai_models(resp.json())
        except ValueError:
            models = []
    elif resp.status_code not in (404, 405):
        raise RuntimeError(f"Server {effective_base} trả về HTTP {resp.status_code}: {resp.text[:200]}")

    if not models:
        parsed = urlsplit(effective_base)
        ollama_url = urlunsplit((parsed.scheme, parsed.netloc, "/api/tags", "", ""))
        try:
            ollama_resp = requests.get(ollama_url, headers=headers, timeout=timeout)
            if ollama_resp.ok:
                ollama_models = _extract_ollama_models(ollama_resp.json())
                if ollama_models:
                    models = ollama_models
                    source = "ollama_tags"
        except requests.exceptions.RequestException:
            pass

    return {
        "models": models,
        "effective_base_url": effective_base,
        "docker_rewritten": docker_rewritten,
        "source": source,
    }
