// App State
let currentScreen = 'consent';
let updateInterval = null;

// Initialize app
async function init() {
  const consentGiven = await window.electronAPI.getConsentStatus();
  const appState = await window.electronAPI.getAppState();

  if (!consentGiven) {
    showScreen('consent');
  } else if (!appState.isLoggedIn) {
    showScreen('login');
  } else {
    showScreen('dashboard');
    updateDashboard(appState);
  }

  setupEventListeners();
}

// Screen Management
function showScreen(screenName) {
  const screens = ['consent', 'login', 'dashboard'];
  screens.forEach(screen => {
    const element = document.getElementById(`${screen}Screen`);
    if (element) {
      element.classList.remove('active');
    }
  });

  const activeScreen = document.getElementById(`${screenName}Screen`);
  if (activeScreen) {
    activeScreen.classList.add('active');
  }
  currentScreen = screenName;
}

function showError(elementId, message) {
  const errorElement = document.getElementById(elementId);
  if (errorElement) {
    errorElement.textContent = message;
    errorElement.classList.add('show');
    setTimeout(() => {
      errorElement.classList.remove('show');
    }, 5000);
  }
}

// Event Listeners
function setupEventListeners() {
  // Consent Screen
  const acceptConsentBtn = document.getElementById('acceptConsentBtn');
  const consentCheckbox = document.getElementById('consentCheckbox');

  if (acceptConsentBtn) {
    acceptConsentBtn.addEventListener('click', async () => {
      if (!consentCheckbox.checked) {
        showError('consentError', 'You must accept the consent to continue');
        return;
      }

      const result = await window.electronAPI.giveConsent();
      if (result.success) {
        showScreen('login');
      }
    });
  }

  // Login Screen
  const loginBtn = document.getElementById('loginBtn');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');

  if (loginBtn) {
    loginBtn.addEventListener('click', async () => {
      const email = emailInput.value.trim();
      const password = passwordInput.value;

      if (!email || !password) {
        showError('loginError', 'Please enter both email and password');
        return;
      }

      loginBtn.disabled = true;
      loginBtn.textContent = 'Logging in...';

      const result = await window.electronAPI.login({ email, password });

      if (result.success) {
        showScreen('dashboard');
        const appState = await window.electronAPI.getAppState();
        updateDashboard(appState);
        startStatsUpdate();
      } else {
        showError('loginError', result.error || 'Login failed. Please check your credentials.');
      }

      loginBtn.disabled = false;
      loginBtn.textContent = 'Login';
    });
  }

  // Allow Enter key to submit login
  if (passwordInput) {
    passwordInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        loginBtn.click();
      }
    });
  }

  // Dashboard Screen
  const startDayBtn = document.getElementById('startDayBtn');
  const endDayBtn = document.getElementById('endDayBtn');
  const logoutBtn = document.getElementById('logoutBtn');

  if (startDayBtn) {
    startDayBtn.addEventListener('click', async () => {
      startDayBtn.disabled = true;
      startDayBtn.textContent = 'Starting...';

      const result = await window.electronAPI.startDay();

      if (result.success) {
        const appState = await window.electronAPI.getAppState();
        updateDashboard(appState);
        startStatsUpdate();
      } else {
        showError('loginError', result.error || 'Failed to start day');
      }

      startDayBtn.disabled = false;
      startDayBtn.textContent = 'Start Day';
    });
  }

  if (endDayBtn) {
    endDayBtn.addEventListener('click', async () => {
      endDayBtn.disabled = true;
      endDayBtn.textContent = 'Ending...';

      const result = await window.electronAPI.endDay();

      if (result.success) {
        const appState = await window.electronAPI.getAppState();
        updateDashboard(appState);
        stopStatsUpdate();
      } else {
        showError('loginError', result.error || 'Failed to end day');
      }

      endDayBtn.disabled = false;
      endDayBtn.textContent = 'End Day';
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      await window.electronAPI.logout();
      stopStatsUpdate();
      showScreen('login');
      
      // Clear form
      emailInput.value = '';
      passwordInput.value = '';
    });
  }
}

// Dashboard Updates
function updateDashboard(appState) {
  const userEmailElement = document.getElementById('userEmail');
  const trackingStatusElement = document.getElementById('trackingStatus');
  const startDayBtn = document.getElementById('startDayBtn');
  const endDayBtn = document.getElementById('endDayBtn');
  const statsContainer = document.getElementById('statsContainer');

  if (userEmailElement && appState.user) {
    userEmailElement.textContent = appState.user.email || appState.user.username || 'User';
  }

  if (trackingStatusElement) {
    if (appState.isDayStarted) {
      trackingStatusElement.textContent = 'Tracking Active';
      trackingStatusElement.classList.remove('status-inactive');
      trackingStatusElement.classList.add('status-active');
    } else {
      trackingStatusElement.textContent = 'Day Not Started';
      trackingStatusElement.classList.remove('status-active');
      trackingStatusElement.classList.add('status-inactive');
    }
  }

  if (startDayBtn && endDayBtn) {
    if (appState.isDayStarted) {
      startDayBtn.style.display = 'none';
      endDayBtn.style.display = 'block';
    } else {
      startDayBtn.style.display = 'block';
      endDayBtn.style.display = 'none';
    }
  }

  if (statsContainer) {
    statsContainer.style.display = appState.isDayStarted ? 'grid' : 'none';
  }
}

async function updateStats() {
  const stats = await window.electronAPI.getTrackingStats();
  
  if (stats) {
    const mouseCount = document.getElementById('mouseCount');
    const keyCount = document.getElementById('keyCount');
    const idleTime = document.getElementById('idleTime');
    const activeApp = document.getElementById('activeApp');

    if (mouseCount) mouseCount.textContent = stats.mouseEvents || 0;
    if (keyCount) keyCount.textContent = stats.keyboardEvents || 0;
    if (idleTime) idleTime.textContent = `${stats.idleSeconds || 0}s`;
    if (activeApp) {
      const appName = stats.activeApp || 'None';
      activeApp.textContent = appName.length > 15 ? appName.substring(0, 12) + '...' : appName;
    }
  }
}

function startStatsUpdate() {
  if (updateInterval) {
    clearInterval(updateInterval);
  }
  
  // Update stats every 2 seconds
  updateInterval = setInterval(updateStats, 2000);
  updateStats(); // Initial update
}

function stopStatsUpdate() {
  if (updateInterval) {
    clearInterval(updateInterval);
    updateInterval = null;
  }
}

// Listen for IPC events
window.electronAPI.onShowConsent(() => {
  showScreen('consent');
});

window.electronAPI.onShowLogin(() => {
  showScreen('login');
});

// Listen for day status changes from backend polling
window.electronAPI.onDayStatusChanged(async (data) => {
  console.log('📡 Day status changed from backend:', data);
  
  // Get fresh app state
  const appState = await window.electronAPI.getAppState();
  
  // Update dashboard if we're on the dashboard screen
  if (currentScreen === 'dashboard') {
    updateDashboard(appState);
    
    if (appState.isDayStarted) {
      startStatsUpdate();
    } else {
      stopStatsUpdate();
    }
  }
});

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
