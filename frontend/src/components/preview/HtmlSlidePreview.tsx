import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Maximize2 } from 'lucide-react';
import { cn } from '@/utils';
import { getImageUrl } from '@/api/client';
import { Modal } from '@/components/shared';

export interface HtmlSlidePreviewProps {
  htmlUrl?: string;
  htmlContent?: string;
  title?: string;
  aspectRatio?: string;
  className?: string;
  allowFullscreen?: boolean;
  interactive?: boolean;
}

function getBaseViewport(aspectRatio: string = '16:9'): { width: number; height: number } {
  const normalized = (aspectRatio || '16:9').trim();
  if (normalized === '4:3') return { width: 1024, height: 768 };
  if (normalized === '1:1') return { width: 1080, height: 1080 };
  if (normalized === '9:16') return { width: 720, height: 1280 };
  if (normalized === '3:4') return { width: 768, height: 1024 };

  const parts = normalized.split(':');
  if (parts.length === 2) {
    const w = Number(parts[0]);
    const h = Number(parts[1]);
    if (w > 0 && h > 0) {
      const width = w >= h ? 1280 : 720;
      const height = Math.max(320, Math.round((width * h) / w));
      return { width, height };
    }
  }
  return { width: 1280, height: 720 };
}

export const HtmlSlidePreview: React.FC<HtmlSlidePreviewProps> = ({
  htmlUrl,
  htmlContent,
  title,
  aspectRatio = '16:9',
  className,
  allowFullscreen = false,
  interactive = false,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(0.25);
  const [isLoaded, setIsLoaded] = useState(false);
  const [isZoomOpen, setIsZoomOpen] = useState(false);

  const viewport = useMemo(() => getBaseViewport(aspectRatio), [aspectRatio]);
  const resolvedSrc = useMemo(() => (htmlUrl ? getImageUrl(htmlUrl) : undefined), [htmlUrl]);

  useEffect(() => {
    setIsLoaded(false);
  }, [resolvedSrc, htmlContent]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const updateScale = () => {
      const w = el.clientWidth;
      if (w > 0) {
        setScale(w / viewport.width);
      }
    };

    updateScale();

    if (typeof ResizeObserver !== 'undefined') {
      const observer = new ResizeObserver(() => updateScale());
      observer.observe(el);
      return () => observer.disconnect();
    }

    window.addEventListener('resize', updateScale);
    return () => window.removeEventListener('resize', updateScale);
  }, [viewport.width]);

  if (!resolvedSrc && !htmlContent) {
    return null;
  }

  return (
    <>
      <div
        ref={containerRef}
        data-testid="html-slide-preview"
        className={cn(
          'group/htmlslide relative w-full overflow-hidden bg-white dark:bg-background-secondary select-none',
          className
        )}
        style={{ aspectRatio: aspectRatio.replace(':', '/') }}
      >
        {!isLoaded && (
          <div className="absolute inset-0 animate-pulse bg-gray-100 dark:bg-background-hover" />
        )}
        <iframe
          title={title || 'HTML Slide Preview'}
          src={!htmlContent ? resolvedSrc : undefined}
          srcDoc={htmlContent}
          sandbox="allow-scripts allow-same-origin"
          scrolling="no"
          loading="lazy"
          onLoad={() => setIsLoaded(true)}
          style={{
            width: `${viewport.width}px`,
            height: `${viewport.height}px`,
            transform: `scale(${scale})`,
            transformOrigin: 'top left',
            border: 'none',
            pointerEvents: interactive ? 'auto' : 'none',
          }}
          className="absolute top-0 left-0 block bg-white"
        />
        {allowFullscreen && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setIsZoomOpen(true);
            }}
            title={title ? `Fullscreen: ${title}` : 'Fullscreen HTML Slide'}
            aria-label={title ? `Fullscreen: ${title}` : 'Fullscreen HTML Slide'}
            className="no-min-touch-target absolute top-2 right-2 z-10 p-1.5 rounded-lg bg-black/55 text-white opacity-0 group-hover/htmlslide:opacity-100 focus:opacity-100 hover:bg-black/75 transition-opacity"
          >
            <Maximize2 size={14} />
          </button>
        )}
      </div>

      {allowFullscreen && isZoomOpen && (
        <Modal
          isOpen={isZoomOpen}
          onClose={() => setIsZoomOpen(false)}
          title={title || 'HTML Slide'}
          size="wide"
        >
          <div className="w-full">
            <HtmlSlidePreview
              htmlUrl={htmlUrl}
              htmlContent={htmlContent}
              title={title}
              aspectRatio={aspectRatio}
              interactive={true}
              className="rounded-xl border border-gray-200 dark:border-border-primary shadow-md"
            />
          </div>
        </Modal>
      )}
    </>
  );
};
