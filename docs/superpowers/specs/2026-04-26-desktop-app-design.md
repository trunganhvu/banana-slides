# Banana Slides Desktop App — Design Spec

Date: 2026-04-26

## Overview

 Banana Slides  Windows (NSIS installer)  macOS (DMG) Electron PyInstaller  Python 

****

# Config

```
desktop/
├── main.js                 # Electron 
├── preload.js              #  IPC API
├── python-manager.js       # Python 
├── auto-updater.js         # GitHub Releases 
├── splash.html             # 
├── package.json            # Electron 
├── electron-builder.yml    # NSIS + DMG
├── resources/
│   ├── icon.ico            # Windows 
│   ├── icon.icns           # macOS 
│   ├── icon.png            # 
│   ├── installer.nsh       # NSIS 
│   └── README.md           # 
├── scripts/
│   └── build-all.bat       # Windows 
└── .gitignore
```

# Config

# Config

 + 

- macOS: `titleBarStyle: 'hidden'`
- Windows: `titleBarStyle: 'hidden'` + `titleBarOverlay`//

```javascript
const win = new BrowserWindow({
  width: 1400,
  height: 900,
  minWidth: 1024,
  minHeight: 700,
  show: false,
  titleBarStyle: 'hidden',
  ...(process.platform !== 'darwin' ? {
    titleBarOverlay: {
      color: '#00000000',  // 
      symbolColor: '#6b7280',
      height: 48
    }
  } : {}),
  webPreferences: {
    preload: path.join(__dirname, 'preload.js'),
    contextIsolation: true,
    nodeIntegration: false,
  }
});
```

# Config

1.  splash 
2.  Python  python-manager
3.  `http://localhost:{port}/health` 
4. 
5.  ready-to-show  splash

# Config


- 
- 
- 

macOS  dock 

# Config


- 
- 
- 
- 
- 

# Config

 `app.getPath('userData')` 
- Windows: `%APPDATA%/BananaSlides/`
- macOS: `~/Library/Application Support/BananaSlides/`


- `data/database.db` — SQLite 
- `uploads/` — 
- `exports/` —  PPT/PDF
- `logs/` — 

`DATABASE_PATH`, `UPLOAD_FOLDER`, `EXPORT_FOLDER`

# Config

 `contextBridge`  API

```javascript
contextBridge.exposeInMainWorld('electronAPI', {
  // Logic
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  // Logic
  checkForUpdates: () => ipcRenderer.invoke('check-for-updates'),
  // Logic
  getPlatform: () => process.platform,
  // Logic
  minimizeWindow: () => ipcRenderer.send('window-minimize'),
  maximizeWindow: () => ipcRenderer.send('window-maximize'),
  closeWindow: () => ipcRenderer.send('window-close'),
  // Logic
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
});
```

# Config

# Config

-  PyInstaller 
- 
- 
- 
- 

# Config

 5000 15000 

# Config


- `DATABASE_PATH` — 
- `UPLOAD_FOLDER` — 
- `EXPORT_FOLDER` — 
- `CORS_ORIGINS` — `http://localhost:{electronPort}`
- `FLASK_ENV` — `production`

# Config

 500ms  `/health` 30 

# Config

`app.on('before-quit')`
-  SIGTERM 
-  5 
-  SIGKILL
- Windows  `taskkill /F /PID`

# Config

# Config

-  GitHub API: `GET https://api.github.com/repos/Anionex/banana-slides/releases/latest`
-  `tag_name`semver `app.getVersion()`
- 

# Config

-  5 
- " → "
-  UpdateChecker  IPC 

# Config


- 
- 
- "" GitHub Releases 
- ""

# Config

 HTML 

- 480×360
- banana 
- Logo logo
- "Banana Slides" 
-  + "..."
- 

# Config

# Config



-  48px
- macOS ~70px paddingWindows  logo + 
- 
- Windows  `titleBarOverlay` macOS 
- `-webkit-app-region: drag` `no-drag`
- /
- `backdrop-filter: blur`

# Config

-  `window.electronAPI` 
-  CSS `env(titlebar-area-*)`  Windows titleBarOverlay 
- macOS  `navigator.platform`  preload  `getPlatform()` 

# Config

-  `window.electronAPI.checkForUpdates()` 
- 
- 
- "" `window.electronAPI.openExternal(url)`
- 

# Config

 Vite proxy 

```typescript
const isDesktop = typeof window !== 'undefined' && 'electronAPI' in window;
const API_BASE_URL = isDesktop
  ? `http://localhost:${window.__BACKEND_PORT__ || 5000}`
  : '';
```

 Electron preload  `contextBridge.exposeInMainWorld`  `window.__BACKEND_PORT__` IPC  preload

# Config

# Config

 import 

```python
if sys.platform == 'win32':
    if sys.stdout is not None:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if sys.stderr is not None:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
```

# Config

`create_app()`  `DATABASE_PATH`, `UPLOAD_FOLDER`, `EXPORT_FOLDER` 

# Config

 `with app.app_context():`  `db.create_all()` Alembic `db.create_all()` 

# Config

# Config

`backend/app.py`

# Config

- `fonts/` — 
- `migrations/` — Alembic 

# Config

flask, sqlalchemy, google.generativeai, openai, pptx, docx, lxml, httpx, aiohttp, reportlab, markitdown 

# Config

tkinter, matplotlib, scipy, IPython, jupyter, notebook — 

# Config

- `banana-backend`
- `console=False`
-  COLLECT 

# Config

```yaml
appId: com.banana.slides
productName: Banana Slides

directories:
  output: dist
  buildResources: resources

files:
  - "main.js"
  - "python-manager.js"
  - "preload.js"
  - "auto-updater.js"
  - "splash.html"
  - "package.json"
  - "node_modules/**/*"

extraResources:
  - from: "backend/"
    to: "backend"
    filter: ["**/*"]
  - from: "frontend/"
    to: "frontend"
    filter: ["**/*"]

win:
  target:
    - target: nsis
      arch: [x64]
  icon: resources/icon.ico
  artifactName: "BananaSlides-${version}-Setup.${ext}"

mac:
  target:
    - target: dmg
      arch: [x64, arm64]
  icon: resources/icon.icns
  artifactName: "BananaSlides-${version}.${ext}"

nsis:
  oneClick: false
  perMachine: false
  allowToChangeInstallationDirectory: true
  createDesktopShortcut: true
  createStartMenuShortcut: true
  shortcutName: "Banana Slides"

compression: maximum
```

# Config

# Config

 `v*` 

# Config

- Windows: `windows-latest`
- macOS: `macos-latest`

# Config

1. Checkout 
2.  tag  `desktop/package.json`  `frontend/package.json`
3.  Node.js 
4.  Python + uv
5.  (`npm run build`)
6. PyInstaller 
7.  `desktop/frontend/`  `desktop/backend/`
8. electron-builder 
9.  GitHub Release

# Config

 `base: './'`  Electron  `file://` 

# Config

-  OCR API Key 
-  + 
- Linux 
- 