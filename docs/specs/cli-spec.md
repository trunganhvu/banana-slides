# Config

# Config

# Config

1.  API  `banana-cli`
2. “ HTTP API ” Python 
3.  `run jobs`
4.  `X-Access-Code` 
5. JSON

# Config

1. 
2.  pip  Python 
3.  Web 
4. CLI  HTTP

# Config

# Config

|  | Endpoint | CLI  | Phase |
|---|---|---|---|
| `GET` | `/api/projects` | `banana-cli projects list` | P1 |
| `POST` | `/api/projects` | `banana-cli projects create` | P1 |
| `GET` | `/api/projects/{project_id}` | `banana-cli projects get` | P1 |
| `PUT` | `/api/projects/{project_id}` | `banana-cli projects update` | P1 |
| `DELETE` | `/api/projects/{project_id}` | `banana-cli projects delete` | P1 |
| `POST` | `/api/projects/{project_id}/generate/outline` | `banana-cli workflows outline` | P1 |
| `POST` | `/api/projects/{project_id}/generate/from-description` | `banana-cli workflows outline --from-description` | P1 |
| `POST` | `/api/projects/{project_id}/generate/descriptions` | `banana-cli workflows descriptions` | P1 |
| `POST` | `/api/projects/{project_id}/generate/images` | `banana-cli workflows images` | P1 |
| `POST` | `/api/projects/{project_id}/refine/outline` | `banana-cli workflows outline --refine` | P1 |
| `POST` | `/api/projects/{project_id}/refine/descriptions` | `banana-cli workflows descriptions --refine` | P1 |
| `GET` | `/api/projects/{project_id}/tasks/{task_id}` | `banana-cli tasks status` | P1 |
| `GET` | `/api/projects/{project_id}/tasks/{task_id}` | `banana-cli tasks wait` | P1 |
| `POST` | `/api/projects/{project_id}/pages` | `banana-cli pages create` | P1 |
| `PUT` | `/api/projects/{project_id}/pages/{page_id}` | `banana-cli pages update` | P1 |
| `DELETE` | `/api/projects/{project_id}/pages/{page_id}` | `banana-cli pages delete` | P1 |
| `PUT` | `/api/projects/{project_id}/pages/{page_id}/outline` | `banana-cli pages set-outline` | P1 |
| `PUT` | `/api/projects/{project_id}/pages/{page_id}/description` | `banana-cli pages set-description` | P1 |
| `POST` | `/api/projects/{project_id}/pages/{page_id}/generate/description` | `banana-cli pages gen-description` | P1 |
| `POST` | `/api/projects/{project_id}/pages/{page_id}/generate/image` | `banana-cli pages gen-image` | P1 |
| `POST` | `/api/projects/{project_id}/pages/{page_id}/edit/image` | `banana-cli pages edit-image` | P1 |
| `POST` | `/api/projects/{project_id}/template` | `banana-cli templates upload` | P1 |
| `DELETE` | `/api/projects/{project_id}/template` | `banana-cli templates delete` | P1 |
| `GET` | `/api/projects/{project_id}/export/pptx` | `banana-cli exports pptx` | P1 |
| `GET` | `/api/projects/{project_id}/export/pdf` | `banana-cli exports pdf` | P1 |
| `GET` | `/api/projects/{project_id}/export/images` | `banana-cli exports images` | P1 |
| `POST` | `/api/projects/{project_id}/export/editable-pptx` | `banana-cli exports editable-pptx` | P1 |
| `POST` | `/api/reference-files/upload` | `banana-cli refs upload` | P1 |
| `GET` | `/api/reference-files/project/{project_id}` | `banana-cli refs list` | P1 |
| `GET` | `/api/reference-files/{file_id}` | `banana-cli refs get` | P1 |
| `POST` | `/api/reference-files/{file_id}/parse` | `banana-cli refs parse` | P1 |
| `POST` | `/api/reference-files/{file_id}/associate` | `banana-cli refs associate` | P1 |
| `POST` | `/api/reference-files/{file_id}/dissociate` | `banana-cli refs dissociate` | P1 |
| `DELETE` | `/api/reference-files/{file_id}` | `banana-cli refs delete` | P1 |
| `GET` | `/api/projects/{project_id}/materials` | `banana-cli materials list --project-id` | P1 |
| `POST` | `/api/projects/{project_id}/materials/upload` | `banana-cli materials upload --project-id` | P1 |
| `POST` | `/api/projects/{project_id}/materials/generate` | `banana-cli materials generate --project-id` | P1 |
| `GET` | `/api/materials` | `banana-cli materials list --scope` | P1 |
| `POST` | `/api/materials/associate` | `banana-cli materials associate` | P1 |
| `DELETE` | `/api/materials/{material_id}` | `banana-cli materials delete` | P1 |

# Config

|  | Endpoint | CLI  | Phase |
|---|---|---|---|
| `POST` | `/api/projects/renovation` | `banana-cli renovation create` | P2 |
| `POST` | `/api/extract-style` | `banana-cli styles extract` | P2 |
| `GET` | `/api/projects/{project_id}/pages/{page_id}/image-versions` | `banana-cli pages versions` | P2 |
| `POST` | `/api/projects/{project_id}/pages/{page_id}/image-versions/{version_id}/set-current` | `banana-cli pages set-current` | P2 |
| `POST` | `/api/projects/{project_id}/pages/{page_id}/regenerate-renovation` | `banana-cli pages regenerate-renovation` | P2 |
| `GET` | `/api/settings` | `banana-cli settings get` | P2 |
| `PUT` | `/api/settings` | `banana-cli settings update` | P2 |
| `POST` | `/api/settings/reset` | `banana-cli settings reset` | P2 |
| `POST` | `/api/settings/verify` | `banana-cli settings verify` | P2 |
| `POST` | `/api/settings/tests/{test_name}` | `banana-cli settings test` | P2 |
| `GET` | `/api/settings/tests/{task_id}/status` | `banana-cli settings test-status` | P2 |
| `POST` | `/api/materials/upload` | `banana-cli materials upload --global` | P2 |
| `POST` | `/api/materials/download` | `banana-cli materials download` | P2 |
| `GET` | `/files/{project_id}/{type}/{filename}` | `banana-cli files fetch` | P2 |
| `GET` | `/files/materials/{filename}` | `banana-cli files fetch` | P2 |
| `GET` | `/files/user-templates/{template_id}/{filename}` | `banana-cli files fetch` | P2 |

# Config

# Config

```bash
banana-cli [GLOBAL_OPTIONS] <domain> <action> [OPTIONS]
```



1. `--base-url <url>` `http://localhost:5011`
2. `--access-code <code>` `X-Access-Code` 
3. `--poll-interval <sec>` `3`
4. `--request-timeout <sec>` `60`
5. `--config <path>`
6. `--json` JSON
7. `--verbose`/

# Config

```bash
banana-cli run jobs --file <jobs.jsonl|jobs.csv> --report <path> [--continue-on-error] [--timeout-sec N] [--state-file <path>] [--progress-interval-sec N]
banana-cli run monitor --state-file <path> [--watch] [--interval N]
banana-cli projects list|get|create|update|delete ...
banana-cli workflows outline|descriptions|images|full ...
banana-cli tasks status|wait --project-id <id> --task-id <id>
banana-cli pages create|update|delete|set-outline|set-description|gen-description|gen-image|edit-image|versions|set-current|regenerate-renovation ...
banana-cli templates upload|delete ...
banana-cli exports pptx|pdf|images|editable-pptx ...
banana-cli refs upload|list|get|parse|associate|dissociate|delete ...
banana-cli materials list|upload|generate|associate|download|delete ...
banana-cli settings get|update|reset|verify|test|test-status ...
banana-cli renovation create ...
banana-cli styles extract ...
banana-cli files fetch --url <download_url> --output <path>
```

# Config

1.  `JSONL/CSV` 
2. 
3.  `policy.continue_on_error` 
4. `steps``tasks``artifacts``error``duration_sec`
5.  `--state-file`  run/job/task 
6.  `--progress-interval-sec` 
7.  `--report`  JSON 

# Config

1.  `run jobs --state-file`  JSON
2. 
3. `--watch`  `--interval`  `status` 
4.  `--json` 

# Config



1. `0`
2. `2`
3. `1`



1. 
2. `--json`  JSON run 
3. `code/message/details`

# Config

# Config

 JSON 

```json
{
  "job_id": "optional-string",
  "job_type": "full_generation|export_only",
  "creation_type": "idea|outline|descriptions",
  "idea_prompt": "...",
  "outline_text": "...",
  "description_text": "...",
  "project_id": "required for export_only",
  "template_image_path": "/abs/path.png",
  "template_style": "text style",
  "extra_requirements": "optional",
  "language": "zh|en|ja|auto",
  "max_description_workers": 5,
  "max_image_workers": 8,
  "use_template": true,
  "reference_files": ["/abs/a.pdf"],
  "material_files": ["/abs/m1.png"],
  "export": {
    "formats": ["pptx", "pdf", "editable_pptx"],
    "filename_prefix": "demo",
    "page_ids": [],
    "editable_max_depth": 1,
    "editable_max_workers": 4
  },
  "policy": {
    "continue_on_error": true,
    "timeout_sec": 1800
  }
}
```

# Config

1. `full_generation`
   1. 
   2. `template_style``extra_requirements`
   3. `template_image_path`
   4.  `reference_files`
   5.  `material_files`
   6. 
      1. `creation_type=descriptions`  `/generate/from-description`
      2.  `/generate/outline` -> `/generate/descriptions`
      3.  `/generate/images`
   7.  `export.formats` 
2. `export_only`
   1.  `project_id` 
   2. 

# Config



```text
job_id,job_type,creation_type,idea_prompt,outline_text,description_text,project_id,template_image_path,template_style,export_formats,options_json
```



1. `export_formats`  `;`  `pptx;pdf;editable_pptx`
2.  `policy/export/page_ids/reference_files/material_files` `options_json`
3.  `options_json` 

# Config

1. `job_type`  `full_generation|export_only`
2. `export_only`  `project_id`
3. `full_generation` 
   1. `creation_type` 
   2. `idea`  `idea_prompt`
   3. `outline`  `outline_text`
   4. `descriptions`  `description_text`
4. 
5. `export.formats` `pptx|pdf|images|editable_pptx`

# Config

# Config

 -> 

1. CLI 
2. 
3. 
4. 

# Config



1. macOS/Linux`${XDG_CONFIG_HOME:-~/.config}/banana-slides/cli.toml`
2. Windows`%APPDATA%/banana-slides/cli.toml`

TOML 

```toml
base_url = "http://localhost:5011"
access_code = ""
poll_interval = 3
request_timeout = 60
continue_on_error = true
report_dir = "./reports"
```

# Config

1. `BANANA_CLI_BASE_URL`
2. `BANANA_CLI_ACCESS_CODE`
3. `BANANA_CLI_POLL_INTERVAL`
4. `BANANA_CLI_REQUEST_TIMEOUT`
5. `BANANA_CLI_CONTINUE_ON_ERROR`

# Config

1.  `access_code`  `/api/*`  `X-Access-Code`
2. `/files/*`  `X-Access-Code`
3.  Bearer Token

# Config

# Config

1. `CONFIG_ERROR`URL 
2. `INPUT_ERROR`CSV/JSONL 
3. `HTTP_ERROR` 2xx
4. `TASK_FAILED` `FAILED`
5. `TASK_TIMEOUT`
6. `IO_ERROR`

# Config

1.  `GET`  `3`  `1s/2s/4s`
2.  `POST/PUT/DELETE` 
3.  `5xx` `4xx` 
4. `run jobs` 
   1. `continue_on_error=true`
   2. `continue_on_error=false` run

# Config

1. `request_timeout` 60 
2. 
   1.  `--timeout-sec` > job `policy.timeout_sec` >  `1800` 
3. `tasks wait`  `TASK_TIMEOUT`

# Config



```text
GET /api/projects/{project_id}/tasks/{task_id}
```



1. `status=COMPLETED`
2. `status=FAILED` `error_message`
3. 

# Config

### 7.1 Phase 1



1. `run jobs`  `full_generation`  `export_only`
2. 
3. ///
4. 

 Python 

```text
cli/banana_cli/
  __init__.py
  __main__.py
  app.py
  config.py
  errors.py
  http_client.py
  models.py
  reporter.py
  jobs/
    loader.py
    runner.py
    workflow.py
  commands/
    run.py
    projects.py
    workflows.py
    tasks.py
    pages.py
    templates.py
    exports.py
    refs.py
    materials.py
```



1. `argparse`
2. HTTP`httpx`
3. `pydantic`

### 7.2 Phase 2



1. `renovation create``styles extract`
2. `versions`/`set-current`
3. `settings test`  `settings test-status`
4.  `files fetch`



1. CLI  >=90%  endpoint
2. /

# Config

# Config

1. 
   1. JSONL/CSV
   2. 
   3. 
2. Mock HTTP
   1. `run jobs` 
   2. 
   3. 
3. 
   1.  `backend/tests/integration/test_api_full_flow.py` 
   2.  Access Code 

# Config

1. 
   1. 
   2. 
   3. CSV/JSONL 
2. 
   1. 
   2.  fail-fast 
3. 
   1. 
   2. 
   3. 
4. 
   1. `pptx`
   2. `pdf`
   3. `images`
   4. `editable_pptx`
5. 
   1. 
   2. 
   3. 
6. 
   1. 
   2. JSON `totals/jobs` 

# Config

1.  10 
2. 
3. `export_only`  URL
4.  `ACCESS_CODE`  `/api/*`

# Config

# Config

1. 
2. 
3. 
4. 

# Config

1. 
2.  `GET` 
3. 
4.  step 

# Config

1. CLI  CLI 
2.  Phase 2  Phase 1 
3. 

# Config

# Config

```json
{"job_id":"job-ai-001","job_type":"full_generation","creation_type":"idea","idea_prompt":" AI Agent  6 ","template_image_path":"/Users/chenzixin/projects/banana-slides/assets/test_img.png","template_style":"","extra_requirements":" 6:4","language":"zh","max_description_workers":5,"max_image_workers":6,"use_template":true,"reference_files":["/Users/chenzixin/projects/banana-slides/docs/quickstart.mdx"],"material_files":[],"export":{"formats":["pptx","pdf","editable_pptx"],"filename_prefix":"ai-agent-practice","page_ids":[],"editable_max_depth":1,"editable_max_workers":4},"policy":{"continue_on_error":true,"timeout_sec":1800}}
```

# Config

```json
{
  "run_id": "37f00fd8-3c3f-4b3f-9dfa-d4f6f3344c19",
  "started_at": "2026-02-28T10:00:00Z",
  "finished_at": "2026-02-28T10:18:24Z",
  "base_url": "http://localhost:5011",
  "totals": {
    "total": 2,
    "success": 1,
    "failed": 1
  },
  "jobs": [
    {
      "job_id": "job-ai-001",
      "status": "SUCCESS",
      "project_id": "9f2e8d1d-becf-4a58-8fc7-3c3f0b2f3e4b",
      "tasks": [
        {"task_id": "70f8c7ee-2eb0-4ce4-9f85-4b3ace3f8ef2", "type": "GENERATE_DESCRIPTIONS", "status": "COMPLETED"},
        {"task_id": "7b5cb67e-95f6-4b2a-8f1b-e14e429d15eb", "type": "GENERATE_IMAGES", "status": "COMPLETED"},
        {"task_id": "8de44d14-e42a-4fd4-b1a7-9c0bf4f18adc", "type": "EXPORT_EDITABLE_PPTX", "status": "COMPLETED"}
      ],
      "artifacts": [
        {"format": "pptx", "download_url": "http://localhost:5011/files/9f2e8d1d-becf-4a58-8fc7-3c3f0b2f3e4b/exports/ai-agent-practice.pptx"},
        {"format": "pdf", "download_url": "http://localhost:5011/files/9f2e8d1d-becf-4a58-8fc7-3c3f0b2f3e4b/exports/ai-agent-practice.pdf"},
        {"format": "editable_pptx", "download_url": "http://localhost:5011/files/9f2e8d1d-becf-4a58-8fc7-3c3f0b2f3e4b/exports/ai-agent-practice_editable.pptx"}
      ],
      "error": {"code": null, "message": null},
      "duration_sec": 684
    },
    {
      "job_id": "job-export-002",
      "status": "FAILED",
      "project_id": "missing-project-id",
      "tasks": [],
      "artifacts": [],
      "error": {"code": "HTTP_ERROR", "message": "Project not found"},
      "duration_sec": 2
    }
  ]
}
```

# Config

### Phase 1

- [ ] `run jobs`  `full_generation`  `export_only`
- [ ]  JSON  spec  schema
- [ ] ///
- [ ] `refs`  `materials` 
- [ ] 
- [ ] “”
- [ ]  `0/1/2` 

### Phase 2

- [ ] `renovation create`  `styles extract` 
- [ ]  `versions`/`set-current` 
- [ ] `settings test`  `settings test-status` 
- [ ]  `files fetch` 
- [ ]  >=90%  endpoint