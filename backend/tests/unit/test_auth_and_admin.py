"""
Unit tests for Google SSO, user model, project isolation, and admin metrics.
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.pool import StaticPool
from app import create_app
from models import db, User, Project
from utils.auth_middleware import generate_token, decode_token


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv('ADMIN_EMAILS', 'admin@example.com')
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'poolclass': StaticPool,
        'connect_args': {'check_same_thread': False}
    }
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_jwt_token_encode_decode(app):
    with app.app_context():
        token = generate_token('u123', 'admin@example.com', 'admin')
        payload = decode_token(token)
        assert payload is not None
        assert payload['user_id'] == 'u123'
        assert payload['email'] == 'admin@example.com'
        assert payload['role'] == 'admin'


def test_dev_login_and_admin_assignment(client, app):
    with app.app_context():
        # Create unassigned project
        p = Project(creation_type='idea', project_title='Legacy Project')
        db.session.add(p)
        db.session.commit()
        assert p.user_id is None

    # Dev login with admin email
    res = client.post('/api/auth/dev-login', json={'email': 'admin@example.com', 'name': 'Admin User'})
    assert res.status_code == 200
    data = res.get_json()['data']
    assert data['user']['role'] == 'admin'
    assert data['user']['email'] == 'admin@example.com'
    token = data['token']

    # Verify unassigned project was assigned to this admin
    with app.app_context():
        updated_p = Project.query.filter_by(project_title='Legacy Project').first()
        assert updated_p.user_id == data['user']['id']

    # Test /api/auth/me
    me_res = client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert me_res.status_code == 200
    assert me_res.get_json()['data']['user']['email'] == 'admin@example.com'


def test_project_isolation_per_user(client, app):
    # Login user 1
    u1_res = client.post('/api/auth/dev-login', json={'email': 'user1@example.com', 'name': 'User 1'})
    t1 = u1_res.get_json()['data']['token']

    # Login user 2
    u2_res = client.post('/api/auth/dev-login', json={'email': 'user2@example.com', 'name': 'User 2'})
    t2 = u2_res.get_json()['data']['token']

    # User 1 creates project
    p1_res = client.post('/api/projects', headers={'Authorization': f'Bearer {t1}'}, json={
        'creation_type': 'idea',
        'idea_prompt': 'Idea from User 1'
    })
    assert p1_res.status_code in [200, 201]

    # User 2 creates project
    p2_res = client.post('/api/projects', headers={'Authorization': f'Bearer {t2}'}, json={
        'creation_type': 'idea',
        'idea_prompt': 'Idea from User 2'
    })
    assert p2_res.status_code in [200, 201]

    # User 1 lists projects: should only see User 1's project
    list1 = client.get('/api/projects', headers={'Authorization': f'Bearer {t1}'})
    assert list1.status_code == 200
    projs1 = list1.get_json()['data']['projects']
    assert len(projs1) == 1
    assert projs1[0]['idea_prompt'] == 'Idea from User 1'

    # User 2 lists projects: should only see User 2's project
    list2 = client.get('/api/projects', headers={'Authorization': f'Bearer {t2}'})
    assert list2.status_code == 200
    projs2 = list2.get_json()['data']['projects']
    assert len(projs2) == 1
    assert projs2[0]['idea_prompt'] == 'Idea from User 2'


def test_admin_stats_and_users(client, app):
    # Admin login
    admin_res = client.post('/api/auth/dev-login', json={'email': 'admin@example.com', 'name': 'Admin'})
    admin_token = admin_res.get_json()['data']['token']

    # Regular user login
    reg_res = client.post('/api/auth/dev-login', json={'email': 'member@example.com', 'name': 'Member'})
    reg_token = reg_res.get_json()['data']['token']

    # Member cannot access admin
    forbidden = client.get('/api/admin/stats', headers={'Authorization': f'Bearer {reg_token}'})
    assert forbidden.status_code == 403

    # Admin accesses stats
    stats_res = client.get('/api/admin/stats', headers={'Authorization': f'Bearer {admin_token}'})
    assert stats_res.status_code == 200
    stats = stats_res.get_json()['data']
    assert stats['total_users'] >= 2
    assert stats['total_visits'] >= 2

    # Admin accesses users list
    users_res = client.get('/api/admin/users', headers={'Authorization': f'Bearer {admin_token}'})
    assert users_res.status_code == 200
    users = users_res.get_json()['data']['users']
    assert len(users) >= 2
    emails = [u['email'] for u in users]
    assert 'admin@example.com' in emails
    assert 'member@example.com' in emails


def test_dev_login_disabled_in_production_by_default(client, app, monkeypatch):
    monkeypatch.setitem(app.config, 'TESTING', False)
    monkeypatch.delenv('ENABLE_DEV_LOGIN', raising=False)

    res = client.post('/api/auth/dev-login', json={'email': 'admin@example.com'})
    assert res.status_code == 403
    assert res.get_json()['code'] == 'DEV_LOGIN_DISABLED'


def test_dev_login_allowed_when_explicitly_enabled(client, app, monkeypatch):
    monkeypatch.setitem(app.config, 'TESTING', False)
    monkeypatch.setenv('ENABLE_DEV_LOGIN', 'true')

    res = client.post('/api/auth/dev-login', json={'email': 'admin@example.com'})
    assert res.status_code == 200
    assert res.get_json()['data']['user']['role'] == 'admin'


def test_empty_admin_emails_only_bootstraps_first_user(client, app, monkeypatch):
    monkeypatch.delenv('ADMIN_EMAILS', raising=False)
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'test-client-id.apps.googleusercontent.com')

    first_resp = MagicMock(status_code=200)
    first_resp.json.return_value = {
        'aud': 'test-client-id.apps.googleusercontent.com',
        'iss': 'https://accounts.google.com',
        'email_verified': 'true',
        'email': 'first@example.com',
        'name': 'First User',
        'sub': 'sub-1',
    }
    second_resp = MagicMock(status_code=200)
    second_resp.json.return_value = {
        'aud': 'test-client-id.apps.googleusercontent.com',
        'iss': 'https://accounts.google.com',
        'email_verified': 'true',
        'email': 'second@example.com',
        'name': 'Second User',
        'sub': 'sub-2',
    }

    with patch('controllers.auth_controller.requests.get', side_effect=[first_resp, second_resp]):
        res1 = client.post('/api/auth/google', json={'credential': 'token-1'})
        assert res1.status_code == 200
        assert res1.get_json()['data']['user']['role'] == 'admin'

        res2 = client.post('/api/auth/google', json={'credential': 'token-2'})
        assert res2.status_code == 200
        assert res2.get_json()['data']['user']['role'] == 'user'


def test_google_sso_rejects_unconfigured_client_id(client, monkeypatch):
    monkeypatch.delenv('GOOGLE_CLIENT_ID', raising=False)

    res = client.post('/api/auth/google', json={'credential': 'token-any'})
    assert res.status_code == 503
    assert res.get_json()['code'] == 'AUTH_NOT_CONFIGURED'


def test_google_sso_rejects_wrong_audience_issuer_and_unverified_email(client, monkeypatch):
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'expected-client-id')

    wrong_aud = MagicMock(status_code=200)
    wrong_aud.json.return_value = {
        'aud': 'other-app-client-id',
        'iss': 'https://accounts.google.com',
        'email_verified': 'true',
        'email': 'user@example.com',
    }

    wrong_iss = MagicMock(status_code=200)
    wrong_iss.json.return_value = {
        'aud': 'expected-client-id',
        'iss': 'https://evil.example.com',
        'email_verified': 'true',
        'email': 'user@example.com',
    }

    unverified_email = MagicMock(status_code=200)
    unverified_email.json.return_value = {
        'aud': 'expected-client-id',
        'iss': 'https://accounts.google.com',
        'email_verified': 'false',
        'email': 'user@example.com',
    }

    with patch('controllers.auth_controller.requests.get', side_effect=[wrong_aud, wrong_iss, unverified_email]):
        res_aud = client.post('/api/auth/google', json={'credential': 't1'})
        assert res_aud.status_code == 401
        assert res_aud.get_json()['code'] == 'INVALID_TOKEN_AUDIENCE'

        res_iss = client.post('/api/auth/google', json={'credential': 't2'})
        assert res_iss.status_code == 401
        assert res_iss.get_json()['code'] == 'INVALID_TOKEN_ISSUER'

        res_verified = client.post('/api/auth/google', json={'credential': 't3'})
        assert res_verified.status_code == 401
        assert res_verified.get_json()['code'] == 'EMAIL_NOT_VERIFIED'


def test_google_sso_valid_token_issues_jwt_and_checks_params(client, monkeypatch):
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'expected-client-id')
    monkeypatch.setenv('ADMIN_EMAILS', 'owner@example.com')

    valid_resp = MagicMock(status_code=200)
    valid_resp.json.return_value = {
        'aud': 'expected-client-id',
        'iss': 'https://accounts.google.com',
        'email_verified': 'true',
        'email': 'owner@example.com',
        'name': 'Owner',
        'sub': 'google-sub-123',
    }

    with patch('controllers.auth_controller.requests.get', return_value=valid_resp) as mock_get:
        res = client.post('/api/auth/google', json={'credential': 'valid-id-token'})

    assert res.status_code == 200
    body = res.get_json()['data']
    assert body['user']['email'] == 'owner@example.com'
    assert body['user']['role'] == 'admin'
    decoded = decode_token(body['token'])
    assert decoded is not None
    assert decoded['email'] == 'owner@example.com'
    mock_get.assert_called_once_with(
        'https://oauth2.googleapis.com/tokeninfo',
        params={'id_token': 'valid-id-token'},
        timeout=10,
    )


def test_auth_me_promotes_user_when_email_added_to_admin_emails(client, app, monkeypatch):
    # First log in while email is NOT in ADMIN_EMAILS -> role='user'
    reg_res = client.post('/api/auth/dev-login', json={'email': 'promoted@example.com', 'name': 'Promoted'})
    assert reg_res.status_code == 200
    reg_data = reg_res.get_json()['data']
    assert reg_data['user']['role'] == 'user'
    token = reg_data['token']

    # Confirm admin endpoints are forbidden initially
    forbidden = client.get('/api/admin/stats', headers={'Authorization': f'Bearer {token}'})
    assert forbidden.status_code == 403

    # Add email to ADMIN_EMAILS and call /api/auth/me
    monkeypatch.setenv('ADMIN_EMAILS', 'admin@example.com, promoted@example.com')
    me_res = client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert me_res.status_code == 200
    assert me_res.get_json()['data']['user']['role'] == 'admin'

    # Now admin endpoints succeed with the same JWT token (auth_middleware reads DB user.role)
    stats_res = client.get('/api/admin/stats', headers={'Authorization': f'Bearer {token}'})
    assert stats_res.status_code == 200
    users_res = client.get('/api/admin/users', headers={'Authorization': f'Bearer {token}'})
    assert users_res.status_code == 200
