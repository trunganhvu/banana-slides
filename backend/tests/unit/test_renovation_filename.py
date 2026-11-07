"""
 ASCII 

Bug: secure_filename()  ASCII 
  '.pdf' → 'pdf' .pdf 

:  'original.<ext>'
"""

import io
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


def _make_minimal_pdf() -> bytes:
    """ Test docstring """
    return b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
190
%%EOF"""


def _post_renovation(client, filename: str, pdf_bytes: bytes):
    """ Test docstring """
    return client.post(
        '/api/projects/renovation',
        data={
            'file': (io.BytesIO(pdf_bytes), filename, 'application/pdf'),
        },
        content_type='multipart/form-data',
    )


@pytest.fixture(autouse=True)
def mock_heavy_deps():
    """ Test docstring """
    mock_ai = MagicMock()
    mock_ai.extract_page_content.return_value = {
        'title': 'Test', 'points': [], 'description': ''
    }

    # Test verification logic
    mock_fitz = MagicMock()
    mock_doc = MagicMock()
    first_page = MagicMock()
    first_page.rect.width = 792
    first_page.rect.height = 612
    mock_doc.__len__ = MagicMock(return_value=1)
    mock_doc.__iter__ = MagicMock(return_value=iter([first_page]))
    mock_doc.__getitem__ = MagicMock(return_value=first_page)
    mock_doc.close = MagicMock()
    mock_fitz.open.return_value = mock_doc
    mock_fitz.Matrix.return_value = MagicMock()

    pix = MagicMock()
    first_page.get_pixmap.return_value = pix

    from PIL import Image as PILImage

    def fake_pix_save(path):
        img = PILImage.new('RGB', (1, 1), color='white')
        img.save(path, 'PNG')

    pix.save.side_effect = fake_pix_save

    with (
        patch('controllers.project_controller.get_ai_service', return_value=mock_ai),
        patch('controllers.project_controller.task_manager') as mock_tm,
        patch('controllers.project_controller.subprocess.run'),   # Test logic
        patch('services.file_parser_service.FileParserService', return_value=MagicMock()),
        patch.dict('sys.modules', {
            'fitz': mock_fitz,                                      # Test logic
        }),
    ):
        mock_tm.submit_task = MagicMock()
        yield mock_tm


class TestRenovationFilename:
    """ Test docstring """

    def test_chinese_filename_saved_as_original_pdf(self, client, app):
        """ Test docstring """
        pdf_bytes = _make_minimal_pdf()
        response = _post_renovation(client, '.pdf', pdf_bytes)

        assert response.status_code == 202, (
            f"Expected 202, got {response.status_code}: {response.get_json()}"
        )

        data = response.get_json()
        project_id = data['data']['project_id']

        upload_folder = app.config['UPLOAD_FOLDER']
        template_dir = Path(upload_folder) / project_id / 'template'

        # Test verification logic
        pdf_files = list(template_dir.glob('*.pdf'))
        assert pdf_files, (
            f"No .pdf file found in {template_dir}. "
            f"Files present: {list(template_dir.iterdir())}"
        )

        # Test verification logic
        assert pdf_files[0].name == 'original.pdf', (
            f"Expected 'original.pdf', got '{pdf_files[0].name}'"
        )

    def test_task_manager_can_discover_pdf(self, client, app):
        """ Test docstring """
        pdf_bytes = _make_minimal_pdf()
        response = _post_renovation(client, '.pdf', pdf_bytes)
        assert response.status_code == 202

        data = response.get_json()
        project_id = data['data']['project_id']

        upload_folder = app.config['UPLOAD_FOLDER']
        project_dir = Path(upload_folder) / project_id
        template_dir = project_dir / 'template'

        # Test verification logic
        pdf_path = None
        for f in template_dir.iterdir() if template_dir.exists() else []:
            if f.suffix.lower() == '.pdf':
                pdf_path = str(f)
                break

        assert pdf_path is not None, (
            "task_manager  PDF  — "
            f"template/ : {list(template_dir.iterdir())}"
        )

    def test_ascii_filename_also_works(self, client, app):
        """ Test docstring """
        pdf_bytes = _make_minimal_pdf()
        response = _post_renovation(client, 'presentation.pdf', pdf_bytes)
        assert response.status_code == 202

        data = response.get_json()
        project_id = data['data']['project_id']

        upload_folder = app.config['UPLOAD_FOLDER']
        template_dir = Path(upload_folder) / project_id / 'template'

        pdf_files = list(template_dir.glob('*.pdf'))
        assert pdf_files, "ASCII  .pdf "
        assert pdf_files[0].name == 'original.pdf'