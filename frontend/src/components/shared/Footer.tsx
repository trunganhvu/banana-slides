import React from 'react';
import { BookOpen, Github } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const GITHUB_REPO = 'trunganhvu/banana-slides';
const GITHUB_URL = `https://github.com/${GITHUB_REPO}`;
const DOCS_URL = 'https://docs.bananaslides.online';

export const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();
  const { i18n } = useTranslation();
  const docsLabel = !i18n.language?.startsWith('en') ? 'Tài liệu' : 'Docs';

  return (
    <footer className="relative w-full py-4 sm:py-6 px-3 sm:px-4 mt-auto">
      <div className="max-w-5xl mx-auto">
        <div className="flex flex-wrap items-center justify-center gap-x-3 sm:gap-x-6 gap-y-2 text-xs sm:text-sm text-gray-500 dark:text-foreground-tertiary text-center">
          {/* Copyright */}
          <div className="inline-flex items-center gap-1.5">
            <span>© {currentYear}</span>
            <span className="font-semibold bg-gradient-to-r from-banana-600 to-orange-500 bg-clip-text text-transparent">
              Banana Slides
            </span>
          </div>

          <span className="text-gray-300 dark:text-border-primary select-none">·</span>

          {/* GitHub Link */}
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 hover:text-gray-900 dark:hover:text-white py-1 px-1.5 rounded active:scale-95 transition-all"
          >
            <Github size={15} />
            <span>GitHub</span>
          </a>

          <span className="text-gray-300 dark:text-border-primary select-none">·</span>

          {/* Documentation Link */}
          <a
            href={DOCS_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 hover:text-gray-900 dark:hover:text-white py-1 px-1.5 rounded active:scale-95 transition-all"
          >
            <BookOpen size={15} />
            <span>{docsLabel}</span>
          </a>
        </div>
      </div>
    </footer>
  );
};
