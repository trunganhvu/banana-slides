"""


PPTX
"""

import pytest
import time
import io
from pathlib import Path
from flask import current_app
from PIL import Image
from conftest import assert_success_response


class TestFullWorkflow:
    """ Test docstring """
    
    def test_create_project_and_get_details(self, client):
        """ Test docstring """
        # Test verification logic
        create_response = client.post('/api/projects', json={
            'creation_type': 'idea',
            'idea_prompt': 'PPT3'
        })
        
        data = assert_success_response(create_response, 201)
        project_id = data['data']['project_id']
        
        # Test verification logic
        get_response = client.get(f'/api/projects/{project_id}')
        
        data = assert_success_response(get_response)
        assert data['data']['project_id'] == project_id
        assert data['data']['status'] == 'DRAFT'
    
    def test_template_upload_workflow(self, client, sample_image_file):
        """ Test docstring """
        # Test verification logic
        create_response = client.post('/api/projects', json={
            'creation_type': 'idea',
            'idea_prompt': ''
        })
        
        data = assert_success_response(create_response, 201)
        project_id = data['data']['project_id']
        
        # Test verification logic
        upload_response = client.post(
            f'/api/projects/{project_id}/template',
            data={'template_image': (sample_image_file, 'template.png')},
            content_type='multipart/form-data'
        )
        
        # Test verification logic
        assert upload_response.status_code in [200, 201]

    def test_invalid_template_upload_is_rejected_and_does_not_replace_existing(self, client, sample_image_file):
        """ Test docstring """
        create_response = client.post('/api/projects', json={
            'creation_type': 'idea',
            'idea_prompt': ''
        })
        data = assert_success_response(create_response, 201)
        project_id = data['data']['project_id']

        upload_response = client.post(
            f'/api/projects/{project_id}/template',
            data={'template_image': (sample_image_file, 'template.png')},
            content_type='multipart/form-data'
        )
        assert_success_response(upload_response)

        template_path = Path(current_app.config['UPLOAD_FOLDER']) / project_id / 'template' / 'template.png'
        assert template_path.exists()

        invalid_response = client.post(
            f'/api/projects/{project_id}/template',
            data={'template_image': (io.BytesIO(b'<html>not an image</html>'), 'template.png')},
            content_type='multipart/form-data'
        )

        assert invalid_response.status_code == 400
        with Image.open(template_path) as image:
            assert image.size == (100, 100)

    def test_invalid_user_template_upload_is_rejected(self, client):
        """ Test docstring """
        response = client.post(
            '/api/user-templates',
            data={'template_image': (io.BytesIO(b'<html>not an image</html>'), 'template.png')},
            content_type='multipart/form-data'
        )

        assert response.status_code == 400
    
    def test_project_lifecycle(self, client):
        """ Test docstring """
        # Test verification logic
        create_response = client.post('/api/projects', json={
            'creation_type': 'idea',
            'idea_prompt': ''
        })
        data = assert_success_response(create_response, 201)
        project_id = data['data']['project_id']
        
        # Test verification logic
        get_response = client.get(f'/api/projects/{project_id}')
        assert_success_response(get_response)
        
        # Test verification logic
        # update_response = client.put(f'/api/projects/{project_id}', json={...})
        
        # Test verification logic
        delete_response = client.delete(f'/api/projects/{project_id}')
        assert_success_response(delete_response)
        
        # Test verification logic
        verify_response = client.get(f'/api/projects/{project_id}')
        assert verify_response.status_code == 404


class TestAPIErrorHandling:
    """ Test docstring """
    
    def test_invalid_json_body(self, client):
        """ Test docstring """
        response = client.post(
            '/api/projects',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code in [400, 415, 422]
    
    def test_missing_required_fields(self, client):
        """ Test docstring """
        response = client.post('/api/projects', json={})
        
        assert response.status_code in [400, 422]
    
    def test_method_not_allowed(self, client):
        """ Test docstring """
        response = client.patch('/api/projects')
        
        # Test verification logic
        assert response.status_code in [404, 405]


class TestConcurrentRequests:
    """ Test docstring """
    
    def test_multiple_project_creation(self, client):
        """ Test docstring """
        project_ids = []
        
        for i in range(3):
            response = client.post('/api/projects', json={
                'creation_type': 'idea',
                'idea_prompt': f' {i}'
            })
            
            data = assert_success_response(response, 201)
            project_ids.append(data['data']['project_id'])
        
        # Test verification logic
        assert len(set(project_ids)) == 3
        
        # Test verification logic
        for pid in project_ids:
            client.delete(f'/api/projects/{pid}')