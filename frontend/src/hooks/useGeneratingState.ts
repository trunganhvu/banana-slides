import type { Page } from '@/types';

/**
 * 
 *  page.status === 'GENERATING_DESCRIPTION' ,  'GENERATING' 
 */
export const useDescriptionGeneratingState = (
  page: Page,
  isAiRefining: boolean
): boolean => {
  return page.status === 'GENERATING_DESCRIPTION' || isAiRefining;
};

/**
 * 
 * : 
 * 1.  (isGenerating) 
 * 2.  GENERATING  () 
 */
export const useImageGeneratingState = (
  page: Page,
  isGenerating: boolean
): boolean => {
  return isGenerating || page.status === 'QUEUED' || page.status === 'GENERATING';
};

/**
 * @deprecated  useDescriptionGeneratingState  useImageGeneratingState 
 * : 
 * : , 
 */
export const useGeneratingState = (
  page: Page,
  isGenerating: boolean,
  isAiRefining: boolean
): boolean => {
  return isGenerating || page.status === 'QUEUED' || page.status === 'GENERATING' || isAiRefining;
};

/**
 * : 
 */
export const usePageGeneratingState = (
  page: Page,
  isGenerating: boolean
): boolean => {
  return isGenerating || page.status === 'QUEUED' || page.status === 'GENERATING';
};
