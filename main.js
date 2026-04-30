const { app, BrowserWindow, ipcMain, shell } = require('electron')
app.setName('Astralis')
const { autoUpdater } = require('electron-updater')
const path = require('path')
const { spawn } = require('child_process')
const fs = require('fs')

const gotSingleInstanceLock = app.requestSingleInstanceLock()
if (!gotSingleInstanceLock) app.quit()

let win = null
let overlayWin = null
let overlayUserMoved = false
let py = null
let isQuitting = false

function canSendToWindow() {
  return win && !win.isDestroyed() && win.webContents && !win.webContents.isDestroyed()
}

function canSendToOverlay() {
  return overlayWin && !overlayWin.isDestroyed() && overlayWin.webContents && !overlayWin.webContents.isDestroyed()
}

function sendToWindow(channel, payload) {
  if (!canSendToWindow()) return
  try { win.webContents.send(channel, payload) } catch {}
}

function sendToOverlay(channel, payload) {
  if (!canSendToOverlay()) return
  try { overlayWin.webContents.send(channel, payload) } catch {}
}

function ensureOverlayWindow() {
  if (overlayWin && !overlayWin.isDestroyed()) return overlayWin
  overlayWin = new BrowserWindow({
    width: 440,
    height: 320,
    show: false,
    frame: false,
    transparent: true,
    resizable: false,
    movable: true,
    minimizable: false,
    maximizable: false,
    skipTaskbar: true,
    alwaysOnTop: true,
    focusable: false,
    hasShadow: false,
    icon: path.join(__dirname, 'assets', 'other', 'Astralis.ico'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      sandbox: false
    }
  })
  overlayWin.setAlwaysOnTop(true, 'screen-saver')
  overlayWin.loadFile('overlay.html')
  overlayWin.on('move', () => { overlayUserMoved = true })
  overlayWin.on('closed', () => { overlayWin = null })
  return overlayWin
}

function applyOverlayStatus(payload) {
  const ow = ensureOverlayWindow()
  if (!overlayUserMoved && payload && Number.isFinite(payload.x) && Number.isFinite(payload.y)) ow.setPosition(Math.round(payload.x), Math.round(payload.y), false)
  sendToOverlay('overlay-status', payload || {})
  if (payload && payload.visible) ow.showInactive()
  else ow.hide()
}

function destroyOverlayWindow() {
  if (!overlayWin || overlayWin.isDestroyed()) return
  const ow = overlayWin
  overlayWin = null
  try { ow.destroy() } catch {}
}

function sendToPython(message) {
  if (!py || !py.stdin || py.stdin.destroyed || !py.stdin.writable) return
  try { py.stdin.write(JSON.stringify(message) + '\n') } catch {}
}

function startPython() {
  if (py) return
  const backendPath = app.isPackaged ? path.join(process.resourcesPath, 'backend', 'astralis_backend.exe') : path.join(__dirname, 'backend', 'astralis_backend.py')
  py = app.isPackaged ? spawn(backendPath, [], { windowsHide: true }) : spawn('python', [backendPath], { windowsHide: true })

  py.stdout.on('data', data => {
    const lines = data.toString().split(/\r?\n/).filter(Boolean)
    for (const line of lines) {
      try {
        const msg = JSON.parse(line)
        sendToWindow('python-message', msg)
        if (msg.type === 'overlay_status') applyOverlayStatus(msg.payload || {})
        if (msg.type === 'overlay_state' && msg.payload && msg.payload.visible === false && overlayWin && !overlayWin.isDestroyed()) overlayWin.hide()
      }
      catch { sendToWindow('python-message', { type: 'raw', payload: { message: line } }) }
    }
  })

  py.stderr.on('data', data => sendToWindow('python-message', { type: 'stderr', payload: { message: data.toString() } }))

  py.on('close', code => {
    sendToWindow('python-message', { type: 'python-exit', payload: { code } })
    py = null
  })

  py.on('error', err => {
    sendToWindow('python-message', { type: 'python-error', payload: { message: String(err) } })
    py = null
  })
}

function setupAutoUpdater() {
  autoUpdater.autoDownload = true
  autoUpdater.on('checking-for-update', () => sendToWindow('update-message', { type: 'checking' }))
  autoUpdater.on('update-available', info => sendToWindow('update-message', { type: 'available', info }))
  autoUpdater.on('update-not-available', info => sendToWindow('update-message', { type: 'not-available', info }))
  autoUpdater.on('download-progress', progress => sendToWindow('update-message', { type: 'progress', progress }))
  autoUpdater.on('update-downloaded', info => sendToWindow('update-message', { type: 'downloaded', info }))
  autoUpdater.on('error', err => sendToWindow('update-message', { type: 'error', message: err && err.message ? err.message : String(err) }))
}

function createWindow() {
  win = new BrowserWindow({
  width: 1440,
  height: 920,
  minWidth: 1100,
  minHeight: 720,
  autoHideMenuBar: true,
  show: false,
  icon: path.join(__dirname, 'assets', 'other', 'Astralis.ico'),
  webPreferences: {
    preload: path.join(__dirname, 'preload.js'),
    contextIsolation: true,
    sandbox: false
  }
})

  win.on('closed', () => {
    win = null
    destroyOverlayWindow()
    if (process.platform !== 'darwin' && !isQuitting) app.quit()
  })
  win.webContents.setWindowOpenHandler(({ url }) => {
    require('electron').shell.openExternal(url)
    return { action: 'deny' }
  })
  win.loadFile('index.html')
  win.once('ready-to-show', () => {
    win.show()
    if (app.isPackaged) autoUpdater.checkForUpdates().catch(() => {})
  })
}

app.on('second-instance', () => {
  if (!win) return
  if (win.isMinimized()) win.restore()
  win.focus()
})

app.whenReady().then(() => {
  setupAutoUpdater()
  createWindow()
  startPython()
  ipcMain.on('send-to-python', (_event, message) => sendToPython(message))
  ipcMain.on('overlay-command', (_event, message) => {
    if (message && message.type === 'stop_bot') destroyOverlayWindow()
    sendToPython(message)
  })
  ipcMain.handle('check-for-updates', async () => {
    if (!app.isPackaged) return { ok: false, message: 'Updates only work in the packaged app.' }
    try {
      await autoUpdater.checkForUpdates()
      return { ok: true }
    } catch (err) {
      return { ok: false, message: err && err.message ? err.message : String(err) }
    }
  })
  ipcMain.handle('install-update', () => {
    autoUpdater.quitAndInstall(false, true)
  })
  ipcMain.handle('open-external', async (_event, url) => {
    if (typeof url !== 'string' || !/^https?:/i.test(url)) return { ok: false, message: 'Invalid URL' }
    try {
      await shell.openExternal(url)
      return { ok: true }
    } catch (err) {
      return { ok: false, message: err && err.message ? err.message : String(err) }
    }
  })
  ipcMain.handle('run-uninstaller', async () => {
    const uninstaller = path.join(path.dirname(process.execPath), 'Uninstall Astralis.exe')
    if (!app.isPackaged || !fs.existsSync(uninstaller)) return { ok: false, message: 'Uninstaller is only available in the installed app.' }
    try {
      spawn(uninstaller, [], { detached: true, stdio: 'ignore' }).unref()
      app.quit()
      return { ok: true }
    } catch (err) {
      return { ok: false, message: err && err.message ? err.message : String(err) }
    }
  })
  app.on('activate', () => {
    if (!win && !isQuitting) createWindow()
  })
})

app.on('before-quit', () => {
  isQuitting = true
  destroyOverlayWindow()
  sendToPython({ type: 'quit' })
  if (py && !py.killed) {
    setTimeout(() => {
      if (py && !py.killed) {
        try { py.kill() } catch {}
      }
    }, 1000)
  }
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})