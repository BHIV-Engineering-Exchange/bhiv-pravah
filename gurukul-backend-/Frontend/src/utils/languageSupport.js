/**
 * Language Support Utilities
 * Provides infrastructure for multi-language support
 * Currently supports Arabic readiness (RTL support)
 */

/**
 * Get current language preference
 */
export const getCurrentLanguage = () => {
    return localStorage.getItem('selected_language') || 'en';
};

/**
 * Set language preference
 */
export const setLanguage = (lang) => {
    localStorage.setItem('selected_language', lang);
    applyLanguageSettings(lang);
};

/**
 * Apply language-specific settings (RTL, text direction, etc.)
 */
export const applyLanguageSettings = (lang) => {
    const html = document.documentElement;
    
    // RTL languages
    const rtlLanguages = ['ar', 'he', 'ur', 'fa'];
    
    if (rtlLanguages.includes(lang)) {
        html.setAttribute('dir', 'rtl');
        html.setAttribute('dir', 'rtl');
    } else {
        html.setAttribute('dir', 'ltr');
        html.removeAttribute('dir');
    }
    
    html.setAttribute('lang', lang);
};

/**
 * Check if current language is RTL
 */
export const isRTL = () => {
    const lang = getCurrentLanguage();
    const rtlLanguages = ['ar', 'he', 'ur', 'fa'];
    return rtlLanguages.includes(lang);
};

/**
 * Get text direction class for Tailwind
 */
export const getTextDirectionClass = () => {
    return isRTL() ? 'rtl' : 'ltr';
};

/**
 * Initialize language support on app load
 */
export const initializeLanguageSupport = () => {
    const lang = getCurrentLanguage();
    applyLanguageSettings(lang);
};

