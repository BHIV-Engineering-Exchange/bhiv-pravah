import { useEffect, useState } from "react";

const STORAGE_KEY = "lang";
const DEFAULT_LANG = "en";

// Simple dictionary-based translations
const dict = {
  en: {
    nav: {
      dashboard: "Dashboard",
      intake: "Intake",
      assignment: "Assignment",
      logoutAdmin: "Logout (Admin)",
      language: "Language",
      selectLanguage: "Select language",
    },
    home: {
      title: "Welcome to Gurukul",
      subtitle: "Your AI-Powered Learning Journey",
      description:
        "Unlock your potential through AI-powered assessments tailored to your unique learning style. Master coding, logic, mathematics, language arts, cultural studies, and Vedic wisdom through our comprehensive evaluation system.",
      journeyTitle: "Your Learning Journey",
      seed: "Seed",
      tree: "Tree",
      sky: "Sky",
      journeyCaption: "Foundation → Growth → Mastery",
      features: {
        smartTitle: "Smart Assessment",
        smartTag: "Tailored evaluation",
        smartDesc:
          "AI analyzes your responses to create personalized learning paths",
        progressTitle: "Progress Insights",
        progressTag: "Detailed feedback",
        progressDesc:
          "Comprehensive analytics track your growth across all domains",
        dynamicTitle: "Dynamic Learning",
        dynamicTag: "Evolving content",
        dynamicDesc:
          "Content adapts and evolves based on your learning preferences",
      },
      ctaLead:
        "Ready to discover your strengths and unlock new possibilities?",
      ctaStart: "🚀 Start Learning",
    },
    dashboard: {
      analyticsHub: "Gurukul Learning Analytics Hub",
      assessmentHistory: "Assessment History",
      assessmentHistoryDesc: "Your recent performance across multi-domain assessments",
      newAssessment: "New Assessment",
      grade: "Grade",
      questions: "questions",
      aiEvaluated: "AI Evaluated",
      quickActions: "Quick Actions",
      takeAssessment: "Take Assessment",
      aiPoweredEvaluation: "AI-powered evaluation",
      editProfile: "Edit Profile",
      updateInformation: "Update information",
      achievements: "Achievements",
      loading: "Loading dashboard...",
      averagePerformance: "Average Performance",
      compositeScoreAcross: "Composite score across",
      assessments: "assessments",
      peakAchievement: "Peak Achievement",
      highestPerformanceBenchmark: "Your highest performance benchmark",
      learningInvestment: "Learning Investment",
      totalFocusedStudyTime: "Total focused study time",
      consistencyStreak: "Consistency Streak",
      consecutiveDaysOfLearning: "Consecutive days of learning",
      ancientGurukul: "Ancient Gurukul Learning System",
      ancientGurukulDesc: "Traditional wisdom meets modern AI-powered learning",
      yearsOld: "5000+ Years Old",
      experienceGurukul: "Experience Gurukul Platform",
      aiPoweredAssessments: "AI-powered assessments and learning",
      tenQuestions: "10 Questions",
      thirtyMinutes: "30 Minutes",
      aiGenerated: "AI Generated",
      aiEvaluation: "AI Evaluation",
      tryAssessmentNow: "Try Assessment Now",
      startYourJourney: "Start Your Journey",
      takeYourFirstAssessment: "Take your first assessment to unlock analytics",
      takeYourFirstAssessmentCta: "Take Your First Assessment",
      currentLevel: "Current Level",
    },
    intake: {
      backToDashboard: "Back to Dashboard",
      back: "Back",
      editYourProfile: "Edit Your Profile",
      welcomeToGurukul: "Welcome to Gurukul!",
      updateInfo: "Update your information and learning preferences",
      tellUsAboutYou: "Tell us about yourself to personalize your learning experience",
      loadingForm: "Loading your personalized form...",
      formConfigNotAvailable: "Form configuration not available",
      returnToDashboard: "Return to Dashboard",
    },
    assignment: {
      evaluatingTitle: "Evaluating Your Assignment",
      evaluatingSubtitle: "Our AI is analyzing your responses...",
      checkingAccuracy: "✓ Checking answers for accuracy",
      evaluatingExplanation: "✓ Evaluating explanation quality",
      analyzingReasoning: "✓ Analyzing reasoning clarity",
      generatingFeedback: "⏳ Generating personalized feedback",
    },
  },
  hi: {
    nav: {
      dashboard: "डैशबोर्ड",
      intake: "प्रवेश",
      assignment: "असाइनमेंट",
      logoutAdmin: "लॉगआउट (एडमिन)",
      language: "भाषा",
      selectLanguage: "भाषा चुनें",
    },
    home: {
      title: "गुरुकुल में आपका स्वागत है",
      subtitle: "आपकी एआई-संचालित सीखने की यात्रा",
      description:
        "अपनी सीखने की शैली के अनुसार तैयार की गई एआई-आधारित आकलन के माध्यम से अपनी क्षमता को अनलॉक करें। कोडिंग, लॉजिक, गणित, भाषा, संस्कृति और वैदिक ज्ञान में महारत हासिल करें हमारे व्यापक मूल्यांकन प्रणाली के साथ।",
      journeyTitle: "आपकी सीखने की यात्रा",
      seed: "बीज",
      tree: "वृक्ष",
      sky: "आकाश",
      journeyCaption: "आधार → विकास → प्रावीण्य",
      features: {
        smartTitle: "स्मार्ट आकलन",
        smartTag: "अनुकूलित मूल्यांकन",
        smartDesc:
          "एआई आपके उत्तरों का विश्लेषण कर व्यक्तिगत सीखने का मार्ग बनाता है",
        progressTitle: "प्रगति अंतर्दृष्टि",
        progressTag: "विस्तृत प्रतिक्रिया",
        progressDesc:
          "समग्र विश्लेषण आपकी सभी क्षेत्रों में वृद्धि को ट्रैक करता है",
        dynamicTitle: "गति���ील सीखना",
        dynamicTag: "विकसित होती सामग्री",
        dynamicDesc:
          "सामग्री आपकी सीखने की प्राथमिकताओं के आधार पर अनुकूलित और विकसित होती है",
      },
      ctaLead:
        "क्या आप अपनी क्षमताओं की खोज करने और नए अवसरों को अनलॉक करने के लिए तैयार हैं?",
      ctaStart: "🚀 सीखना शुरू करें",
    },
    dashboard: {
      analyticsHub: "गुरुकुल लर्निंग एनालिटिक्स हब",
      assessmentHistory: "मूल्यांकन इतिहास",
      assessmentHistoryDesc: "बहु-डोमेन आकलनों में आपकी हाल की प्रदर्शन",
      newAssessment: "नया आकलन",
      grade: "ग्रेड",
      questions: "प्रश्न",
      aiEvaluated: "एआई मूल्यांकित",
      quickActions: "त्वरित क्रियाएँ",
      takeAssessment: "आकलन लें",
      aiPoweredEvaluation: "एआई-संचालित मू��्यांकन",
      editProfile: "प्रोफ़ाइल संपादित करें",
      updateInformation: "जानकारी अपडेट करें",
      achievements: "उपलब्धियाँ",
      loading: "डैशबोर्ड लोड हो रहा है...",
      averagePerformance: "औसत प्रदर्शन",
      compositeScoreAcross: "कुल स्कोर",
      assessments: "आकलन",
      peakAchievement: "सर्वोच्च उपलब्धि",
      highestPerformanceBenchmark: "आपकी सर्वोच्च प्रदर्शन मानक",
      learningInvestment: "सीखने में निवेश",
      totalFocusedStudyTime: "कुल केंद्रित अध्ययन समय",
      consistencyStreak: "निरंतरता श्रृंखला",
      consecutiveDaysOfLearning: "लगातार सीखने के दिन",
      ancientGurukul: "प्राचीन गुरुकुल शिक्षण प्रणाली",
      ancientGurukulDesc: "पारंपरिक ज्ञान और आधुनिक एआई-संचालित शिक्षण का संगम",
      yearsOld: "5000+ वर्ष पुरानी",
      experienceGurukul: "गुरुकुल प्लेटफ़ॉर्म का अनुभव करें",
      aiPoweredAssessments: "एआई-संचालित आकलन और सीख",
      tenQuestions: "10 प्रश्न",
      thirtyMinutes: "30 मिनट",
      aiGenerated: "एआई द्वारा निर्मित",
      aiEvaluation: "एआई मूल्यांकन",
      tryAssessmentNow: "अभी आकलन आज़माएँ",
      startYourJourney: "अपनी यात्रा शुरू करें",
      takeYourFirstAssessment: "एनालिटिक्स अनलॉक करने के लिए अपना पहला आकलन लें",
      takeYourFirstAssessmentCta: "अपना पहला आकलन लें",
      currentLevel: "वर्तमान स्तर",
    },
    intake: {
      backToDashboard: "डैशबोर्ड पर लौटें",
      back: "वापस",
      editYourProfile: "अपनी प्रोफ़ाइल संपादित करें",
      welcomeToGurukul: "गुरुकुल में आपका स्वागत है!",
      updateInfo: "अपनी जानकारी और सीखने की प्राथमिकताएँ अपडे�� करें",
      tellUsAboutYou: "अपने बारे में बताएं ताकि हम आपकी सीखने का अनुभव वैयक्तिकृत कर सकें",
      loadingForm: "आपका वैयक्तिकृत फॉर्म लोड हो रहा है...",
      formConfigNotAvailable: "फॉर्म कॉन्फ़िगरेशन उपलब्ध नहीं है",
      returnToDashboard: "डैशबोर्ड पर लौटें",
    },
    assignment: {
      evaluatingTitle: "आपके असाइनमेंट का मूल्यांकन हो रहा है",
      evaluatingSubtitle: "हमारा एआई आपके उत्तरों का विश्लेषण कर रहा है...",
      checkingAccuracy: "✓ उत्तरों की सटीकता जाँच रहा है",
      evaluatingExplanation: "✓ स्पष्टीकरण की गुणवत्ता का मूल्यांकन",
      analyzingReasoning: "✓ तर्क की स्��ष्टता का विश्लेषण",
      generatingFeedback: "⏳ व्यक्तिगत प्रतिक्रिया उत्पन्न की जा रही है",
    },
  },
  mr: {
    nav: {
      dashboard: "डॅशबोर्ड",
      intake: "इंटेक",
      assignment: "असाइनमेंट",
      logoutAdmin: "लॉगआउट (अ‍ॅडमिन)",
      language: "भाषा",
      selectLanguage: "भाषा निवडा",
    },
    home: {
      title: "गुरुकुलमध्ये आपले स्वागत आहे",
      subtitle: "तुमची एआय-संचालित शिकण्याची यात्रा",
      description:
        "तुमच्या शिकण्याच्या शैलीनुसार तयार केलेल्या एआय-आधारित मूल्यांकनाद्वारे तुमची क्षमता उघडा. कोडिंग, लॉजिक, गणित, भाषा, संस्कृती आणि वैदिक ज्ञान यात प्राविण्य मिळवा आमच्या सर्वसमावेशक मूल्यमापन प्रणालीद्वारे.",
      journeyTitle: "तुमची शिकण्याची यात्रा",
      seed: "बीज",
      tree: "वृक्ष",
      sky: "आकाश",
      journeyCaption: "पायाभूत → वाढ → प्राविण्य",
      features: {
        smartTitle: "स्मार्ट मूल्यमापन",
        smartTag: "अनुरूप मूल्यांकन",
        smartDesc:
          "एआय तुमच्या उत्तरांचे विश्लेषण करून वैयक्तिक शिकण्याचे मार्ग तयार करते",
        progressTitle: "प्रगती अंतर्दृष्टी",
        progressTag: "तपशीलवार अभिप्राय",
        progressDesc:
          "सर्व क्षेत्रांमधील तुमची वाढ सर्वसमावेशक विश्लेषणाद्वारे ट्रॅक केली जाते",
        dynamicTitle: "गतिमान शिक्षण",
        dynamicTag: "बदलणारी सामग्री",
        dynamicDesc:
          "सामग्री तुमच्या शिकण्याच्या पसंतीनुसार जुळवून घेत आणि विकसित होत राहते",
      },
      ctaLead:
        "तुमच्या सामर्थ्यांचा शोध घेऊन नवे संधी उघडण्यासाठी तयार आहात का?",
      ctaStart: "🚀 शिकायला सुरुवात करा",
    },
    dashboard: {
      analyticsHub: "गुरुकुल लर्निंग अ‍ॅनालिटिक्स हब",
      assessmentHistory: "मूल्यमापन इतिहास",
      assessmentHistoryDesc: "अनेक क्षेत्रांतील मूल्यमापनांतील तुमचा अलीकडील परफॉर्मन्स",
      newAssessment: "नवीन मूल्यमापन",
      grade: "ग्रेड",
      questions: "प्रश्न",
      aiEvaluated: "एआय मूल्यमापन",
      quickActions: "जलद क्रिया",
      takeAssessment: "मूल्यमापन द्या",
      aiPoweredEvaluation: "एआय-संचालित मूल्यमापन",
      editProfile: "प्रोफाइल सं��ादित करा",
      updateInformation: "माहिती अपडेट करा",
      achievements: "उपलब्धी",
      loading: "डॅशबोर्ड लोड होत आहे...",
      averagePerformance: "सरासरी कामगिरी",
      compositeScoreAcross: "एकत्रित गुण",
      assessments: "मूल्यमापन",
      peakAchievement: "सर्वोच्च उपलब्धी",
      highestPerformanceBenchmark: "तुमचा सर्वोच्च कामगिरी मानदंड",
      learningInvestment: "शिकण्यामधील गुंतवणूक",
      totalFocusedStudyTime: "एकूण केंद्रित अभ्यास वेळ",
      consistencyStreak: "सातत्य मालिक",
      consecutiveDaysOfLearning: "सलग शिकण्याचे दिवस",
      ancientGurukul: "प्राचीन गुरुकुल शिक्षण प्रणाली",
      ancientGurukulDesc: "पारंपरिक ज्ञान आणि आधुनिक एआय-संचालित शिक्षण यांचा संगम",
      yearsOld: "5000+ वर्षे जुनी",
      experienceGurukul: "गुरुकुल प्लॅटफॉर्मचा अनुभव घ्या",
      aiPoweredAssessments: "एआय-संचालित मूल्यमापन आणि शिक्षण",
      tenQuestions: "10 प्रश्न",
      thirtyMinutes: "30 मिनिटे",
      aiGenerated: "एआय निर्मित",
      aiEvaluation: "एआय मूल्यमापन",
      tryAssessmentNow: "आता मूल्यमापन करून पहा",
      startYourJourney: "तुमची यात्रा सुरू करा",
      takeYourFirstAssessment: "एनालिटिक्स अनलॉक करण्यासाठी तुमचे पह��ले मूल्यमापन द्या",
      takeYourFirstAssessmentCta: "तुमचे पहिले मूल्यमापन द्या",
      currentLevel: "सध्याचा स्तर",
    },
    intake: {
      backToDashboard: "डॅशबोर्डवर परत",
      back: "मागे",
      editYourProfile: "तुमची प्रोफाइल संपादित करा",
      welcomeToGurukul: "गुरुकुलमध्ये आपले स्वागत आहे!",
      updateInfo: "तुमची माहिती आणि शिकण्याच्या पसंती अपडेट करा",
      tellUsAboutYou: "तुमच्या शिकण्याचा अनुभव वैयक्तिक करण्यासाठी तुमच्याबद्दल सांगा",
      loadingForm: "तुमचा वैयक्तिक फॉर्म लोड होत आहे...",
      formConfigNotAvailable: "फॉर्म कॉन्फिगरेशन उपलब्ध नाही",
      returnToDashboard: "डॅशबोर्डवर परत",
    },
    assignment: {
      evaluatingTitle: "तुमच्या असाइनमेंटचे मूल्यमापन होत आहे",
      evaluatingSubtitle: "आमचा एआय तुमच्या उत्तरांचे विश्लेषण करत आहे...",
      checkingAccuracy: "✓ उत्तरांची अचूकता तपासत आहे",
      evaluatingExplanation: "✓ स्पष्टीकरणाची गुणवत्ता मूल्यमापन",
      analyzingReasoning: "✓ विचारशक्तीची स्पष्टता विश्लेषित",
      generatingFeedback: "⏳ वैयक्तिक अभिप्राय तयार करत आहे",
    },
  },
};

const getFromPath = (obj, path) => {
  if (!path) return undefined;
  return path.split(".").reduce((acc, part) => (acc ? acc[part] : undefined), obj);
};

export const i18n = {
  getLang() {
    if (typeof window === "undefined") return DEFAULT_LANG;
    return localStorage.getItem(STORAGE_KEY) || DEFAULT_LANG;
  },
  setLang(code) {
    if (typeof window === "undefined") return;
    localStorage.setItem(STORAGE_KEY, code);
    if (typeof document !== "undefined") document.documentElement.lang = code;
    window.dispatchEvent(new CustomEvent("languagechange", { detail: { lang: code } }));
  },
  t(key) {
    const lang = this.getLang();
    const byLang = dict[lang] || dict[DEFAULT_LANG];
    return getFromPath(byLang, key) || getFromPath(dict[DEFAULT_LANG], key) || key;
  },
  has(key) {
    const lang = this.getLang();
    const byLang = dict[lang] || dict[DEFAULT_LANG];
    return getFromPath(byLang, key) != null;
  },
};

export function useI18n() {
  const [lang, setLang] = useState(i18n.getLang());

  useEffect(() => {
    const onChange = (e) => {
      setLang((e && e.detail && e.detail.lang) || i18n.getLang());
    };
    const onStorage = (e) => {
      if (e.key === STORAGE_KEY) setLang(e.newValue || DEFAULT_LANG);
    };
    window.addEventListener("languagechange", onChange);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener("languagechange", onChange);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  const t = (key) => {
    const byLang = dict[lang] || dict[DEFAULT_LANG];
    return getFromPath(byLang, key) || getFromPath(dict[DEFAULT_LANG], key) || key;
  };

  return { t, lang };
}
