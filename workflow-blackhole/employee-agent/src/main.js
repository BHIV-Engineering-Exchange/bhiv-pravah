const { app, BrowserWindow, Tray, Menu, ipcMain, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');
const Store = require('electron-store');
const ActivityTracker = require('./managers/activityTracker');
const AttendanceStatusPoller = require('./managers/attendancePoller');
const ApiService = require('./services/apiService');

// Initialize store for persistent data
const store = new Store();

let tray = null;
let mainWindow = null;
let activityTracker = null;
let attendancePoller = null;
let apiService = null;

// App state
let appState = {
  isLoggedIn: false,
  isDayStarted: false,
  user: null,
  consentGiven: false
};

function createWindow() {
  const windowOptions = {
    width: 400,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    },
    show: false,
    frame: true,
    resizable: false
  };
  
  // Add icon if file exists
  const iconPath = path.join(__dirname, '../assets/icon.png');
  if (fs.existsSync(iconPath)) {
    windowOptions.icon = iconPath;
  }
  
  mainWindow = new BrowserWindow(windowOptions);

  mainWindow.loadFile(path.join(__dirname, 'renderer/index.html'));

  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.once('ready-to-show', () => {
    // Check consent on first run
    appState.consentGiven = store.get('consentGiven', false);
    
    if (!appState.consentGiven) {
      mainWindow.webContents.send('show-consent');
    } else {
      mainWindow.webContents.send('show-login');
    }
    
    mainWindow.show();
  });
}

function createTray() {
  // Create a simple tray icon (you should replace with actual icon file)
  const iconPath = path.join(__dirname, '../assets/tray-icon.png');
  let icon;
  
  // Use icon file if exists, otherwise use default Electron icon
  if (fs.existsSync(iconPath)) {
    icon = nativeImage.createFromPath(iconPath);
    icon = icon.resize({ width: 16, height: 16 });
  } else {
    // Create a simple colored square as fallback
    icon = nativeImage.createFromDataURL('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABHSURBVDiN7dMxDgAgCAPA1v//5o6NJk0aF3EgJCRwAwAA/1YZY1lr7d57cc49hqiqqqoqMzPGmKp67NZ1XVVVVd/rAwD8sQNJMwstxTIWbQAAAABJRU5ErkJggg==');
  }
  
  tray = new Tray(icon);
  
  updateTrayMenu();
  
  tray.on('click', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        mainWindow.show();
      }
    }
  });
}

function updateTrayMenu() {
  const contextMenu = Menu.buildFromTemplate([
    {
      label: appState.isLoggedIn ? `Logged in as: ${appState.user?.email || 'User'}` : 'Not logged in',
      enabled: false
    },
    { type: 'separator' },
    {
      label: appState.isDayStarted ? 'Day Started ✓' : 'Day Not Started',
      enabled: false
    },
    { type: 'separator' },
    {
      label: 'Open Dashboard',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
        }
      }
    },
    {
      label: 'Quit',
      click: () => {
        app.isQuitting = true;
        app.quit();
      }
    }
  ]);

  tray.setContextMenu(contextMenu);
  
  // Update tooltip
  const status = appState.isDayStarted ? 'Tracking Active' : 'Tracking Inactive';
  tray.setToolTip(`Employee Agent - ${status}`);
}

// IPC Handlers
ipcMain.handle('get-consent-status', () => {
  return appState.consentGiven;
});

ipcMain.handle('give-consent', () => {
  appState.consentGiven = true;
  store.set('consentGiven', true);
  return { success: true };
});

ipcMain.handle('login', async (event, credentials) => {
  try {
    const result = await apiService.login(credentials);
    
    if (result.success) {
      appState.isLoggedIn = true;
      appState.user = result.user;
      store.set('authToken', result.token);
      apiService.setAuthToken(result.token);
      
      // Start polling backend for attendance status
      startAttendancePoller();
      
      // Immediately check current status to sync with Vercel
      const currentStatus = await apiService.checkAttendanceStatus();
      if (currentStatus.dayStarted && !appState.isDayStarted) {
        console.log('🟢 Day already started on backend! Syncing...');
        appState.isDayStarted = true;
        
        // Start activity tracking
        if (activityTracker && currentStatus.attendanceId) {
          activityTracker.start(currentStatus.attendanceId);
        }
      }
      
      updateTrayMenu();
      
      // Send initial status to renderer
      if (mainWindow) {
        mainWindow.webContents.send('day-status-changed', { 
          dayStarted: appState.isDayStarted,
          attendanceId: currentStatus.attendanceId 
        });
      }
    }
    
    return result;
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('logout', () => {
  // Stop polling
  if (attendancePoller) {
    attendancePoller.stop();
  }
  
  // Stop tracking if active
  if (appState.isDayStarted) {
    activityTracker.stop();
    appState.isDayStarted = false;
  }
  
  appState.isLoggedIn = false;
  appState.user = null;
  store.delete('authToken');
  apiService.setAuthToken(null);
  updateTrayMenu();
  
  return { success: true };
});

ipcMain.handle('start-day', async () => {
  try {
    const result = await apiService.startDay();
    
    if (result.success) {
      appState.isDayStarted = true;
      
      // Start activity tracking
      activityTracker.start(result.attendanceId);
      
      updateTrayMenu();
    }
    
    return result;
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('end-day', async () => {
  try {
    const result = await apiService.endDay();
    
    if (result.success) {
      appState.isDayStarted = false;
      
      // Stop activity tracking immediately
      activityTracker.stop();
      
      updateTrayMenu();
    }
    
    return result;
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-app-state', async () => {
  // If logged in and poller exists, get fresh status from backend
  if (appState.isLoggedIn && attendancePoller) {
    try {
      const currentStatus = await attendancePoller.forceCheck();
      appState.isDayStarted = currentStatus.dayStarted;
    } catch (error) {
      console.error('Error fetching app state:', error);
    }
  }
  
  return {
    isLoggedIn: appState.isLoggedIn,
    isDayStarted: appState.isDayStarted,
    user: appState.user,
    consentGiven: appState.consentGiven
  };
});

ipcMain.handle('get-tracking-stats', () => {
  if (activityTracker) {
    return activityTracker.getCurrentStats();
  }
  return null;
});

// App lifecycle
app.whenReady().then(() => {
  // Initialize services
  apiService = new ApiService();
  activityTracker = new ActivityTracker(apiService);
  
  // Check for stored auth token
  const savedToken = store.get('authToken');
  if (savedToken) {
    apiService.setAuthToken(savedToken);
    // Start polling if already logged in
    startAttendancePoller();
  }
  
  createWindow();
  createTray();
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  // Don't quit on window close - keep running in tray
  // Will only quit when user selects "Quit" from tray menu
});

app.on('before-quit', () => {
  if (activityTracker) {
    activityTracker.stop();
  }
  if (attendancePoller) {
    attendancePoller.stop();
  }
});

/**
 * Start polling backend for attendance status
 * This enables automatic start/stop tracking based on Vercel dashboard actions
 */
function startAttendancePoller() {
  if (!attendancePoller) {
    attendancePoller = new AttendanceStatusPoller(apiService);
    
    // Listen for day-started event
    attendancePoller.on('day-started', (data) => {
      console.log('🟢 Workday started! Attendance ID:', data.attendanceId);
      appState.isDayStarted = true;
      
      // Start activity tracking
      if (activityTracker) {
        activityTracker.start(data.attendanceId);
      }
      
      updateTrayMenu();
      
      // Notify UI
      if (mainWindow) {
        mainWindow.webContents.send('day-status-changed', { dayStarted: true });
      }
    });
    
    // Listen for day-ended event
    attendancePoller.on('day-ended', () => {
      console.log('🔴 Workday ended! Stopping tracking...');
      appState.isDayStarted = false;
      
      // Stop activity tracking
      if (activityTracker) {
        activityTracker.stop();
      }
      
      updateTrayMenu();
      
      // Notify UI
      if (mainWindow) {
        mainWindow.webContents.send('day-status-changed', { dayStarted: false });
      }
    });
  }
  
  // Start polling
  attendancePoller.start();
}

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
});
