"""
pytest - fixtures

fixtures
"""

import os
import sys
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Test verification logic
# Test verification logic
backend_path = Path(__file__).parent.parent
project_root = backend_path.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_path))

# Test verification logic
os.environ['TESTING'] = 'true'
os.environ['USE_MOCK_AI'] = 'true'  # Test logic
os.environ['GOOGLE_API_KEY'] = os.environ.get('GOOGLE_API_KEY', 'mock-api-key-for-testing')
os.environ['FLASK_ENV'] = 'testing'


@pytest.fixture(scope='session')
def app():
    """ Test docstring """
    # Test verification logic
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, 'test.db')
    
    # Test verification logic
    os.environ['DATABASE_PATH'] = temp_db
    os.environ.pop('DATABASE_URL', None)
    os.environ.pop('ACCESS_CODE', None)
    
    # Test verification logic
    from app import create_app
    
    # Test verification logic
    test_app = create_app()
    
    # Test verification logic
    test_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{temp_db}',
        'WTF_CSRF_ENABLED': False,
        'UPLOAD_FOLDER': temp_dir,
    })
    
    # Test verification logic
    with test_app.app_context():
        from models import db
        db.create_all()
    
    yield test_app
    
    # Test verification logic
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass


@pytest.fixture(scope='function')
def client(app):
    """ Test docstring """
    with app.test_client() as test_client:
        with app.app_context():
            from models import db
            # Test verification logic
            db.session.rollback()
            for table in reversed(db.metadata.sorted_tables):
                db.session.execute(table.delete())
            db.session.commit()
            yield test_client
            db.session.rollback()


@pytest.fixture(scope='function')
def db_session(app):
    """

     drop_allapp fixture  session 
     drop_all  client fixture 
     "no such table"
    """
    with app.app_context():
        from models import db
        db.create_all()
        yield db.session
        db.session.rollback()
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        db.session.remove()


@pytest.fixture
def sample_project(client):
    """ Test docstring """
    response = client.post('/api/projects', 
        json={
            'creation_type': 'idea',
            'idea_prompt': 'PPT'
        }
    )
    data = response.get_json()
    return data['data'] if data.get('success') else None


@pytest.fixture
def mock_ai_service():
    """ Test docstring """
    with patch('services.ai_service.AIService') as mock:
        # Test verification logic
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        
        # Test verification logic
        mock_instance.generate_outline.return_value = [
            {'title': '1', 'points': ['1', '2']},
            {'title': '2', 'points': ['3', '4']},
        ]
        
        # Test verification logic
        mock_instance.flatten_outline.return_value = [
            {'title': '1', 'points': ['1', '2']},
            {'title': '2', 'points': ['3', '4']},
        ]
        
        # Test verification logic
        mock_instance.generate_page_description.return_value = {
            'title': '',
            'text_content': ['1', '2'],
            'extra_fields': {'Bố cục & Trọng tâm': ''}
        }
        
        # Test verification logic
        from PIL import Image
        test_image = Image.new('RGB', (1920, 1080), color='blue')
        mock_instance.generate_image.return_value = test_image
        
        yield mock_instance


@pytest.fixture
def temp_upload_dir():
    """ Test docstring """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_image_file():
    """ Test docstring """
    # Test verification logic
    import io
    from PIL import Image
    
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes


# =====================================
# Test verification logic
# =====================================

def assert_success_response(response, status_code=200):
    """ Test docstring """
    assert response.status_code == status_code
    data = response.get_json()
    assert data is not None
    assert data.get('success') is True
    return data


def assert_error_response(response, expected_status=None):
    """ Test docstring """
    if expected_status:
        assert response.status_code == expected_status
    data = response.get_json()
    assert data is not None
    assert data.get('success') is False or 'error' in data
    return data