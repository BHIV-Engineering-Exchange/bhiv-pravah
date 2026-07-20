import React, { useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { i18n, useI18n } from "../lib/i18n";

export default function Layout() {
  const { user, login } = useAuth();
  const [isAdmin, setIsAdmin] = React.useState(
    () =>
      typeof window !== "undefined" &&
      sessionStorage.getItem("is_admin") === "1"
  );
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const location = useLocation();
  const isHome = location.pathname === "/";

  // Language selection state using i18n
  const { t, lang } = useI18n();
  const [isLangOpen, setIsLangOpen] = React.useState(false);
  const langRefDesktop = React.useRef(null);
  const langRefMobile = React.useRef(null);
  const languages = [
    { code: "en", label: "English" },
    { code: "hi", label: "हिन्दी" },
    { code: "mr", label: "मराठी" },
  ];

  React.useEffect(() => {
    const onClick = (e) => {
      const inDesktop = langRefDesktop.current && langRefDesktop.current.contains(e.target);
      const inMobile = langRefMobile.current && langRefMobile.current.contains(e.target);
      if (!inDesktop && !inMobile) {
        setIsLangOpen(false);
      }
    };
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, []);

  // DOM-level translation pass to cover pages not yet wired to i18n
  React.useEffect(() => {
    if (typeof document === "undefined") return;
    if (lang === "en") return;

    const maps = {
      hi: {
        "Assessment History": "मूल्यांकन इतिहास",
        "Your recent performance across multi-domain assessments": "बहु-डोमेन आकलनों में आपकी हाल की प्रदर्शन",
        "New Assessment": "नया आकलन",
        "Grade": "ग्रेड",
        "questions": "प्रश्न",
        "AI Evaluated": "एआई मूल्यांकित",
        "Quick Actions": "त्वरित क्रियाएँ",
        "Take Assessment": "आकलन लें",
        "AI-powered evaluation": "ए��ई-संचालित मूल्यांकन",
        "Edit Profile": "प्रोफ़ाइल संपादित करें",
        "Update information": "जानकारी अपडेट करें",
        "Achievements": "उपलब्धियाँ",
        "Ancient Gurukul Learning System": "प्राचीन गुरुकुल शिक्षण प्रणाली",
        "Traditional wisdom meets modern AI-powered learning": "पारंपरिक ज्ञान और आधुनिक एआई-संचालित शिक्षण का संगम",
        "5000+ Years Old": "5000+ वर्ष पुरानी",
        "Loading dashboard...": "डैशबोर्ड लोड हो रहा है...",
        "Average Performance": "औसत प्रदर्शन",
        "Composite score across": "कुल स्कोर",
        "assessments": "आकलन",
        "Peak Achievement": "सर्वोच्च उपलब्धि",
        "Your highest performance benchmark": "आपकी सर्वोच्च प्रदर्शन मानक",
        "Learning Investment": "सीखने में निवेश",
        "Total focused study time": "कुल केंद्रित अ���्ययन समय",
        "Consistency Streak": "निरंतरता श्रृंखला",
        "Consecutive days of learning": "लगातार सीखने के दिन",
        "Welcome back,": "वापसी पर स्वागत है,",
        "Welcome,": "स्वागत है,",
        "Gurukul Learning Analytics Hub": "गुरुकुल लर्निंग एनालिटिक्स हब",
        "Back to Dashboard": "डैशबोर्ड पर लौटें",
        "Back": "वापस",
        "Edit Your Profile": "अपनी प्रोफ़ाइल संपादित करें",
        "Welcome to Gurukul!": "गुरुकुल में आपका स्वागत है!",
        "Update your information and learning preferences": "अपनी जानकारी और सीखने की प्राथमिकताएँ अपडेट करें",
        "Tell us about yourself to personalize your learning experience": "अपने बारे में बताएं ताकि हम आपकी सीखने का अनुभव वैयक्तिकृत कर सकें",
        "Loading your personalized form...": "आपका वैयक्तिकृत फॉ��्म लोड हो रहा है...",
        "Form configuration not available": "फ��र्म कॉन्फ़िगरेशन उपलब्ध नहीं है",
        "Return to Dashboard": "डैशबोर्ड पर लौटें",
        "Evaluating Your Assignment": "आपके असाइनमेंट का मूल्यांकन हो रहा है",
        "Our AI is analyzing your responses...": "हमारा एआई आपके उत्तरों का विश्लेषण कर रहा है...",
        "✓ Checking answers for accuracy": "✓ उत्तरों की सटीकता जाँच रहा है",
        "✓ Evaluating explanation quality": "✓ स्पष्टीकरण की गुणवत्ता का मूल्यांकन",
        "✓ Analyzing reasoning clarity": "✓ तर्क की स्पष्टता का विश्लेषण",
        "⏳ Generating personalized feedback": "⏳ व्यक्तिगत प्रतिक्रिया उत्पन्न की जा रही है",
        "Start Your Journey": "अपनी यात्रा शुरू करें",
        "Take your first assessment to unlock analytics": "एनालिटिक्स अनलॉक करने के लिए अपना पहला आकलन लें",
        "10 Questions": "10 प्रश्न",
        "30 Minutes": "30 मिनट",
        "AI Generated": "एआई द्वारा निर्मित",
        "AI Evaluation": "एआई मूल्यांकन",
        "Take Your First Assessment": "अपना पहला आकलन लें",
        "Experience Gurukul Platform": "गुरुकुल प्लेटफ़ॉर्म का अनुभव करें",
        "AI-powered assessments and learning": "एआई-संचालित आकलन और सीख",
        "Try Assessment Now": "अभी आकलन आज़माएँ"
      },
      mr: {
        "Assessment History": "मूल्यमापन इतिहास",
        "Your recent performance across multi-domain assessments": "अनेक क्षेत्रांतील मूल्यमापनांतील तुमचा अलीकडील परफॉर्मन्स",
        "New Assessment": "नवीन मूल्यमापन",
        "Grade": "ग्रेड",
        "questions": "प्रश्न",
        "AI Evaluated": "एआय मूल्यमापन",
        "Quick Actions": "जलद क्रिया",
        "Take Assessment": "मूल्यमापन द्या",
        "AI-powered evaluation": "एआय-संचालित मूल्यमापन",
        "Edit Profile": "प्रोफाइल संपादित करा",
        "Update information": "माहिती अपडेट करा",
        "Achievements": "उपलब्धी",
        "Ancient Gurukul Learning System": "प्राचीन गुरुकुल शिक्षण प्रणाली",
        "Traditional wisdom meets modern AI-powered learning": "पारंपरिक ज्ञान आणि आधुनिक एआय-संचालित शिक्षण यांचा संगम",
        "5000+ Years Old": "5000+ वर्षे जुनी",
        "Loading dashboard...": "डॅशबोर्ड लोड होत आहे...",
        "Average Performance": "सरासरी कामगिरी",
        "Composite score across": "एकत्रित गुण",
        "assessments": "मूल्यमापन",
        "Peak Achievement": "सर्वोच्च उपलब्धी",
        "Your highest performance benchmark": "तुमचा सर्वोच्च कामगिरी मानदंड",
        "Learning Investment": "शिकण्यामधील गुंतवण��क",
        "Total focused study time": "एकूण केंद्रित अभ्यास वेळ",
        "Consistency Streak": "सातत्य मालिक",
        "Consecutive days of learning": "सलग शिकण्याचे दिवस",
        "Welcome back,": "पुन्हा स्वागत आहे,",
        "Welcome,": "स्वागत आहे,",
        "Gurukul Learning Analytics Hub": "गुरुकुल लर्निंग अ‍ॅनालिटिक्स हब",
        "Back to Dashboard": "डॅशबोर्डवर परत",
        "Back": "मागे",
        "Edit Your Profile": "तुमची प्रोफाइल संपादित करा",
        "Welcome to Gurukul!": "गुरुकुलमध्ये आपले स्वागत आहे!",
        "Update your information and learning preferences": "तुमची माहिती आणि शिकण्याच्या पसंती अपडेट करा",
        "Tell us about yourself to personalize your learning experience": "तुमच्या शिकण्याचा अनुभव वैयक्तिक करण्यासाठी तुमच्याबद्दल सांगा",
        "Loading your personalized form...": "तुमचा वैयक्तिक फॉर्म लोड होत आहे...",
        "Form configuration not available": "फॉर्म कॉन्फिगरेशन उपलब्ध नाही",
        "Return to Dashboard": "डॅशबोर्डवर परत",
        "Evaluating Your Assignment": "तुमच्या असाइनमेंटचे मूल्यमापन होत आहे",
        "Our AI is analyzing your responses...": "आमचा एआय तुमच्या उत्तरांचे विश्लेषण करत आहे...",
        "✓ Checking answers for accuracy": "✓ उत्तरांची अचूकता तपासत आहे",
        "✓ Evaluating explanation quality": "✓ स्पष्टीकरणाची गुणवत्ता मूल्यमापन",
        "✓ Analyzing reasoning clarity": "✓ विचारशक्तीची स्पष्टता विश्लेषित",
        "⏳ Generating personalized feedback": "⏳ वैयक्तिक अभिप्राय तयार करत आहे",
        "Start Your Journey": "तुमची यात्रा सुरू करा",
        "Take your first assessment to unlock analytics": "एन��लिटिक्स अनलॉक करण्यासाठी तुमचे पहिले मूल्यमापन द्या",
        "10 Questions": "10 प्रश्न",
        "30 Minutes": "30 मिनिटे",
        "AI Generated": "एआय निर्मित",
        "AI Evaluation": "एआय मूल्यमापन",
        "Take Your First Assessment": "तुमचे पहिले मूल्यमापन द्या",
        "Experience Gurukul Platform": "गुरुकुल प्लॅटफॉर्मचा अनुभव घ्या",
        "AI-powered assessments and learning": "एआय-संचालित मूल्यमापन आणि शिक्षण",
        "Try Assessment Now": "आता मूल्यमापन करून पहा"
      }
    };

    const map = maps[lang];
    if (!map) return;

    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);

    nodes.forEach((node) => {
      const p = node.parentElement;
      if (!p) return;
      const tag = p.tagName;
      if (tag === 'SCRIPT' || tag === 'STYLE') return;
      let text = node.nodeValue;
      if (!text || !text.trim()) return;
      let changed = false;
      for (const [en, tr] of Object.entries(map)) {
        if (text.includes(en)) {
          text = text.split(en).join(tr);
          changed = true;
        }
      }
      if (changed) node.nodeValue = text;
    });
  }, [lang, location.pathname]);

  // Listen for changes to sessionStorage to update admin state
  React.useEffect(() => {
    const handleStorageChange = () => {
      setIsAdmin(sessionStorage.getItem("is_admin") === "1");
    };

    // Listen for storage events (when sessionStorage changes in other tabs/windows)
    window.addEventListener("storage", handleStorageChange);

    // Also check periodically for changes in the same tab
    const interval = setInterval(handleStorageChange, 1000);

    return () => {
      window.removeEventListener("storage", handleStorageChange);
      clearInterval(interval);
    };
  }, []);

  const handleAdminLogout = () => {
    sessionStorage.removeItem("is_admin");
    setIsAdmin(false);
    window.location.href = "/";
  };

  return (
    <div className="min-h-screen text-white">
      <header className="sticky top-0 z-40 border-b border-white/20 bg-white/10 backdrop-blur-md">
        <div className="mx-auto max-w-6xl px-4 py-3 sm:py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img
              src="/blackhole-logo.png"
              alt="Blackhole logo"
              className="h-10 w-auto sm:h-12"
            />
            <Link to="/" className="text-lg sm:text-xl font-semibold">
              Gurukul
            </Link>
          </div>


          {/* Desktop navigation */}
          <div className="hidden md:flex items-center gap-3">
            {/* Language Dropdown */}
            <div className="relative" ref={langRefDesktop}>
              <button
                onClick={() => setIsLangOpen((v) => !v)}
                className="rounded-md px-3 py-1.5 text-sm border border-transparent hover:border-white/20 hover:bg-white/10 flex items-center gap-2"
                aria-haspopup="listbox"
                aria-expanded={isLangOpen ? "true" : "false"}
                aria-label={t("nav.selectLanguage")}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 opacity-80" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2a10 10 0 100 20 10 10 0 000-20zm7.94 9h-3.17a15.8 15.8 0 00-.77-4.02A8.02 8.02 0 0119.94 11zM12 4a13.9 13.9 0 011.9 5H10.1A13.9 13.9 0 0112 4zM8 5.98A15.8 15.8 0 007.23 11H4.06A8.02 8.02 0 018 5.98zM4.06 13h3.17c.16 1.39.5 2.74.99 3.98A8.02 8.02 0 014.06 13zM12 20a13.9 13.9 0 01-1.9-5h3.8A13.9 13.9 0 0112 20zm4-1.98A15.8 15.8 0 0016.77 13h3.17A8.02 8.02 0 0116 18.02zM8.94 13h6.12c-.15 1.37-.48 2.71-.98 3.94H9.92A17.9 17.9 0 018.94 13zm0-2c.15-1.37.48-2.71.98-3.94h4.16c.5 1.23.83 2.57.98 3.94H8.94z" />
                </svg>
                <span>
                  {languages.find((l) => l.code === lang)?.label || "English"}
                </span>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 opacity-70" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.08 1.04l-4.25 4.25a.75.75 0 01-1.08 0L5.21 8.27a.75.75 0 01.02-1.06z" clipRule="evenodd" />
                </svg>
              </button>
              {isLangOpen && (
                <div className="absolute right-0 mt-2 w-40 rounded-md border border-white/20 bg-black/60 backdrop-blur-md shadow-lg">
                  {languages.map((l) => (
                    <button
                      key={l.code}
                      onClick={() => {
                        i18n.setLang(l.code);
                        setIsLangOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-sm hover:bg-white/10 ${lang === l.code ? "bg-white/10" : ""}`}
                      role="option"
                      aria-selected={lang === l.code ? "true" : "false"}
                    >
                      {l.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {isAdmin ? (
              <button
                onClick={handleAdminLogout}
                className="rounded-md bg-red-500 px-3 py-1.5 text-sm hover:bg-red-600"
              >
                {t("nav.logoutAdmin")}
              </button>
            ) : (
              user ? (
                <div className="flex items-center gap-2">
                  <NavLink
                    to="/dashboard"
                    className={({ isActive }) =>
                      `rounded-md px-3 py-1.5 text-sm ${isActive
                        ? "bg-white/20 border border-white/30"
                        : "border border-transparent hover:border-white/20 hover:bg-white/10"
                      }`
                    }
                  >
                    {t("nav.dashboard")}
                  </NavLink>
                  <NavLink
                    to="/assessment/intake"
                    className={({ isActive }) =>
                      `rounded-md px-3 py-1.5 text-sm ${isActive
                        ? "bg-white/20 border border-white/30"
                        : "border border-transparent hover:border-white/20 hover:bg-white/10"
                      }`
                    }
                  >
                    {t("nav.intake")}
                  </NavLink>
                  <NavLink
                    to="/assessment/assignment"
                    className={({ isActive }) =>
                      `rounded-md px-3 py-1.5 text-sm ${isActive
                        ? "bg-white/20 border border-white/30"
                        : "border border-transparent hover:border-white/20 hover:bg-white/10"
                      }`
                    }
                  >
                    {t("nav.assignment")}
                  </NavLink>
                  <div className="h-8 w-8 rounded-full bg-orange-500/20 border border-orange-500/40 flex items-center justify-center text-orange-400 font-bold">
                    {user.full_name?.charAt(0) || user.email?.charAt(0).toUpperCase()}
                  </div>
                </div>
              ) : (
                <Link
                  to="/login"
                  className="rounded-md bg-orange-500 px-4 py-2 text-sm font-medium hover:bg-orange-600 transition-colors"
                >
                  Sign In
                </Link>
              )
            )}
          </div>
          {/* Mobile controls: language + menu */}
          <div className="md:hidden flex items-center gap-2">
            <div className="relative" ref={langRefMobile}>
              <button
                onClick={() => setIsLangOpen((v) => !v)}
                className="rounded-md p-2 text-white hover:bg-white/10 border border-transparent hover:border-white/20 flex items-center gap-2"
                aria-haspopup="listbox"
                aria-expanded={isLangOpen ? "true" : "false"}
                aria-label={t("nav.selectLanguage")}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 opacity-80" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2a10 10 0 100 20 10 10 0 000-20zm7.94 9h-3.17a15.8 15.8 0 00-.77-4.02A8.02 8.02 0 0119.94 11zM12 4a13.9 13.9 0 011.9 5H10.1A13.9 13.9 0 0112 4zM8 5.98A15.8 15.8 0 007.23 11H4.06A8.02 8.02 0 018 5.98zM4.06 13h3.17c.16 1.39.5 2.74.99 3.98A8.02 8.02 0 014.06 13zM12 20a13.9 13.9 0 01-1.9-5h3.8A13.9 13.9 0 0112 20zm4-1.98A15.8 15.8 0 0016.77 13h3.17A8.02 8.02 0 0116 18.02zM8.94 13h6.12c-.15 1.37-.48 2.71-.98 3.94H9.92A17.9 17.9 0 018.94 13zm0-2c.15-1.37.48-2.71.98-3.94h4.16c.5 1.23.83 2.57.98 3.94H8.94z" />
                </svg>
                <span className="text-sm">{languages.find((l) => l.code === lang)?.label || "English"}</span>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 opacity-70" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.08 1.04l-4.25 4.25a.75.75 0 01-1.08 0L5.21 8.27a.75.75 0 01.02-1.06z" clipRule="evenodd" />
                </svg>
              </button>
              {isLangOpen && (
                <div className="absolute right-0 mt-2 w-40 rounded-md border border-white/20 bg-black/60 backdrop-blur-md shadow-lg">
                  {languages.map((l) => (
                    <button
                      key={l.code}
                      onClick={() => {
                        i18n.setLang(l.code);
                        setIsLangOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-sm hover:bg-white/10 ${lang === l.code ? "bg-white/10" : ""}`}
                      role="option"
                      aria-selected={lang === l.code ? "true" : "false"}
                    >
                      {l.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {!isHome && (
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="rounded-md p-2 text-white hover:bg-white/10"
              >
                <svg
                  className="h-6 w-6"
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  {isMobileMenuOpen ? (
                    <path d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* Mobile menu dropdown */}
        {!isHome && isMobileMenuOpen && (
          <div className="md:hidden border-t border-white/20">
            {isAdmin ? (
              <div className="p-4 space-y-3">
                <button
                  onClick={handleAdminLogout}
                  className="w-full rounded-md bg-red-500 px-3 py-1.5 text-sm hover:bg-red-600"
                >
                  {t("nav.logoutAdmin")}
                </button>
              </div>
            ) : user ? (
              <div className="space-y-2 p-4">
                <NavLink
                  to="/dashboard"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `block w-full rounded-md px-3 py-1.5 text-sm ${isActive
                      ? "bg-white/20 border border-white/30"
                      : "border border-transparent hover:border-white/20 hover:bg-white/10"
                    }`
                  }
                >
                  {t("nav.dashboard")}
                </NavLink>
                <NavLink
                  to="/assessment/intake"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `block w-full rounded-md px-3 py-1.5 text-sm ${isActive
                      ? "bg-white/20 border border-white/30"
                      : "border border-transparent hover:border-white/20 hover:bg-white/10"
                    }`
                  }
                >
                  {t("nav.intake")}
                </NavLink>
                <NavLink
                  to="/assessment/assignment"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `block w-full rounded-md px-3 py-1.5 text-sm ${isActive
                      ? "bg-white/20 border border-white/30"
                      : "border border-transparent hover:border-white/20 hover:bg-white/10"
                    }`
                  }
                >
                  {t("nav.assignment")}
                </NavLink>
              </div>
            ) : (
              <div className="p-4">
                <Link
                  to="/login"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="block w-full text-center rounded-md bg-orange-500 px-4 py-2 text-sm font-medium hover:bg-orange-600 transition-colors"
                >
                  Sign In
                </Link>
              </div>
            )}
          </div>
        )}
      </header>
      <main key={`lang-${lang}`} className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
