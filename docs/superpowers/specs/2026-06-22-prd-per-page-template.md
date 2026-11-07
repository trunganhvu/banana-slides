# Config

> 2026-03-22 ~ 03-23 Codex session 

---

# Config

""****""

# Config

- ****
- **AI **AI  AI 

---

# Config

```
Home → OutlineEditor → DetailEditor → TemplateSetupPage → SlidePreview
```

- `Home` / 
- `OutlineEditor`
- `DetailEditor`
- **`TemplateSetupPage`** + 
- `SlidePreview`

# Config

- DetailEditor 
- AI 
- ""

---

# Config

# Config

|  |  |
|------|------|
| **** |  +  |
| **** |  +  |

****" `template_asset_id` + `template_style_text`"****—— UI hint

# Config

>  PRD" → "

****
- A)  PRD→→
- B) →→→
- C) →"" UI hint
- D) →
- E) → UI 

**C**

****
-  C PRD  1 ""
-  A""UI 
-  B C """ `template_image_path`"
-  D""
-  EUI """ UI hint"

****
- 
- ** → ** `template_mode = 'multi'`
- ** → **"" /  →  →  `template_asset_id`  `template_style_text` → `template_mode = 'single'`
- **** `generated_image_url` 

****
- `DetailEditor` / `SlidePreview`  `` 
- `TemplateSetupPage` / `SlidePreview`  `` 

**** `projects.template_mode`  UI  `pages.template_asset_id` / `pages.template_style_text` 

# Config

""""
-  = 
-  = 
-  = 

---

# Config



|  |  |
|------|------|
|  | `template_asset_id` |
|  | `template_style_text` |

# Config

1. 
2. 
3.  + 

****

# Config

- ****SlidePreview

---

# Config

# Config

|  |  |  |
|------|------|------|
| `id` | string |  |
| `project_id` | string |  |
| `image_path` | string |  |
| `thumb_path` | string |  |
| `analysis_status` | enum | `pending / processing / completed / failed` |
| `analysis_json` | json |  5.3 |
| `analysis_notes` | string | AI  |
| `user_label` | string | """""" |
| `sort_order` | int |  |
| `created_at` | datetime |  |

# Config

- 
- **** 1:1 
- 

# Config

 AI  JSON

```json
{
  "summary": " +  + ",
  "template_type": "content",
  "layout_structure": "title-top-two-column",
  "content_capacity": "medium",
  "text_regions": [
    { "role": "title", "count": 1 },
    { "role": "body", "count": 2 }
  ],
  "image_regions": [
    { "role": "illustration", "count": 1 }
  ],
  "visual_density": "medium",
  "style_keywords": ["academic", "clean", "blue"],
  "notes": " logo "
}
```

- 
- `notes`  AI 
- ** TemplateSetupPage **

# Config

1. ****
2. ** PDF ** PDF 

# Config

- `````A/B ``` 
-  AI 
-  TemplateSetupPage 

---

# Config

 `pages` 

|  |  |  |
|------|------|------|
| `template_asset_id` | string / null |  |
| `template_style_text` | string / null |  |
| `template_selection_source` | enum | `manual / auto / batch_apply` |
| `template_match_reason` | string / null |  |
| `template_match_confidence` | number / null |  |

# Config

|  |  |
|------|------|
|  | `template_asset_id`  `template_style_text`  |
|  |  `undecided` |

---

# Config

# Config

 `DetailEditor` `SlidePreview` 

1. 
2.  /  PDF 
3. 
4.  AI 
5.  AI 
6. 
7. 
8. 
9. 
10.  SlidePreview

# Config


- 
- 
- AI 
- 

---

# Config

# Config

- ** LLM **
-  + ///
-  JSON

# Config

```json
[
  {
    "page_id": "...",
    "template_asset_id": "tpl_003",
    "status": "matched",
    "confidence": 0.86,
    "reason": ""
  },
  {
    "page_id": "...",
    "template_asset_id": null,
    "status": "undecided",
    "confidence": 0.32,
    "reason": ""
  }
]
```

# Config

- ****
-   
  > " N /"

# Config

- ****
- 
- `` `template_asset_id` 
-  LLM  `undecided`****""

# Config

- ****
- `undecided` 
- 

---

# Config

# Config

 `` ""

# Config

- ****

# Config

-   
  > ""
-  ``

---

# Config

# Config

 `` 

# Config

- ****
  - 
  - `` 
  - `` 
- 

# Config

- 
  1. 
  2. ****
  3. 

---

# Config

- 
- 
- ""

---

# Config

|  |  |  |
|------|------|------|
|  | Home  |  /  |
|  | DetailEditor  |  |
|  | TemplateSetupPage  |  |
|  |  |  |
|  |  |  /  |
|  | TemplateSetupPage |  |

---

# Config

|  |  |
|---------|---------|
|  `template_image_path` |  |
|  `template_style` |  |
|  | "" |
|  |  `template_asset_id` `template_style_text` |

---

# Config

>  PRD  6 " →  → "

# Config

****
- A) 
- B) 
- C) 
- D) 

**B**

****
-  B`feat/per-page-template`  Home "/" Home  `TemplateSelector` setup  setup  7 "" TemplateSetupPage 
-  AUX ""
-  C 6——
-  D

---

# Config

****
- A) 
- B) UI 
- C)  fallback 
- D) ""

**B**

****
-  B" + " JSON  `generate_json()`  3  AI """"
-  A AI
-  C
-  D AI  9  schema

---

# Config

****
- A) MVP  PDF v2 
- B) MVP  PDF  `backend/services/pdf_image_service.py` PyMuPDF (`fitz`)  PNG
- C) MVP  PDF  `backend/services/file_parser_service.py`  MinerU 
- D) MVP  PDF  PDF.js 

**B**

****
-  B——`PyMuPDF>=1.24.0``backend/pyproject.toml:39``PyPDF2>=3.0.0`L38`backend/controllers/project_controller.py`  `fitz.open() + page.get_pixmap()` `task_manager.py`  `ResourceLimiter` + `_commit_with_retry` +  8-10hPDF  deck "" MVP 
-  A MVP 
-  C`file_parser_service.py`  MinerU **** Markdown +  API 
-  D PDF.js  DPI ""

** spec **
-  `backend/services/pdf_image_service.py``pdf_to_page_images(pdf_path, output_dir, dpi=150) -> List[str]`
- `task_manager.py`  `process_pdf_to_template_images_task` `image_resource_limiter`
- `template_controller.py`  `POST /api/projects/:projectId/template-assets/upload-pdf` task_id 
-  50DPI  150

---

# Config

****
- A)  `generate_json()` ——few-shot + markdown JSON  + 3 
- B) Anthropic provider  `tool_use`  schemaOpenAI/Gemini  A
- C)  provider OpenAI `response_format=json_schema`Gemini `response_schema`Anthropic `tool_use`
- D)  few-shot prompt 

**A**

****
-  A`prompts.py`  7  JSON  promptL280/L413/L680/L815  9  schema  outlinedescriptions 
-  Bprovider  provider 
-  COpenAI/Gemini  provider  schema provider 
-  D9  `text_regions[]``image_regions[]` 

****
- prompt  2-3  few-shot
-  `get_template_analysis_prompt()`  `prompts.py`
-  `ai_service.py`  `analyze_template(image_path)` `generate_with_image` + `generate_json`

---

# Config

****
- A) 
- B)  +  ≤ 50  ≤ 20  30 
- C)  30 
- D)  Embedding  Top-5  LLM 
- E) N  = N 

**B**

****
-  B 50  + 10  ≈ 6K input tokensGemini 32KClaude 200KGPT-4 128K`generate_descriptions_stream``prompts.py:615-677` `ai_service.py` 
-  A>50 token 
-  C ≤ 50 
-  DEmbedding  /  / Embedding MVP  ≤ 20  Top-5 ""
-  EN "" 5 

****
-  `get_template_auto_match_prompt(templates, page_summaries)`  `prompts.py`
-  `ai_service.py`  `auto_match_templates(project_id)`
-  title + 100  +  `analysis_json`  + `user_label``notes`  200 
-  > 50  > 20 30 

---

# Config

****
- A)  TemplateSetupPageHome → OutlineEditor
- B)  + ""
- C) 

**A**

****
-  A 1 —— Home `TemplateSelector` setup `feat/per-page-template`  Home  `templateMode` 
-  B"→"/""
-  C""""

****
- Home `initializeProject` `templateMode === 'multi'`  navigate  `/project/:projectId/template-setup`
-  navigate  `/project/:projectId/outline`

---

> **2026-06-22** `~/.claude/plans/prd-unified-biscuit.md` 3.2 "" 7