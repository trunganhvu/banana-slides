import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { Project, Page } from '@/types';

/**
 *  className ( Tailwind CSS)
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * 
 */
export function normalizeProject(data: any): Project {
  return {
    ...data,
    id: data.project_id || data.id,
    template_image_path: data.template_image_url || data.template_image_path,
    pages: (data.pages || []).map(normalizePage),
  };
}

/**
 * 
 */
export function normalizePage(data: any): Page {
  return {
    ...data,
    id: data.page_id || data.id,
    generated_image_path: data.generated_image_url || data.generated_image_path,
  };
}

/**
 * 
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null;
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * 
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * 
 */
export function downloadFile(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

export function downloadFromUrl(url: string, filename?: string) {
  const link = document.createElement('a');
  link.href = url;
  if (filename) {
    link.download = filename;
  }
  link.rel = 'noopener';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/**
 * 
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const lang = localStorage.getItem('i18nextLng') || navigator.language || 'zh-CN';
  const locale = lang.startsWith('zh') ? 'zh-CN' : 'en-US';
  return date.toLocaleString(locale, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * ID
 */
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * 
 */
export function normalizeErrorMessage(
  errorMessage: string | null | undefined,
  language?: string,
): string {
  const lang = language || localStorage.getItem('i18nextLng') || navigator.language || 'zh';
  const isVi = lang.startsWith('zh');

  if (!errorMessage) return isVi ? 'Thao tác thất bại' : 'Operation failed';

  const rawMessage = typeof errorMessage === 'string'
    ? errorMessage
    : (() => {
        try {
          return JSON.stringify(errorMessage);
        } catch {
          return String(errorMessage);
        }
      })();

  if (!rawMessage) return isVi ? 'Thao tác thất bại' : 'Operation failed';

  const message = rawMessage.toLowerCase();
  const isCodexContext = (
    message.includes('codex')
    || message.includes('chatgpt.com')
    || message.includes('/backend-api/codex/')
    || message.includes('openai oauth')
  );

  // Handle specific error messages
  if (message.includes('no template image found')) {
    return isVi
      ? 'Dự án hiện tại chưa có mẫu phong cách. Vui lòng chọn hoặc tải lên ảnh mẫu trước khi tạo.'
      : 'No template found. Please select or upload a template image first.';
  } else if (message.includes('page must have description content')) {
    return isVi
      ? 'Trang này chưa có mô tả. Vui lòng tạo hoặc nhập mô tả trước.'
      : 'This page has no description. Please generate or write a description first.';
  } else if (message.includes('image already exists')) {
    return isVi
      ? 'Trang này đã có ảnh. Vui lòng chọn Tạo lại nếu muốn làm mới.'
      : 'Image already exists. Choose "Regenerate" to create a new one.';
  }

  // Handle HTTP error codes
  if (message.includes('503') || message.includes('service unavailable')) {
    return isVi ? 'Dịch vụ AI tạm thời không khả dụng, vui lòng thử lại sau hoặc kiểm tra cấu hình API trong Cài đặt.' : 'AI service temporarily unavailable. Please try again later.';
  } else if (message.includes('500') || message.includes('internal server error')) {
    return isVi ? 'Lỗi nội bộ máy chủ, vui lòng thử lại sau.' : 'Internal server error. Please try again later.';
  } else if (message.includes('502') || message.includes('bad gateway')) {
    return isVi ? 'Lỗi cổng kết nối, vui lòng thử lại sau.' : 'Bad gateway. Please try again later.';
  } else if (message.includes('504') || message.includes('gateway timeout')) {
    return isVi ? 'Hết thời gian chờ yêu cầu, vui lòng thử lại sau.' : 'Gateway timeout. Please try again later.';
  } else if (message.includes('429') || message.includes('too many requests')) {
    return isVi ? 'Yêu cầu quá thường xuyên, vui lòng thử lại sau.' : 'Too many requests. Please try again later.';
  } else if (message.includes('401') || message.includes('unauthorized')) {
    if (isCodexContext || (message.includes('oauth') && message.includes('not connected'))) {
      return isVi
        ? 'Đăng nhập Codex đã hết hạn hoặc chưa kết nối, vui lòng vào Cài đặt để kết nối lại tài khoản OpenAI.'
        : 'Your Codex login has expired or is disconnected. Please reconnect your OpenAI account in Settings and try again.';
    }
    return isVi ? 'Xác thực thất bại, vui lòng kiểm tra cấu hình API Key.' : 'Authentication failed. Please check API key settings.';
  } else if (message.includes('403') || message.includes('forbidden')) {
    return isVi ? 'Truy cập bị từ chối, vui lòng kiểm tra quyền API.' : 'Access denied. Please check API permissions.';
  } else if (message.includes('aspect_ratio') || message.includes('aspect ratio')) {
    return isVi
      ? 'Tỷ lệ khung hình hiện tại không được mô hình này hỗ trợ, vui lòng thử tỷ lệ khác trong cài đặt dự án.'
      : 'The selected aspect ratio is not supported by this model. Please try a different ratio in project settings.';
  } else if (message.includes('network error') || message.includes('econnrefused')) {
    return isVi ? 'Kết nối mạng thất bại, vui lòng kiểm tra kết nối mạng hoặc máy chủ backend.' : 'Network error. Please check your connection.';
  } else if (message.includes('timeout')) {
    return isVi ? 'Hết thời gian chờ yêu cầu, vui lòng thử lại sau.' : 'Request timed out. Please try again later.';
  } else if (
    message.includes('sslerror')
    || message.includes('ssleoferror')
    || message.includes('unexpected_eof_while_reading')
    || message.includes('eof occurred in violation of protocol')
    || message.includes('max retries exceeded')
    || message.includes('httpsconnectionpool')
  ) {
    if (isCodexContext) {
      return isVi
        ? 'Kết nối tới dịch vụ Codex bị gián đoạn dẫn đến xuất thất bại. Vui lòng kết nối lại tài khoản OpenAI trong Cài đặt.'
        : 'The connection to Codex was interrupted and the export failed. Please try again later, or reconnect your OpenAI account in Settings if it keeps happening.';
    }
    return isVi
      ? 'Kết nối mạng bị gián đoạn khiến thao tác thất bại, vui lòng thử lại.'
      : 'The connection was interrupted and the operation failed. Please try again later.';
  } else if (message.includes('Trích xuất phong cách thất bại') || message.includes('style extraction failed')) {
    if (message.includes('Không hỗ trợ ảnh đầu vào') || message.includes('support image input')) {
      return isVi
        ? 'Xuất PPTX chỉnh sửa thất bại: Mô hình trích xuất không hỗ trợ ảnh đầu vào. Vui lòng đổi mô hình hỗ trợ thị giác trong Cài đặt.'
        : 'Editable PPTX export failed: the current style extraction model does not support image input. Switch to a vision-capable image caption model and try again.';
    }
    return isVi
      ? 'Xuất PPTX chỉnh sửa thất bại: Trích xuất phong cách văn bản không hoàn tất. Vui lòng kiểm tra cấu hình trong Cài đặt.'
      : 'Editable PPTX export failed because text style extraction did not complete. Check the image caption model/API settings, or enable partial results and try again.';
  }

  return rawMessage;
}

/**
 * PPT  MinerU  PDF. , 
 *  provider  MinerU. 
 */
export function normalizeRenovationErrorMessage(errorMessage: string | null | undefined): string {
  const rawMessage = typeof errorMessage === 'string' ? errorMessage : String(errorMessage || '');
  const message = rawMessage.toLowerCase();
  const lang = localStorage.getItem('banana-slides-language') || navigator.language || 'zh';
  const isVi = lang.startsWith('zh');
  const normalized = normalizeErrorMessage(errorMessage, lang);
  const looksLikeMineruCredentialStage = message.includes('get upload url')
    || message.includes('requesting upload url')
    || message.includes('file-urls/batch')
    || message.includes('task status')
    || message.includes('extract-results')
    || message.includes('file parsing failed');
  const looksLikeCredentialFailure = message.includes('401')
    || message.includes('403')
    || message.includes('unauthorized')
    || message.includes('forbidden')
    || message.includes('token expired')
    || message.includes('invalid token')
    || message.includes('token invalid')
    || message.includes('token has expired')
    || message.includes('authenticate failed')
    || message.includes('authentication failed');

  if (message.includes('mineru') && looksLikeMineruCredentialStage && looksLikeCredentialFailure) {
    return isVi
      ? 'Làm mới PPT không thể phân tích PDF: MinerU Token không hợp lệ hoặc đã hết hạn. Vui lòng cập nhật Token trong Cài đặt.'
      : 'PPT Renovation could not parse the PDF because the MinerU token is expired, invalid, or unauthorized. Update it in Settings → MinerU Configuration, run the "MinerU PDF Parsing" service test, then create the renovation project again.';
  }

  return normalized;
}

export const isDesktop = typeof window !== 'undefined' && 'electronAPI' in window;
export const DESKTOP_TITLEBAR_HEIGHT = 50;