const { app, BrowserWindow, Tray, Menu, ipcMain, shell, dialog, nativeImage, nativeTheme } = require('electron');
const { autoUpdater: electronAutoUpdater, CancellationToken } = require('electron-updater');
const path = require('path');
const log = require('electron-log');
const fs = require('fs');
const pythonManager = require('./python-manager');
const { DesktopAutoUpdateManager, detectAutoUpdateSupport } = require('./auto-updater');
const {
  copyLocalExportToPath,
  createUniqueDownloadUrl,
  downloadToPath,
  resolveLocalExportPath,
} = require('./download-manager');
const {
  getApplicationIconPath,
  getTrayIconPath,
  shouldSetDockIcon,
} = require('./icon-policy');
const {
  initializeDataRoot,
  inspectDataRoot,
  prepareDataRoot,
  writeStorageConfig,
} = require('./storage-config');

let mainWindow = null;
let splashWindow = null;
let tray = null;
let isQuitting = false;
let backendStopped = false;
let backendStopRequested = false;
let activeDataRoot = null;
let activeDataRootIsDefault = true;
let desktopAutoUpdater = null;
const runtimeIconState = {
  dockOverrideApplied: false,
  trayTemplateImage: false,
};

function isDev() {
  return process.env.NODE_ENV === 'development';
}

function isSmokeMode() {
  return process.env.BANANA_DESKTOP_SMOKE === '1';
}

function getSmokeQuitDelayMs() {
  const delay = Number(process.env.BANANA_DESKTOP_SMOKE_QUIT_DELAY_MS || 10000);
  return Number.isFinite(delay) && delay >= 0 ? delay : 10000;
}

function configureSmokeUserDataPath() {
  const smokeUserDataPath = process.env.BANANA_DESKTOP_SMOKE_USER_DATA_DIR;
  if (!isSmokeMode() || !smokeUserDataPath) return;
  const resolvedPath = path.resolve(smokeUserDataPath);
  fs.mkdirSync(resolvedPath, { recursive: true });
  app.setPath('userData', resolvedPath);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForSmokeCaptureReady(webContents) {
  if (!webContents || webContents.isDestroyed()) return;
  if (webContents.isLoadingMainFrame()) {
    await Promise.race([
      new Promise((resolve) => webContents.once('did-stop-loading', resolve)),
      sleep(10000),
    ]);
  }
  await sleep(Number(process.env.BANANA_DESKTOP_SMOKE_CAPTURE_DELAY_MS || 1500));
}

async function writeSmokeResult(extra = {}) {
  if (!isSmokeMode()) return;

  const resultPath = process.env.BANANA_DESKTOP_SMOKE_RESULT || '';
  const screenshotPath = process.env.BANANA_DESKTOP_SMOKE_SCREENSHOT || '';
  const result = {
    ok: true,
    version: app.getVersion(),
    platform: process.platform,
    backendPort: pythonManager.getPort(),
    windowBounds: mainWindow?.getBounds() || null,
    windowVisible: mainWindow?.isVisible() || false,
    windowTitle: mainWindow?.getTitle() || '',
    url: mainWindow?.webContents?.getURL() || '',
    dataRoot: activeDataRoot,
    iconPolicy: runtimeIconState,
    timestamp: new Date().toISOString(),
    ...extra,
  };

  try {
    if (screenshotPath && mainWindow && !mainWindow.isDestroyed()) {
      await waitForSmokeCaptureReady(mainWindow.webContents);
      const image = await mainWindow.webContents.capturePage();
      fs.mkdirSync(path.dirname(screenshotPath), { recursive: true });
      fs.writeFileSync(screenshotPath, image.toPNG());
      result.screenshotPath = screenshotPath;
    }
    if (resultPath) {
      fs.mkdirSync(path.dirname(resultPath), { recursive: true });
      fs.writeFileSync(resultPath, JSON.stringify(result, null, 2));
    }
  } catch (error) {
    log.error('[main] Failed to write smoke result:', error);
    if (resultPath) {
      fs.mkdirSync(path.dirname(resultPath), { recursive: true });
      fs.writeFileSync(resultPath, JSON.stringify({
        ok: false,
        error: error.message,
        ...result,
      }, null, 2));
    }
  } finally {
    setTimeout(() => {
      isQuitting = true;
      app.quit();
    }, getSmokeQuitDelayMs());
  }
}

function getIconPath() {
  return getApplicationIconPath({
    platform: process.platform,
    isPackaged: app.isPackaged,
    resourcesPath: process.resourcesPath,
    desktopDir: __dirname,
  });
}

function getTrayPath() {
  return getTrayIconPath({
    platform: process.platform,
    isPackaged: app.isPackaged,
    resourcesPath: process.resourcesPath,
    desktopDir: __dirname,
  });
}

function shouldOpenInExternalBrowser(targetUrl) {
  try {
    const parsedUrl = new URL(targetUrl);
    return ['http:', 'https:'].includes(parsedUrl.protocol);
  } catch (error) {
    return false;
  }
}

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 480,
    height: 360,
    frame: false,
    resizable: false,
    transparent: false,
    backgroundColor: nativeTheme.shouldUseDarkColors ? '#111111' : '#ffffff',
    center: true,
    skipTaskbar: true,
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  });
  splashWindow.loadFile(path.join(__dirname, 'splash.html'));
  splashWindow.on('closed', () => { splashWindow = null; });
}

function createMainWindow() {
  const isMac = process.platform === 'darwin';
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 750,
    minWidth: 680,
    minHeight: 480,
    show: false,
    ...(isMac
      ? {
          titleBarStyle: 'hidden',
          trafficLightPosition: { x: 16, y: 16 },
          backgroundColor: '#ffffff',
        }
      : {
          frame: false,
          icon: getIconPath(),
        }),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (app.dock && shouldSetDockIcon({ platform: process.platform, isPackaged: app.isPackaged })) {
    app.dock.setIcon(getIconPath());
    runtimeIconState.dockOverrideApplied = true;
  }

  mainWindow.on('close', (e) => {
    if (!isQuitting) {
      e.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('ready-to-show', () => {
    if (splashWindow) {
      splashWindow.close();
    }
    mainWindow.webContents.setZoomFactor(0.8);
    mainWindow.show();
    mainWindow.focus();
    setTimeout(() => writeSmokeResult(), 1000);
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (shouldOpenInExternalBrowser(url)) {
      shell.openExternal(url);
    }
    return { action: 'deny' };
  });

  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (shouldOpenInExternalBrowser(url)) {
      event.preventDefault();
      shell.openExternal(url);
    }
  });
}

function createTray() {
  const trayPath = getTrayPath();
  let icon = nativeImage.createFromPath(trayPath);
  let usesTemplateImage = process.platform === 'darwin';
  let usesFallbackImage = false;
  if (icon.isEmpty()) {
    const fallbackPath = path.join(__dirname, 'resources', 'icon.png');
    log.error('[main] Failed to load tray icon, using app icon fallback:', { trayPath, fallbackPath });
    icon = nativeImage.createFromPath(fallbackPath);
    usesTemplateImage = false;
    usesFallbackImage = true;
  }
  if (icon.isEmpty()) {
    log.error('[main] Failed to load both the Tray icon and its fallback:', trayPath);
    return;
  }

  if (usesTemplateImage) {
    icon.setTemplateImage(true);
    runtimeIconState.trayTemplateImage = true;
  } else if (process.platform === 'linux' || usesFallbackImage) {
    icon = icon.resize({ width: 16, height: 16 });
  }
  tray = new Tray(icon);
  tray.setToolTip('Banana Slides');

  const contextMenu = Menu.buildFromTemplate([
    { label: 'Hiển thị cửa sổ chính', click: () => { mainWindow?.show(); mainWindow?.focus(); } },
    { type: 'separator' },
    { label: 'Thoát', click: () => { isQuitting = true; app.quit(); } },
  ]);
  tray.setContextMenu(contextMenu);
  tray.on('double-click', () => { mainWindow?.show(); mainWindow?.focus(); });
}

function sendUpdateState(state) {
  if (!mainWindow || mainWindow.isDestroyed() || mainWindow.webContents.isDestroyed()) return;
  mainWindow.webContents.send('update-status-changed', state);
}

async function installDownloadedUpdate() {
  if (!desktopAutoUpdater?.isUpdateDownloaded()) {
    return { success: false, error: 'UPDATE_NOT_DOWNLOADED' };
  }

  isQuitting = true;
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.hide();
  }
  backendStopRequested = true;
  try {
    await pythonManager.stopBackend();
  } catch (error) {
    log.error('[main] Failed to stop backend before installing update:', error);
  }
  backendStopped = true;
  const started = desktopAutoUpdater.quitAndInstall();
  return { success: started };
}

async function showDownloadedUpdateDialog(checkResult) {
  const result = await dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: 'Bản cập nhật đã sẵn sàng',
    message: `Phiên bản mới v${checkResult.update.version} đã tải xuống hoàn tất`,
    detail: 'Khởi động lại Banana Slides để hoàn tất cập nhật. ',
    buttons: ['Khởi động lại và cập nhật', 'Khởi động lại sau'],
    defaultId: 0,
    cancelId: 1,
  });
  if (result.response === 0) {
    await installDownloadedUpdate();
  }
}

async function showManualUpdateDialog() {
  try {
    const checkResult = await desktopAutoUpdater.checkForUpdates();
    if (checkResult.status === 'update_downloaded') {
      await showDownloadedUpdateDialog(checkResult);
      return;
    }

    if (checkResult.update) {
      const primaryAction = checkResult.canAutoUpdate ? 'Tải bản cập nhật' : 'Đi tới trang tải xuống';
      const releaseNotes = checkResult.update.notes.trim();
      const result = await dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'Phát hiện phiên bản mới',
        message: `Phiên bản mới v${checkResult.update.version} khả dụng`,
        ...(releaseNotes ? { detail: releaseNotes.substring(0, 300) } : {}),
        buttons: [primaryAction, 'Xem toàn bộ nhật ký cập nhật', 'Cập nhật sau'],
        defaultId: 0,
        cancelId: 2,
      });
      if (result.response === 0) {
        if (checkResult.canAutoUpdate) {
          const downloadedState = await desktopAutoUpdater.downloadUpdate();
          if (downloadedState.status === 'update_downloaded') {
            await showDownloadedUpdateDialog(downloadedState);
          }
        } else {
          await shell.openExternal(checkResult.update.url);
        }
      } else if (result.response === 1) {
        await shell.openExternal(checkResult.update.url);
      }
      return;
    }

    await dialog.showMessageBox(mainWindow, {
      type: 'info',
      title: 'Kiểm tra cập nhật',
      message: 'Hiện tại đã là phiên bản mới nhất',
    });
  } catch (error) {
    log.error('[main] Failed to check for updates:', error);
    await dialog.showMessageBox(mainWindow, {
      type: 'error',
      title: 'Kiểm tra cập nhật thất bại',
      message: 'Không thể kết nối tới dịch vụ cập nhật, vui lòng kiểm tra mạng rồi thử lại',
    });
  }
}

function createAppMenu() {
  const isMac = process.platform === 'darwin';
  const template = [
    ...(isMac ? [{
      label: app.name,
      submenu: [
        { label: 'Giới thiệu Banana Slides', role: 'about' },
        { type: 'separator' },
        { label: 'Ẩn', role: 'hide' },
        { label: 'Ẩn các cửa sổ khác', role: 'hideOthers' },
        { label: 'Hiển thị tất cả', role: 'unhide' },
        { type: 'separator' },
        { label: 'Thoát', role: 'quit' },
      ],
    }] : []),
    {
      label: 'Tệp',
      submenu: [
        ...(!isMac ? [
          { type: 'separator' },
          { label: 'Thoát', role: 'quit' },
        ] : [
          { label: 'Đóng cửa sổ', role: 'close' },
        ]),
      ],
    },
    {
      label: 'Chỉnh sửa',
      submenu: [
        { label: 'Hoàn tác', role: 'undo' },
        { label: 'Làm lại', role: 'redo' },
        { type: 'separator' },
        { label: 'Cắt', role: 'cut' },
        { label: 'Sao chép', role: 'copy' },
        { label: 'Dán', role: 'paste' },
        { label: 'Chọn tất cả', role: 'selectAll' },
      ],
    },
    {
      label: 'Hiển thị',
      submenu: [
        { label: 'Phóng to', role: 'zoomIn', accelerator: 'CmdOrCtrl+=' },
        { label: 'Thu nhỏ', role: 'zoomOut', accelerator: 'CmdOrCtrl+-' },
        { label: 'Đặt lại thu phóng', role: 'resetZoom', accelerator: 'CmdOrCtrl+0' },
        { type: 'separator' },
        { label: 'Toàn màn hình', role: 'togglefullscreen' },
        { type: 'separator' },
        { label: 'Tải lại', role: 'reload' },
        { label: 'Tải lại bắt buộc', role: 'forceReload' },
        { label: 'Công cụ nhà phát triển', role: 'toggleDevTools' },
      ],
    },
    {
      label: 'Cửa sổ',
      submenu: [
        { label: 'Thu nhỏ', role: 'minimize' },
        ...(isMac ? [
          { type: 'separator' },
          { label: 'Đưa tất cả cửa sổ lên trước', role: 'front' },
        ] : [
          { label: 'Đóng', role: 'close' },
        ]),
      ],
    },
    {
      label: 'Trợ giúp',
      submenu: [
        {
          label: 'Kiểm tra cập nhật...',
          click: showManualUpdateDialog,
        },
        { type: 'separator' },
        {
          label: 'Giới thiệu',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'Giới thiệu Banana Slides',
              message: `Banana Slides v${app.getVersion()}`,
              detail: 'AI-Native Presentation Generator',
            });
          },
        },
      ],
    },
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

function setupIPC() {
  ipcMain.handle('get-app-version', () => app.getVersion());
  ipcMain.handle('get-backend-port', () => pythonManager.getPort());
  ipcMain.handle('check-for-updates', () => desktopAutoUpdater.checkForUpdates());
  ipcMain.handle('get-update-state', () => desktopAutoUpdater.getState());
  ipcMain.handle('get-auto-update-settings', () => desktopAutoUpdater.getSettings());
  ipcMain.handle('set-automatic-updates-enabled', (_, enabled) => (
    desktopAutoUpdater.setAutomaticUpdatesEnabled(enabled)
  ));
  ipcMain.handle('download-update', () => desktopAutoUpdater.downloadUpdate());
  ipcMain.handle('install-update', () => installDownloadedUpdate());
  ipcMain.handle('open-external', (_, url) => {
    try {
      const parsedUrl = new URL(url);
      if (['http:', 'https:'].includes(parsedUrl.protocol)) {
        return shell.openExternal(url);
      }
    } catch (e) {
      log.error('[main] Invalid URL for open-external:', url);
    }
  });

  ipcMain.on('window-minimize', () => { mainWindow?.minimize(); });
  ipcMain.on('window-maximize', () => {
    if (mainWindow?.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow?.maximize();
    }
  });
  ipcMain.on('window-close', () => { mainWindow?.close(); });

  ipcMain.on('zoom-in', () => {
    const wc = mainWindow?.webContents;
    if (wc) wc.setZoomLevel(wc.getZoomLevel() + 0.5);
  });
  ipcMain.on('zoom-out', () => {
    const wc = mainWindow?.webContents;
    if (wc) wc.setZoomLevel(wc.getZoomLevel() - 0.5);
  });
  ipcMain.on('zoom-reset', () => {
    mainWindow?.webContents?.setZoomLevel(0);
  });
  ipcMain.handle('get-zoom-level', () => {
    return mainWindow?.webContents?.getZoomLevel() ?? 0;
  });

  ipcMain.handle('get-data-storage-info', async () => {
    const inspection = await inspectDataRoot(activeDataRoot);
    return {
      dataRoot: inspection.dataRoot,
      isDefault: activeDataRootIsDefault,
      hasDatabase: inspection.hasDatabase,
      configurable: !isDev(),
    };
  });
  ipcMain.handle('choose-data-storage-directory', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
      title: 'Chọn vị trí lưu trữ dữ liệu',
      defaultPath: activeDataRoot,
      properties: ['openDirectory', 'createDirectory'],
    });
    return result.canceled ? null : result.filePaths[0];
  });
  ipcMain.handle('inspect-data-storage-directory', (_, dataRoot) => inspectDataRoot(dataRoot));
  ipcMain.handle('open-data-storage-directory', async () => {
    const error = await shell.openPath(activeDataRoot);
    return error ? { success: false, error } : { success: true };
  });
  ipcMain.handle('apply-data-storage-directory', async (_, dataRoot, allowInitialize = false) => {
    if (isDev()) {
      const error = new Error('DATA_STORAGE_UNAVAILABLE_IN_DEV: Data storage location is managed by the external development backend.');
      error.code = 'DATA_STORAGE_UNAVAILABLE_IN_DEV';
      throw error;
    }
    const inspection = await prepareDataRoot(dataRoot, allowInitialize);
    await writeStorageConfig(app.getPath('userData'), inspection.dataRoot);
    setTimeout(async () => {
      isQuitting = true;
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.hide();
      }
      backendStopRequested = true;
      try {
        await pythonManager.stopBackend();
      } catch (error) {
        log.error('[main] Failed to stop backend during data storage restart:', error);
      }
      backendStopped = true;
      app.relaunch();
      app.exit(0);
    }, 100);
    return { success: true, restarting: true };
  });

  // Logic
  ipcMain.handle('download-file', async (_, { url, filename }) => {
    const currentWindow = mainWindow;
    if (!currentWindow || currentWindow.isDestroyed()) return { success: false };
    const ext = (filename || 'file').split('.').pop() || '*';
    const downloadUrl = createUniqueDownloadUrl(url);
    const { filePath: savePath, canceled } = await dialog.showSaveDialog(currentWindow, {
      defaultPath: filename || 'download',
      filters: [{ name: 'Tất cả tệp', extensions: [ext, '*'] }],
    });
    if (canceled || !savePath) return { success: false, canceled: true };
    if (currentWindow.isDestroyed()) return { success: false };
    const localExportPath = await resolveLocalExportPath(downloadUrl, activeDataRoot);
    if (currentWindow.isDestroyed()) return { success: false };
    const result = localExportPath
      ? await copyLocalExportToPath(localExportPath, savePath)
      : await downloadToPath({
          downloadSession: currentWindow.webContents.session,
          downloadUrl,
          savePath,
          currentWindow,
        });
    if (!result.success) {
      log.error('[main] Download failed:', { url: downloadUrl, savePath, ...result });
      if (!currentWindow.isDestroyed()) {
        const localizedError = {
          interrupted: 'Tải xuống bị gián đoạn, Vui lòng thử lại. ',
          timeout: 'Tải xuống quá thời gian chờ, Vui lòng thử lại. ',
          missing: 'Tệp đích chưa được ghi. ',
          empty: 'Tệp đích bị trống. ',
          failed: 'Sao chép hoặc tải tệp thất bại. ',
          cancelled: 'Đã hủy tải xuống. ',
        }[result.state];
        await dialog.showMessageBox(currentWindow, {
          type: 'error',
          title: 'Lưu thất bại',
          message: 'Tệp chưa được lưu thành công',
          detail: `${localizedError || result.error || 'Tải xuống thất bại'}\n\nVị trí đích: ${savePath}`,
        });
      }
    } else {
      log.info('[main] Download completed:', result.filePath);
    }
    return result;
  });
}

async function selectRecoveryDataRoot(startupError) {
  let error = startupError;
  let skipErrorDialog = false;
  while (true) {
    const parentWindow = splashWindow && !splashWindow.isDestroyed() ? splashWindow : null;
    if (!skipErrorDialog) {
      const choice = await dialog.showMessageBox(parentWindow, {
        type: 'error',
        title: 'Không thể truy cập vị trí lưu trữ dữ liệu',
        message: 'Banana Slides Không thể truy cập vị trí lưu trữ dữ liệu đã cấu hình. ',
        detail: error.message,
        buttons: ['Chọn vị trí khác', 'Thoát'],
        defaultId: 0,
        cancelId: 1,
        noLink: true,
      });
      if (choice.response !== 0) return null;
    }
    skipErrorDialog = false;

    const selection = await dialog.showOpenDialog(parentWindow, {
      title: 'Chọn vị trí lưu trữ dữ liệu',
      properties: ['openDirectory', 'createDirectory'],
    });
    if (selection.canceled || !selection.filePaths[0]) {
      error = new Error('Chưa chọn vị trí lưu trữ dữ liệu khả dụng. ');
      continue;
    }
    try {
      const inspection = await inspectDataRoot(selection.filePaths[0]);
      if (!inspection.hasDatabase) {
        const confirmation = await dialog.showMessageBox(parentWindow, {
          type: 'warning',
          title: 'Xác nhận sử dụng vị trí dữ liệu mới',
          message: 'Trong thư mục đã chọn không có Banana Slides cơ sở dữ liệu. ',
          detail: 'Sau khi tiếp tục sẽ sử dụng vị trí này làm thư mục dữ liệu trống mới. Ứng dụng sẽ không di chuyển hoặc xóa bất kỳ dữ liệu nào trong thư mục gốc. ',
          buttons: ['Sử dụng vị trí này', 'Chọn lại'],
          defaultId: 1,
          cancelId: 1,
          noLink: true,
        });
        if (confirmation.response !== 0) {
          skipErrorDialog = true;
          continue;
        }
      }
      const prepared = await prepareDataRoot(inspection.dataRoot, !inspection.hasDatabase);
      await writeStorageConfig(app.getPath('userData'), prepared.dataRoot);
      return { ...prepared, isDefault: false };
    } catch (nextError) {
      error = nextError;
    }
  }
}

async function bootstrap() {
  createSplashWindow();
  createMainWindow();
  createTray();

  try {
    desktopAutoUpdater = new DesktopAutoUpdateManager({
      app,
      updater: electronAutoUpdater,
      CancellationToken,
      logger: log,
      canAutoUpdate: detectAutoUpdateSupport({ app }),
    });
    await desktopAutoUpdater.initialize();
    desktopAutoUpdater.subscribe(sendUpdateState);
    createAppMenu();
    setupIPC();

    let storageInfo;
    try {
      storageInfo = await initializeDataRoot(app.getPath('userData'));
    } catch (error) {
      log.error('[main] Configured data storage location is unavailable:', error);
      storageInfo = await selectRecoveryDataRoot(error);
      if (!storageInfo) {
        isQuitting = true;
        app.quit();
        return;
      }
    }
    activeDataRoot = storageInfo.dataRoot;
    activeDataRootIsDefault = storageInfo.isDefault;

    const port = await pythonManager.startBackend(activeDataRoot);
    await pythonManager.waitForBackend(port);

    if (isDev()) {
      mainWindow.loadURL(`http://localhost:${process.env.FRONTEND_PORT || 3000}?backendPort=${port}`);
    } else {
      mainWindow.loadFile(path.join(process.resourcesPath, 'frontend', 'index.html'), {
        query: { backendPort: String(port) },
      });
    }
    if (!isSmokeMode()) {
      desktopAutoUpdater.startAutomaticChecks();
    }
  } catch (err) {
    log.error('[main] Startup failed:', err);
    if (splashWindow) splashWindow.close();
    dialog.showErrorBox('Khởi chạy thất bại', `Khởi động dịch vụ backend thất bại: ${err.message}`);
    app.quit();
  }
}

configureSmokeUserDataPath();
app.whenReady().then(bootstrap);
if (process.platform === 'win32') {
  app.setAppUserModelId('com.banana.slides');
}

app.on('activate', () => {
  if (mainWindow) {
    mainWindow.show();
    mainWindow.focus();
  }
});

app.on('before-quit', (event) => {
  isQuitting = true;
  if (backendStopped) return;

  event.preventDefault();
  if (backendStopRequested) return;
  backendStopRequested = true;

  pythonManager.stopBackend().finally(() => {
    backendStopped = true;
    if (desktopAutoUpdater?.shouldInstallOnQuit()) {
      desktopAutoUpdater.quitAndInstall();
    } else {
      app.quit();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    // On Windows/Linux, closing all windows doesn't quit (tray keeps running)
  }
});