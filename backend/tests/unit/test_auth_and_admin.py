"""
Unit tests for Google SSO, user model, project isolation, and admin metrics.
"""
import pytest
from app import create_app
from models import db, User, Project
from utils.auth_middleware import generate_token, decode_token


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
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
        token = generate_token('u123', 'vutrunganh1@gmail.com', 'admin')
        payload = decode_token(token)
        assert payload is not None
        assert payload['user_id'] == 'u123'
        assert payload['email'] == 'vutrunganh1@gmail.com'
        assert payload['role'] == 'admin'


def test_dev_login_and_admin_assignment(client, app):
    with app.app_context():
        # Create unassigned project
        p = Project(creation_type='idea', project_title='Legacy Project')
        db.session.add(p)
        db.session.commit()
        assert p.user_id is None

    # Dev login with admin email
    res = client.post('/api/auth/dev-login', json={'email': 'vutrunganh1@gmail.com', 'name': 'Trung Anh'})
    assert res.status_code == 200
    data = res.get_json()['data']
    assert data['user']['role'] == 'admin'
    assert data['user']['email'] == 'vutrunganh1@gmail.com'
    token = data['token']

    # Verify unassigned project was assigned to this admin
    with app.app_context():
        updated_p = Project.query.filter_by(project_title='Legacy Project').first()
        assert updated_p.user_id == data['user']['id']

    # Test /api/auth/me
    me_res = client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert me_res.status_code == 200
    assert me_res.get_json()['data']['user']['email'] == 'vutrunganh1@gmail.com'


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
    assert p1_res.status_code == 200

    # User 2 creates project
    p2_res = client.post('/api/projects', headers={'Authorization': f'Bearer {t2}'}, json={
        'creation_type': 'idea',
        'idea_prompt': 'Idea from User 2'
    })
    assert p2_res.status_code == 200

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
    admin_res = client.post('/api/auth/dev-login', json={'email': 'vutrunganh1@gmail.com', 'name': 'Admin'})
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
    assert 'vutrunganh1@gmail.com' in emails
    assert 'member@example.com' in emails
