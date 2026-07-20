# Icon Placeholder

This is a placeholder for the application icon. Replace with actual icon files:

- **icon.png** - Main application icon (256x256 or larger)
- **tray-icon.png** - System tray icon (16x16 for Windows, 22x22 for macOS)
- **icon.ico** - Windows executable icon
- **icon.icns** - macOS application icon

## Creating Icons

You can use tools like:
- [electron-icon-builder](https://www.npmjs.com/package/electron-icon-builder)
- Online converters for .ico and .icns formats
- Design tools like GIMP, Photoshop, or Figma

## Quick Icon Generation

```bash
# Install icon builder
npm install -g electron-icon-builder

# Generate icons from a source image
electron-icon-builder --input=./source-icon.png --output=./assets
```

For now, the application will use default Electron icons.
