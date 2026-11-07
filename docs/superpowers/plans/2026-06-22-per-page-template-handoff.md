# Config

> 2026-06-22  
> per-page-template /   
>  PRD AI 

# Config

# Config



```bash
tar -xOzf ~/Downloads/per-page-template.tar.gz per-page-template-pack/docs/prd-per-page-template.md
```



```text
per-page-template-pack/
  docs/prd-per-page-template.md
  code/commits.txt
  code/changed-files.txt
  code/changes-vs-main.patch
  sessions/
```

`code/changes-vs-main.patch`  diff `origin/main`  diff 

# Config



```bash
git fetch origin --prune
git show --no-patch --decorate --oneline origin/feat/per-page-template
git diff --name-status origin/main...origin/feat/per-page-template
```

 HEAD

```text
8f940d4 origin/feat/per-page-template tmp commit
```

 worktree

```text
/Users/davidyang/banana-slides-per-page-template
```

 worktree 

```text
feat/per-page-template -> origin/feat/per-page-template
```

# Config

 `origin/main`  8 

```text
frontend/src/components/preview/PageFineTuneDrawer.tsx
frontend/src/pages/SlidePreview.tsx
frontend/src/pages/Home.tsx
frontend/src/pages/DetailEditor.tsx
frontend/src/store/useProjectStore.ts
frontend/src/types/index.ts
frontend/e2e/fine-tune-drawer.spec.ts
frontend/e2e/drawer-screenshot.spec.ts
```



- `PageFineTuneDrawer.tsx`“”
- `Home.tsx` / 
- `useProjectStore.ts` `template_mode_${projectId}`  `localStorage` mock
- `types/index.ts` `TemplateAsset``TemplateMatchResult`
- `fine-tune-drawer.spec.ts`/
- `drawer-screenshot.spec.ts`

# Config

 PRD 

1. “”“”
2. “”
3. 
4. 

```text
Home -> OutlineEditor -> DetailEditor -> TemplateSetupPage -> SlidePreview
```

5. 
   - 
   - 
   - 
6. “”“”
7. 
   - `template_asset_id`
   - `template_style_text`
8.  `project_template_assets`
9. 
   - `template_asset_id`
   - `template_style_text`
   - `template_selection_source`
   - `template_match_reason`
   - `template_match_confidence`
10. TemplateSetupPage 
11.  LLM 
12. 
13. 

# Config

PRD 

1. `TemplateSetupPage`  `SlidePreview`
2. 
3. PDF  `file_parser_service.py`
4.  prompt  schema
5.  prompt  token 
6.  `TemplateSetupPage` 



1.  API  request/response schema
2.  migration  backfill 
3. 
4.  AI provider
5. URL 
6.  `localStorage`  demo
7.  MVP  AI PDF 
8. E2E  spec

# Config

# Config

 PRD

- 
- 
- 
- 
- 
- TemplateSetupPage 
- 
- 
- 
- 
- 

 PRD 

# Config



- “ / ”
- `SlidePreview` “”
- 
  - 
  - 
  - 
  - 
  - 
  - 
- 
  - 
  - 
- 
-  E2E smoke tests 

# Config

 `localStorage` mock

```text
template_mode_${projectId}
template_assets_${projectId}
page_template_assign_${projectId}
page_fine_tune_drawer_width
```

 demo 

# Config

 worktree 

```text
frontend: http://localhost:3465
backend:  http://localhost:5465
```

screen 

```text
banana-per-page-frontend
banana-per-page-backend
```

 `.env`

```bash
cd /Users/davidyang/banana-slides-per-page-template
rg -n '^(BACKEND_PORT|FRONTEND_PORT)=' .env
lsof -iTCP:5465 -sTCP:LISTEN -n -P
lsof -iTCP:3465 -sTCP:LISTEN -n -P
```

# Config

 merge  tar  patch  `main` /

# Config

 spec

```text
docs/superpowers/specs/2026-06-22-per-page-template-backend-design.md
```



- MVP 
- 
- API schema
- 
- 
-  localStorage 
- 

 MVP 

1.  `template_mode`
2. 
3.  `template_asset_id` / `template_style_text`
4. 
5.  API



- AI 
- 
- PDF 
- TemplateSetupPage 

# Config



- `projects.template_mode`
- `project_template_assets` 
- `pages.template_asset_id`
- `pages.template_style_text`
- `pages.template_selection_source`
- `pages.template_match_reason`
- `pages.template_match_confidence`



- `template_asset_id`  `project_template_assets.id`
- `template_mode`  `single`
- 

# Config

 API

```text
GET    /api/projects/:projectId/template-assets
POST   /api/projects/:projectId/template-assets
PATCH  /api/projects/:projectId/template-assets/:assetId
DELETE /api/projects/:projectId/template-assets/:assetId

PATCH  /api/projects/:projectId/template-mode
PATCH  /api/projects/:projectId/pages/:pageId/template
```

 API



```text
POST /api/projects/:projectId/template-assets/:assetId/analyze
POST /api/projects/:projectId/templates/auto-match
POST /api/projects/:projectId/pages/:pageId/template/auto-match
```

# Config



- 
- 
- 
- 
-  URL
- 

 file/material/template “”“”

# Config



1.  `template_asset_id` 
2.  `template_style_text`
3.  `template_image_path`
4.  `template_style`
5. 



- `backend/services/task_manager.py`
- `backend/services/ai_service.py`
- `backend/services/prompts.py`
-  image provider 



# Config

 `templateLocalStore`

- `listAssets` -> `GET template-assets`
- `saveAssets` ->  / PATCH / DELETE API
- `getAssignment` ->  `page` 
- `setAssignment` -> `PATCH page template`
- `template_mode_${projectId}` -> `project.template_mode`

 UX 

- 
- 
-  UI 
- 
- 

# Config

 mock



 / 

-  `template_mode`
-  URL
- 
- 
- PATCH  GET 
- 

 E2E

- 
- 
- 
- 
- 
-  spec 



- 
-  mock

# Config

1.  `main`  merge 
2.  spec MVP  AI //PDF 
3.  migration + model
4.  API
5. 
6. 
7. / API 
8. E2E 
9.  TemplateSetupPageAI 

# Config

- 
-  tar  patch 
-  `localStorage` demo
- PRD 
-  prompt 
- 

# Config



1. 
2. 
3. 
4. 
5. 
6. 
7. 
8. 
9. E2E 
