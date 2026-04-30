const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('astralisAPI', {
  onPythonMessage: callback => ipcRenderer.on('python-message', (_event, data) => callback(data)),
  sendToPython: message => ipcRenderer.send('send-to-python', message),
  getAssetUrl: (...parts) => `assets/${parts.join('/')}`,
  openExternal: url => ipcRenderer.invoke('open-external', url),
  runUninstaller: () => ipcRenderer.invoke('run-uninstaller'),
  checkForUpdates: () => ipcRenderer.invoke('check-for-updates'),
  installUpdate: () => ipcRenderer.invoke('install-update'),
  onUpdateMessage: callback => ipcRenderer.on('update-message', (_event, data) => callback(data)),
  onOverlayStatus: callback => ipcRenderer.on('overlay-status', (_event, data) => callback(data)),
  sendOverlayCommand: message => ipcRenderer.send('overlay-command', message)
})