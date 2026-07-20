import { useState, useEffect } from 'react';

export default function useLanguage() {
  const [language, setLanguageState] = useState(() => {
    return localStorage.getItem('pref_language') || 'en';
  });

  useEffect(() => {
    const handleStorageChange = () => {
      const newLang = localStorage.getItem('pref_language') || 'en';
      setLanguageState(newLang);
    };

    window.addEventListener('storage', handleStorageChange);
    
    const interval = setInterval(handleStorageChange, 500);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      clearInterval(interval);
    };
  }, []);

  const setLanguage = (lang) => {
    localStorage.setItem('pref_language', lang);
    setLanguageState(lang);
  };

  return { language, setLanguage };
}
