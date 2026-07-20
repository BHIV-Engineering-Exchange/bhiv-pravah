import React, { useEffect, useState, useRef } from 'react';
import { FaUserCircle, FaBars, FaTimes, FaGlobe, FaChevronDown, FaVolumeUp, FaVolumeMute, FaEye } from 'react-icons/fa';
import { Link, useNavigate } from 'react-router-dom';
import logo from '../assets/logo.svg';
import { useAuth } from '../contexts/AuthContext';
import { useSidebar } from '../contexts/SidebarContext';
import { useDemo } from '../contexts/DemoContext';
import { useVoice } from './VoiceManager';
import { getCurrentLanguage, setLanguage, applyLanguageSettings } from '../utils/languageSupport';

const Navbar = () => {
  const { user, logout } = useAuth();
  const { toggleSidebar, isSidebarOpen } = useSidebar();
  const { isDemoMode, toggleDemoMode } = useDemo();
  const { isMuted, toggleMute, isPlaying } = useVoice() || { isMuted: false, toggleMute: () => { }, isPlaying: false };
  const navigate = useNavigate();
  const [isLanguageOpen, setIsLanguageOpen] = useState(false);
  const [currentLang, setCurrentLang] = useState('English');
  const languageMenuRef = useRef(null);

  useEffect(() => {
    // Initialize Google Translate if available
    const initTranslate = () => {
      if (window.google && window.google.translate && window.google.translate.TranslateElement) {
        const translateElement = document.getElementById('google_translate_element');
        if (translateElement && !translateElement.hasChildNodes()) {
          try {
            if (typeof window.googleTranslateElementInit === 'function') {
              window.googleTranslateElementInit();
            }
          } catch (error) {
            if (process.env.NODE_ENV === 'development') {
              console.error('Error initializing Google Translate:', error);
            }
          }
        }
        return true; // Successfully initialized
      }
      return false; // Not ready yet
    };

    // Load saved language preference
    const savedLang = localStorage.getItem('selected_language') || 'en';
    const langNames = {
      'en': 'English',
      'hi': 'हिंदी',
      'es': 'Español',
      'fr': 'Français',
      'de': 'Deutsch',
      'it': 'Italiano',
      'pt': 'Português',
      'ru': 'Русский',
      'ja': '日本語',
      'ko': '한국어',
      'zh-CN': '中文',
      'ar': 'العربية',
      'bn': 'বাংলা',
      'gu': 'ગુજરાતી',
      'kn': 'ಕನ್ನಡ',
      'ml': 'മലയാളം',
      'mr': 'मराठी',
      'ne': 'नेपाली',
      'pa': 'ਪੰਜਾਬੀ',
      'ta': 'தமிழ்',
      'te': 'తెలుగు',
      'ur': 'اردو',
      'vi': 'Tiếng Việt'
    };

    if (langNames[savedLang]) {
      setCurrentLang(langNames[savedLang]);
      applyLanguageSettings(savedLang);
    }

    // Special case for 'en': actively tell Google Translate to use English
    // Setting googtrans=/en/en is more reliable than trying to delete the cookie,
    // because deletion may fail due to domain restrictions on deployed sites.
    if (savedLang === 'en') {
      const host = window.location.hostname;
      const parts = host.split('.');
      const domainVariants = [host, '.' + host];
      if (parts.length > 2) {
        const rootDomain = parts.slice(-2).join('.');
        domainVariants.push(rootDomain, '.' + rootDomain);
      }
      const pastDate = 'Thu, 01 Jan 1970 00:00:00 UTC';
      // First expire any existing translation cookie
      domainVariants.forEach(domain => {
        document.cookie = `googtrans=; expires=${pastDate}; path=/; domain=${domain};`;
        document.cookie = `googtrans=/en/en; expires=${pastDate}; path=/; domain=${domain};`;
      });
      // Fallback: set /en/en without domain (same-origin)
      document.cookie = `googtrans=; expires=${pastDate}; path=/;`;
    }

    // Wait for Google Translate to load, then initialize
    let attempts = 0;
    const maxAttempts = 50; // 5 seconds max wait
    const timeoutIds = [];

    const tryInit = () => {
      attempts++;
      if (initTranslate()) {
        // Successfully initialized, now set language if saved
        if (savedLang && savedLang !== 'en') {
          const timeoutId = setTimeout(() => {
            const select = document.querySelector('.goog-te-combo');
            if (select && select.value !== savedLang) {
              select.value = savedLang;
              const event = new Event('change', { bubbles: true });
              select.dispatchEvent(event);
            }
          }, 400);
          timeoutIds.push(timeoutId);
        }
      } else if (attempts < maxAttempts) {
        const timeoutId = setTimeout(tryInit, 100);
        timeoutIds.push(timeoutId);
      }
    };

    // Start trying to initialize
    tryInit();

    // Cleanup timeouts on unmount
    return () => {
      timeoutIds.forEach(id => clearTimeout(id));
    };
  }, []);

  useEffect(() => {
    // Close language menu when clicking outside
    const handleClickOutside = (event) => {
      if (languageMenuRef.current && !languageMenuRef.current.contains(event.target)) {
        setIsLanguageOpen(false);
      }
    };

    if (isLanguageOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isLanguageOpen]);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/signin');
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to log out', error);
      }
    }
  };

  const handleLanguageChange = (langCode) => {
    // Store selected language
    localStorage.setItem('selected_language', langCode);

    // Update current language state
    const langNames = {
      'en': 'English',
      'hi': 'हिंदी',
      'es': 'Español',
      'fr': 'Français',
      'de': 'Deutsch',
      'it': 'Italiano',
      'pt': 'Português',
      'ru': 'Русский',
      'ja': '日本語',
      'ko': '한국어',
      'zh-CN': '中文',
      'ar': 'العربية',
      'bn': 'বাংলা',
      'gu': 'ગુજરાતી',
      'kn': 'ಕನ್ನಡ',
      'ml': 'മലയാളം',
      'mr': 'मराठी',
      'ne': 'नेपाली',
      'pa': 'ਪੰਜਾਬੀ',
      'ta': 'தமிழ்',
      'te': 'తెలుగు',
      'ur': 'اردو',
      'vi': 'Tiếng Việt'
    };
    setCurrentLang(langNames[langCode] || 'English');
    setIsLanguageOpen(false);

    // Notify other components (e.g. Chatbot TTS) so they sync to this language
    window.dispatchEvent(new CustomEvent('gurukul-language-changed', { detail: { language: langCode } }));

    // Function to trigger Google Translate
    const triggerTranslation = () => {
      try {
        applyLanguageSettings(langCode);

        if (langCode === 'en') {
          // Step 1: Use Google Translate's own restore function if available
          try {
            const iframe = document.querySelector('.goog-te-menu-frame') ||
                           document.querySelector('iframe[src*="translate"]');
            if (window.google && window.google.translate) {
              const te = document.querySelector('.goog-te-combo');
              if (te) {
                te.value = 'en';
                te.dispatchEvent(new Event('change', { bubbles: true }));
              }
            }
          } catch (e) { /* ignore */ }

          // Step 2: Expire the googtrans cookie on ALL domain variants
          const host = window.location.hostname;
          const parts = host.split('.');
          // e.g. gurukul.blackholeinfiverse.com → also try .blackholeinfiverse.com
          const domainVariants = [host, '.' + host];
          if (parts.length > 2) {
            const rootDomain = parts.slice(-2).join('.');
            domainVariants.push(rootDomain, '.' + rootDomain);
          }
          const pastDate = 'Thu, 01 Jan 1970 00:00:00 UTC';
          domainVariants.forEach(domain => {
            ['/'].forEach(path => {
              document.cookie = `googtrans=; expires=${pastDate}; path=${path}; domain=${domain};`;
              document.cookie = `googtrans=/en/en; expires=${pastDate}; path=${path}; domain=${domain};`;
            });
          });
          // Also clear without explicit domain (catches same-origin cookies)
          document.cookie = `googtrans=; expires=${pastDate}; path=/;`;
          document.cookie = `googtrans=/en/en; expires=${pastDate}; path=/;`;
        } else {
          // For non-English: set cookie BEFORE reload so Google picks it up on next load
          const oneYear = new Date();
          oneYear.setFullYear(oneYear.getFullYear() + 1);
          document.cookie = `googtrans=/en/${langCode}; expires=${oneYear.toUTCString()}; path=/;`;
          // NOTE: We always reload here — even if the select element exists.
          // Google Translate cannot re-translate an already-translated page in-place;
          // it needs a fresh load to translate again from the original English source.
          const select = document.querySelector('.goog-te-combo');
          if (select && select.tagName === 'SELECT') {
            select.value = langCode;
            select.dispatchEvent(new Event('change', { bubbles: true }));
          }
        }

        window.location.reload();
        return true;
      } catch (err) {
        window.location.reload();
        return true;
      }
    };

    // Try to trigger translation immediately
    if (!triggerTranslation()) {
      // If not found, wait and retry
      let attempts = 0;
      const maxAttempts = 15;

      const retry = () => {
        attempts++;
        try {
          if (triggerTranslation()) {
            // Cleanup timeouts on success
            timeoutIds.forEach(id => clearTimeout(id));
            return; // Success
          }
          if (attempts < maxAttempts) {
            const timeoutId = setTimeout(retry, 200);
            timeoutIds.push(timeoutId);
          } else {
            // Cleanup timeouts before fallback
            timeoutIds.forEach(id => clearTimeout(id));
            // Final fallback: reload page with cookie
            const expireDate = new Date();
            expireDate.setFullYear(expireDate.getFullYear() + 1);
            if (langCode === 'en') {
              const oldDate = 'Thu, 01 Jan 1970 00:00:00 UTC';
              document.cookie = `googtrans=; expires=${oldDate}; path=/;`;
              document.cookie = `googtrans=/en/en; expires=${oldDate}; path=/;`;
            } else {
              document.cookie = `googtrans=/en/${langCode}; expires=${expireDate.toUTCString()}; path=/;`;
            }
            window.location.reload();
          }
        } catch (err) {
          // Cleanup on error
          timeoutIds.forEach(id => clearTimeout(id));
          if (process.env.NODE_ENV === 'development') {
            console.warn('Translation retry error:', err);
          }
        }
      };

      const initialTimeout = setTimeout(retry, 300);
      timeoutIds.push(initialTimeout);
    }
  };

  const getCurrentLanguage = () => {
    const langNames = {
      'en': 'English',
      'hi': 'हिंदी',
      'es': 'Español',
      'fr': 'Français',
      'de': 'Deutsch',
      'it': 'Italiano',
      'pt': 'Português',
      'ru': 'Русский',
      'ja': '日本語',
      'ko': '한국어',
      'zh-CN': '中文',
      'ar': 'العربية',
      'bn': 'বাংলা',
      'gu': 'ગુજરાતી',
      'kn': 'ಕನ್ನಡ',
      'ml': 'മലയാളം',
      'mr': 'मराठी',
      'ne': 'नेपाली',
      'pa': 'ਪੰਜਾਬੀ',
      'ta': 'தமிழ்',
      'te': 'తెలుగు',
      'ur': 'اردو',
      'vi': 'Tiếng Việt'
    };

    // Try to get from Google Translate select
    if (window.google && window.google.translate) {
      const select = document.querySelector('.goog-te-combo');
      if (select && select.value) {
        return langNames[select.value] || 'English';
      }
    }

    // Fallback to saved preference
    const savedLang = localStorage.getItem('selected_language');
    if (savedLang && langNames[savedLang]) {
      return langNames[savedLang];
    }

    return currentLang;
  };

  const languages = [
    { code: 'en', name: 'English', native: 'English' },
    { code: 'hi', name: 'Hindi', native: 'हिंदी' },
    { code: 'es', name: 'Spanish', native: 'Español' },
    { code: 'fr', name: 'French', native: 'Français' },
    { code: 'de', name: 'German', native: 'Deutsch' },
    { code: 'it', name: 'Italian', native: 'Italiano' },
    { code: 'pt', name: 'Portuguese', native: 'Português' },
    { code: 'ru', name: 'Russian', native: 'Русский' },
    { code: 'ja', name: 'Japanese', native: '日本語' },
    { code: 'ko', name: 'Korean', native: '한국어' },
    { code: 'zh-CN', name: 'Chinese', native: '中文' },
    { code: 'ar', name: 'Arabic', native: 'العربية' },
    { code: 'bn', name: 'Bengali', native: 'বাংলা' },
    { code: 'gu', name: 'Gujarati', native: 'ગુજરાતી' },
    { code: 'kn', name: 'Kannada', native: 'ಕನ್ನಡ' },
    { code: 'ml', name: 'Malayalam', native: 'മലയാളം' },
    { code: 'mr', name: 'Marathi', native: 'मराठी' },
    { code: 'ne', name: 'Nepali', native: 'नेपाली' },
    { code: 'pa', name: 'Punjabi', native: 'ਪੰਜਾਬੀ' },
    { code: 'ta', name: 'Tamil', native: 'தமிழ்' },
    { code: 'te', name: 'Telugu', native: 'తెలుగు' },
    { code: 'ur', name: 'Urdu', native: 'اردو' },
    { code: 'vi', name: 'Vietnamese', native: 'Tiếng Việt' }
  ];

  return (
    <nav className="absolute top-0 left-0 w-full z-50 py-3 sm:py-6 transition-all duration-300">
      <div className="container mx-auto px-3 sm:px-6">
        <div className="glass-panel px-4 sm:px-8 py-3 sm:py-4 rounded-full flex items-center justify-between bg-black/60 backdrop-blur-xl border-white/5">

          {/* Brand & Toggle */}
          <div className="flex items-center gap-4">
            {/* Mobile Sidebar Toggle - Visible only when user is logged in (sidebar exists) */}
            {user && (
              <button
                onClick={toggleSidebar}
                className="lg:hidden text-gray-300 hover:text-white transition-colors"
              >
                {isSidebarOpen ? <FaTimes size={20} /> : <FaBars size={20} />}
              </button>
            )}

            <Link to="/" className="flex items-center gap-2 sm:gap-3 cursor-pointer group">
              <img src={logo} alt="Gurukul Logo" className="h-6 w-6 sm:h-8 sm:w-8 object-contain" />
              <span className="text-lg sm:text-2xl font-bold font-heading tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400 group-hover:to-white transition-all">
                Gurukul
              </span>
            </Link>
          </div>

          {/* Links & Actions */}
          <div className="flex items-center gap-2 sm:gap-4 lg:gap-8">
            {/* Voice Toggle */}
            <button
              onClick={toggleMute}
              className={`p-2 rounded-full transition-all border ${isMuted ? 'text-red-400 bg-red-400/10 border-red-500/20' : 'text-accent bg-accent/10 border-accent/20 hover:bg-accent/20'}`}
              title={isMuted ? "Unmute Sovereign Voice" : "Mute Sovereign Voice"}
            >
              {isMuted ? <FaVolumeMute /> : <FaVolumeUp className={isPlaying ? 'animate-pulse' : ''} />}
            </button>

            {/* Language Selector */}
            <div className="relative" ref={languageMenuRef}>
              <button
                onClick={() => setIsLanguageOpen(!isLanguageOpen)}
                className="flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full bg-black/40 hover:bg-black/60 text-gray-300 hover:text-white transition-all border border-white/5 text-xs sm:text-sm"
                title="Change Language"
              >
                <FaGlobe className="text-sm sm:text-base" />
                <span className="hidden sm:inline">{currentLang}</span>
                <FaChevronDown className={`text-[10px] transition-transform ${isLanguageOpen ? 'rotate-180' : ''}`} />
              </button>

              {/* Language Dropdown */}
              {isLanguageOpen && (
                <div className="absolute right-0 top-full mt-2 w-48 sm:w-56 bg-[#0a0c08] border border-white/5 rounded-xl shadow-2xl overflow-hidden z-50 max-h-[400px] overflow-y-auto custom-scrollbar">
                  {languages.map((lang) => (
                    <button
                      key={lang.code}
                      onClick={() => handleLanguageChange(lang.code)}
                      className="w-full text-left px-4 py-3 text-sm text-gray-300 hover:bg-black/40 hover:text-orange-400 transition-colors flex items-center justify-between border-b border-white/5 last:border-b-0"
                    >
                      <div className="flex flex-col">
                        <span className="font-medium">{lang.native}</span>
                        <span className="text-xs text-gray-500">{lang.name}</span>
                      </div>
                      {currentLang === lang.native && (
                        <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                      )}
                    </button>
                  ))}
                </div>
              )}

              {/* Hidden Google Translate Element */}
              <div id="google_translate_element" className="hidden"></div>
            </div>

            {/* Sign In Section */}
            <div className="hidden lg:flex items-center">
              {/* Drishti Link */}
              <Link 
                to="/drishti" 
                className="mr-4 text-xs font-bold text-orange-400 hover:text-orange-300 flex items-center gap-1.5 bg-orange-500/10 px-3.5 py-1.5 rounded-full border border-orange-500/20 hover:bg-orange-500/20 transition-all"
                title="Open Drishti Dashboard Control Panel"
              >
                <FaEye className="text-sm" />
                <span>Drishti Panel</span>
              </Link>

              {/* Demo Mode Toggle (Visible to everyone) */}
              <div className="flex items-center gap-2 mr-4 bg-black/40 px-3 py-1.5 rounded-full border border-white/10">
                <span className={`text-xs font-bold ${isDemoMode ? 'text-green-400' : 'text-gray-400'}`}>DEMO MODE</span>
                <button
                  onClick={toggleDemoMode}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${isDemoMode ? 'bg-green-500' : 'bg-gray-600'}`}
                >
                  <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${isDemoMode ? 'translate-x-4.5' : 'translate-x-1'}`} />
                </button>
              </div>

              {user ? (
                <div className="flex items-center gap-2 sm:gap-4">
                  <div className="text-xs sm:text-sm text-gray-300 flex items-center gap-1 sm:gap-2">
                    <FaUserCircle className="text-base sm:text-lg" />
                    <span className="hidden xl:inline">{user.email?.split('@')[0] || user.full_name || 'User'}</span>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="text-xs font-bold px-3 sm:px-4 py-1.5 sm:py-2 rounded-full bg-red-500/10 hover:bg-red-500/20 text-red-500 transition-all border border-red-500/20"
                  >
                    Log Out
                  </button>
                </div>
              ) : (
                <Link to="/signup" className="text-xs font-bold px-4 sm:px-6 py-1.5 sm:py-2 rounded-full bg-black/60 hover:bg-black/80 text-white transition-all border border-white/5 shadow-lg">
                  Sign Up
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
