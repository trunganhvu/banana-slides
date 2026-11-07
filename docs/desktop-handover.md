# Config

# Config

- `feat/electron-desktop`
- Worktree`/home/aa/banana-slides-electron`
- PRhttps://github.com/Anionex/banana-slides/pull/377

---

# Config

# Config

|  |  |  |
|------|------|------|
| Electron  | ✅ | `desktop/main.js` |
|  / IPC | ✅ | `desktop/preload.js` |
| Python  | ✅ | `desktop/python-manager.js` |
| GitHub Releases  | ✅ | `desktop/auto-updater.js` |
|  Splash  | ✅ | `desktop/splash.html` |
| electron-builder  | ✅ | `desktop/electron-builder.yml` |
| PyInstaller  | ✅ | `backend/banana-slides.spec` |
| 50px | ✅ | `frontend/src/components/shared/DesktopTitleBar.tsx` |
|  | ✅ |  |
|  | ✅ | `frontend/src/components/shared/UpdateChecker.tsx` |
| HashRouterfile://  | ✅ | `frontend/src/App.tsx` |
| API client  | ✅ | `frontend/src/api/client.ts` |
|  | ✅ | `frontend/src/config/presetStyles.ts`, `TemplateSelector.tsx` |
| Logo import  | ✅ | `DesktopTitleBar.tsx`, `Home.tsx`, `Landing.tsx`, `HelpModal.tsx` |
| Windows NSIS  | ✅ |  |
| Linux AppImage + deb | ✅  | `electron-builder.yml`, CI workflow |
| GitHub Actions  | ✅ | `.github/workflows/release-desktop.yml` |
|  | ✅ 15/15 | `frontend/src/tests/desktop-*.test.ts` |

---

# Config

# Config

**** 
```
Error: Path doesn't exist: migrations. Please use the 'init' command to create a new scripts folder.
```

**** `flask_migrate.upgrade()`  migrations PyInstaller  migrations  `_internal/migrations/` `flask_migrate`  `migrations/` `__file__` 

****
-  Electron  `DATABASE_PATH` / `UPLOAD_FOLDER` / `EXPORT_FOLDER` `.env` 
- `backend/app.py` `DATABASE_PATH`  Alembic `db.create_all()`  SQLite
- `backend/desktop_bootstrap.py`  SQLite schema `settings``projects``pages``user_templates` Docker/
-  Alembic/fallback  Docker

****
-  `backend/`  `DATABASE_PATH``/health`  200
-  `settings.enable_text_reasoning``projects.outline_requirements``user_templates.thumb_path`  SQLite  `/api/settings``/api/projects``/api/user-templates`  200
- `C:\tmp\banana-build\backend\banana-backend.exe` `/health`  200

****
- `backend/app.py`
- `backend/desktop_bootstrap.py`
- `backend/banana-slides.spec`
- `backend/tests/unit/test_desktop_backend_startup.py`

# Config

****  GitHub  release  release 

****
-  `semver`  `app.getVersion()`  `releases/latest`
-  `desktop/build-meta.json` dirty 
-  release  tag  release 
-  dirty  release 

****
- `desktop/auto-updater.js`
- `desktop/update-policy.js`
- `desktop/scripts/sync-build-meta.js`

---

# Config

# Config

- Windows  WSL2 + Windows interop
- Windows Node.js 20+Python 3.11 .venv Python
- WSL uvNode.js

# Config

```bash
# Config
cd /home/aa/banana-slides-electron/frontend
./node_modules/.bin/vite build

# Config
cd /home/aa/banana-slides-electron/desktop
node scripts/sync-build-meta.js

# Config
rsync -a /home/aa/banana-slides-electron/desktop/ /mnt/c/tmp/banana-build/desktop/ --exclude=node_modules --exclude=dist
rsync -a /home/aa/banana-slides-electron/frontend/dist/ /mnt/c/tmp/banana-build/frontend/
rsync -a /home/aa/banana-slides-electron/backend/ /mnt/c/tmp/banana-build/backend_src/ \
  --exclude=__pycache__ --exclude=.venv --exclude=dist --exclude=build --exclude='*.egg-info'

# Config
# Config
powershell.exe -Command "cd 'C:\tmp\banana-build\backend_src'; & '..\\.venv\\Scripts\\python.exe' -m PyInstaller banana-slides.spec --noconfirm --log-level WARN"

# Config
powershell.exe -Command "Remove-Item -Recurse -Force 'C:\tmp\banana-build\backend'; Copy-Item -Recurse 'C:\tmp\banana-build\backend_src\dist\banana-backend' 'C:\tmp\banana-build\backend'"

# Config
powershell.exe -Command "
  \$env:ELECTRON_MIRROR='https://npmmirror.com/mirrors/electron/'
  \$env:CSC_IDENTITY_AUTO_DISCOVERY='false'
  cd 'C:\tmp\banana-build\desktop'
  npx electron-builder --win
"
```

`C:\tmp\banana-build\desktop\dist\BananaSlides-0.3.0-Setup.exe`

# Config

1. **PyInstaller  .venv  Python** Python torch  10+ 
2. **`package.json`  `"build": {}`** `electron-builder.yml` 
3. **`extraResources`  `from` ** `desktop/` backend  frontend  `../backend/`  `../frontend/`
4. ** `build-meta.json`** semver-only 
5. ** `signAndEditExecutable=false`** Windows 
6. **Windows SmartScreen**  exe →  → 

---

# Config

```bash
# Config
cd /home/aa/banana-slides-electron/backend
nohup uv run python app.py > /tmp/electron-backend.log 2>&1 &

# Config
cd /home/aa/banana-slides-electron/frontend
nohup ./node_modules/.bin/vite --port 3034 > /tmp/electron-frontend.log 2>&1 &

# Config
# Config
cd C:\tmp\electron-app
$env:NODE_ENV='development'
$env:FRONTEND_PORT='3034'
$env:BACKEND_PORT='5034'
node node_modules\electron\cli.js .
```

---

# Config

-  50px `#ffffff``z-index: 9999`
- Zoom
- / URL params `?action=material-generate` / `?action=material-center`  Home  modal
- Home  web 
- Splash  logo
- Windows /
-  1100×750 680×480
- `isDesktop`  `@/utils` 

---

# Config

```
desktop/
├── main.js                 # 
├── preload.js              # IPC bridge
├── python-manager.js       # 
├── auto-updater.js         # 
├── splash.html             # 
├── electron-builder.yml    # 
├── package.json            #  "build": {}
└── resources/
    ├── icon.ico            # Windows
    ├── icon.png            # Linux/
    ├── installer-icon.ico  # 
    ├── installerSidebar.bmp
    └── installerHeader.bmp

backend/
└── banana-slides.spec      # PyInstaller 

frontend/src/
├── components/shared/
│   ├── DesktopTitleBar.tsx # 
│   └── UpdateChecker.tsx   # 
├── App.tsx                 # HashRouter/BrowserRouter 
├── api/client.ts           #  baseURL 
└── utils/index.ts          # isDesktop 

.github/workflows/
└── release-desktop.yml     # v* tag Win + macOS + Linux
```