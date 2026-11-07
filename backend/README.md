# Banana Slides Backend

Banana Slides (Banana Slides)  - AIPPT

# Backend logic

- ****: Flask 3.0
- ****: SQLite + SQLAlchemy ORM
- **AI**: Google Gemini API
- **PPT**: python-pptx
- ****: ThreadPoolExecutor
- ****: uv

# Backend logic

```
backend/
├── app.py                    # Backend logic
├── config.py                 # Backend logic
├── models/                   # Backend logic
│   ├── __init__.py
│   ├── project.py           # Backend logic
│   ├── page.py              # Backend logic
│   └── task.py              # Backend logic
├── services/                 # Backend logic
│   ├── __init__.py
│   ├── ai_service.py        # Backend logic
│   ├── file_service.py      # Backend logic
│   ├── export_service.py    # Backend logic
│   └── task_manager.py      # Backend logic
├── controllers/              # Backend logic
│   ├── __init__.py
│   ├── project_controller.py
│   ├── page_controller.py
│   ├── template_controller.py
│   ├── export_controller.py
│   └── file_controller.py
├── utils/                    # Backend logic
│   ├── __init__.py
│   ├── response.py          # Backend logic
│   └── validators.py        # Backend logic
├── instance/                 # Backend logic
├── uploads/                  # Backend logic
├── .env.example             # Backend logic
└── README.md                # Backend logic
```

# Backend logic

# Backend logic

 [uv](https://github.com/astral-sh/uv)  Python .  `pyproject.toml` . 

: 
```bash
uv sync
```

. 

# Backend logic

 `.env.example`  `.env` : 

```bash
cp .env.example .env
```

 `.env` : 

```env
GOOGLE_API_KEY=your-google-api-key
GOOGLE_API_BASE=https://generativelanguage.googleapis.com

# Backend logic
VOLCENGINE_ACCESS_KEY=your-volcengine-access-key
VOLCENGINE_SECRET_KEY=your-volcengine-secret-key
VOLCENGINE_INPAINTING_TIMEOUT=60
VOLCENGINE_INPAINTING_MAX_RETRIES=3
```

# Backend logic

,  Alembic . 

```bash
cd backend
uv run alembic upgrade head
```

> :   
> -  `alembic_version` ;   
> - ,  `models/`,  `alembic revision --autogenerate` ,  `alembic upgrade head`. 

# Backend logic

 uv : 
```bash
cd backend
uv run python app.py
```
 `http://localhost:5011` . 

# Backend logic

API `API.md`. 

# Backend logic

# Backend logic
- `POST /api/projects` - 
- `GET /api/projects/{project_id}` - 
- `PUT /api/projects/{project_id}` - 
- `DELETE /api/projects/{project_id}` - 

# Backend logic
- `POST /api/projects/{project_id}/generate/outline` - 

# Backend logic
- `POST /api/projects/{project_id}/generate/descriptions` -  () 
- `POST /api/projects/{project_id}/pages/{page_id}/generate/description` - 

# Backend logic
- `POST /api/projects/{project_id}/generate/images` -  () 
- `POST /api/projects/{project_id}/pages/{page_id}/generate/image` - 
- `POST /api/projects/{project_id}/pages/{page_id}/edit/image` - 

# Backend logic
- `POST /api/projects/{project_id}/template` - 
- `DELETE /api/projects/{project_id}/template` - 

# Backend logic
- `GET /api/projects/{project_id}/export/pptx` - PPTX
- `GET /api/projects/{project_id}/export/pdf` - PDF

# Backend logic
- `GET /files/{project_id}/{type}/{filename}` - 

# Backend logic

# Backend logic

 Google Gemini API, : 
- PPT
- 
- 
- 

# Backend logic

 `ThreadPoolExecutor` : 
- 
- 
- 

# Backend logic

: 
- 
- 
- 
- 

# Backend logic

 Inpainting , : 
-  (bbox) 
- 
-  (, ) 
- 

: 
```python
from services.inpainting_service import InpaintingService, remove_regions
from PIL import Image

# Backend logic
service = InpaintingService()
image = Image.open('original.png')
bboxes = [(100, 100, 200, 200), (300, 150, 400, 250)]  # Backend logic
result = service.remove_regions_by_bboxes(image, bboxes)

# Backend logic
result = remove_regions(image, bboxes, expand_pixels=5)
```

# Backend logic

 SQLite + SQLAlchemy: 
- , 
- 
- 

# Backend logic

# Backend logic

# Backend logic
- 
- 
- 
- 

# Backend logic
- 
-  (JSON) 
-  (JSON) 
- 
- 

# Backend logic
-  (/) 
- 
-  (JSON) 
- 

# Backend logic

# Backend logic
```
DRAFT → OUTLINE_GENERATED → DESCRIPTIONS_GENERATED → GENERATING_IMAGES → COMPLETED
```

# Backend logic
```
DRAFT → DESCRIPTION_GENERATED → GENERATING → COMPLETED | FAILED
```

# Backend logic
```
PENDING → PROCESSING → COMPLETED | FAILED
```

# Backend logic

# Backend logic

 `services/ai_service.py` : 

```python
class AIService:
    def __init__(self, api_key: str, model_type: str = 'gemini'):
        if model_type == 'gemini':
            # Gemini implementation
        elif model_type == 'openai':
            # OpenAI implementation
        # ...
```

# Backend logic

 `services/ai_service.py` : 

```python
def generate_image_prompt(self, ...):
    prompt = dedent(f"""
        # Backend logic
        ...
    """)
    return prompt
```

# Backend logic

 `services/export_service.py` : 

```python
class ExportService:
    @staticmethod
    def create_custom_format(image_paths, output_file):
        # Backend logic
        pass
```


# Backend logic

# Backend logic

```bash
curl http://localhost:5011/health
```

# Backend logic

```bash
curl -X POST http://localhost:5011/api/projects \
  -H "Content-Type: application/json" \
  -d '{"creation_type":"idea","idea_prompt":"ppt"}'
```

# Backend logic

```bash
curl -X POST http://localhost:5011/api/projects/{project_id}/template \
  -F "template_image=@template.png"
```

# Backend logic

```bash
curl -X POST http://localhost:5011/api/projects/{project_id}/generate/outline \
  -H "Content-Type: application/json" \
  -d '{"idea_prompt":"ppt"}'
```

# Backend logic

# Backend logic
A:  `backend/instance/database.db`, . 

# Backend logic
A:  `uploads/{project_id}/` , . 

# Backend logic
A:  ( `.env` ) ;  `.env`  `MAX_DESCRIPTION_WORKERS`  `MAX_IMAGE_WORKERS` , "" DB. 

# Backend logic
A: , "":   
-  / API Base / API Key  
-  (`TEXT_MODEL`) /  (`IMAGE_MODEL`)  
- MinerU  (`MINERU_API_BASE`) /  (`IMAGE_CAPTION_MODEL`)  

 `settings`  `.env` , "" `.env` . 

# Backend logic
A: PNG, JPG, JPEG, GIF, WEBP.  `config.py`  `ALLOWED_EXTENSIONS` . 


# Backend logic

 **Noto Sans CJK SC** () ,  PPT . 

- ****: `fonts/NotoSansSC-Regular.ttf`
- ****: [Google Noto CJK Fonts](https://github.com/googlefonts/noto-cjk)
- ****: [SIL Open Font License 1.1 (OFL)](https://scripts.sil.org/OFL)

OFL , . 

# Backend logic

,  GitHub Issues . 