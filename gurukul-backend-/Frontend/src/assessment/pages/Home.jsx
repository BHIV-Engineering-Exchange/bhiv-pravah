import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { Target, BarChart3, Zap } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import StudentRedirect from "../components/StudentRedirect";
import { useI18n } from "../lib/i18n";

export default function Home() {
  const [isMobile, setIsMobile] = useState(false);
  const { t } = useI18n();

  // Detect mobile via coarse pointer or small viewport; update on resize/orientation
  useEffect(() => {
    const check = () =>
      window.matchMedia('(pointer: coarse)').matches || window.innerWidth <= 768;
    const update = () => setIsMobile(check());

    update();
    window.addEventListener('resize', update);
    window.addEventListener('orientationchange', update);
    return () => {
      window.removeEventListener('resize', update);
      window.removeEventListener('orientationchange', update);
    };
  }, []);

  // Control page scrolling: disabled on desktop, enabled on mobile
  useEffect(() => {
    if (isMobile) {
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    } else {
      document.body.style.overflow = 'hidden';
      document.documentElement.style.overflow = 'hidden';
    }
    return () => {
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    };
  }, [isMobile]);

  const homeContent = (
    <div className={`${isMobile ? 'min-h-screen overflow-y-auto' : 'fixed inset-0 overflow-hidden'} flex items-center justify-center p-4 text-white`}>
      <div className={`w-full max-w-4xl ${isMobile ? 'h-auto overflow-visible' : 'h-full overflow-hidden'} flex items-center justify-center`}>
        <div className={`bg-gradient-to-br from-white/10 via-white/5 to-transparent backdrop-blur-lg border border-white/20 rounded-2xl shadow-2xl p-6 sm:p-8 space-y-4 ${isMobile ? 'overflow-y-auto max-h-none' : 'overflow-hidden max-h-full'} relative`}>
          {/* Decorative elements */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-purple-500/20 to-transparent rounded-full blur-2xl"></div>
          <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-blue-500/20 to-transparent rounded-full blur-xl"></div>

          {/* Main Hero Section */}
          <div className="text-center space-y-2 relative z-10">
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold bg-gradient-to-r from-white via-blue-100 to-purple-200 bg-clip-text text-transparent drop-shadow-sm">
              {t("home.title")}
            </h1>
            <p className="text-sm sm:text-base lg:text-lg text-white/90 font-medium">
              {t("home.subtitle")}
            </p>
            <p className="text-xs sm:text-sm text-white/80 max-w-2xl mx-auto leading-relaxed">
              {t("home.description")}
            </p>
          </div>

          {/* Learning Path */}
          <div className="text-center space-y-2 relative z-10">
            <h2 className="text-sm sm:text-lg font-semibold text-white/90 mb-2">{t("home.journeyTitle")}</h2>
            <div className="flex justify-center items-center gap-1.5 sm:gap-4 bg-white/5 rounded-xl p-2 sm:p-3 border border-white/10">
              <div className="flex items-center gap-1.5 sm:gap-2 bg-green-500/20 rounded-lg px-2 sm:px-3 py-0.5 sm:py-1 border border-green-500/30">
                <span className="text-xs sm:text-lg">🌱</span>
                <span className="text-green-300 font-medium text-xs sm:text-sm">{t("home.seed")}</span>
              </div>
              <span className="text-white/70 text-xs sm:text-sm font-bold">→</span>
              <div className="flex items-center gap-1.5 sm:gap-2 bg-blue-500/20 rounded-lg px-2 sm:px-3 py-0.5 sm:py-1 border border-blue-500/30">
                <span className="text-xs sm:text-lg">🌳</span>
                <span className="text-blue-300 font-medium text-xs sm:text-sm">{t("home.tree")}</span>
              </div>
              <span className="text-white/70 text-xs sm:text-sm font-bold">→</span>
              <div className="flex items-center gap-1.5 sm:gap-2 bg-purple-500/20 rounded-lg px-2 sm:px-3 py-0.5 sm:py-1 border border-purple-500/30">
                <span className="text-xs sm:text-lg">🌌</span>
                <span className="text-purple-300 font-medium text-xs sm:text-sm">{t("home.sky")}</span>
              </div>
            </div>
            <p className="text-white/70 text-xs max-w-lg mx-auto italic">
              {t("home.journeyCaption")}
            </p>
          </div>



          {/* Features Overview */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 relative z-10">
            <div className="bg-gradient-to-br from-orange-500/15 to-red-500/10 backdrop-blur-sm rounded-2xl p-4 border border-orange-400/30 hover:border-orange-400/50 hover:shadow-lg hover:shadow-orange-500/20 transition-all duration-300 group cursor-pointer">
              <div className="flex flex-col items-center text-center space-y-3">
                <div className="group-hover:scale-110 transition-transform duration-300 p-3 bg-gradient-to-br from-orange-400/20 to-red-500/20 rounded-xl border border-orange-300/30">
                  <Target className="w-6 h-6 sm:w-8 sm:h-8 text-orange-300" strokeWidth={2} />
                </div>
                <div className="space-y-1">
                  <h3 className="font-bold text-white text-sm sm:text-base leading-tight">{t("home.features.smartTitle")}</h3>
                  <p className="text-orange-200/80 text-xs sm:text-sm font-medium">{t("home.features.smartTag")}</p>
                  <p className="text-orange-100/60 text-xs leading-relaxed hidden sm:block">{t("home.features.smartDesc")}</p>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-500/15 to-cyan-500/10 backdrop-blur-sm rounded-2xl p-4 border border-blue-400/30 hover:border-blue-400/50 hover:shadow-lg hover:shadow-blue-500/20 transition-all duration-300 group cursor-pointer">
              <div className="flex flex-col items-center text-center space-y-3">
                <div className="group-hover:scale-110 transition-transform duration-300 p-3 bg-gradient-to-br from-blue-400/20 to-cyan-500/20 rounded-xl border border-blue-300/30">
                  <BarChart3 className="w-6 h-6 sm:w-8 sm:h-8 text-blue-300" strokeWidth={2} />
                </div>
                <div className="space-y-1">
                  <h3 className="font-bold text-white text-sm sm:text-base leading-tight">{t("home.features.progressTitle")}</h3>
                  <p className="text-blue-200/80 text-xs sm:text-sm font-medium">{t("home.features.progressTag")}</p>
                  <p className="text-blue-100/60 text-xs leading-relaxed hidden sm:block">{t("home.features.progressDesc")}</p>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-purple-500/15 to-pink-500/10 backdrop-blur-sm rounded-2xl p-4 border border-purple-400/30 hover:border-purple-400/50 hover:shadow-lg hover:shadow-purple-500/20 transition-all duration-300 group cursor-pointer">
              <div className="flex flex-col items-center text-center space-y-3">
                <div className="group-hover:scale-110 transition-transform duration-300 p-3 bg-gradient-to-br from-purple-400/20 to-pink-500/20 rounded-xl border border-purple-300/30">
                  <Zap className="w-6 h-6 sm:w-8 sm:h-8 text-purple-300" strokeWidth={2} />
                </div>
                <div className="space-y-1">
                  <h3 className="font-bold text-white text-sm sm:text-base leading-tight">{t("home.features.dynamicTitle")}</h3>
                  <p className="text-purple-200/80 text-xs sm:text-sm font-medium">{t("home.features.dynamicTag")}</p>
                  <p className="text-purple-100/60 text-xs leading-relaxed hidden sm:block">{t("home.features.dynamicDesc")}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Call to Action */}
          <div className="text-center space-y-3 relative z-10">
            <p className="text-white/80 text-xs sm:text-sm font-medium">
              {t("home.ctaLead")}
            </p>

            <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">
              <Link
                to="/dashboard"
                className="bg-gradient-to-r from-orange-600 via-orange-500 to-red-600 hover:from-orange-700 hover:via-orange-600 hover:to-red-700 text-white px-6 sm:px-8 py-3 rounded-xl text-sm sm:text-base font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 w-full sm:w-auto border border-orange-500/30"
              >
                {t("home.ctaStart")}
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {user ? (
        <StudentRedirect>
          {homeContent}
        </StudentRedirect>
      ) : (
        homeContent
      )}
    </>
  );
}
