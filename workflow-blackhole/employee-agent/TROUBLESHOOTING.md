# Troubleshooting Guide

Common issues and solutions for the Employee Activity Agent.

## Installation Issues

### Windows: "npm install fails with iohook error"

**Error:**
```
gyp ERR! build error
gyp ERR! stack Error: `C:\Program Files (x86)\MSBuild\14.0\bin\msbuild.exe` failed
```

**Solution:**
1. Install Windows Build Tools (as Administrator):
   ```cmd
   npm install --global windows-build-tools
   ```

2. Restart your computer

3. Try again:
   ```cmd
   npm install
   ```

**Alternative Solution:**
```cmd
npm install --global --production windows-build-tools --vs2015
npm config set msvs_version 2015
npm install
```

### macOS: "Permission denied" during npm install

**Error:**
```
EACCES: permission denied
```

**Solution:**
1. Don't use sudo with npm install
2. Fix npm permissions:
   ```bash
   mkdir ~/.npm-global
   npm config set prefix '~/.npm-global'
   echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bash_profile
   source ~/.bash_profile
   ```

3. Try again:
   ```bash
   npm install
   ```

### macOS: "xcode-select: error: tool not found"

**Error:**
```
xcode-select: error: tool 'xcodebuild' requires Xcode
```

**Solution:**
```bash
xcode-select --install
```

Follow the prompts to install Command Line Tools.

## Runtime Issues

### "Cannot connect to backend"

**Symptoms:**
- Login fails with "Network Error"
- "Failed to start day" message

**Solutions:**

1. **Check .env file:**
   ```env
   AGENT_API_BASE_URL=https://your-backend.com
   ```
   - No trailing slash
   - Use HTTPS in production
   - Verify URL is correct

2. **Test backend directly:**
   ```bash
   curl https://your-backend.com/api/agent/login
   ```

3. **Check firewall:**
   - Windows Firewall may block the app
   - Corporate firewall may block the backend URL
   - Add exception if needed

4. **Check backend logs:**
   - Is backend running?
   - Are there any errors?
   - Is CORS configured?

### "Activity tracking not working"

**Symptoms:**
- Start Day succeeds but no activity data
- Stats show all zeros

**Solutions:**

1. **Windows: Check if iohook loaded:**
   - Open DevTools (View → Toggle Developer Tools)
   - Check console for iohook errors
   - Reinstall if needed: `npm rebuild iohook`

2. **macOS: Grant permissions:**
   - System Preferences → Security & Privacy → Privacy
   - Accessibility → Enable for Employee Activity Agent
   - Input Monitoring → Enable for Employee Activity Agent
   - Restart the app

3. **Check backend:**
   - Is `/api/activity/ingest` endpoint working?
   - Check backend logs for errors
   - Verify attendance record is active

### "Login successful but immediately logged out"

**Symptoms:**
- Can login but app shows login screen again
- Token seems invalid

**Solutions:**

1. **Check JWT token:**
   - Backend must return valid JWT
   - Token must include `userId` in payload
   - Token expiration should be reasonable (7-30 days)

2. **Check electron-store:**
   - Delete stored data and try again:
     - Windows: `%APPDATA%\employee-activity-agent`
     - macOS: `~/Library/Application Support/employee-activity-agent`

3. **Check backend `/api/agent/verify` endpoint:**
   - If implemented, must validate tokens correctly

### "Start Day fails with 'Already started'"

**Symptoms:**
- Can't start day
- Backend says day already started

**Solutions:**

1. **End previous day in backend:**
   ```bash
   # Using backend admin panel or directly in database
   # Set status to 'ended' for today's attendance
   ```

2. **Fix agent to handle already-started:**
   - This is expected behavior
   - Agent should accept existing attendance ID
   - Check backend returns `attendanceId` even when already started

### macOS: "App can't be opened because it is from an unidentified developer"

**Symptoms:**
- macOS Gatekeeper blocks the app

**Solutions:**

1. **Right-click workaround:**
   - Right-click the app
   - Select "Open"
   - Click "Open" in the dialog

2. **System Preferences:**
   - System Preferences → Security & Privacy → General
   - Click "Open Anyway"

3. **For IT: Code sign the app:**
   - Get Apple Developer account
   - Sign the app with your certificate
   - Notarize the app

## UI Issues

### "App window is blank/white screen"

**Symptoms:**
- Window opens but shows nothing
- White or blank screen

**Solutions:**

1. **Check DevTools:**
   - Press `Ctrl+Shift+I` (Windows) or `Cmd+Option+I` (macOS)
   - Check Console for errors

2. **Check file paths:**
   - Verify `renderer/index.html` exists
   - Verify `renderer/app.js` exists
   - Check file permissions

3. **Reinstall:**
   ```bash
   rm -rf node_modules
   npm install
   npm start
   ```

### "Tray icon not showing"

**Symptoms:**
- App running but no tray icon
- Can't access app

**Solutions:**

1. **Windows:**
   - Check system tray settings
   - Click up arrow to show hidden icons
   - Enable "Always show all icons" in taskbar settings

2. **macOS:**
   - Check menu bar
   - May need to reduce number of menu bar items
   - Icon should appear on right side

3. **Icon file missing:**
   - App will use fallback icon
   - Add proper icon files to `assets/` folder

## Performance Issues

### "High CPU usage"

**Symptoms:**
- Electron process uses lots of CPU
- Computer becomes slow

**Solutions:**

1. **Check activity tracker interval:**
   - Should send data every 30 seconds (default)
   - If modified, restore to 30 seconds

2. **Check for errors:**
   - Open DevTools
   - Look for errors in Console
   - Fix any infinite loops

3. **Restart app:**
   - Sometimes tracking thread gets stuck
   - Restart usually fixes it

### "High memory usage"

**Symptoms:**
- Electron process uses lots of RAM

**Solutions:**

1. **Normal behavior:**
   - Electron apps typically use 100-200 MB
   - This is normal for Chromium-based apps

2. **If excessive (>500 MB):**
   - Check for memory leaks in DevTools
   - Restart app
   - Report bug if persistent

## Data Issues

### "Activity data not appearing in backend"

**Symptoms:**
- Tracking active but no data in database
- Backend receives no requests

**Solutions:**

1. **Check network tab:**
   - Open DevTools → Network
   - Start tracking
   - Look for POST requests to `/api/activity/ingest`
   - Check response status

2. **Check backend logs:**
   - Is endpoint receiving requests?
   - Are there validation errors?
   - Is data being saved to database?

3. **Check attendance record:**
   - Must have active attendance record
   - Backend must return `attendanceId`
   - Verify in database that record exists

### "Stats showing weird numbers"

**Symptoms:**
- Negative numbers
- Extremely high numbers
- NaN or undefined

**Solutions:**

1. **Reset tracking:**
   - End Day
   - Start Day again

2. **Check backend response:**
   - Backend might be returning invalid data
   - Check API response format

3. **Clear stored data:**
   - Delete electron-store data
   - Restart app

## Building Issues

### "electron-builder fails"

**Symptoms:**
- `npm run build` fails
- Build errors

**Solutions:**

1. **Check disk space:**
   - Build requires several GB
   - Free up space if needed

2. **Clean build:**
   ```bash
   rm -rf dist
   npm run build
   ```

3. **Platform-specific:**
   - Build Windows on Windows
   - Build macOS on macOS
   - Or use CI/CD like GitHub Actions

### "Built app doesn't work"

**Symptoms:**
- Build succeeds but app crashes
- Works in dev but not in production

**Solutions:**

1. **Check paths:**
   - Use `path.join(__dirname, ...)` not relative paths
   - Verify all assets are included in build

2. **Check asar packaging:**
   - Some native modules don't work in asar
   - Add to `asarUnpack` in package.json if needed

3. **Test on clean machine:**
   - Install on machine without Node.js
   - This simulates real employee environment

## Getting Help

### Before Reporting Issues

1. **Check this guide** for common solutions
2. **Check DevTools Console** for errors
3. **Check backend logs** for API errors
4. **Try on different machine** to isolate issue
5. **Collect information:**
   - Operating system and version
   - Node.js version: `node --version`
   - npm version: `npm --version`
   - Electron version (from package.json)
   - Error messages (full text)
   - Steps to reproduce

### Support Channels

1. **IT Help Desk**: [Your internal support]
2. **Documentation**: See README.md, QUICK_START.md
3. **Backend Team**: For API/database issues
4. **Development Team**: For app bugs

### Useful Commands

```bash
# Check versions
node --version
npm --version
electron --version

# Clear npm cache
npm cache clean --force

# Rebuild native modules
npm rebuild

# Rebuild iohook specifically
npm rebuild iohook

# Full clean reinstall
rm -rf node_modules package-lock.json
npm install

# Run with verbose logging
DEBUG=* npm start

# Check for outdated packages
npm outdated

# Security audit
npm audit
```

### Log Locations

**Windows:**
- App Data: `%APPDATA%\employee-activity-agent`
- Logs: `%APPDATA%\employee-activity-agent\logs`

**macOS:**
- App Data: `~/Library/Application Support/employee-activity-agent`
- Logs: `~/Library/Logs/employee-activity-agent`

**Linux:**
- App Data: `~/.config/employee-activity-agent`
- Logs: `~/.config/employee-activity-agent/logs`

---

**Can't find your issue?**
Contact your IT support team with:
- Description of the problem
- Error messages
- Screenshots (if applicable)
- Steps you've already tried
