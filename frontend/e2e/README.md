# Test verification logic

# Test verification logic

** E2E **" E2E"

# Test verification logic

```
        ┌──────────────────┐
        │   E2E         │  ←  API
        │  (api-full-flow)  │
        └──────────────────┘
              ▲
              │
      ┌───────────────────┐
      │            │  ←  API  mock
      │  (backend/tests/)  │
      └───────────────────┘
            ▲
            │
    ┌─────────────────────┐
    │              │  ← 
    │ ( + )        │
    └─────────────────────┘
```

---

# Test verification logic

# Test verification logic

****
- ✅ 
- ✅  AI APIGoogle Gemini
- ✅ 
- ✅  CI  API key

****
```
1. //
   ↓
2.  AI 
   ↓
3. 
   ↓
4. 
   ↓
5.  PPT 
```

****
- ⚠️  `GOOGLE_API_KEY`
- ⚠️  10-15 
- ⚠️  API  $0.01-0.05/

****
```bash
# Test verification logic
# Test verification logic
docker compose up -d

# Test verification logic
./scripts/wait-for-health.sh http://localhost:5011/health 60 2
./scripts/wait-for-health.sh http://localhost:3011 60 2

# Test verification logic
npx playwright test api-full-flow.spec.ts --workers=1
```

**CI **
-  `docker-test` job 
- `GOOGLE_API_KEY`  GitHub Secrets 
-  API key

---

# Test verification logic

****
- ✅  UI 
- ✅ 
- ✅  AI APIGoogle Gemini
- ⚠️ 15-20 
- ✅  CI  API key

****
- 
- 
- CI/CD 

****
```bash
# Test verification logic
# Test verification logic
docker compose up -d

# Test verification logic
./scripts/wait-for-health.sh http://localhost:5011/health 60 2
./scripts/wait-for-health.sh http://localhost:3011 60 2

# Test verification logic
npx playwright test ui-full-flow.spec.ts --workers=1
```

**CI **
-  `docker-test` job 
- `GOOGLE_API_KEY`  GitHub Secrets 
-  API key  Fork PR

---

# Test verification logic



- ~~`home.spec.ts`~~ -  UI  E2E
- ~~`create-ppt.spec.ts`~~ - API  E2E

****
-  AI API
- 
  - UI  → 
  - API  → 
  -  → `api-full-flow.spec.ts`

---

# Test verification logic

# Test verification logic

```yaml
# .github/workflows/ci-test.yml

docker-test job:
  ├─  Docker 
  ├─ 
  ├─ 
  ├─ Docker 
  └─ E2E  (api-full-flow.spec.ts)
      ├─  GOOGLE_API_KEY →  E2E
      └─  API key → 
```

# Test verification logic

 CI  E2E 

1.  → **Settings** → **Secrets and variables** → **Actions**
2.  Secret
   - Name: `GOOGLE_API_KEY`
   - Value:  Google Gemini API 
   - https://aistudio.google.com/app/apikey

# Test verification logic

CI  E2E 

```
⚠️  Skipping E2E tests

Reason: GOOGLE_API_KEY not configured or using mock key

Note: Other tests already passed:
  ✅ Backend unit tests
  ✅ Backend integration tests (with mock AI)
  ✅ Frontend unit tests
  ✅ Docker environment tests

E2E tests require a real Google API key to test the complete AI generation workflow.
```

**** 

---

# Test verification logic

|  |  |  API |  | CI  |
|---------|---------|-------------|---------|---------|
| **** | React hooks | ❌ | < 1  | ✅  |
| **** | ServicesUtilsModels | ❌ | < 2  | ✅  |
| **** | API mock AI | ❌ | < 3  | ✅  |
| **Docker ** |  | ❌ | < 5  | ✅  |
| **E2E ** |  AI  | ✅ | 10-15  | ⚠️  API key  |

---

# Test verification logic

# Test verification logic

1. ****
   ```bash
   # Test verification logic
   cd backend && uv run pytest tests/
   
   # Test verification logic
   cd frontend && npm test
   ```

2. ** PR ** CI 
   - Light Check
   - Full Test `ready-for-test` 

3. **** E2E 
   ```bash
   # Test verification logic
   npx playwright test api-full-flow.spec.ts
   ```

# Test verification logic

1. **** UI E2E 
   ```bash
   npx playwright test ui-full-flow.spec.ts
   ```

2. ** CI** E2E

---

# Test verification logic

# Test verification logic

```bash
# Test verification logic
npx playwright show-report
```

# Test verification logic

Playwright 
- `test-results/**/test-failed-*.png`
- `test-results/**/video.webm`
- `test-results/**/trace.zip`

# Test verification logic

```bash
npx playwright show-trace test-results/**/trace.zip
```

# Test verification logic

```bash
# Test verification logic
npx playwright test --ui
```

---

# Test verification logic

- [Playwright ](https://playwright.dev)
- [CI ](../.github/CI_SETUP.md)
- [ README](../README.md)

---

****: 2025-12-22  
****:  E2E 