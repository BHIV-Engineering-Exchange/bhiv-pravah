import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { initializeLanguageSupport } from './utils/languageSupport.js'
import { BUILD_VERSION } from './config.js'
import '../gurukul_prana.js'

// Initialize language support
initializeLanguageSupport();

// Log build version to prevent tree-shaking
console.log('Gurukul Build Version:', BUILD_VERSION);

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
