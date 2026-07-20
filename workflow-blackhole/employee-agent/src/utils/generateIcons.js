const fs = require('fs');
const path = require('path');

/**
 * Simple SVG Icon Generator for Employee Activity Agent
 * 
 * This script creates basic SVG icons that can be used as placeholders
 * or converted to PNG/ICO/ICNS formats.
 * 
 * Usage:
 *   node generateIcons.js
 * 
 * Output:
 *   - icon.svg (app icon)
 *   - tray-icon-active.svg (tray icon - tracking active)
 *   - tray-icon-inactive.svg (tray icon - tracking inactive)
 */

const assetsDir = path.join(__dirname, '../../assets');

// Ensure assets directory exists
if (!fs.existsSync(assetsDir)) {
  fs.mkdirSync(assetsDir, { recursive: true });
}

// Main app icon (eye symbol)
const appIcon = `<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- Background circle -->
  <circle cx="128" cy="128" r="120" fill="url(#grad1)"/>
  
  <!-- Eye outline -->
  <ellipse cx="128" cy="128" rx="80" ry="50" fill="white" stroke="none"/>
  
  <!-- Iris -->
  <circle cx="128" cy="128" r="30" fill="#667eea"/>
  
  <!-- Pupil -->
  <circle cx="128" cy="128" r="15" fill="#1a202c"/>
  
  <!-- Highlight -->
  <circle cx="135" cy="121" r="6" fill="white" opacity="0.8"/>
</svg>`;

// Tray icon - Active (green dot)
const trayIconActive = `<?xml version="1.0" encoding="UTF-8"?>
<svg width="22" height="22" viewBox="0 0 22 22" xmlns="http://www.w3.org/2000/svg">
  <!-- Eye outline -->
  <ellipse cx="11" cy="11" rx="8" ry="5" fill="none" stroke="#4caf50" stroke-width="1.5"/>
  
  <!-- Pupil -->
  <circle cx="11" cy="11" r="2" fill="#4caf50"/>
  
  <!-- Active indicator (green dot) -->
  <circle cx="18" cy="4" r="3" fill="#4caf50"/>
</svg>`;

// Tray icon - Inactive (gray)
const trayIconInactive = `<?xml version="1.0" encoding="UTF-8"?>
<svg width="22" height="22" viewBox="0 0 22 22" xmlns="http://www.w3.org/2000/svg">
  <!-- Eye outline -->
  <ellipse cx="11" cy="11" rx="8" ry="5" fill="none" stroke="#9e9e9e" stroke-width="1.5"/>
  
  <!-- Pupil -->
  <circle cx="11" cy="11" r="2" fill="#9e9e9e"/>
</svg>`;

// Write SVG files
try {
  fs.writeFileSync(path.join(assetsDir, 'icon.svg'), appIcon);
  console.log('✓ Created icon.svg');
  
  fs.writeFileSync(path.join(assetsDir, 'tray-icon-active.svg'), trayIconActive);
  console.log('✓ Created tray-icon-active.svg');
  
  fs.writeFileSync(path.join(assetsDir, 'tray-icon-inactive.svg'), trayIconInactive);
  console.log('✓ Created tray-icon-inactive.svg');
  
  console.log('\n📦 SVG icons created successfully!');
  console.log('\n📝 Next steps:');
  console.log('1. Convert SVG to PNG using an online tool or:');
  console.log('   npm install -g svg2png-cli');
  console.log('   svg2png icon.svg -o icon.png -w 256 -h 256');
  console.log('   svg2png tray-icon-active.svg -o tray-icon.png -w 22 -h 22');
  console.log('\n2. For Windows .ico: Use https://convertio.co/png-ico/');
  console.log('3. For macOS .icns: Use https://cloudconvert.com/png-to-icns');
  console.log('\n4. Or use electron-icon-builder:');
  console.log('   npm install -g electron-icon-builder');
  console.log('   electron-icon-builder --input=icon.png --output=./');
  
} catch (error) {
  console.error('Error creating icon files:', error);
  process.exit(1);
}
