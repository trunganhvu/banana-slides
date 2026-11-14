import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Home, ArrowUp } from "lucide-react";
import { Button, Card } from "@/components/shared";
import { useT } from "@/hooks/useT";
import { settingsI18n } from "./settingsI18n";
const SCROLL_SHOW_THRESHOLD = 300;

export const SettingsPageFrame: React.FC<{
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
}> = ({ children, title, subtitle }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const t = useT(settingsI18n);
  const [showTop, setShowTop] = useState(false);
  const hasInAppBackHistory =
    typeof window !== "undefined" &&
    typeof window.history.state?.idx === "number"
      ? window.history.state.idx > 0
      : false;
  const canNavigateBack =
    hasInAppBackHistory ||
    Boolean((location.state as { from?: string } | null)?.from);

  const handleBack = () => {
    if (canNavigateBack) {
      navigate(-1);
      return;
    }
    navigate("/");
  };

  useEffect(() => {
    const onScroll = () => setShowTop(window.scrollY > SCROLL_SHOW_THRESHOLD);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-banana-50 dark:from-background-primary to-yellow-50 dark:to-background-primary">
      <div className="container mx-auto px-2.5 sm:px-4 py-4 sm:py-8 max-w-4xl">
        <Card className="p-3.5 sm:p-6 md:p-8 rounded-xl sm:rounded-2xl">
          <div className="space-y-6 sm:space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 sm:pb-6 border-b border-gray-200 dark:border-border-primary">
              <div className="flex items-center gap-2.5 sm:gap-4 min-w-0">
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<Home size={18} />}
                  onClick={handleBack}
                  className="shrink-0 whitespace-nowrap px-2.5 sm:px-3"
                  title={t("nav.backToHome")}
                >
                  <span className="hidden sm:inline">{t("nav.backToHome")}</span>
                </Button>
                <div className="min-w-0">
                  <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-foreground-primary leading-tight">
                    {title || t("settings.title")}
                  </h1>
                  <p className="text-xs sm:text-sm text-gray-500 dark:text-foreground-tertiary mt-0.5 sm:mt-1">
                    {subtitle || t("settings.subtitle")}
                  </p>
                </div>
              </div>
            </div>

            {children}
          </div>
        </Card>
      </div>

      {showTop && (
        <button
          data-testid="back-to-top-button"
          aria-label="Back to top"
          title="Back to top"
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          className="fixed bottom-6 right-6 p-3 rounded-full bg-banana-500 text-white shadow-lg hover:bg-banana-600 transition-all z-50"
        >
          <ArrowUp size={20} />
        </button>
      )}
    </div>
  );
};