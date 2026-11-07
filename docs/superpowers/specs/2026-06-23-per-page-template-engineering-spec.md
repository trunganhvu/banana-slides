# Config

> :2026-06-23  
>  PRD:`docs/superpowers/specs/2026-06-22-prd-per-page-template.md`  
> :`docs/superpowers/plans/2026-06-22-per-page-template-handoff.md`  
> :****, MVP/v2 PRD §14 (1-6)+ §3.2  7 

---

# Config

# Config

 PRD , v2 :

|  |  |  |
|------|------|------|
| (`project_template_assets`) | PRD §5 |  |
| (`pages`  5 ) | PRD §6 |  |
| TemplateSetupPage  | PRD §7 | ( 1) |
| PDF  | PRD §5.4 +  3 |  |
| AI ( + ) | PRD §5.3 +  4 |  |
| ( + ) | PRD §8/§9 +  5 |  |
| () | PRD §10 |  |
|  +  | PRD §11 |  |
| (↔) | PRD §3.2  7 |  |
|  | PRD §13 |  |
| (,) |  2 |  |
|  |  6 |  |

# Config

," + ":

- ****:`GET /api/templates`(`template_controller.py:98`),,
- **/**:`project_template_assets`  `version` , `analysis_json`  JSON ,schema  migration
- ****:`pages.template_selection_source` enum  `auto_v2 / hybrid` , `manual / auto / batch_apply`

---

# Config

# Config

```python
template_mode = db.Column(db.String(10), nullable=False, server_default='single', default='single')
# Config
```

# Config

```python
class ProjectTemplateAsset(db.Model):
    __tablename__ = 'project_template_assets'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    image_path = db.Column(db.String(500), nullable=False)        # 
    thumb_path = db.Column(db.String(500), nullable=True)         # ,
    file_size = db.Column(db.Integer, nullable=True)
    source = db.Column(db.String(20), nullable=False, default='upload')  # upload | pdf_split | system_preset
    source_pdf_id = db.Column(db.String(36), nullable=True)       # PDF  PDF task_id
    source_page_index = db.Column(db.Integer, nullable=True)      # PDF  PDF 

    analysis_status = db.Column(db.String(20), nullable=False, default='pending')  # pending|processing|completed|failed
    analysis_json = db.Column(db.Text, nullable=True)             # JSON ,9  schema(PRD §5.3)
    analysis_notes = db.Column(db.Text, nullable=True)            # AI 
    analysis_error = db.Column(db.Text, nullable=True)            # ( 2)
    user_label = db.Column(db.String(200), nullable=True)         # 
    user_edited_analysis = db.Column(db.Boolean, nullable=False, default=False)  # 

    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = db.relationship('Project', back_populates='template_assets')
    pages_referenced = db.relationship('Page', back_populates='template_asset', foreign_keys='Page.template_asset_id')
```

`Project.template_assets = db.relationship('ProjectTemplateAsset', back_populates='project', cascade='all, delete-orphan', order_by='ProjectTemplateAsset.sort_order')`

# Config

```python
template_asset_id = db.Column(db.String(36), db.ForeignKey('project_template_assets.id', ondelete='SET NULL'), nullable=True, index=True)
template_style_text = db.Column(db.Text, nullable=True)
template_selection_source = db.Column(db.String(20), nullable=True)  # manual | auto | batch_apply
template_match_reason = db.Column(db.Text, nullable=True)
template_match_confidence = db.Column(db.Float, nullable=True)
```

 `ondelete='SET NULL'`  PRD §11""

### 2.4 Alembic migration

:`backend/migrations/versions/2026_06_23_add_per_page_template.py`

upgrade :
1.  `projects.template_mode` 
2.  `project_template_assets` 
3.  `pages` 5 
4. **Backfill**:, `projects.template_image_path` / `template_style` :
   -  `template_image_path`  ****: `project_template_assets` (source='upload', analysis_status='pending', image_path ,thumb_path ), `template_asset_id` 
   -  `template_image_path` : asset , warning log,( setup )
   -  `template_style` : `template_style_text` 
   - `template_mode`  `'single'`(——)

downgrade ()

# Config

- , `template_asset_id` `template_style_text` ——/; DB  trigger
- "":`template_asset_id IS NULL AND (template_style_text IS NULL OR template_style_text = '')`
- (PRD §4): `SlidePreview` , DB  check

---

## 3. API Schema

# Config

 `template_assets_bp = Blueprint('template_assets', __name__, url_prefix='/api/projects')`, `template_controller.py` , `template_bp` ("",, 7 )

# Config

**`GET /api/projects/:projectId/template-assets`** — 
```json
// Response
{ "assets": [
  { "id": "...", "image_url": "/files/...", "thumb_url": "/files/...",
    "analysis_status": "completed", "analysis_json": {...}, "analysis_notes": "...",
    "user_label": "", "source": "upload", "sort_order": 0,
    "referenced_page_ids": ["p1", "p2"] }
]}
```

**`POST /api/projects/:projectId/template-assets`** — 
```
Content-Type: multipart/form-data
Form: image=@file.png, user_label=()
```
- : +  +  `project_template_assets` (`analysis_status='pending'`)
- : `analyze_template_task`( 4),
- Response:`{ "asset": {...}, "analyze_task_id": "..." }`
-  query  `bind_to_page=:pageId`( PRD §10.3 "")

**`POST /api/projects/:projectId/template-assets/upload-pdf`** —  PDF ( 3)
```
Content-Type: multipart/form-data
Form: pdf=@file.pdf
```
- : PDF  `uploads/:projectId/template-pdf/:taskId.pdf`, `Task(task_type='SPLIT_TEMPLATE_PDF')`
- :`process_pdf_to_template_images_task`  →  `project_template_assets`(`source='pdf_split'`, `source_pdf_id` / `source_page_index` )→ 
- Response:`{ "task_id": "..." }`, `GET /api/tasks/:taskId` (progress  `total/completed/failed`)
- : ≤ 50, `bad_request`

**`PATCH /api/projects/:projectId/template-assets/:assetId`** — ( / )
```json
// Request
{ "user_label": "",
  "analysis_json": { ... 9 ... },
  "analysis_notes": "..." }
```
- ;`analysis_json` , `user_edited_analysis=true`
-  `analysis_status`()

**`DELETE /api/projects/:projectId/template-assets/:assetId`** — 
- ( + )
- DB  `ON DELETE SET NULL`  `template_asset_id`
-  `template_selection_source`  `NULL`, PRD §11""
- Response:`{ "deleted": true, "cleared_page_ids": ["p1", "p2"] }`( toast )

**`POST /api/projects/:projectId/template-assets/:assetId/reanalyze`** — ( 2)
-  `analyze_template_task`, `analysis_status`  `pending`
- Response:`{ "analyze_task_id": "..." }`

# Config

**`PATCH /api/projects/:projectId/pages/:pageId/template`** — 
```json
// Request
{ "template_asset_id": "..." | null,
  "template_style_text": "..." | null,
  "selection_source": "manual" }  //  manual
```
- ; null ""
- :`pageId`  `projectId`;`template_asset_id` 
- ""(), SlidePreview  PRD §4 
- Response:`{ "page": { ...page.to_dict()... } }`

**`PATCH /api/projects/:projectId/template-mode`** — ( 7,JSON )
```json
// Logic
{ "mode": "multi" }

// Logic
{ "mode": "single",
  "unified_asset_id": "..." | null,    //  asset_id  style_text 
  "unified_style_text": "..." | null }
```
- →: `projects.template_mode='multi'`,
- →: `unified_asset_id` / `unified_style_text` ****, `template_mode='single'`;( `update().where(Page.project_id==pid)`)
- :`unified_asset_id` ; `bad_request`

**`POST /api/projects/:projectId/template-mode/single-with-upload`** — → + (multipart )
```
Content-Type: multipart/form-data
Form: image=@file.png, unified_style_text=...()
```
-  asset( §3.2 ),, `template_mode='single'`,
- Response:`{ "asset": {...}, "project": {...} }`

**`POST /api/projects/:projectId/template-assets/auto-match`** — ( 5)
```json
// Request
{ "overwrite_existing": true,        //  true, PRD §8.4 
  "preserve_non_empty": false }      // "" true
```
- :(PRD §8.3), `{ "error": "missing_descriptions", "missing_page_ids": [...] }`
-  `auto_match_templates_task`,Response:`{ "task_id": "..." }`
- : 5 —— ≤ 50  ≤ 20 , 30 
- , `template_asset_id` / `template_match_reason` / `template_match_confidence` / `template_selection_source='auto'` 

**`POST /api/projects/:projectId/pages/:pageId/template/auto-match`** — (PRD §9)
- :; `analysis_status='completed'`  asset  `{ "error": "no_analyzed_templates" }`
- ,Response:`{ "task_id": "..." }`(,)

# Config

 `GET /api/tasks/:taskId`(`task_manager.py`),3 (`SPLIT_TEMPLATE_PDF` / `ANALYZE_TEMPLATE` / `AUTO_MATCH_TEMPLATES`) `progress` JSON :
```json
// Logic
{ "total": 12, "completed": 8, "failed": 0, "created_asset_ids": ["..."] }
// Logic
{ "asset_id": "...", "stage": "calling_ai" | "parsing_json" | "done" | "failed" }
// Logic
{ "total_pages": 30, "matched": 25, "undecided": 5, "batch_index": 1, "batch_total": 1 }
```
:`SPLIT_TEMPLATE_PDF` / `AUTO_MATCH_TEMPLATES` ;`ANALYZE_TEMPLATE`  chip (pending/processing/completed/failed)

---

# Config

# Config

 `UPLOAD_FOLDER`( `FileService` ):

```
uploads/
  :projectId/
    template/                    # :( 7 )
      template.png
    template-assets/             # :
      :assetId/
        original.png             # ()
        thumb.jpg                # , 480px,JPEG q85
    template-pdf/                # PDF  PDF
      :taskId.pdf                #  PDF, 7 
      :taskId/                   #  PNG, template-assets/ 
        page_1.png ...
    pages/...                    # 
    materials/...                # 
```

URL  `/files/:projectId/...`, `file_controller.py:14-47` `template-assets/:assetId/original.png`  `thumb.jpg`  `file_controller` ( `template/`)

# Config

 `backend/services/file_service.py`( `save_user_template_thumbnail`  Pillow , file_service.py:209-243):

```python
def save_template_asset(self, file, project_id: str, asset_id: str) -> tuple[str, str]:
    """ + , (image_path, thumb_path) PIL verify """

def save_template_asset_from_path(self, src_path: str, project_id: str, asset_id: str) -> tuple[str, str]:
    """(PDF ), (image_path, thumb_path)"""

def delete_template_asset(self, project_id: str, asset_id: str) -> None:
    """ template-assets/:assetId/ """

def save_template_pdf(self, file, project_id: str, task_id: str) -> str:
    """ PDF,"""

def cleanup_template_pdf_temp(self, project_id: str, task_id: str) -> None:
    """ PDF  PNG ( PDF)"""
```

# Config

-  asset:
-  project:cascade  ORM , `cleanup_project_files()`()
- PDF : `:taskId/` ; PDF  7 (""),(,, TODO )
- :`thumb_url`  null  fallback  `image_url`( store )

---

# Config

# Config

** `backend/services/pdf_image_service.py`:**

```python
import fitz
from pathlib import Path

def pdf_to_page_images(pdf_path: str, output_dir: str, dpi: int = 150,
                       max_pages: int = 50) -> list[dict]:
    """
     PDF  PNG, [{"index": 1, "path": "..."}], path=None  index
     max_pages  ValueError( controller  bad_request)
    """
    doc = fitz.open(pdf_path)
    if len(doc) > max_pages:
        raise ValueError(f"PDF too long: {len(doc)} pages, max {max_pages}")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    for i, page in enumerate(doc):
        out_path = Path(output_dir) / f"page_{i+1}.png"
        try:
            pix = page.get_pixmap(matrix=matrix)
            pix.save(str(out_path))
            results.append({"index": i + 1, "path": str(out_path)})
        except Exception as e:
            logger.warning(f"PDF page {i+1} render failed: {e}")
            results.append({"index": i + 1, "path": None, "error": str(e)})
    doc.close()
    return results
```

:`backend/controllers/project_controller.py`  `fitz.open() + page.get_pixmap()` 

# Config

** `backend/services/prompts.py`:**

#### 5.2.1 `get_template_analysis_prompt(language: str = 'zh') -> str`

 prompts.py (), `get_outline_generation_prompt`(L280)——markdown JSON ,3  `generate_json()` 

:
-  2-3 (few-shot)," /  / " layout
- 9  schema (PRD §5.3),`text_regions[]` / `image_regions[]`  array of objects
- `notes` "AI ",
- : slide, `{"error": "not_a_slide"}`, `analysis_status='failed'`

#### 5.2.2 `get_template_auto_match_prompt(templates: list[dict], pages: list[dict], language: str) -> str`

( 5 ):
- :`{ page_id, order_index, title, summary[≤100], content_density: 'low'|'medium'|'high' }`
  - `content_density`  controller ,: `len(page.description)` ——`<200`  low200-600 medium`>600` high()
- :`{ asset_id, user_label, layout_structure, content_capacity, visual_density, style_keywords[≤5], notes[≤200] }`
-  schema  PRD §8.2(, `page_id / template_asset_id / status / confidence / reason`)
- prompt " asset_id"
- `status` enum: `matched | undecided`(`undecided`  `template_asset_id=null`, PRD §8.4)

# Config

**`backend/services/ai_service.py`:**

```python
def analyze_template(self, image_path: str, language: str = 'zh') -> dict:
    """
     generate_with_image + JSON 
     self.generate_json  3 (L202-232),
     9  dict(PRD §5.3 schema) {"error": "not_a_slide"}
    """

def auto_match_templates(self, project_id: str, language: str = 'zh',
                         overwrite_existing: bool = True,
                         preserve_non_empty: bool = False) -> list[dict]:
    """
    : 5 
    -  ProjectTemplateAsset( analysis_status != 'completed' , 2)
    -  Page(, controller)
    -  len(pages)<=50 and len(templates)<=20:
    - : 30 ,batch 
     [{"page_id", "template_asset_id"|None, "status", "confidence", "reason"}]
    """
```

# Config

**`backend/services/task_manager.py`  3  task type :**

| Task Type |  |  |  |
|-----------|--------|--------|------|
| `SPLIT_TEMPLATE_PDF` | `POST .../template-assets/upload-pdf` | `image_resource_limiter` |  `pdf_to_page_images` →  `save_template_asset_from_path` →  asset  →  `ANALYZE_TEMPLATE`  |
| `ANALYZE_TEMPLATE` | // reanalyze | `text_resource_limiter` |  `ai_service.analyze_template`, `analysis_json` / `analysis_notes` / `analysis_status` |
| `AUTO_MATCH_TEMPLATES` | `POST .../template-assets/auto-match` | `text_resource_limiter` |  `ai_service.auto_match_templates`, pages |

: `_commit_with_retry`(`task_manager.py:261-273`), JSON  failed +1 

:
-  PDF  N  `ANALYZE_TEMPLATE`  `text_resource_limiter` ( `generate_descriptions_task` )
- `AUTO_MATCH_TEMPLATES` (,controller  `Task.query.filter_by(project_id, task_type, status='PROCESSING').first()` )

---

# Config

# Config

:`backend/services/task_manager.py:645-668`( `use_template` ), `prompts.py:815-860`  `generate_image_prompt`

# Config

 `use_template = bool(project.template_image_path)` ,:

```python
# Config
def resolve_page_template(page: Page, project: Project) -> tuple[str | None, str | None]:
    """ (image_path_for_ref, style_text)"""
    image_path = None
    style_text = None

    # Config
    if page.template_asset_id:
        asset = page.template_asset  # relationship
        if asset:
            image_path = file_service.resolve_template_asset_path(asset)

    # Config
    if page.template_style_text:
        style_text = page.template_style_text

    # Config
    # Config
    # Config
    if image_path is None and project.template_image_path:
        image_path = file_service.get_template_path(project.id)
    if style_text is None and project.template_style:
        style_text = project.template_style

    return image_path, style_text
```

# Config

`generate_image_prompt`  `has_template: bool`,:
```python
def generate_image_prompt(..., has_template_image: bool, page_style_text: str | None, ...) -> str:
    # Config
    # Config
```

:`task_manager.py`  `generate_image_prompt`  `resolve_page_template(page, project)`  (image_path, style_text),

# Config

`generate_single_page_image_task`(),"" `template_asset_id`  7 ""——,

# Config

- :migration backfill ,
- : `PATCH .../template-mode` ,
-  `task_manager.py` ,

---

# Config

# Config

`frontend/src/App.tsx` ( 1 +  6):

```
/                                     Home
/project/:projectId/outline           OutlineEditor
/project/:projectId/detail            DetailEditor
/project/:projectId/template-setup    TemplateSetupPage(,)
/project/:projectId/preview           SlidePreview
```

**`Home.initializeProject` **: `templateMode`  single  multi, `navigate(/project/:id/outline)`—— outline / detail (PRD §2 )

**`DetailEditor` ""**( 1 /  6 ):
```ts
project.template_mode === 'multi'
  ? navigate(`/project/${id}/template-setup`)
  : navigate(`/project/${id}/preview`)
```

**`TemplateSetupPage` **( 6 ): `project.template_mode === 'single'`, mount  `navigate('/preview', { replace: true })`, URL 

### 7.2 Store(`frontend/src/store/useProjectStore.ts`)

# Config

 4  key( §4.3), API:

|  key |  |
|--------|---------|
| `template_mode_${projectId}` | `project.template_mode`() |
| `template_assets_${projectId}` | `GET /api/projects/:id/template-assets` |
| `page_template_assign_${projectId}` | `page.template_asset_id` / `template_style_text`( page.to_dict) |
| `page_fine_tune_drawer_width` |  localStorage( UI ,) |

:Store  localStorage key,(`removeItem`),—— §3 " demo "

# Config

```ts
// Logic
loadTemplateAssets(projectId): Promise<TemplateAsset[]>
uploadTemplateAsset(projectId, file, opts?: { bindToPageId?: string }): Promise<TemplateAsset>
uploadTemplatePdf(projectId, file): Promise<{ taskId: string }>
updateTemplateAsset(projectId, assetId, patch): Promise<TemplateAsset>
deleteTemplateAsset(projectId, assetId): Promise<{ clearedPageIds: string[] }>
reanalyzeTemplateAsset(projectId, assetId): Promise<{ taskId: string }>

// Logic
updatePageTemplate(projectId, pageId, patch): Promise<Page>

// Logic
switchTemplateMode(projectId, payload: SwitchModePayload): Promise<Project>
// SwitchModePayload:
//   { mode: 'multi' }
//   | { mode: 'single', unifiedAssetId?: string, unifiedStyleText?: string }
// Logic

// Logic
autoMatchAll(projectId, opts): Promise<{ taskId: string }>
autoMatchPage(projectId, pageId): Promise<{ taskId: string }>
```

# Config

- : `/api/tasks/:taskId`, asset(`loadTemplateAssets`  in-place )
- : `loadProject(projectId)`  page
- :, `clearedPageIds`  page 

# Config

`feat/per-page-template` ,:

```ts
export interface TemplateAsset {
  id: string;
  image_url: string;
  thumb_url: string | null;
  analysis_status: 'pending' | 'processing' | 'completed' | 'failed';
  analysis_json: TemplateAnalysis | null;
  analysis_notes: string | null;
  analysis_error: string | null;
  user_label: string | null;
  user_edited_analysis: boolean;
  source: 'upload' | 'pdf_split' | 'system_preset';
  sort_order: number;
  referenced_page_ids: string[];
}

export interface TemplateAnalysis {
  summary: string;
  template_type: string;
  layout_structure: string;
  content_capacity: 'low' | 'medium' | 'high';
  text_regions: Array<{ role: string; count: number }>;
  image_regions: Array<{ role: string; count: number }>;
  visual_density: 'low' | 'medium' | 'high';
  style_keywords: string[];
  notes: string;
}

// Logic
template_mode: 'single' | 'multi';

// Logic
template_asset_id: string | null;
template_style_text: string | null;
template_selection_source: 'manual' | 'auto' | 'batch_apply' | null;
template_match_reason: string | null;
template_match_confidence: number | null;
```

# Config

# Config

:
- :(`` , DetailEditor "")+ `` 
- :****—— TemplateAsset 
  -  / (inline )/  / ( 9 )
  - :`` / ``()
  - :`` + ` PDF` ,PDF 
- :****——,
  -  +  +  chip
  - ()/ ()/  chip
  - :``()/ `` / ``
- : disabled + tooltip(PRD §8.3)

# Config

 `feat/per-page-template` "/", `initializeProject`  API:
- :(`POST /api/projects`  `template_mode='single'` + `template_image_path` / `template_style`)→  `project_template_assets`,** pages **——:
  1. ** pages **: `task_manager`  outline  commit pages , `project.template_mode='single'`  asset  style_text 
  2. ****: `PATCH /template-mode`(,""),
- :(`template_mode='multi'`,)→  outline, TemplateSetupPage 

# Config

"":
-  `single`: `` , `switchTemplateMode({ mode: 'multi' })` → `template-setup`
-  `multi`:","

# Config

 `feat/per-page-template` ""(`PageFineTuneDrawer.tsx`),:
-  localStorage  store
- :"",( 6 )
- : +  + 
-  `project.template_mode` :
  - `single`  ``, `switchTemplateMode({ mode: 'multi' })` →  SlidePreview( template-setup)
  - `multi`  ``, `SwitchToSingleModeDialog`
- →"": + `` +  textarea,:
  -  asset /  → `PATCH /template-mode`(JSON )
  -  → `POST /template-mode/single-with-upload`(multipart )

# Config

- `TemplatePickerModal.tsx`:(PRD §10.2),"", `updatePageTemplate`
- `TemplateAnalysisEditor.tsx`:9 , TemplateSetupPage ; + 
- `SwitchToSingleModeDialog.tsx`:→
- `TemplateMatchProgress.tsx`:

### 7.5 i18n

(CLAUDE.md "Component-level `useT()` hook with inline zh/en translations"), inline, i18n 

---

# Config

# Config

 pytest ,:

**`test_template_assets_api.py`**
- POST/GET/PATCH/DELETE asset  CRUD
-  `analysis_status='pending'`, `completed`
- DELETE  NULL(`SET NULL` )
- (asset belongs to other project)

**`test_template_pdf_split.py`**
-  PDF ( fixture  3  PDF)
-  N  asset  + 
-  50  400
- (`failed` )

**`test_template_analysis.py`**
- Mock `ai_service.analyze_template`  9 ,
- AI  `{"error": "not_a_slide"}`  `analysis_status='failed'` + `analysis_error` 
-  status  pending

**`test_template_auto_match.py`**
- Mock LLM ,
- `preserve_non_empty=true`  asset_id 
- `undecided`  NULL(PRD §8.4)
-  missing_descriptions 
- :51 ,

**`test_template_mode_switch.py`**
- →: mode ,
- → + `unified_asset_id`:,()
- → + `unified_upload`:multipart  asset 
-  `generated_image_url` ( 7)

**`test_image_generation_template_priority.py`**()
-  3 ,page1  asset,page2  style_text,page3 ( fallback)
- ,** AI provider**( CLAUDE.md "")
-  prompt  ref_image ( task_manager  log  provider mock  prompt)

# Config

- `TemplatePickerModal`: asset"" input
- `TemplateAnalysisEditor`:9  `updateTemplateAsset`
- `SwitchToSingleModeDialog`:
- `useProjectStore`: / asset  /  action 

### 8.3 E2E(Playwright,`frontend/e2e/`)

 `e2e/helpers/seed-project.ts` ,:

**`template-mode-creation.spec.ts`(mock + , CLAUDE.md)**
- Home  → outline → detail → preview, preview 
- Home  → outline → detail → template-setup →  2  →  → preview,

**`template-pdf-split.spec.ts`**
-  3  PDF →  →  3  →  analysis  completed

**`template-auto-match.spec.ts`**
- , ≥2  →  →  →  asset_id  undecided  →  reason/confidence 

**`template-delete-cascade.spec.ts`**
- , 1  N  →  → "" → toast  → 

**`template-mode-switch.spec.ts`( 7 )**
- →:DetailEditor "" →  template-setup → 
- →:SlidePreview "" →  →  → 
- →: page1 ,,page1 

**`template-fine-tune-drawer.spec.ts`( `fine-tune-drawer.spec.ts`)**
- 
- ,//

**`template-route-guard.spec.ts`( 6 )**
-  `/project/:id/template-setup`, `replace`  `/preview`, `template-setup` ( detail, template-setup)
-  `/template-setup` ,

# Config

 AI ():
1.  3 
2.  2 ()
3. ( LLM )
4. ( API )
5. :

---

# Config

,,:

# Config
1.  `feat/per-page-template-v2`( `main`, `feat/per-page-template`)
2.  SQLAlchemy model:`ProjectTemplateAsset` + `Project.template_mode` + `Page` 5 
3.  Alembic migration  backfill
4.  model ( to_dictrelationship )

# Config
5. `FileService`  + `file_controller` 
6.  `pdf_image_service.py`
7. `test_template_pdf_split.py` ( AI)

# Config
8. `template_controller.py`  endpoints( §3.2 / §3.3 )
9. `task_manager`  `SPLIT_TEMPLATE_PDF` task type
10. `test_template_assets_api.py` + `test_template_mode_switch.py` 

# Config
11. `prompts.py`  prompt
12. `ai_service.py`  `analyze_template` / `auto_match_templates`
13. `task_manager`  `ANALYZE_TEMPLATE` / `AUTO_MATCH_TEMPLATES` task type
14. `test_template_analysis.py` + `test_template_auto_match.py` (LLM  mock)

# Config
15. `resolve_page_template`  + `task_manager:645-668` 
16. `generate_image_prompt` 
17. `test_image_generation_template_priority.py` (** AI**)

# Config
18.  +  + store 
19.  `TemplateSetupPage` + 4 
20.  `Home` / `DetailEditor` / `SlidePreview`
21.  store
22.  Vitest 

# Config
23. 6  Playwright 
24. 
25. (`docs/zh/` + README )

# Config
26.  commit: /  / Asset API / AI /  /  / E2E / 
27.  PR, Gemini review, inline comments
28.  worktree() `feat/per-page-template` 

**:9.5 **

# Config

- PDF  OOM:DPI  150,
- LLM : 2 , >30%  prompt(`prompts.py` )
- :→ N+1, `update().where(Page.project_id == ...)`  SQL
-  `feat/per-page-template` ,,

# Config

- ( `GET /api/templates` )
- /(`analysis_json`  JSON  schema )
- Embedding ( 5 ,N>20 )
- (`UserTemplate` ,)
- " LLM "( 5 )



