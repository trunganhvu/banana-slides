"""
Unit tests for default image model (gemini-3.1-flash-lite-image) and 1K/2K resolution constraints.
"""
import pytest
from sqlalchemy.pool import StaticPool
from app import create_app
from config import Config
from models import db, Settings
from services.ai_providers import get_default_models_for_provider


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'poolclass': StaticPool,
        'connect_args': {'check_same_thread': False},
    }
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_default_gemini_image_model_is_flash_lite_image(monkeypatch):
    monkeypatch.delenv('IMAGE_MODEL', raising=False)
    assert Config.IMAGE_MODEL == 'gemini-3.1-flash-lite-image'
    assert get_default_models_for_provider('gemini')['image'] == 'gemini-3.1-flash-lite-image'


def test_settings_auto_migrates_legacy_image_model_and_4k_resolution(app):
    with app.app_context():
        s = Settings(
            id=1,
            ai_provider_format='gemini',
            image_model='gemini-2.5-flash-image',
            image_resolution='4K',
        )
        db.session.add(s)
        db.session.commit()

        loaded = Settings.get_settings()
        assert loaded.image_model == 'gemini-3.1-flash-lite-image'
        assert loaded.image_resolution == '2K'


def test_update_settings_allows_1k_2k_and_rejects_4k(client, app):
    res_1k = client.put('/api/settings', json={'image_resolution': '1K'})
    assert res_1k.status_code == 200
    assert res_1k.get_json()['data']['image_resolution'] == '1K'

    res_2k = client.put('/api/settings', json={'image_resolution': '2K'})
    assert res_2k.status_code == 200
    assert res_2k.get_json()['data']['image_resolution'] == '2K'

    res_4k = client.put('/api/settings', json={'image_resolution': '4K'})
    assert res_4k.status_code == 400
    assert '1K or 2K' in res_4k.get_json()['error']['message']
