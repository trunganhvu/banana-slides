# Backend Integration Tests

# Test verification logic

# Test verification logic
****: `test_full_workflow.py`

 Flask `client` fixture

****
- ✅ 
- ✅ 
- ✅  CI  `backend-integration-test` 
- ✅  mock  API key

****
```bash
cd backend
uv run pytest tests/integration/test_full_workflow.py -v
```

# Test verification logic
****: `test_api_full_flow.py`

 `requests`  HTTP 

****
- ⏱️  HTTP 
- 🔧  `http://localhost:5011`
- 🏗️  CI  `docker-test` 
- 🔑  AI API key

****: `@pytest.mark.requires_service`

****
```bash
# Test verification logic
docker compose up -d

# Test verification logic
cd backend
uv run pytest tests/integration/test_api_full_flow.py -v -m "requires_service"
```

# Test verification logic

# Test verification logic
****:  PR  push 

****: 
- ✅  Flask test client 
- ❌ 

```yaml
# Test verification logic
pytest tests/integration -v -m "not requires_service"
```

****:
```yaml
TESTING: true
SKIP_SERVICE_TESTS: true
GOOGLE_API_KEY: mock-api-key-for-testing
```

# Test verification logic
****:  PR  `ready-for-test` 

****:
- ✅ 
- ✅  API 

```yaml
# Test verification logic
pytest tests/integration/test_api_full_flow.py -v -m "requires_service"
```

****:
```yaml
SKIP_SERVICE_TESTS: false
GOOGLE_API_KEY: <real-api-key-from-secrets>
```

## Pytest Markers

 markers  `pytest.ini` 

| Marker |  |  |
|--------|------|------|
| `unit` |  |  |
| `integration` |  |  |
| `slow` |  |  AI API  |
| `requires_service` |  |  requests  HTTP  |
| `mock` |  mock |  |
| `docker` | Docker  |  Docker  |

# Test verification logic

# Test verification logic
```bash
cd backend
SKIP_SERVICE_TESTS=true uv run pytest tests/integration/ -v -m "not requires_service"
```

# Test verification logic
```bash
# Test verification logic
docker compose up -d

# Test verification logic
cd backend
SKIP_SERVICE_TESTS=false uv run pytest tests/integration/ -v -m "requires_service"
```

# Test verification logic
```bash
# Test verification logic
docker compose up -d

# Test verification logic
cd backend
uv run pytest tests/integration/ -v
```

# Test verification logic
```bash
# Test verification logic
cd backend
uv run pytest tests/integration/test_api_full_flow.py::TestAPIFullFlow::test_quick_api_flow_no_ai -v

# Test verification logic
cd backend
uv run pytest tests/integration/test_api_full_flow.py::TestAPIFullFlow::test_api_full_flow_create_to_export -v
```

# Test verification logic

# Test verification logic

****:  `localhost:5011`

****:
1. `docker compose up -d`
2. `pytest -m "not requires_service"`

# Test verification logic

****:  `requires_service` 

****:  CI  pytest 
```yaml
pytest tests/integration -v -m "not requires_service"
```

# Test verification logic

1. ****:
   -  Flask test client →  `test_full_workflow.py`
   -  HTTP  →  `test_api_full_flow.py`  `@pytest.mark.requires_service`

2. **Marker **:
   ```python
   @pytest.mark.integration
   @pytest.mark.requires_service
   def test_real_api_call(self):
       response = requests.post('http://localhost:5011/api/projects', ...)
   ```

3. ****:
   -  `pytestmark = pytest.mark.skipif(...)`
   -  `@pytest.mark.skipif(...)`

---

****: 2025-12-22  
****: Banana Slides Team