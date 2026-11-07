"""Task manager image prompt field filtering regression tests."""

import json

import pytest

from models import Settings, db
from services.task_manager import _append_extra_fields, get_image_prompt_field_names


@pytest.fixture(autouse=True)
def restore_image_prompt_fields(client):
    with client.application.app_context():
        settings = Settings.get_settings()
        original_value = settings.image_prompt_extra_fields
    yield
    with client.application.app_context():
        db.session.rollback()
        settings = Settings.get_settings()
        settings.image_prompt_extra_fields = original_value
        db.session.commit()


def _set_image_prompt_fields(client, value):
    with client.application.app_context():
        settings = Settings.get_settings()
        settings.image_prompt_extra_fields = value
        db.session.commit()


def test_image_prompt_field_names_fallback_to_default_when_not_set(client):
    _set_image_prompt_fields(client, None)

    with client.application.app_context():
        fields = get_image_prompt_field_names()
        assert fields == set(Settings.DEFAULT_IMAGE_PROMPT_FIELDS)
        assert 'Ghi chú thuyết trình' not in fields


def test_append_extra_fields_filters_by_allowlist(client):
    _set_image_prompt_fields(client, json.dumps(['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm']))

    with client.application.app_context():
        desc_content = {
            'extra_fields': {
                'Hình ảnh & Tư liệu': '',
                'Ghi chú thuyết trình': '',
            }
        }
        result = _append_extra_fields('', desc_content)
        assert 'Hình ảnh & Tư liệu' in result
        assert 'Ghi chú thuyết trình' not in result


def test_append_extra_fields_respects_empty_allowlist(client):
    _set_image_prompt_fields(client, json.dumps([]))

    with client.application.app_context():
        desc_content = {
            'extra_fields': {
                'Hình ảnh & Tư liệu': '',
                'Bố cục & Trọng tâm': '',
            }
        }
        result = _append_extra_fields('', desc_content)
        assert result == ''


def test_append_extra_fields_uses_prefetched_allowlist(monkeypatch):
    def fail_if_fetching_settings():
        raise AssertionError('settings should be pre-fetched by the task')

    monkeypatch.setattr(
        'services.task_manager.get_image_prompt_field_names',
        fail_if_fetching_settings,
    )

    desc_content = {
        'extra_fields': {
            'Hình ảnh & Tư liệu': '',
            'Ghi chú thuyết trình': '',
        }
    }

    result = _append_extra_fields('', desc_content, {'Hình ảnh & Tư liệu'})
    assert 'Hình ảnh & Tư liệu' in result
    assert 'Ghi chú thuyết trình' not in result


def test_append_extra_fields_handles_missing_description_text():
    result = _append_extra_fields(None, {'extra_fields': {'Hình ảnh & Tư liệu': ''}}, {'Hình ảnh & Tư liệu'})

    assert result == 'Hình ảnh & Tư liệu'


def test_append_extra_fields_handles_missing_description_content():
    result = _append_extra_fields('', None, {'Hình ảnh & Tư liệu'})

    assert result == ''


def test_append_extra_fields_keeps_zero_values():
    result = _append_extra_fields(
        '',
        {'extra_fields': {'': 0, '': '   ', '': None}},
        {'', '', ''},
    )

    assert '0' in result
    assert '' not in result
    assert '' not in result