import React, { useState } from 'react';
import { Sparkles, FileText, Palette, MessageSquare, Download, ChevronLeft, ChevronRight, ExternalLink, Settings, Check, Video, Lightbulb } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Modal } from './Modal';
import { Button } from './Button';
import { useT } from '@/hooks/useT';
import { useTranslation } from 'react-i18next';
import logoUrl from '@/assets/logo.png';

// ---------------------------------------------------------------------------
// i18n
// ---------------------------------------------------------------------------
const i18nDict = {
  zh: {
    guide: {
      brand: 'Banana Slides · Banana Slides',
      setup: 'Bắt đầu nhanh',
      setupSub: 'Hoàn tất cấu hình cơ bản, bật AI hành trình sáng tạo',
      features: 'Giới thiệu tính năng',
      featuresSub: 'Khám phá cách sử dụng AI nhanh chóng tạo bản trình chiếu đẹp mắt PPT',
      gallery: 'Ví dụ kết quả',
      gallerySub: 'Banana Slides PPT ',
      galleryMore: 'Xem thêm các ví dụ thực tế',
      hi: 'Banana Slides! ',
      hiSub: 'Trước khi bắt đầu, Hãy hoàn tất cấu hình cơ bản trước',
      s1: 'Cấu hình API Key',
      s1d: 'Đi tới trang Cài đặt, Cấu hình dự án cần sử dụngAPIdịch vụ, bao gồm: ',
      s1i: ['của bạn AI của nhà cung cấp dịch vụ API Base và API Key', 'Cấu hình văn bản, Mô hình tạo ảnh(banana pro)và mô hình mô tả ảnh', 'Nếu cần tính năng phân tích tệp, Vui lòng cấu hình MinerU Token', 'Nếu cần tính năng xuất tệp có thể chỉnh sửa, Vui lòng cấu hìnhMinerU TOKEN và Baidu API KEY'],
      s2: 'Lưu và kiểm tra',
      s2d: 'Sau khi hoàn tất cấu hình, nhất định phải nhấnLưu cài đặtnút, sau đó kiểm tra dịch vụ ở cuối trang, Đảm bảo các dịch vụ hoạt động bình thường. ',
      s3: 'Bắt đầu sáng tạo',
      s3d: 'Sau khi cấu hình thành công, Quay lại trang chủ để bắt đầu sử dụng AI tạo bản trình chiếu đẹp mắt PPT! ',
      s4: '*Phản hồi vấn đề',
      s4d: 'Nếu gặp sự cố trong quá trình sử dụng, Có thể tạigithub issueđưa ra',
      issueLink: 'Đi tớiGithub issue',
      settingsBtn: 'Đi tới trang Cài đặt',
      featuresOverview: 'Tổng quan tính năng',
      featuresOverviewDesc: 'Tìm hiểu Banana Slides quy trình làm việc hoàn chỉnh, lộ trình sáng tạo, hỗ trợ tư liệu và khả năng xuất tệp. ',
      feishuTutorial: 'Hướng dẫn chi tiết trang Cài đặt',
      feishuTutorialDesc: 'Hoàn tất cấu hình trang Cài đặt theo từng bước. ',
      faq: 'Câu hỏi thường gặp',
      faqDesc: 'Xem API Cấu hình, Các câu hỏi thường gặp trong quá trình xuất và sử dụng. ',
      hint: 'Gợi ý',
      hintBody: 'Nếu bạn chưa có API Key, Có thể truy cập trang chủ của nhà cung cấp tương ứng để đăng ký và lấy mã. Sau khi hoàn tất cấu hình, Khuyến nghị kiểm tra dịch vụ trước, tránh gặp sự cố trong quá trình sử dụng sau này. ',
      prev: 'Trang trước',
      next: 'Trang sau',
      cases: { softwareDev: 'Thực hành tốt nhất trong phát triển phần mềm', deepseek: 'DeepSeek-V3.2Trình diễn kỹ thuật', prefabFood: 'Nghiên cứu phát triển và công nghiệp hóa dây chuyền thiết bị thông minh', moneyHistory: 'Sự tiến hóa của tiền tệ: Hành trình từ vỏ sò đến tiền giấy' },
      feat: {
        paths: { t: 'Lộ trình sáng tạo linh hoạt, đa dạng', d: 'Hỗ trợ từ ý tưởng, Dàn ý, và mô tả trang — 3 cách khởi đầu, đáp ứng mọi thói quen sáng tạo. ', items: ['Tạo từ một câu: Nhập một chủ đề, AI Tự động tạo dàn ý có cấu trúc rõ ràng và mô tả nội dung từng trang', 'Chỉnh sửa bằng ngôn ngữ tự nhiên: Hỗ trợ dùng Vibe để chỉnh sửa dàn ý hoặc mô tả bằng ngôn ngữ tự nhiên, AI phản hồi điều chỉnh theo thời gian thực', 'Dàn ý/Chế độ mô tả: Vừa có thể tạo hàng loạt chỉ với một cú nhấp, hoặc chỉnh sửa chi tiết thủ công'] },
        parse: { t: 'Khả năng phân tích tư liệu mạnh mẽ', d: 'tải lên nhiều định dạng tệp, Tự động phân tích nội dung, cung cấp nguồn tư liệu phong phú cho việc tạo slide. ', items: ['Hỗ trợ đa định dạng: Tải lên PDF/Docx/MD/Txt và các tệp khác, tự động phân tích nội dung dưới nền', 'trích xuất thông minh: Tự động nhận diện các điểm chính trong văn bản, liên kết ảnh và thông tin biểu đồ', 'Tham chiếu phong cách: Hỗ trợ tải lên ảnh tham chiếu hoặc mẫu, tùy biến PPT phong cách'] },
        vibe: { t: 'VibeChỉnh sửa bằng ngôn ngữ tự nhiên', d: 'Không còn bị giới hạn bởi các nút menu phức tạp, Đưa ra yêu cầu chỉnh sửa trực tiếp bằng ngôn ngữ tự nhiên. ', items: ['Vẽ lại cục bộ: Chỉnh sửa bằng ngôn ngữ tự nhiên cho các vùng chưa ưng ý ( như Đổi biểu đồ này thành biểu đồ tròn) ', 'tối ưu toàn trang: dựa trên nano banana pro tạo độ nét cao, các trang có phong cách đồng nhất'] },
        export: { t: 'Xuất định dạng dùng ngay', d: 'Xuất định dạng chuẩn chỉ với một cú nhấp, trình chiếu ngay không cần chỉnh sửa. ', items: ['Hỗ trợ đa định dạng: Xuất chuẩn chỉ với một cú nhấp PPTX hoặc PDF Tệp', 'tương thích hoàn hảo: mặc định 16:9 tỷ lệ, bố cục chuẩn đẹp không cần chỉnh lại'] },
        video: { t: 'TTS Xuất video thuyết trình', d: 'Chuyển đổi slide chỉ với một cú nhấp thành AI video thuyết trình có giọng đọc và phụ đề. ', items: ['AI Tự động chuyển mô tả trang thành lời thuyết minh tự nhiên, qua edge-tts Tổng hợp giọng nói', 'Hỗ trợ tiếng Việt/Anh/Nhật (3 ngôn ngữ), nhiều giọng đọc tùy chọn', 'phụ đề cuộn từng câu, tự động chuyển cảnh theo nhịp giọng đọc', 'tùy chọn Ken Burns hiệu ứng chuyển cảnh (thu phóng/dịch chuyển) '] },
      },
    },
  },
  en: {
    guide: {
      brand: 'Banana Slides',
      setup: 'Quick Start',
      setupSub: 'Complete basic configuration and start your AI creation journey',
      features: 'Features',
      featuresSub: 'Explore how to use AI to quickly create beautiful PPT',
      gallery: 'Showcases',
      gallerySub: 'Here are PPT examples generated with Banana Slides',
      galleryMore: 'View more examples',
      hi: 'Welcome to Banana Slides!',
      hiSub: "Let's complete the basic configuration before you start",
      s1: 'Configure API Key',
      s1d: 'Go to settings page to configure the API services needed for the project, including:',
      s1i: ["Your AI service provider's API Base and API Key", 'Configure text, image generation model (banana pro) and image caption model', 'If you need file parsing, configure MinerU Token', 'If you need editable export, configure MinerU TOKEN and Baidu API KEY'],
      s2: 'Save and Test',
      s2d: 'After configuration, be sure to click "Save Settings" button, then test services at the bottom of the page to ensure everything works properly.',
      s3: 'Start Creating',
      s3d: 'After successful configuration, return to home page to start using AI to generate beautiful PPT!',
      s4: '*Feedback',
      s4d: 'If you encounter issues while using, please raise them on GitHub issues',
      issueLink: 'Go to GitHub Issues',
      settingsBtn: 'Go to Settings',
      featuresOverview: 'Features Overview',
      featuresOverviewDesc: 'Learn the full workflow, creation paths, material support, and export options in Banana Slides.',
      feishuTutorial: 'Settings Guide',
      feishuTutorialDesc: 'Follow the step-by-step guide to configure Settings.',
      faq: 'FAQ',
      faqDesc: 'Review common questions about API setup, export, and everyday use.',
      hint: 'Tip',
      hintBody: "If you don't have an API Key yet, you can register on the corresponding service provider's website. After configuration, it's recommended to test services first to avoid issues later.",
      prev: 'Previous',
      next: 'Next',
      cases: { softwareDev: 'Software Development Best Practices', deepseek: 'DeepSeek-V3.2 Technical Showcase', prefabFood: 'Prefab Food Intelligent Production Line R&D', moneyHistory: 'The Evolution of Money: From Shells to Paper' },
      feat: {
        paths: { t: 'Flexible Creation Paths', d: 'Support idea, outline, and page description as starting points to meet different creative habits.', items: ['One-line generation: Enter a topic, AI automatically generates a clear outline and page-by-page content description', 'Natural language editing: Support Vibe-style verbal modification of outlines or descriptions, AI responds in real-time', 'Outline/Description mode: Either batch generate with one click, or manually adjust details'] },
        parse: { t: 'Powerful Material Parsing', d: 'Upload multiple format files, automatically parse content to provide rich materials for generation.', items: ['Multi-format support: Upload PDF/Docx/MD/Txt files, backend automatically parses content', 'Smart extraction: Automatically identify key points, image links and chart information in text', 'Style reference: Support uploading reference images or templates to customize PPT style'] },
        vibe: { t: '"Vibe" Style Natural Language Editing', d: 'No longer limited by complex menu buttons, directly issue modification commands through natural language.', items: ['Partial redraw: Make verbal modifications to unsatisfying areas (e.g., "Change this chart to a pie chart")', 'Full page optimization: Generate HD, style-consistent pages based on nano banana pro'] },
        export: { t: 'Ready-to-Use Format Export', d: 'One-click export to standard formats, present directly without adjustments.', items: ['Multi-format support: One-click export to standard PPTX or PDF files', 'Perfect fit: Default 16:9 ratio, no secondary layout adjustments needed'] },
        video: { t: 'TTS Narration Video Export', d: 'One-click conversion of slides into narrated videos with AI voiceover and subtitles.', items: ['AI converts page descriptions into natural spoken narration via edge-tts', 'Supports Chinese, English, and Japanese with multiple voice options', 'Sentence-by-sentence scrolling subtitles synchronized with speech', 'Optional Ken Burns animation effect (zoom/pan)'] },
      },
    },
  },
};

// ---------------------------------------------------------------------------
// Static data
// ---------------------------------------------------------------------------
const SHOWCASES = [
  { img: 'https://github.com/user-attachments/assets/d58ce3f7-bcec-451d-a3b9-ca3c16223644', key: 'softwareDev' },
  { img: 'https://github.com/user-attachments/assets/c64cd952-2cdf-4a92-8c34-0322cbf3de4e', key: 'deepseek' },
  { img: 'https://github.com/user-attachments/assets/383eb011-a167-4343-99eb-e1d0568830c7', key: 'prefabFood' },
  { img: 'https://github.com/user-attachments/assets/1a63afc9-ad05-4755-8480-fc4aa64987f1', key: 'moneyHistory' },
];

const FEATURES: { key: string; icon: React.ReactNode }[] = [
  { key: 'paths', icon: <Sparkles className="text-yellow-500" size={24} /> },
  { key: 'parse', icon: <FileText className="text-blue-500" size={24} /> },
  { key: 'vibe', icon: <MessageSquare className="text-green-500" size={24} /> },
  { key: 'export', icon: <Download className="text-purple-500" size={24} /> },
  { key: 'video', icon: <Video className="text-red-500" size={24} /> },
];

const CONFIG_LINKS = [
  {
    key: 'featuresOverview',
    descKey: 'featuresOverviewDesc',
    href: { zh: 'https://docs.bananaslides.online/zh/features/overview', en: 'https://docs.bananaslides.online/features/overview' },
  },
  {
    key: 'feishuTutorial',
    descKey: 'feishuTutorialDesc',
    href: {
      zh: 'https://ziy68cvfvu3.feishu.cn/wiki/GiNawdmpiinSRqkGspocqEWAnkh?from=from_copylink',
      en: 'https://ziy68cvfvu3.feishu.cn/wiki/GiNawdmpiinSRqkGspocqEWAnkh?from=from_copylink',
    },
  },
  {
    key: 'faq',
    descKey: 'faqDesc',
    href: { zh: 'https://docs.bananaslides.online/zh/faq', en: 'https://docs.bananaslides.online/faq' },
  },
];

// ---------------------------------------------------------------------------
// Page renderers
// ---------------------------------------------------------------------------
/** Retrieve an array value from i18nDict by dot-path (useT only handles strings). */
function tList(lang: 'zh' | 'en', path: string): string[] {
  const dict = i18nDict[lang] as Record<string, unknown>;
  let cur: unknown = dict;
  for (const seg of path.split('.')) {
    if (cur && typeof cur === 'object' && seg in (cur as Record<string, unknown>)) {
      cur = (cur as Record<string, unknown>)[seg];
    } else {
      return [];
    }
  }
  return Array.isArray(cur) ? cur : [];
}

type PageRenderer = (ctx: {
  t: ReturnType<typeof useT>;
  lang: 'zh' | 'en';
  navigate: ReturnType<typeof useNavigate>;
  onClose: () => void;
  showcaseIdx: number;
  setShowcaseIdx: (i: number) => void;
  expandedFeat: number | null;
  setExpandedFeat: (i: number | null) => void;
}) => React.ReactNode;

const renderSetupPage: PageRenderer = ({ t, lang, navigate, onClose }) => {
  const steps = [
    { num: '1', bg: 'bg-banana-500', content: (
      <div className="flex-1 space-y-2">
        <h4 className="font-semibold text-gray-800 dark:text-foreground-primary">{t('guide.s1')}</h4>
        <p className="text-sm text-gray-600 dark:text-foreground-tertiary">{t('guide.s1d')}</p>
        <ul className="text-sm text-gray-600 dark:text-foreground-tertiary space-y-1 pl-4">
          {tList(lang, 'guide.s1i').map((item, i) => (
            <li key={i}>• {item}</li>
          ))}
        </ul>
      </div>
    ), highlight: true },
    { num: '2', bg: 'bg-orange-500', content: (
      <div className="flex-1 space-y-2">
        <h4 className="font-semibold text-gray-800 dark:text-foreground-primary">{t('guide.s2')}</h4>
        <p className="text-sm text-gray-600 dark:text-foreground-tertiary">{t('guide.s2d')}</p>
      </div>
    ) },
    { num: <Check size={18} />, bg: 'bg-green-500', content: (
      <div className="flex-1 space-y-2">
        <h4 className="font-semibold text-gray-800 dark:text-foreground-primary">{t('guide.s3')}</h4>
        <p className="text-sm text-gray-600 dark:text-foreground-tertiary">{t('guide.s3d')}</p>
      </div>
    ) },
  ];

  return (
    <div className="space-y-6">
      <div className="text-center space-y-3">
        <div className="inline-flex items-center justify-center mr-4">
          <img src={logoUrl} alt="Banana Slides Logo" className="h-16 w-16 object-contain" />
        </div>
        <h3 className="text-2xl font-bold text-gray-800 dark:text-foreground-primary">{t('guide.hi')}</h3>
        <p className="text-sm text-gray-600 dark:text-foreground-tertiary">{t('guide.hiSub')}</p>
      </div>

      <div className="space-y-4">
        {steps.map((s, i) => (
          <div
            key={i}
            className={`flex gap-4 p-4 rounded-xl border ${
              s.highlight
                ? 'bg-gradient-to-r from-banana-50 dark:from-background-primary to-orange-50 border-banana-200'
                : 'bg-white dark:bg-background-secondary border-gray-200 dark:border-border-primary'
            }`}
          >
            <div className={`flex-shrink-0 w-8 h-8 ${s.bg} text-white rounded-full flex items-center justify-center font-bold`}>
              {s.num}
            </div>
            {s.content}
          </div>
        ))}
      </div>

      <div className="flex gap-4 p-4 bg-white dark:bg-background-secondary rounded-xl border border-gray-200 dark:border-border-primary">
        <div className="flex-shrink-0 w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center font-bold">4</div>
        <div className="flex-1 space-y-2">
          <h4 className="font-semibold text-gray-800 dark:text-foreground-primary">{t('guide.s4')}</h4>
          <p className="text-sm text-gray-600 dark:text-foreground-tertiary">{t('guide.s4d')}</p>
        </div>
        <a href="https://github.com/Anionex/banana-slides/issues" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-sm text-banana-600 hover:text-banana-700 font-medium">
          <ExternalLink size={14} />
          {t('guide.issueLink')}
        </a>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {CONFIG_LINKS.map((link) => (
          <a
            key={link.key}
            href={link.href[lang]}
            target="_blank"
            rel="noopener noreferrer"
            className="group rounded-xl border border-gray-200 bg-white p-3 transition hover:border-banana-300 hover:bg-banana-50/60 dark:border-border-primary dark:bg-background-secondary dark:hover:border-banana-400 dark:hover:bg-background-hover"
          >
            <span className="flex items-center justify-between gap-2 text-sm font-semibold text-gray-800 dark:text-foreground-primary">
              {t(`guide.${link.key}`)}
              <ExternalLink size={14} className="flex-shrink-0 text-gray-400 transition group-hover:text-banana-600 dark:group-hover:text-banana-300" />
            </span>
            <span className="mt-1 block text-xs leading-relaxed text-gray-500 dark:text-foreground-tertiary">
              {t(`guide.${link.descKey}`)}
            </span>
          </a>
        ))}
      </div>

      <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
        <p className="text-xs text-blue-800 flex items-start gap-1.5">
          <Lightbulb size={14} className="flex-shrink-0 mt-0.5" />
          <span><strong>{t('guide.hint')}</strong>: {t('guide.hintBody')}</span>
        </p>
      </div>

      <div className="flex justify-center pt-2">
        <Button onClick={() => { onClose(); navigate('/settings', { state: { from: window.location.pathname } }); }} className="bg-banana-500 hover:bg-banana-600 text-black dark:text-white shadow-lg" icon={<Settings size={18} />}>
          {t('guide.settingsBtn')}
        </Button>
      </div>
    </div>
  );
};

const renderFeaturesPage: PageRenderer = ({ t, lang, expandedFeat, setExpandedFeat }) => (
  <div className="space-y-3">
    {FEATURES.map((f, idx) => (
      <div
        key={f.key}
        className={`border rounded-xl transition-all cursor-pointer ${
          expandedFeat === idx
            ? 'border-banana-300 bg-banana-50/50 shadow-sm dark:shadow-background-primary/30'
            : 'border-gray-200 dark:border-border-primary hover:border-gray-300 dark:hover:border-gray-500 hover:bg-gray-50 dark:hover:bg-background-hover'
        }`}
        onClick={() => setExpandedFeat(expandedFeat === idx ? null : idx)}
      >
        <div className="flex items-center gap-3 p-4">
          <div className="flex-shrink-0 w-10 h-10 bg-white dark:bg-background-secondary rounded-lg shadow-sm dark:shadow-background-primary/30 flex items-center justify-center">
            {f.icon}
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-base font-semibold text-gray-800 dark:text-foreground-primary">{t(`guide.feat.${f.key}.t`)}</h4>
            <p className="text-sm text-gray-500 dark:text-foreground-tertiary truncate">{t(`guide.feat.${f.key}.d`)}</p>
          </div>
          <ChevronRight size={18} className={`text-gray-400 transition-transform flex-shrink-0 ${expandedFeat === idx ? 'rotate-90' : ''}`} />
        </div>
        {expandedFeat === idx && (
          <div className="px-4 pb-4 pt-0">
            <div className="pl-13 space-y-2">
              {tList(lang, `guide.feat.${f.key}.items`).map((line, li) => (
                <div key={li} className="flex items-start gap-2 text-sm text-gray-600 dark:text-foreground-tertiary">
                  <span className="text-banana-500 mt-1">•</span>
                  <span>{line}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    ))}
  </div>
);

const renderGalleryPage: PageRenderer = ({ t, showcaseIdx, setShowcaseIdx }) => {
  const prev = () => setShowcaseIdx(showcaseIdx === 0 ? SHOWCASES.length - 1 : showcaseIdx - 1);
  const next = () => setShowcaseIdx(showcaseIdx === SHOWCASES.length - 1 ? 0 : showcaseIdx + 1);

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600 dark:text-foreground-tertiary text-center">{t('guide.gallerySub')}</p>

      <div className="relative">
        <div className="aspect-video bg-gray-100 dark:bg-background-secondary rounded-xl overflow-hidden shadow-lg">
          <img src={SHOWCASES[showcaseIdx].img} alt={t(`guide.cases.${SHOWCASES[showcaseIdx].key}`)} className="w-full h-full object-cover" />
        </div>
        <button onClick={prev} className="absolute left-2 top-1/2 -translate-y-1/2 w-10 h-10 bg-white/90 hover:bg-white rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-110">
          <ChevronLeft size={20} />
        </button>
        <button onClick={next} className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 bg-white/90 hover:bg-white rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-110">
          <ChevronRight size={20} />
        </button>
      </div>

      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-foreground-primary">{t(`guide.cases.${SHOWCASES[showcaseIdx].key}`)}</h3>
      </div>

      <div className="flex justify-center gap-2">
        {SHOWCASES.map((_, i) => (
          <button key={i} onClick={() => setShowcaseIdx(i)} className={`w-2 h-2 rounded-full transition-all ${i === showcaseIdx ? 'bg-banana-500 w-6' : 'bg-gray-300 hover:bg-gray-400'}`} />
        ))}
      </div>

      <div className="grid grid-cols-4 gap-2 mt-4">
        {SHOWCASES.map((sc, i) => (
          <button key={i} onClick={() => setShowcaseIdx(i)} className={`aspect-video rounded-lg overflow-hidden border-2 transition-all ${i === showcaseIdx ? 'border-banana-500 ring-2 ring-banana-200' : 'border-transparent hover:border-gray-300 dark:hover:border-gray-500'}`}>
            <img src={sc.img} alt={t(`guide.cases.${sc.key}`)} className="w-full h-full object-cover" />
          </button>
        ))}
      </div>

      <div className="text-center pt-4">
        <a href="https://github.com/Anionex/banana-slides/issues/2" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-sm text-banana-600 hover:text-banana-700 font-medium">
          <ExternalLink size={14} />
          {t('guide.galleryMore')}
        </a>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Pages definition
// ---------------------------------------------------------------------------
interface PageDef {
  titleKey: string;
  subtitleKey: string;
  render: PageRenderer;
}

const PAGES: PageDef[] = [
  { titleKey: 'guide.setup', subtitleKey: 'guide.setupSub', render: renderSetupPage },
  { titleKey: 'guide.features', subtitleKey: 'guide.featuresSub', render: renderFeaturesPage },
  { titleKey: 'guide.gallery', subtitleKey: 'guide.gallerySub', render: renderGalleryPage },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HelpModal: React.FC<HelpModalProps> = ({ isOpen, onClose }) => {
  const t = useT(i18nDict);
  const { i18n } = useTranslation();
  const lang: 'zh' | 'en' = !i18n.language?.startsWith('en') ? 'zh' : 'en';
  const navigate = useNavigate();
  const [pageIdx, setPageIdx] = useState(0);
  const [showcaseIdx, setShowcaseIdx] = useState(0);
  const [expandedFeat, setExpandedFeat] = useState<number | null>(null);

  const page = PAGES[pageIdx];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="" size="lg">
      <div className="space-y-6">
        {/* header */}
        <div className="text-center pb-4 border-b border-gray-100 dark:border-border-primary">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-banana-50 dark:from-background-primary to-orange-50 rounded-full mb-3">
            <Palette size={18} className="text-banana-600" />
            <span className="text-sm font-medium text-gray-700 dark:text-foreground-secondary">{t('guide.brand')}</span>
          </div>
          <h2 className="text-2xl font-bold text-gray-800 dark:text-foreground-primary">{t(page.titleKey)}</h2>
          <p className="text-sm text-gray-500 dark:text-foreground-tertiary mt-1">{t(page.subtitleKey)}</p>
        </div>

        {/* dots */}
        <div className="flex justify-center gap-2">
          {PAGES.map((p, i) => (
            <button
              key={i}
              onClick={() => setPageIdx(i)}
              className={`h-2 rounded-full transition-all ${i === pageIdx ? 'bg-banana-500 w-8' : 'bg-gray-300 hover:bg-gray-400 w-2'}`}
              title={t(p.titleKey)}
            />
          ))}
        </div>

        {/* body */}
        <div className="min-h-[400px]">
          {page.render({ t, lang, navigate, onClose, showcaseIdx, setShowcaseIdx, expandedFeat, setExpandedFeat })}
        </div>

        {/* footer */}
        <div className="pt-4 border-t flex justify-between items-center">
          <div className="flex items-center gap-2">
            {pageIdx > 0 && (
              <Button variant="ghost" onClick={() => setPageIdx(pageIdx - 1)} icon={<ChevronLeft size={16} />} size="sm">
                {t('guide.prev')}
              </Button>
            )}
          </div>

          <a href="https://github.com/Anionex/banana-slides" target="_blank" rel="noopener noreferrer" className="text-sm text-gray-500 dark:text-foreground-tertiary hover:text-gray-700 dark:hover:text-gray-200 flex items-center gap-1">
            <ExternalLink size={14} />
            GitHub
          </a>

          <div className="flex items-center gap-2">
            {pageIdx < PAGES.length - 1 ? (
              <Button onClick={() => setPageIdx(pageIdx + 1)} icon={<ChevronRight size={16} />} size="sm" className="bg-banana-500 hover:bg-banana-600 text-black dark:text-white">
                {t('guide.next')}
              </Button>
            ) : (
              <Button variant="ghost" onClick={onClose} size="sm">
                {t('common.close')}
              </Button>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
};