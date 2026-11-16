import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Sparkles,
  Zap,
  Layers,
  Download,
  ChevronRight,
  ChevronLeft,
  ArrowRight,
  Star,
  Sun,
  Moon,
  Laptop,
  CheckCircle2,
  Sliders,
  ExternalLink,
  Presentation,
  Flame,
  FileCode2,
  LogIn,
  ChevronUp
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/hooks/useTheme';
import { useT } from '@/hooks/useT';
import logoUrl from '@/assets/logo.png';

// Localized strings with 0 CJK characters
const landingI18n = {
  zh: {
    landing: {
      nav: {
        login: "Đăng nhập ngay",
        getStarted: "Bắt đầu miễn phí"
      },
      hero: {
        badge: "Trình tạo Slide AI Thế Hệ Mới • Nhanh gấp 10 lần",
        title_start: "Ý Tưởng Trượt Thành Slide",
        title_highlight: "AI Thực Hiện Chuẩn Thiết Kế",
        title_end: "",
        subtitle: "Từ ý tưởng đến bài thuyết trình chuyên nghiệp. Chỉ cần trò chuyện để AI hoàn thiện từng slide theo ý muốn và đặc biệt có thể tải về và tiếp tục biên tập trên PowerPoint.",
        cta_primary: "Bắt đầu ngay",
        cta_secondary: "Khám phá các phong cách slide"
      },
      showcase: {
        badge: "Thư viện mẫu thực tế",
        title: "Bộ Sưu Tập Slide Đẳng Cấp Đa Phong Cách",
        subtitle: "Khám phá các slide trình bày chuyên nghiệp được AI tối ưu hóa tỷ lệ vàng và bố cục phân cấp thị giác.",
        ctaUseStyle: "Sử dụng phong cách này",
        tagAutoCreated: "Được tạo tự động bởi Banana Slides AI"
      },
      features: {
        badge: "Sức mạnh vượt trội",
        title: "Tại Sao Nên Chọn Banana Slides?",
        subtitle: "Được thiết kế dành riêng cho nhà quản lý, diễn giả, doanh nhân và người sáng tạo nội dung.",
        f1_title: "Đa Dạng Phương Thức Nhập Liệu",
        f1_desc: "Tạo từ 1 câu ý tưởng ngắn, dán dàn ý thô, tài liệu mô tả chi tiết hoặc tải lên tệp PDF/PPTX cũ để AI tái tạo lại.",
        f2_title: "Bố Cục Chuẩn Studio Thiết Kế",
        f2_desc: "Tự động phân bổ tiêu đề, phân cấp ý chính và chọn hình minh họa trực quan, mang lại diện mạo chỉn chu nhất.",
        f3_title: "Chỉnh Sửa Bằng Ngôn Ngữ Tự Nhiên",
        f3_desc: "Tương tác dễ dàng như trò chuyện với designer: yêu cầu đổi màu, thay đổi cấu trúc hoặc khoanh vùng vẽ lại tức thì.",
        f4_title: "Xuất File PPTX Thật & Vector",
        f4_desc: "Tải về tệp PowerPoint gốc có thể chỉnh sửa tự do từng dòng chữ, hình khối và bảng màu trên Office hoặc Google Slides."
      },
      comparison: {
        title: "Cách Làm Cũ vs. Đột Phá Với Banana Slides",
        subtitle: "So sánh hiệu quả thực tế giữa thiết kế thủ công truyền thống và quy trình tự động hóa bằng AI.",
        oldWay: "Cách làm truyền thống",
        old1: "Mất 4 - 8 tiếng loay hoay tìm mẫu slide trên mạng",
        old2: "Tốn công căn lề, kéo thả từng hộp chữ và icon",
        old3: "Khó tìm hình minh họa chất lượng cao và đồng bộ",
        old4: "Màu sắc và font chữ dễ bị rối, thiếu chuyên nghiệp",
        newWay: "Với Banana Slides",
        new1: "Chỉ 30 giây từ ý tưởng thành bài thuyết trình hoàn chỉnh",
        new2: "Bố cục tự động tính toán theo tỷ lệ vàng và nhịp đọc",
        new3: "Kho tư liệu & hình ảnh tự động gán theo ngữ cảnh bài học/báo cáo",
        new4: "Bộ nhận diện đồng bộ, xuất file PPTX sẵn sàng trình bày",
        ctaButton: "Tiết kiệm 4 giờ ngay hôm nay"
      },
      steps: {
        title: "3 Bước Đơn Giản Để Sở Hữu Slide Đỉnh Cao",
        s1_title: "1. Đăng nhập & Nhập nội dung",
        s1_desc: "Đăng nhập nhanh với tài khoản Google và nhập ý tưởng, dàn ý hoặc tài liệu sẵn có.",
        s2_title: "2. Chọn phong cách & AI tạo slide",
        s2_desc: "Lựa chọn 1 trong 4 phong cách chủ đạo, AI tự động thiết kế toàn bộ bài thuyết trình.",
        s3_title: "3. Tinh chỉnh & Xuất PPTX",
        s3_desc: "Xem trước slide, ra lệnh chỉnh sửa nhanh bằng văn bản và tải về file PowerPoint."
      },
      ctaBanner: {
        title: "Sẵn Sàng Nâng Tầm Bài Thuyết Trình Của Bạn?",
        subtitle: "Cùng khám phá hiệu suất tạo slide mới.",
        button: "Bắt đầu ngay"
      },
      mobileSticky: {
        text: "Tạo slide AI trong 30s",
        button: "Đăng nhập"
      }
    }
  },
  en: {
    landing: {
      nav: {
        login: "Sign In",
        getStarted: "Get Started Free"
      },
      hero: {
        badge: "Next Gen AI Presentation Platform • 10x Faster",
        title_start: "Ideas Slide into Presentations",
        title_highlight: "Design-Perfect AI Execution",
        title_end: "",
        subtitle: "From raw ideas to professional presentation decks. Simply chat with AI to refine each slide and easily download native PowerPoint files to continue editing.",
        cta_primary: "Get Started Now",
        cta_secondary: "Explore Slide Styles"
      },
      showcase: {
        badge: "Real Template Showcase",
        title: "Signature Slide Collection",
        subtitle: "Explore professional presentation slides optimized by AI with golden ratios and visual hierarchy.",
        ctaUseStyle: "Use this style",
        tagAutoCreated: "Auto-generated by Banana Slides AI"
      },
      features: {
        badge: "Unmatched Capabilities",
        title: "Why Choose Banana Slides?",
        subtitle: "Designed for managers, speakers, entrepreneurs and content creators.",
        f1_title: "Multiple Input Methods",
        f1_desc: "Create from a single prompt, paste raw outlines, detailed notes or upload legacy PDF/PPTX files.",
        f2_title: "Studio-Grade Layouts",
        f2_desc: "Automatic visual hierarchy, balanced proportions and contextual illustrations for a polished presentation.",
        f3_title: "Natural Language & Inpainting",
        f3_desc: "Chat with AI to refine slides, change color palettes or lasso specific areas to redraw elements.",
        f4_title: "Genuine Editable PPTX",
        f4_desc: "Download native PowerPoint files with full control over text, shapes and colors in Office or Google Slides."
      },
      comparison: {
        title: "Traditional Way vs. Banana Slides",
        subtitle: "Compare manual design hassles with AI-powered workflow automation.",
        oldWay: "Traditional Way",
        old1: "4 - 8 hours spent browsing templates and formatting",
        old2: "Tedious manual dragging of text boxes and icons",
        old3: "Hard to find consistent high-resolution illustrations",
        old4: "Mismatched colors and messy typography",
        newWay: "With Banana Slides",
        new1: "Complete deck ready in 30 seconds from your raw idea",
        new2: "Layouts automatically structured by visual hierarchy",
        new3: "Context-aware visuals and diagrams selected automatically",
        new4: "Unified brand identity with instant PPTX download",
        ctaButton: "Save 4 Hours Today"
      },
      steps: {
        title: "3 Simple Steps to Stunning Slides",
        s1_title: "1. Sign in & Input Prompt",
        s1_desc: "Sign in with Google and enter your topic, outline or reference document.",
        s2_title: "2. Pick Style & AI Generates",
        s2_desc: "Choose from 4 signature styles and let AI create your complete presentation.",
        s3_title: "3. Refine & Download PPTX",
        s3_desc: "Preview, refine with natural language commands, and download PowerPoint files."
      },
      ctaBanner: {
        title: "Ready to Elevate Your Presentations?",
        subtitle: "Discover a new standard of presentation performance.",
        button: "Get Started Now"
      },
      mobileSticky: {
        text: "Create AI Slides in 30s",
        button: "Sign In"
      }
    }
  }
};

// 4 Signature slide showcase templates (100% English, studio quality, no Chinese)
const DEMO_SLIDES = [
  {
    id: 'slide_1',
    pageNumber: '01',
    title: 'Apple Liquid Glass',
    styleName: 'Apple Liquid Glass',
    badge: 'Công nghệ & Pitch Deck',
    image: '/templates/template_liquid_glass.png',
    thumb: '/templates/template_liquid_glass-thumb.webp',
    glowColor: 'rgba(245, 158, 11, 0.35)',
  },
  {
    id: 'slide_2',
    pageNumber: '02',
    title: 'Tối Giản Thanh Lịch',
    styleName: 'Tối Giản Thanh Lịch',
    badge: 'Ý Tưởng Cốt Lõi',
    image: '/templates/template_minimalist_clean.png',
    thumb: '/templates/template_minimalist_clean-thumb.webp',
    glowColor: 'rgba(100, 116, 139, 0.35)',
  },
  {
    id: 'slide_3',
    pageNumber: '03',
    title: 'Infographic & Màu Sắc',
    styleName: 'Infographic & Màu Sắc',
    badge: 'Số Liệu & Quy Trình',
    image: '/templates/template_vibrant_infographic.png',
    thumb: '/templates/template_vibrant_infographic-thumb.webp',
    glowColor: 'rgba(59, 130, 246, 0.35)',
  },
  {
    id: 'slide_4',
    pageNumber: '04',
    title: 'Doanh Nghiệp & Học Thuật',
    styleName: 'Doanh Nghiệp & Học Thuật',
    badge: 'Báo Cáo Quản Trị',
    image: '/templates/template_corporate_consulting.png',
    thumb: '/templates/template_corporate_consulting-thumb.webp',
    glowColor: 'rgba(99, 102, 241, 0.35)',
  },
];

const COMPARISON_OLD_KEYS = ['old1', 'old2', 'old3', 'old4'] as const;
const COMPARISON_NEW_KEYS = ['new1', 'new2', 'new3', 'new4'] as const;

export const Landing: React.FC = () => {
  const { i18n } = useTranslation();
  const t = useT(landingI18n);
  const { openLoginModal, renderGoogleButton } = useAuth();
  const { theme, setTheme } = useTheme();
  const [activeSlideIdx, setActiveSlideIdx] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);
  const [showGoTop, setShowGoTop] = useState(false);
  const filmstripRef = useRef<HTMLDivElement>(null);

  // Monitor scroll for Go to Top button
  useEffect(() => {
    const handleScroll = () => {
      setShowGoTop(window.scrollY > 300);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Auto-rotate showcase
  useEffect(() => {
    if (!isAutoPlaying) return;
    const timer = setInterval(() => {
      setActiveSlideIdx((prev) => (prev + 1) % DEMO_SLIDES.length);
    }, 4500);
    return () => clearInterval(timer);
  }, [isAutoPlaying]);

  // Attempt to render Google one-tap / sign-in button slot
  useEffect(() => {
    const timer = setTimeout(() => {
      renderGoogleButton('landing-hero-google-slot');
    }, 200);
    return () => clearTimeout(timer);
  }, [renderGoogleButton]);

  const currentSlide = DEMO_SLIDES[activeSlideIdx];

  const handleManualSlideSelect = (idx: number) => {
    setIsAutoPlaying(false);
    setActiveSlideIdx(idx);
  };

  const handleNextSlide = () => {
    setIsAutoPlaying(false);
    setActiveSlideIdx((prev) => (prev + 1) % DEMO_SLIDES.length);
  };

  const handlePrevSlide = () => {
    setIsAutoPlaying(false);
    setActiveSlideIdx((prev) => (prev === 0 ? DEMO_SLIDES.length - 1 : prev - 1));
  };

  const toggleLanguage = () => {
    const currentLang = i18n.language || 'vi';
    const nextLang = currentLang.startsWith('en') ? 'vi' : 'en';
    i18n.changeLanguage(nextLang);
  };

  const toggleTheme = () => {
    if (theme === 'dark') {
      setTheme('light');
    } else {
      setTheme('dark');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0c0f17] text-slate-900 dark:text-slate-100 relative overflow-hidden font-sans selection:bg-amber-400 selection:text-black">
      {/* Dynamic Ambient Background Glows */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-40 -left-40 w-[600px] h-[600px] bg-gradient-to-br from-amber-400/20 via-yellow-400/10 to-transparent rounded-full blur-[120px] dark:from-amber-500/10 dark:via-yellow-500/5" />
        <div className="absolute top-1/4 -right-40 w-[500px] h-[500px] bg-gradient-to-bl from-amber-500/15 via-orange-400/10 to-transparent rounded-full blur-[100px] dark:from-amber-600/10" />
        <div className="absolute -bottom-40 left-1/3 w-[650px] h-[650px] bg-gradient-to-tr from-yellow-300/15 via-amber-400/10 to-transparent rounded-full blur-[140px] dark:from-yellow-600/5" />
        <div className="absolute inset-0 bg-[radial-gradient(#cbd5e1_1px,transparent_1px)] [background-size:24px_24px] opacity-40 dark:bg-[radial-gradient(#1e293b_1px,transparent_1px)] dark:opacity-30" />
      </div>

      {/* Header / Sticky Navigation Bar */}
      <header className="sticky top-0 z-40 w-full backdrop-blur-xl bg-white/80 dark:bg-[#0c0f17]/80 border-b border-slate-200/60 dark:border-slate-800/80 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 sm:h-20 flex items-center justify-between">
          {/* Logo & Brand */}
          <div className="flex items-center gap-2.5 sm:gap-3 group cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <div className="relative">
              <div className="absolute -inset-1 bg-gradient-to-r from-amber-400 to-yellow-500 rounded-xl blur-sm opacity-70 group-hover:opacity-100 transition duration-300" />
              <img
                src={logoUrl}
                alt="Banana Slides"
                className="relative w-8 h-8 sm:w-10 sm:h-10 object-contain rounded-xl shadow-sm"
              />
            </div>
            <div className="flex items-center">
              <span className="text-lg sm:text-xl font-black tracking-tight bg-gradient-to-r from-amber-600 via-amber-500 to-yellow-500 dark:from-amber-400 dark:via-yellow-400 dark:to-amber-300 bg-clip-text text-transparent">
                Banana Slides
              </span>
            </div>
          </div>

          {/* Right Action Controls */}
          <div className="flex items-center gap-2 sm:gap-4">
            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              aria-label="Toggle theme"
              className="p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/80 border border-transparent hover:border-slate-200 dark:hover:border-slate-700 transition-colors"
            >
              {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
            </button>

            {/* Language Switcher */}
            <button
              onClick={toggleLanguage}
              className="px-2.5 py-1.5 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 border border-slate-200 dark:border-slate-800 transition-colors"
            >
              {i18n.language?.startsWith('en') ? 'VI' : 'EN'}
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 pt-10 pb-12 sm:pt-16 sm:pb-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="max-w-4xl mx-auto space-y-6 sm:space-y-8">
          {/* Main Headline - Single-line on both mobile and desktop */}
          <h1 className="text-[20px] min-[360px]:text-[22px] min-[400px]:text-2xl sm:text-4xl md:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 dark:text-white leading-[1.25]">
            <span className="block whitespace-nowrap">{t('landing.hero.title_start')}</span>
            <span className="bg-gradient-to-r from-amber-500 via-yellow-400 to-orange-500 bg-clip-text text-transparent block mt-1 sm:mt-2 whitespace-nowrap">
              {t('landing.hero.title_highlight')}
            </span>
            {t('landing.hero.title_end') ? (
              <span className="text-slate-800 dark:text-slate-200 block mt-1 sm:mt-2 whitespace-nowrap">
                {t('landing.hero.title_end')}
              </span>
            ) : null}
          </h1>

          {/* Subtitle */}
          <p className="text-base sm:text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
            {t('landing.hero.subtitle')}
          </p>

          {/* Primary CTA Area - Maximized to drive Google Login */}
          <div className="pt-2 sm:pt-4 flex flex-col items-center gap-4">
            <div className="w-full sm:w-auto flex flex-col sm:flex-row items-center justify-center gap-3">
              {/* Giant SSO Login Button */}
              <button
                onClick={openLoginModal}
                className="w-full sm:w-auto relative group overflow-hidden px-8 py-4 rounded-2xl bg-gradient-to-r from-amber-500 via-yellow-400 to-amber-500 text-slate-950 font-black text-base sm:text-lg shadow-[0_12px_35px_rgba(245,158,11,0.35)] hover:shadow-[0_16px_45px_rgba(245,158,11,0.5)] hover:scale-[1.02] active:scale-[0.98] transition-all duration-300 flex items-center justify-center gap-3.5 border-2 border-yellow-300/70"
              >
                {/* Shimmer light sweep */}
                <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/30 to-transparent transform -skew-x-12" />

                <span>{t('landing.hero.cta_primary')}</span>
                <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
              </button>

              {/* Secondary button scrolling to showcase */}
              <button
                onClick={() => {
                  const el = document.getElementById('showcase-section');
                  el?.scrollIntoView({ behavior: 'smooth' });
                }}
                className="w-full sm:w-auto px-6 py-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-200 font-bold text-sm sm:text-base hover:bg-slate-100 dark:hover:bg-slate-800/70 transition-all flex items-center justify-center gap-2 shadow-sm"
              >
                <Presentation className="w-4 h-4 text-amber-500" />
                <span>{t('landing.hero.cta_secondary')}</span>
              </button>
            </div>

            {/* Slot for Google One-Tap if loaded */}
            <div id="landing-hero-google-slot" className="hidden" />
          </div>
        </div>
      </section>

      {/* Showcase Section: 4 Signature Styles with Real Slide Previews */}
      <section id="showcase-section" className="relative z-10 py-12 sm:py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-8 sm:mb-12 space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 text-xs font-semibold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            <span>{t('landing.showcase.badge')}</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tight">
            {t('landing.showcase.title')}
          </h2>
          <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400">
            {t('landing.showcase.subtitle')}
          </p>
        </div>

        {/* Big Interactive Slide Mockup Viewport */}
        <div className="relative max-w-5xl mx-auto">
          {/* Outer glowing frame */}
          <div
            className="rounded-2xl sm:rounded-3xl p-1 sm:p-2.5 bg-gradient-to-b from-slate-200 via-slate-100 to-slate-200 dark:from-slate-700/60 dark:via-slate-800/40 dark:to-slate-900/80 shadow-2xl transition-all duration-500"
            style={{ boxShadow: `0 25px 60px -15px ${currentSlide.glowColor}` }}
          >
            {/* Presentation Window Mockup */}
            <div className="rounded-xl sm:rounded-2xl overflow-hidden bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
              {/* Window Header */}
              <div className="h-9 sm:h-11 bg-slate-100 dark:bg-slate-800/90 border-b border-slate-200 dark:border-slate-700/60 px-3 sm:px-4 flex items-center justify-between">
                <div className="flex items-center gap-1.5 sm:gap-2">
                  <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-rose-500/80" />
                  <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-amber-500/80" />
                  <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-emerald-500/80" />
                </div>
                <div className="flex items-center gap-2 text-[11px] sm:text-xs font-mono text-slate-500 dark:text-slate-400">
                  <span className="font-bold text-amber-600 dark:text-amber-400">
                    Slide {currentSlide.pageNumber}/{DEMO_SLIDES.length.toString().padStart(2, '0')}
                  </span>
                  <span>•</span>
                  <span className="font-semibold text-slate-700 dark:text-slate-200 truncate max-w-[180px] sm:max-w-md">
                    {currentSlide.title}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-slate-400">
                  <button onClick={handlePrevSlide} aria-label="Previous slide" className="no-min-touch-target w-7 h-7 flex items-center justify-center rounded hover:text-slate-700 dark:hover:text-white transition-colors">
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <button onClick={handleNextSlide} aria-label="Next slide" className="no-min-touch-target w-7 h-7 flex items-center justify-center rounded hover:text-slate-700 dark:hover:text-white transition-colors">
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Slide Preview 16:9 Screen */}
              <div className="relative aspect-[16/9] w-full bg-slate-950 overflow-hidden group">
                <img
                  key={currentSlide.id}
                  src={currentSlide.image}
                  alt={currentSlide.title}
                  className="w-full h-full object-cover sm:object-contain transition-all duration-500 group-hover:scale-[1.01]"
                />

                {/* Floating Tag */}
                <div className="absolute top-3 left-3 sm:top-5 sm:left-5 backdrop-blur-md bg-slate-950/70 text-white text-[10px] sm:text-xs font-medium px-3 py-1.5 rounded-lg border border-white/20 flex items-center gap-1.5 shadow-lg">
                  <Sparkles className="w-3 h-3 text-amber-400" />
                  <span>{currentSlide.styleName}</span>
                </div>

                {/* Center Hover Overlay CTA Button */}
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end justify-center p-6">
                  <button
                    onClick={openLoginModal}
                    className="px-6 py-3 rounded-xl bg-amber-500 text-slate-950 font-bold text-sm shadow-xl hover:bg-amber-400 transition-all flex items-center gap-2 transform translate-y-2 group-hover:translate-y-0"
                  >
                    <span>{t('landing.showcase.ctaUseStyle')}</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Select Slide Cards */}
          <div className="mt-5">
            <div ref={filmstripRef} className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1 px-1">
              {DEMO_SLIDES.map((slide, idx) => {
                const isSelected = idx === activeSlideIdx;
                return (
                  <div
                    key={slide.id}
                    onClick={() => handleManualSlideSelect(idx)}
                    className={`cursor-pointer rounded-xl overflow-hidden border p-1.5 transition-all bg-white dark:bg-slate-900 ${
                      isSelected
                        ? 'border-amber-500 ring-2 ring-amber-400/40 shadow-lg scale-[1.02]'
                        : 'border-slate-200 dark:border-slate-800 hover:border-slate-400 opacity-70 hover:opacity-100'
                    }`}
                  >
                    <div className="relative aspect-[16/9] rounded-lg overflow-hidden bg-slate-950 mb-1.5">
                      <img src={slide.thumb} alt={slide.title} className="w-full h-full object-cover" />
                      <div className="absolute top-1 left-1 px-1.5 py-0.5 rounded bg-black/70 text-[9px] font-mono text-white font-bold">
                        {slide.pageNumber}
                      </div>
                    </div>
                    <p className="text-[11px] font-bold text-slate-800 dark:text-slate-200 truncate">
                      {slide.title}
                    </p>
                    <p className="text-[9px] text-slate-500 dark:text-slate-400 truncate">
                      {slide.badge}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Feature Highlights Grid */}
      <section className="relative z-10 py-16 sm:py-24 bg-white/60 dark:bg-slate-900/40 backdrop-blur-md border-y border-slate-200/60 dark:border-slate-800/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12 sm:mb-16 space-y-3">
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tight">
              {t('landing.features.title')}
            </h2>
            <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400">
              {t('landing.features.subtitle')}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Feature 1 */}
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-amber-400/50 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 space-y-4">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center">
                <Layers className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-lg text-slate-900 dark:text-white">
                {t('landing.features.f1_title')}
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                {t('landing.features.f1_desc')}
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-amber-400/50 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 space-y-4">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-lg text-slate-900 dark:text-white">
                {t('landing.features.f2_title')}
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                {t('landing.features.f2_desc')}
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-amber-400/50 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 space-y-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
                <Sliders className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-lg text-slate-900 dark:text-white">
                {t('landing.features.f3_title')}
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                {t('landing.features.f3_desc')}
              </p>
            </div>

            {/* Feature 4 */}
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-amber-400/50 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 space-y-4">
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-500 flex items-center justify-center">
                <Download className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-lg text-slate-900 dark:text-white">
                {t('landing.features.f4_title')}
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                {t('landing.features.f4_desc')}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Comparison Section: Old Way vs Banana Slides */}
      <section className="relative z-10 py-16 sm:py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12 sm:mb-16 space-y-3">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tight">
            {t('landing.comparison.title')}
          </h2>
          <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400">
            {t('landing.comparison.subtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8 max-w-4xl mx-auto">
          {/* Traditional Way */}
          <div className="p-6 sm:p-8 rounded-2xl bg-slate-100/80 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-6">
            <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
              <span className="text-lg">❌</span>
              <h3 className="font-bold text-lg sm:text-xl text-slate-700 dark:text-slate-300">
                {t('landing.comparison.oldWay')}
              </h3>
            </div>
            <ul className="space-y-3 text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              {COMPARISON_OLD_KEYS.map((key) => (
                <li key={key} className="flex items-start gap-2.5">
                  <span className="text-rose-500 font-bold shrink-0 mt-0.5">•</span>
                  <span>{t(`landing.comparison.${key}`)}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Banana Slides Way */}
          <div className="p-6 sm:p-8 rounded-2xl bg-gradient-to-b from-amber-500/10 via-amber-500/5 to-transparent dark:bg-slate-900/90 border-2 border-amber-400/60 shadow-xl space-y-6 relative overflow-hidden">
            <div className="flex items-center gap-2">
              <span className="text-lg">✨</span>
              <h3 className="font-black text-lg sm:text-xl text-amber-700 dark:text-amber-400">
                {t('landing.comparison.newWay')}
              </h3>
            </div>
            <ul className="space-y-3 text-xs sm:text-sm text-slate-700 dark:text-slate-200">
              {COMPARISON_NEW_KEYS.map((key) => (
                <li key={key} className="flex items-start gap-2.5 font-medium">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                  <span>{t(`landing.comparison.${key}`)}</span>
                </li>
              ))}
            </ul>

            <button
              onClick={openLoginModal}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-500 to-yellow-400 text-slate-950 font-bold text-xs sm:text-sm shadow-md shadow-amber-500/25 hover:shadow-lg hover:shadow-amber-500/40 hover:scale-[1.01] transition-all flex items-center justify-center gap-2"
            >
              <span>{t('landing.comparison.ctaButton')}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </section>

      {/* 3 Steps Workflow */}
      <section className="relative z-10 py-12 sm:py-20 bg-slate-100/50 dark:bg-slate-900/30 border-y border-slate-200/60 dark:border-slate-800/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-10 sm:mb-14">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-black text-slate-900 dark:text-white">
              {t('landing.steps.title')}
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {/* Step 1 */}
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center space-y-3">
              <div className="w-10 h-10 rounded-full bg-amber-500 text-slate-950 font-black text-base mx-auto flex items-center justify-center shadow-md shadow-amber-500/30">
                1
              </div>
              <h3 className="font-bold text-base sm:text-lg text-slate-900 dark:text-white">
                {t('landing.steps.s1_title')}
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
                {t('landing.steps.s1_desc')}
              </p>
            </div>

            {/* Step 2 */}
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center space-y-3">
              <div className="w-10 h-10 rounded-full bg-amber-500 text-slate-950 font-black text-base mx-auto flex items-center justify-center shadow-md shadow-amber-500/30">
                2
              </div>
              <h3 className="font-bold text-base sm:text-lg text-slate-900 dark:text-white">
                {t('landing.steps.s2_title')}
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
                {t('landing.steps.s2_desc')}
              </p>
            </div>

            {/* Step 3 */}
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center space-y-3">
              <div className="w-10 h-10 rounded-full bg-amber-500 text-slate-950 font-black text-base mx-auto flex items-center justify-center shadow-md shadow-amber-500/30">
                3
              </div>
              <h3 className="font-bold text-base sm:text-lg text-slate-900 dark:text-white">
                {t('landing.steps.s3_title')}
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
                {t('landing.steps.s3_desc')}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pre-footer Big CTA Banner */}
      <section className="relative z-10 py-16 sm:py-24 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="relative rounded-3xl overflow-hidden p-8 sm:p-14 bg-gradient-to-br from-amber-500 via-yellow-400 to-amber-600 text-slate-950 shadow-[0_20px_60px_rgba(245,158,11,0.35)]">
          <div className="absolute top-0 right-0 -mt-10 -mr-10 w-60 h-60 bg-white/20 rounded-full blur-2xl pointer-events-none" />
          <div className="relative z-10 space-y-6 max-w-2xl mx-auto">
            <h2 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
              {t('landing.ctaBanner.title')}
            </h2>
            <p className="text-base sm:text-lg font-medium opacity-90">
              {t('landing.ctaBanner.subtitle')}
            </p>
            <div className="pt-2">
              <button
                onClick={openLoginModal}
                className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-slate-950 hover:bg-slate-900 text-amber-400 hover:text-amber-300 font-black text-base sm:text-lg shadow-2xl hover:scale-[1.03] active:scale-[0.98] transition-all duration-200 flex items-center justify-center gap-3 mx-auto border border-amber-400/40"
              >
                <LogIn className="w-5 h-5" />
                <span>{t('landing.ctaBanner.button')}</span>
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-slate-200 dark:border-slate-800/80 py-8 sm:py-10 text-center text-xs text-slate-500 dark:text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-center gap-4">
          <div className="flex items-center gap-2">
            <img src={logoUrl} alt="Logo" className="w-5 h-5 object-contain" />
            <span className="font-bold text-slate-700 dark:text-slate-300">Banana Slides</span>
            <span>• &copy; {new Date().getFullYear()} All rights reserved.</span>
          </div>
        </div>
      </footer>

      {/* Floating Go to Top Button */}
      {showGoTop && (
        <button
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          aria-label="Lên đầu trang"
          className="no-min-touch-target fixed bottom-6 right-6 z-50 w-11 h-11 rounded-2xl bg-gradient-to-r from-amber-500 to-yellow-400 hover:from-amber-400 hover:to-yellow-300 text-slate-950 shadow-xl shadow-amber-500/30 hover:scale-110 active:scale-95 transition-all duration-300 border border-amber-300/80 flex items-center justify-center group"
        >
          <ChevronUp className="w-5 h-5 transition-transform group-hover:-translate-y-0.5" />
        </button>
      )}
    </div>
  );
};
