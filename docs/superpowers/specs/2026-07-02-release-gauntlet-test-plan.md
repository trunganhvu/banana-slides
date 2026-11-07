# Config

>  `npm run release:gauntlet`
> 

# Config

 bug 

1. **Reachability**
2. **Oracle**"/"

 unit + e2e

- ""
  
- Banana Slides ** AI **
  `expect(x).toBe(y)` " PPT """——
  ""

""**Oracle
**

|  |  |  Oracle |
|---|---|---|
| API  / DB /  /  |  | Schema  |
|  UI  /  / i18n /  |  | e2e  +  +  |
|  |  | ****+ Agent  |
| AI  |  | **VLM-as-Judge** |
|  /  |  |  Oracle →  |

**""invariant**

- →  i18n zh/en
   VLM ""
- →  >800ms  pending 
   loading spinner/skeleton/progress
  Playwright ** 70  e2e **
- →  click  2s  DOM 
- /→  console  uncaught errorroot 

# Config

"fail-fast"L0–L3 
L4–L7 

```
L0 ~2min      → lint / tsc / py_compile /  /  / i18n 
L1 +~5min     →  pytest + vitest
L2 ~3min    →  OpenAPI schema ⇄  mock ⇄  
L3  E2E~15min   →  70  spec +  + 
L4 ~10min     → PPTX/PDF// PPTX 
L5  AI ~25min→  ui-full-flow + provider  + VLM 
L6 Agent ~40min→  AI agent /
L7 ~15min   → 
→ +
```

 ≈ 2 L5–L7  ~1h CLAUDE.md ""
 API  $3–8

---

# Config

# Config

flake8eslint`npm run build`

1. **`tsc --noEmit` **build 
2. **** `alembic upgrade head` → `downgrade base` →  `upgrade head`
   ** release tag  DB fixture**  upgrade L7
3. **i18n ** `useT()`  zh/en 
    `TODO`/ i18n 

# Config

 **property-based testing** `hypothesis`

- `file_parser_service`/// UTF-8  PDF/DOCX/MD
   = 
- `task_manager`//
   = Task  pending 
- // → 

# Config

 70  e2e  `page.route()` mock**mock **
mock e2e 



1.  flask  OpenAPI schema`apispec`  schema 
2.  pytest seed  schema 
3.  lint  `frontend/e2e/* Documentation */*.spec.ts`  `page.route()` 
   mock JSON schema **mock  schema = **

 schema 

# Config

 `playwright.config.ts`  fixture** spec
 §0 **

```
- console error/warn  uncaught error / React warning → 
-  4xx/5xx → >800ms pending  loading  → 
-  click  2s  → 
- a11y axe-core →  label 
  ""
```

**** `visual-regression.spec.ts` 
`{zh, en}` × `{desktop 1280, mobile 375}` × Home / Outline / Detail /
Preview / Settings / Historydiff 
memory  hover-only 

# Config

 seed 
`frontend/e2e/helpers/seed-project.ts`  AI 
**** HTTP 200

- **PPTX**`python-pptx`  → 
   LibreOffice headless  PDF " Office "
- ** PPTX**/
- **PDF**`pypdf` 
- ****`ffprobe`  >0

# Config

 nightly `ui-full-flow.spec.ts` Gemini

1. **Provider **gemini openai/vertex " + 
   " API key 
2. **VLM-as-Judge** + 
   Gemini/Claude

   ```
    0–2  /  /  /
    /  /  AI 
    0  →  FAIL
   ```

    3 ""
3. **** L3  VLM 
   ""
   ——  CLAUDE.md  UX  #1

# Config

 Claude Agent SDK Claude Code headless + Playwright MCP **5 
agent** seed  30 
L3 ///+ agent 

|  |  |
|---|---|
|  |  |
|  |  loading / |
|  | emoji/RTL 0  200MB  |
|  | SQLite  |
|  | en locale + 375px  |

Agent ** LLM **
 agent  findings +  agent
** Playwright **——
 bug  flaky 

# Config

1. ****Playwright route + 
   - AI API  429/500// JSON → 
   -  50%  kill  →  pending
   -  tmpfs  uploads/→ 
2. ****10  → ThreadPoolExecutor SQLite 
   `database is locked` 
3. ****** release  DB + uploads fixture**
    → 
    release  fixture
4. ****docker-composeDockerfile.allinone
    →  →  → seed 

---

# Config

 `release-report/RISK.md`**
**

1. **** provider×model 
    ChromiumSafari/Firefox 
2. ** Oracle ** + VLM 
   - PPTX  PowerPoint / WPS / Keynote 
     LibreOffice 
   - VLM """"
   - 
   -  AI API 
3. **≤10 **
   " PowerPoint  release-artifacts/sample.pptx "
   " VLM  1  3 "
4. **Flaky **—— bug 

---

# Config

|  |  |  |  |
|---|---|---|---|
| P1 | L3  + console//loading  70  specL0 L4  | ~3  |  ×  Oracle |
| P2 | L2 L1 L7 / | ~4  |  mock  |
| P3 | L5 VLM-as-Judge + provider  | ~3  |  |
| P4 | L6  agent  +  | ~5  |  |



```bash
npm run release:gauntlet          # release 
npm run release:gauntlet -- --fast  # L0–L4
```

CI  `ci-test.yml` PR nightly  `--fast`
 release tag  GitHub Release

# Config

- " 99% "****—— bug 
  Dijkstra****
  /
  ""
- VLM  agent ——
  ——
- L5–L6  API ""
   `--fast` 