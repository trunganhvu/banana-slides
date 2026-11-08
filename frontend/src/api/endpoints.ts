import { apiClient, getBaseURL } from './client';
import { getCachedClientHeaders } from '@/utils/clientKeyStorage';
import i18n from '@/i18n';
import type { Project, Task, ApiResponse, CreateProjectRequest, Page, Material, TemplateAsset } from '@/types';
import type { Settings } from '../types/index';

export type { Material };

// API client endpoint

export const checkAccessCode = async (): Promise<ApiResponse<{ enabled: boolean }>> => {
  const response = await apiClient.get<ApiResponse<{ enabled: boolean }>>('/api/access-code/check');
  return response.data;
};

export const verifyAccessCode = async (code: string): Promise<ApiResponse<{ valid: boolean }>> => {
  const response = await apiClient.post<ApiResponse<{ valid: boolean }>>('/api/access-code/verify', { code });
  return response.data;
};

// API client endpoint

/**
 * API
 */
export const createProject = async (data: CreateProjectRequest): Promise<ApiResponse<Project>> => {
  // API client endpoint
  let creation_type: string = data.creation_type ?? 'idea';
  if (!data.creation_type) {
    if (data.description_text) {
      creation_type = 'descriptions';
    } else if (data.outline_text) {
      creation_type = 'outline';
    }
  }

  const response = await apiClient.post<ApiResponse<Project>>('/api/projects', {
    creation_type,
    idea_prompt: data.idea_prompt,
    outline_text: data.outline_text,
    description_text: data.description_text,
    template_style: data.template_style,
    image_aspect_ratio: data.image_aspect_ratio,
  });
  return response.data;
};

/**
 * API
 */
export const uploadTemplate = async (
  projectId: string,
  templateImage: File
): Promise<ApiResponse<{ template_image_url: string }>> => {
  const formData = new FormData();
  formData.append('template_image', templateImage);

  const response = await apiClient.post<ApiResponse<{ template_image_url: string }>>(
    `/api/projects/${projectId}/template`,
    formData
  );
  return response.data;
};

/**
 * API (API) 
 */
export const listProjects = async (limit?: number, offset?: number): Promise<ApiResponse<{ projects: Project[]; total: number }>> => {
  const params = new URLSearchParams();
  if (limit !== undefined) params.append('limit', limit.toString());
  if (offset !== undefined) params.append('offset', offset.toString());

  const queryString = params.toString();
  const url = `/api/projects${queryString ? `?${queryString}` : ''}`;
  const response = await apiClient.get<ApiResponse<{ projects: Project[]; total: number }>>(url);
  return response.data;
};

/**
 * API
 */
export const getProject = async (projectId: string): Promise<ApiResponse<Project>> => {
  const response = await apiClient.get<ApiResponse<Project>>(`/api/projects/${projectId}`);
  return response.data;
};

/**
 * API
 */
export const deleteProject = async (projectId: string): Promise<ApiResponse> => {
  const response = await apiClient.delete<ApiResponse>(`/api/projects/${projectId}`);
  return response.data;
};

/**
 * API
 */
export const updateProject = async (
  projectId: string,
  data: Partial<Project>
): Promise<ApiResponse<Project>> => {
  const response = await apiClient.put<ApiResponse<Project>>(`/api/projects/${projectId}`, data);
  return response.data;
};

/**
 * API
 */
export const updatePagesOrder = async (
  projectId: string,
  pageIds: string[]
): Promise<ApiResponse<Project>> => {
  const response = await apiClient.put<ApiResponse<Project>>(
    `/api/projects/${projectId}`,
    { pages_order: pageIds }
  );
  return response.data;
};

// API client endpoint

/**
 * API
 * @param projectId APIID
 * @param language API (API, API sessionStorage API) 
 */
export const generateOutline = async (projectId: string, language?: OutputLanguage): Promise<ApiResponse> => {
  const lang = language || await getStoredOutputLanguage();
  const response = await apiClient.post<ApiResponse>(
    `/api/projects/${projectId}/generate/outline`,
    { language: lang }
  );
  return response.data;
};

/**
 * API (SSE) 
 * API ReadableStream, API page API
 */
export interface OutlineStreamPage {
  index: number;
  title: string;
  points: string[];
  part?: string;
  description_text?: string;
  extra_fields?: Record<string, string>;
}

export interface OutlineStreamCallbacks {
  onPage: (page: OutlineStreamPage) => void;
  onDone: (data: { total: number; pages: Page[] }) => void;
  onError: (message: string) => void;
}

export const generateOutlineStream = async (
  projectId: string,
  callbacks: OutlineStreamCallbacks,
  language?: OutputLanguage,
  lockPageCount?: boolean,
): Promise<void> => {
  const lang = language || await getStoredOutputLanguage();
  const accessCode = localStorage.getItem('banana-access-code');

  const response = await fetch(`${getBaseURL()}/api/projects/${projectId}/generate/outline/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept-Language': i18n.language || 'zh',
      ...(accessCode ? { 'X-Access-Code': accessCode } : {}),
      ...(getCachedClientHeaders() || {}),
    },
    body: JSON.stringify({ language: lang, lock_page_count: lockPageCount }),
  });

  if (!response.ok || !response.body) {
    callbacks.onError(`HTTP ${response.status}`);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  let readResult = await reader.read();
  while (!readResult.done) {
    const { value } = readResult;

    buffer += decoder.decode(value, { stream: true });

    // Parse SSE events from buffer
    const parts = buffer.split('\n\n');
    buffer = parts.pop() || '';

    for (const part of parts) {
      const lines = part.split('\n');
      let eventType = '';
      let eventData = '';

      for (const line of lines) {
        if (line.startsWith('event: ')) eventType = line.slice(7);
        else if (line.startsWith('data: ')) eventData = line.slice(6);
      }

      if (!eventType || !eventData) continue;

      try {
        const parsed = JSON.parse(eventData);
        if (eventType === 'page') callbacks.onPage(parsed);
        else if (eventType === 'done') callbacks.onDone(parsed);
        else if (eventType === 'error') callbacks.onError(parsed.message);
      } catch {
        // Skip malformed events
      }
    }

    readResult = await reader.read();
  }
};

// API client endpoint

/**
 * API (API) 
 * @param projectId APIID
 * @param descriptionText API (API) 
 * @param language API (API, API sessionStorage API) 
 */
export const generateFromDescription = async (projectId: string, descriptionText?: string, language?: OutputLanguage): Promise<ApiResponse> => {
  const lang = language || await getStoredOutputLanguage();
  const response = await apiClient.post<ApiResponse>(
    `/api/projects/${projectId}/generate/from-description`,
    { 
      ...(descriptionText ? { description_text: descriptionText } : {}),
      language: lang 
    }
  );
  return response.data;
};

/**
 * API (API) 
 * @param projectId APIID
 * @param language API (API, API sessionStorage API) 
 */
export const generateDescriptions = async (projectId: string, language?: OutputLanguage, detailLevel?: string): Promise<ApiResponse> => {
  const lang = language || await getStoredOutputLanguage();
  const response = await apiClient.post<ApiResponse>(
    `/api/projects/${projectId}/generate/descriptions`,
    { language: lang, detail_level: detailLevel || 'default' }
  );
  return response.data;
};

/**
 * API (SSE) 
 */
export interface DescriptionStreamEvent {
  page_index: number;
  page_id: string;
  text: string;
  extra_fields?: Record<string, string>;
}

export interface DescriptionStreamCallbacks {
  onDescription: (data: DescriptionStreamEvent) => void;
  onDone: (data: { total: number; pages: Page[] }) => void;
  onError: (message: string) => void;
}

export const generateDescriptionsStream = async (
  projectId: string,
  callbacks: DescriptionStreamCallbacks,
  language?: OutputLanguage,
  detailLevel?: string,
): Promise<void> => {
  const lang = language || await getStoredOutputLanguage();
  const accessCode = localStorage.getItem('banana-access-code');

  const response = await fetch(`${getBaseURL()}/api/projects/${projectId}/generate/descriptions/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept-Language': i18n.language || 'zh',
      ...(accessCode ? { 'X-Access-Code': accessCode } : {}),
      ...(getCachedClientHeaders() || {}),
    },
    body: JSON.stringify({ language: lang, detail_level: detailLevel || 'default' }),
  });

  if (!response.ok || !response.body) {
    callbacks.onError(`HTTP ${response.status}`);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  let readResult = await reader.read();
  while (!readResult.done) {
    const { value } = readResult;

    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split('\n\n');
    buffer = parts.pop() || '';

    for (const part of parts) {
      const lines = part.split('\n');
      let eventType = '';
      let eventData = '';

      for (const line of lines) {
        if (line.startsWith('event: ')) eventType = line.slice(7);
        else if (line.startsWith('data: ')) eventData = line.slice(6);
      }

      if (!eventType || !eventData) continue;

      try {
        const parsed = JSON.parse(eventData);
        if (eventType === 'description') callbacks.onDescription(parsed);
        else if (eventType === 'done') callbacks.onDone(parsed);
        else if (eventType === 'error') callbacks.onError(parsed.message);
      } catch {
        // Skip malformed events
      }
    }

    readResult = await reader.read();
  }
};

/**
 * API
 */
export const generatePageDescription = async (
  projectId: string,
  pageId: string,
  forceRegenerate: boolean = false,
  language?: OutputLanguage,
  detailLevel?: string
): Promise<ApiResponse> => {
  const lang = language || await getStoredOutputLanguage();
  const response = await apiClient.post<ApiResponse>(
    `/api/projects/${projectId}/pages/${pageId}/generate/description`,
    { force_regenerate: forceRegenerate, language: lang, detail_level: detailLevel || 'default' }
  );
  return response.data;
};

/**
 * API PPT API (API PDF API) 
 */
export const regenerateRenovationPage = async (
  projectId: string,
  pageId: string,
  keepLayout: boolean = false,
  language?: OutputLanguage
): Promise<ApiResponse> => {
  const lang = language || await getStoredOutputLanguage();
  const response = await apiClient.post<ApiResponse>(
    `/api/projects/${projectId}/pages/${pageId}/regenerate-renovation`,
    { keep_layout: keepLayout, language: lang }
  );
  return response.data;
};

/**
 * API
 * @param projectId APIID
 * @param userRequirement API
 * @param previousRequirements API (API) 
 * @param language API (API, API sessionStorage API) 
 */
export const refineOutline = async (
  projectId: string,
  userRequirement: string,
  previousRequirements?: string[],
  language?: OutputLanguage
): Promise<ApiResponse<{ pages: Page[]; message: string }>> => {
  const lang = language || await getStoredOutputLanguage();
  const response = await apiClient.post<ApiResponse<{ pages: Page[]; message: string }>>(
    `/api/projects/${projectId}/refine/outline`,
    {
      user_requirement: userRequirement,
      previous_requirements: previousRequirements || [],
      language: lang
    }
  );
  return response.data;
};

/**
 * API
 * @param projectId APIID
 * @param userRequirement API
 * @param previousRequirements API (API) 
 * @param language API (API, API sessionStorage API) 
 */
export const refineDescriptions = async (
  projectId: string,
  userRequirement: string,
  previousRequirements?: string[],
  language?: OutputLanguage
): Promise<ApiResponse<{ pages: Page[]; message: string }>> => {
  const lang = language || await getStoredOutputLanguage();
  const response = await apiClient.post<ApiResponse<{ pages: Page[]; message: string }>>(
    `/api/projects/${projectId}/refine/descriptions`,
    {
      user_requirement: userRequirement,
      previous_requirements: previousRequirements || [],
      language: lang
    }
  );
  return response.data;
};

// API client endpoint

/**
 * API
 * @param projectId APIID
 * @param language API (API, API sessionStorage API) 
 * @param pageIds APIIDAPI, API
 */
export const generateImages = async (projectId: string, language?: OutputLanguage, pageIds?: string[]): Promise<ApiResponse> => {
  const lang = language || await getStoredOutputLanguage();
  const response = await apiClient.post<ApiResponse>(
    `/api/projects/${projectId}/generate/images`,
    { language: lang, page_ids: pageIds }
  );
  return response.data;
};

/**
 * API
 */
export const generatePageImage = async (
  projectId: string,
  pageId: string,
  forceRegenerate: boolean = false,
  language?: OutputLanguage
): Promise<ApiResponse> => {
  const lang = language || await getStoredOutputLanguage();
  const response = await apiClient.post<ApiResponse>(
    `/api/projects/${projectId}/pages/${pageId}/generate/image`,
    { force_regenerate: forceRegenerate, language: lang }
  );
  return response.data;
};

/**
 * API (API) 
 */
export const editPageImage = async (
  projectId: string,
  pageId: string,
  editPrompt: string,
  contextImages?: {
    useTemplate?: boolean;
    descImageUrls?: string[];
    uploadedFiles?: File[];
  }
): Promise<ApiResponse> => {
  // API client endpoint
  if (contextImages?.uploadedFiles && contextImages.uploadedFiles.length > 0) {
    const formData = new FormData();
    formData.append('edit_instruction', editPrompt);
    formData.append('use_template', String(contextImages.useTemplate || false));
    if (contextImages.descImageUrls && contextImages.descImageUrls.length > 0) {
      formData.append('desc_image_urls', JSON.stringify(contextImages.descImageUrls));
    }
    // API client endpoint
    contextImages.uploadedFiles.forEach((file) => {
      formData.append('context_images', file);
    });

    const response = await apiClient.post<ApiResponse>(
      `/api/projects/${projectId}/pages/${pageId}/edit/image`,
      formData
    );
    return response.data;
  } else {
    // API client endpoint
    const response = await apiClient.post<ApiResponse>(
      `/api/projects/${projectId}/pages/${pageId}/edit/image`,
      {
        edit_instruction: editPrompt,
        context_images: {
          use_template: contextImages?.useTemplate || false,
          desc_image_urls: contextImages?.descImageUrls || [],
        },
      }
    );
    return response.data;
  }
};

/**
 * API
 */
export const getPageImageVersions = async (
  projectId: string,
  pageId: string
): Promise<ApiResponse<{ versions: any[] }>> => {
  const response = await apiClient.get<ApiResponse<{ versions: any[] }>>(
    `/api/projects/${projectId}/pages/${pageId}/image-versions`
  );
  return response.data;
};

/**
 * API
 */
export const setCurrentImageVersion = async (
  projectId: string,
  pageId: string,
  versionId: string
): Promise<ApiResponse> => {
  const response = await apiClient.post<ApiResponse>(
    `/api/projects/${projectId}/pages/${pageId}/image-versions/${versionId}/set-current`
  );
  return response.data;
};

// API client endpoint

/**
 * API
 */
export const updatePage = async (
  projectId: string,
  pageId: string,
  data: Partial<Page>
): Promise<ApiResponse<Page>> => {
  const response = await apiClient.put<ApiResponse<Page>>(
    `/api/projects/${projectId}/pages/${pageId}`,
    data
  );
  return response.data;
};

/**
 * API
 */
export const updatePageDescription = async (
  projectId: string,
  pageId: string,
  descriptionContent: any,
  language?: OutputLanguage
): Promise<ApiResponse<Page>> => {
  const lang = language || await getStoredOutputLanguage();
  const response = await apiClient.put<ApiResponse<Page>>(
    `/api/projects/${projectId}/pages/${pageId}/description`,
    { description_content: descriptionContent, language: lang }
  );
  return response.data;
};

/**
 * API
 */
export const updatePageOutline = async (
  projectId: string,
  pageId: string,
  outlineContent: any,
  language?: OutputLanguage
): Promise<ApiResponse<Page>> => {
  const lang = language || await getStoredOutputLanguage();
  const response = await apiClient.put<ApiResponse<Page>>(
    `/api/projects/${projectId}/pages/${pageId}/outline`,
    { outline_content: outlineContent, language: lang }
  );
  return response.data;
};

/**
 * API
 */
export const deletePage = async (projectId: string, pageId: string): Promise<ApiResponse> => {
  const response = await apiClient.delete<ApiResponse>(
    `/api/projects/${projectId}/pages/${pageId}`
  );
  return response.data;
};

/**
 * API
 */
export const addPage = async (projectId: string, data: Partial<Page>): Promise<ApiResponse<Page>> => {
  const response = await apiClient.post<ApiResponse<Page>>(
    `/api/projects/${projectId}/pages`,
    data
  );
  return response.data;
};

/**
 * API
 */
export const addPages = async (projectId: string, pages: Partial<Page>[]): Promise<ApiResponse<Page[]>> => {
  const response = await apiClient.post<ApiResponse<Page[]>>(
    `/api/projects/${projectId}/pages/batch`,
    { pages }
  );
  return response.data;
};

// API client endpoint

/**
 * API
 */
export const getTaskStatus = async (projectId: string, taskId: string): Promise<ApiResponse<Task>> => {
  const response = await apiClient.get<ApiResponse<Task>>(`/api/projects/${projectId}/tasks/${taskId}`);
  return response.data;
};

// API client endpoint

/**
 * API
 */
export const updatePageNarration = async (
  projectId: string,
  pageId: string,
  narrationText: string
): Promise<ApiResponse<Page>> => {
  const response = await apiClient.put<ApiResponse<Page>>(
    `/api/projects/${projectId}/pages/${pageId}/narration`,
    { narration_text: narrationText }
  );
  return response.data;
};

/**
 * AI API
 */
export const generatePageNarration = async (
  projectId: string,
  pageId: string,
  language?: OutputLanguage
): Promise<ApiResponse<Page>> => {
  const lang = language || await getStoredOutputLanguage();
  const response = await apiClient.post<ApiResponse<Page>>(
    `/api/projects/${projectId}/pages/${pageId}/generate/narration`,
    { language: lang }
  );
  return response.data;
};

/**
 * API
 */
export const generateAllNarrations = async (
  projectId: string,
  language?: OutputLanguage,
  forceRegenerate?: boolean
): Promise<ApiResponse<{ total: number; generated: number; skipped: number; failed: number; pages: Page[] }>> => {
  const lang = language || await getStoredOutputLanguage();
  const response = await apiClient.post<ApiResponse<{ total: number; generated: number; skipped: number; failed: number; pages: Page[] }>>(
    `/api/projects/${projectId}/generate/narrations`,
    { language: lang, force_regenerate: forceRegenerate || false }
  );
  return response.data;
};

// API client endpoint

/**
 * Helper function to build query string with page_ids
 */
const buildPageIdsQuery = (pageIds?: string[]): string => {
  if (!pageIds || pageIds.length === 0) return '';
  const params = new URLSearchParams();
  params.set('page_ids', pageIds.join(','));
  return `?${params.toString()}`;
};

const buildExportQuery = (params: Record<string, string | string[] | boolean | undefined>): string => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined) return;
    if (Array.isArray(value)) {
      if (value.length > 0) query.set(key, value.join(','));
      return;
    }
    query.set(key, String(value));
  });
  const queryString = query.toString();
  return queryString ? `?${queryString}` : '';
};

/**
 * APIPPTX
 * @param projectId APIID
 * @param pageIds APIIDAPI, API
 * @param clientTaskId APIID, API
 */
export const exportPPTX = async (
  projectId: string,
  pageIds?: string[],
  options?: {
    transitionEnabled?: boolean;
    transitionEffects?: string[];
  }
): Promise<ApiResponse<{ download_url: string; download_url_absolute?: string }>> => {
  const url = `/api/projects/${projectId}/export/pptx${buildExportQuery({
    page_ids: pageIds,
    transition_enabled: options?.transitionEnabled ? true : undefined,
    transition_effects: options?.transitionEnabled ? options.transitionEffects : undefined,
  })}`;
  const response = await apiClient.get<
    ApiResponse<{ download_url: string; download_url_absolute?: string }>
  >(url);
  return response.data;
};

/**
 * APIPDF
 * @param projectId APIID
 * @param pageIds APIIDAPI, API
 */
export const exportPDF = async (
  projectId: string,
  pageIds?: string[]
): Promise<ApiResponse<{ download_url: string; download_url_absolute?: string }>> => {
  const url = `/api/projects/${projectId}/export/pdf${buildPageIdsQuery(pageIds)}`;
  const response = await apiClient.get<
    ApiResponse<{ download_url: string; download_url_absolute?: string }>
  >(url);
  return response.data;
};

/**
 * API (API, APIZIP) 
 */
export const exportImages = async (
  projectId: string,
  pageIds?: string[]
): Promise<ApiResponse<{ download_url: string; download_url_absolute?: string }>> => {
  const url = `/api/projects/${projectId}/export/images${buildPageIdsQuery(pageIds)}`;
  const response = await apiClient.get<
    ApiResponse<{ download_url: string; download_url_absolute?: string }>
  >(url);
  return response.data;
};

/**
 * APIPPTX (API) 
 * @param projectId APIID
 * @param filename API
 * @param pageIds APIIDAPI, API
 */
export const exportEditablePPTX = async (
  projectId: string,
  filename?: string,
  pageIds?: string[],
  clientTaskId?: string,
): Promise<ApiResponse<{ task_id: string }>> => {
  const response = await apiClient.post<
    ApiResponse<{ task_id: string }>
  >(`/api/projects/${projectId}/export/editable-pptx`, {
    filename,
    page_ids: pageIds,
    client_task_id: clientTaskId,
  });
  return response.data;
};

/**
 * API
 */
export const listExports = async (
  projectId: string,
): Promise<ApiResponse<{ files: Array<{
  filename: string;
  type: string;
  size: number;
  modified_at: string;
  download_url: string;
}> }>> => {
  const response = await apiClient.get(`/api/projects/${projectId}/exports`);
  return response.data;
};

/**
 * API
 */
export const deleteExport = async (
  projectId: string,
  filename: string,
): Promise<ApiResponse<{ filename: string }>> => {
  const response = await apiClient.delete(
    `/api/projects/${projectId}/exports/${encodeURIComponent(filename)}`
  );
  return response.data;
};

/**
 * API (API) 
 * @param projectId APIID
 * @param options API
 */
export const exportVideo = async (
  projectId: string,
  options?: {
    filename?: string;
    pageIds?: string[];
    voice?: string;
    rate?: string;
    speed?: number;
    language?: string;
    generateNarration?: boolean;
    enableKenBurns?: boolean;
    includeNoImagePages?: boolean;
    presentationTopic?: string;
    narrationConfig?: {
      speaker_persona?: string;
      target_audience?: string;
      speech_tone?: string;
      presentation_topic?: string;
      min_words?: number;
      max_words?: number;
    };
  }
): Promise<ApiResponse<{ task_id: string }>> => {
  const response = await apiClient.post<
    ApiResponse<{ task_id: string }>
  >(`/api/projects/${projectId}/export/video`, {
    filename: options?.filename,
    page_ids: options?.pageIds,
    voice: options?.voice,
    rate: options?.rate,
    speed: options?.speed,
    language: options?.language,
    generate_narration: options?.generateNarration ?? true,
    enable_ken_burns: options?.enableKenBurns ?? false,
    include_no_image_pages: options?.includeNoImagePages ?? false,
    presentation_topic: options?.presentationTopic,
    narration_config: options?.narrationConfig,
  });
  return response.data;
};

// API client endpoint

/**
 * API (API) 
 * APIID, APIgetTaskStatusAPI
 */
export const generateMaterialImage = async (
  projectId: string,
  prompt: string,
  refImage?: File | null,
  extraImages?: File[],
  aspectRatio?: string
): Promise<ApiResponse<{ task_id: string; status: string }>> => {
  const formData = new FormData();
  formData.append('prompt', prompt);
  if (aspectRatio) {
    formData.append('aspect_ratio', aspectRatio);
  }
  if (refImage) {
    formData.append('ref_image', refImage);
  }

  if (extraImages && extraImages.length > 0) {
    extraImages.forEach((file) => {
      formData.append('extra_images', file);
    });
  }

  const response = await apiClient.post<ApiResponse<{ task_id: string; status: string }>>(
    `/api/projects/${projectId}/materials/generate`,
    formData
  );
  return response.data;
};

export type MaterialProcessOperation =
  | 'generate'
  | 'edit_full'
  | 'region_edit'
  | 'erase_region';

export interface MaterialSelectionRect {
  x: number;
  y: number;
  width: number;
  height: number;
  image_width: number;
  image_height: number;
}

export interface ProcessMaterialOptions {
  operation: MaterialProcessOperation;
  prompt?: string;
  sourceImage?: File | null;
  refImage?: File | null;
  extraImages?: File[];
  aspectRatio?: string;
  selection?: MaterialSelectionRect | null;
  applyMode?: 'overlay_selection' | 'replace_full';
}

export const processMaterialImage = async (
  projectId: string,
  options: ProcessMaterialOptions
): Promise<ApiResponse<{ task_id: string; status: string }>> => {
  const formData = new FormData();
  formData.append('operation', options.operation);
  if (options.prompt) {
    formData.append('prompt', options.prompt);
  }
  if (options.aspectRatio) {
    formData.append('aspect_ratio', options.aspectRatio);
  }
  if (options.applyMode) {
    formData.append('apply_mode', options.applyMode);
  }
  if (options.selection) {
    formData.append('selection', JSON.stringify(options.selection));
  }
  if (options.sourceImage) {
    formData.append('source_image', options.sourceImage);
  }
  if (options.refImage) {
    formData.append('ref_image', options.refImage);
  }
  if (options.extraImages && options.extraImages.length > 0) {
    options.extraImages.forEach((file) => {
      formData.append('extra_images', file);
    });
  }

  const response = await apiClient.post<ApiResponse<{ task_id: string; status: string }>>(
    `/api/projects/${projectId}/materials/process`,
    formData
  );
  return response.data;
};

/**
 * API
 * @param projectId APIID, API
 *   - If provided and not 'all' or 'none': Get materials for specific project via /api/projects/{projectId}/materials
 *   - If 'all': Get all materials via /api/materials?project_id=all
 *   - If 'none': Get global materials (not bound to any project) via /api/materials?project_id=none
 *   - If not provided: Get all materials via /api/materials
 */
export const listMaterials = async (
  projectId?: string
): Promise<ApiResponse<{ materials: Material[]; count: number }>> => {
  let url: string;

  if (!projectId || projectId === 'all') {
    // Get all materials using global endpoint
    url = '/api/materials?project_id=all';
  } else if (projectId === 'none') {
    // Get global materials (not bound to any project)
    url = '/api/materials?project_id=none';
  } else {
    // Get materials for specific project
    url = `/api/projects/${projectId}/materials`;
  }

  const response = await apiClient.get<ApiResponse<{ materials: Material[]; count: number }>>(url);
  return response.data;
};

/**
 * API
 * @param file API
 * @param projectId APIID
 *   - If provided: Upload material bound to the project
 *   - If not provided or 'none': Upload as global material (not bound to any project)
 */
export const uploadMaterial = async (
  file: File,
  projectId?: string | null,
  generateCaption?: boolean
): Promise<ApiResponse<Material & { caption?: string }>> => {
  const formData = new FormData();
  formData.append('file', file);

  let url: string;
  if (!projectId || projectId === 'none') {
    // Use global upload endpoint for materials not bound to any project
    url = '/api/materials/upload';
  } else {
    // Use project-specific upload endpoint
    url = `/api/projects/${projectId}/materials/upload`;
  }

  if (generateCaption) {
    url += (url.includes('?') ? '&' : '?') + 'generate_caption=true';
  }

  const response = await apiClient.post<ApiResponse<Material & { caption?: string }>>(url, formData);
  return response.data;
};

/**
 * API
 */
export const deleteMaterial = async (materialId: string): Promise<ApiResponse<{ id: string }>> => {
  const response = await apiClient.delete<ApiResponse<{ id: string }>>(`/api/materials/${materialId}`);
  return response.data;
};

/**
 * Generate caption for an existing material
 */
export const getMaterialCaption = async (materialId: string): Promise<ApiResponse<{ caption: string }>> => {
  const response = await apiClient.get<ApiResponse<{ caption: string }>>(`/api/materials/${materialId}/caption`);
  return response.data;
};

/**
 * Get material by URL and ensure it has a caption
 */
export const getMaterialByUrl = async (url: string): Promise<ApiResponse<Material>> => {
  const response = await apiClient.get<ApiResponse<Material>>(`/api/materials/by-url`, { params: { url } });
  return response.data;
};

/**
 * Download selected materials bundled as a zip archive.
 */
export const downloadMaterialsZip = async (
  materialIds: string[]
): Promise<ApiResponse<{ download_url: string }>> => {
  const { data: blob } = await apiClient.post<Blob>(
    '/api/materials/download',
    { material_ids: materialIds },
    { responseType: 'blob' },
  );

  const href = URL.createObjectURL(blob);
  const link = Object.assign(document.createElement('a'), {
    href,
    download: 'materials.zip',
  });
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(href);

  return { success: true, data: { download_url: '' } };
};

/**
 * API (APIURL) 
 * @param projectId APIID
 * @param materialUrls APIURLAPI
 */
export const associateMaterialsToProject = async (
  projectId: string,
  materialUrls: string[]
): Promise<ApiResponse<{ updated_ids: string[]; count: number }>> => {
  const response = await apiClient.post<ApiResponse<{ updated_ids: string[]; count: number }>>(
    '/api/materials/associate',
    { project_id: projectId, material_urls: materialUrls }
  );
  return response.data;
};

// API client endpoint

export interface UserTemplate {
  template_id: string;
  name?: string;
  template_image_url: string;
  thumb_url?: string;  // Thumbnail URL for faster loading
  created_at?: string;
  updated_at?: string;
}

/**
 * API
 */
export const uploadUserTemplate = async (
  templateImage: File,
  name?: string
): Promise<ApiResponse<UserTemplate>> => {
  const formData = new FormData();
  formData.append('template_image', templateImage);
  if (name) {
    formData.append('name', name);
  }

  const response = await apiClient.post<ApiResponse<UserTemplate>>(
    '/api/user-templates',
    formData
  );
  return response.data;
};

/**
 * API
 */
export const listUserTemplates = async (): Promise<ApiResponse<{ templates: UserTemplate[] }>> => {
  const response = await apiClient.get<ApiResponse<{ templates: UserTemplate[] }>>(
    '/api/user-templates'
  );
  return response.data;
};

/**
 * API
 */
export const deleteUserTemplate = async (templateId: string): Promise<ApiResponse> => {
  const response = await apiClient.delete<ApiResponse>(`/api/user-templates/${templateId}`);
  return response.data;
};

// API client endpoint

export interface UserStyleTemplate {
  id: string;
  name: string;
  description: string;
  color?: string;
  created_at?: string;
}

export const createUserStyleTemplate = async (
  data: { name: string; description: string; color?: string }
): Promise<ApiResponse<UserStyleTemplate>> => {
  const response = await apiClient.post<ApiResponse<UserStyleTemplate>>(
    '/api/user-style-templates',
    data
  );
  return response.data;
};

export const listUserStyleTemplates = async (): Promise<ApiResponse<{ templates: UserStyleTemplate[] }>> => {
  const response = await apiClient.get<ApiResponse<{ templates: UserStyleTemplate[] }>>(
    '/api/user-style-templates'
  );
  return response.data;
};

export const deleteUserStyleTemplate = async (id: string): Promise<ApiResponse> => {
  const response = await apiClient.delete<ApiResponse>(`/api/user-style-templates/${id}`);
  return response.data;
};

// API client endpoint

export interface ReferenceFile {
  id: string;
  project_id: string | null;
  filename: string;
  file_size: number;
  file_type: string;
  parse_status: 'pending' | 'parsing' | 'completed' | 'failed';
  markdown_content: string | null;
  error_message: string | null;
  image_caption_failed_count?: number;  // Optional, calculated dynamically
  created_at: string;
  updated_at: string;
}

/**
 * API
 * @param file API
 * @param projectId APIID (API'none', API) 
 */
export const uploadReferenceFile = async (
  file: File,
  projectId?: string | null
): Promise<ApiResponse<{ file: ReferenceFile }>> => {
  const formData = new FormData();
  formData.append('file', file);
  if (projectId && projectId !== 'none') {
    formData.append('project_id', projectId);
  }

  const response = await apiClient.post<ApiResponse<{ file: ReferenceFile }>>(
    '/api/reference-files/upload',
    formData
  );
  return response.data;
};

/**
 * API
 * @param fileId APIID
 */
export const getReferenceFile = async (fileId: string): Promise<ApiResponse<{ file: ReferenceFile }>> => {
  const response = await apiClient.get<ApiResponse<{ file: ReferenceFile }>>(
    `/api/reference-files/${fileId}`
  );
  return response.data;
};

/**
 * API
 * @param projectId APIID ('global' API 'none' API) 
 */
export const listProjectReferenceFiles = async (
  projectId: string
): Promise<ApiResponse<{ files: ReferenceFile[] }>> => {
  const response = await apiClient.get<ApiResponse<{ files: ReferenceFile[] }>>(
    `/api/reference-files/project/${projectId}`
  );
  return response.data;
};

/**
 * API
 * @param fileId APIID
 */
export const deleteReferenceFile = async (fileId: string): Promise<ApiResponse<{ message: string }>> => {
  const response = await apiClient.delete<ApiResponse<{ message: string }>>(
    `/api/reference-files/${fileId}`
  );
  return response.data;
};

/**
 * API
 * @param fileId APIID
 */
export const triggerFileParse = async (fileId: string): Promise<ApiResponse<{ file: ReferenceFile; message: string }>> => {
  const response = await apiClient.post<ApiResponse<{ file: ReferenceFile; message: string }>>(
    `/api/reference-files/${fileId}/parse`
  );
  return response.data;
};

/**
 * API
 * @param fileId APIID
 * @param projectId APIID
 */
export const associateFileToProject = async (
  fileId: string,
  projectId: string
): Promise<ApiResponse<{ file: ReferenceFile }>> => {
  const response = await apiClient.post<ApiResponse<{ file: ReferenceFile }>>(
    `/api/reference-files/${fileId}/associate`,
    { project_id: projectId }
  );
  return response.data;
};

/**
 * API (API) 
 * @param fileId APIID
 */
export const dissociateFileFromProject = async (
  fileId: string
): Promise<ApiResponse<{ file: ReferenceFile; message: string }>> => {
  const response = await apiClient.post<ApiResponse<{ file: ReferenceFile; message: string }>>(
    `/api/reference-files/${fileId}/dissociate`
  );
  return response.data;
};

// API client endpoint

export type OutputLanguage = 'vi' | 'zh' | 'ja' | 'en' | 'auto';

export interface OutputLanguageOption {
  value: OutputLanguage;
  label: string;
}

export const OUTPUT_LANGUAGE_OPTIONS: OutputLanguageOption[] = [
  { value: 'vi', label: 'Tiếng Việt' },
  { value: 'ja', label: 'Japanese' },
  { value: 'en', label: 'English' },
  { value: 'auto', label: 'Tự động' },
];

/**
 * API (API) 
 *
 * API: API. 
 * API sessionStorage API, 
 * API language API. 
 */
export const getDefaultOutputLanguage = async (): Promise<ApiResponse<{ language: OutputLanguage }>> => {
  const response = await apiClient.get<ApiResponse<{ language: OutputLanguage }>>(
    '/api/output-language'
  );
  return response.data;
};

/**
 * API Settings API
 * API, API 'zh'
 */
export const getStoredOutputLanguage = async (): Promise<OutputLanguage> => {
  try {
    const response = await apiClient.get<ApiResponse<{ language: OutputLanguage }>>('/api/output-language');
    return response.data.data?.language || 'zh';
  } catch (error) {
    console.warn('Failed to load output language from settings, using default', error);
    return 'zh';
  }
};

/**
 * API
 */
export const getSettings = async (): Promise<ApiResponse<Settings>> => {
  const response = await apiClient.get<ApiResponse<Settings>>('/api/settings');
  return response.data;
};

export const getElevenLabsVoices = async (): Promise<ApiResponse<{ voices: { id: string; name: string; category: string; languages?: string[]; accent?: string | null }[] }>> => {
  const response = await apiClient.get('/api/settings/elevenlabs-voices');
  return response.data;
};

/**
 * API
 */
export const updateSettings = async (
  data: Partial<Omit<Settings, 'id' | 'api_key_length' | 'mineru_token_length' | 'baidu_api_key_length' | 'elevenlabs_api_key_length' | 'created_at' | 'updated_at'>> & {
    api_key?: string;
    mineru_token?: string;
    baidu_api_key?: string;
    elevenlabs_api_key?: string;
    text_api_key?: string;
    image_api_key?: string;
    image_caption_api_key?: string;
    lazyllm_api_keys?: Record<string, string>;
  }
): Promise<ApiResponse<Settings>> => {
  const response = await apiClient.put<ApiResponse<Settings>>('/api/settings', data);
  return response.data;
};

/**
 * API
 */
export const resetSettings = async (): Promise<ApiResponse<Settings>> => {
  const response = await apiClient.post<ApiResponse<Settings>>('/api/settings/reset');
  return response.data;
};

/**
 * OpenAI OAuth: get authorization URL
 */
export const getOpenAIOAuthUrl = async (): Promise<ApiResponse<{ auth_url: string; callback_server_available?: boolean }>> => {
  const response = await apiClient.get<ApiResponse<{ auth_url: string; callback_server_available?: boolean }>>('/api/settings/openai-oauth/authorize');
  return response.data;
};

/**
 * OpenAI OAuth: disconnect
 */
export const disconnectOpenAIOAuth = async (): Promise<ApiResponse<{ message: string }>> => {
  const response = await apiClient.post<ApiResponse<{ message: string }>>('/api/settings/openai-oauth/disconnect');
  return response.data;
};

/**
 * OpenAI OAuth: get connection status
 */
export const getOpenAIOAuthStatus = async (): Promise<ApiResponse<{ connected: boolean; account_id: string | null }>> => {
  const response = await apiClient.get<ApiResponse<{ connected: boolean; account_id: string | null }>>('/api/settings/openai-oauth/status');
  return response.data;
};

/**
 * OpenAI OAuth: list available models
 */
export const getOpenAIOAuthModels = async (): Promise<ApiResponse<{ models: string[] }>> => {
  const response = await apiClient.get<ApiResponse<{ models: string[] }>>('/api/settings/openai-oauth/models');
  return response.data;
};

/**
 * API OAuth API URL (API 1455 API) 
 */
export const submitOAuthManualCallback = async (callbackUrl: string): Promise<ApiResponse<{ message: string; account_id: string | null }>> => {
  const response = await apiClient.post<ApiResponse<{ message: string; account_id: string | null }>>('/api/settings/openai-oauth/manual-callback', { callback_url: callbackUrl });
  return response.data;
};

/**
 * API API key API
 */
export const verifyApiKey = async (): Promise<ApiResponse<{ available: boolean; message: string }>> => {
  const response = await apiClient.post<ApiResponse<{ available: boolean; message: string }>>('/api/settings/verify');
  return response.data;
};

/**
 * API
 */
export interface TestSettingsOverride {
  api_key?: string;
  api_base_url?: string;
  text_model?: string;
  image_model?: string;
  image_caption_model?: string;
  image_caption_model_source?: string;
  mineru_api_base?: string;
  mineru_token?: string;
  baidu_api_key?: string;
  ai_provider_format?: string;
  image_resolution?: string;
  image_quality?: string;
  enable_text_reasoning?: boolean;
  text_thinking_budget?: number;
  enable_image_reasoning?: boolean;
  image_thinking_budget?: number;
}

/**
 * API OCR API (API) 
 * @param settings API (API) 
 * @returns APIID, API getTestStatus API
 */
export const testBaiduOcr = async (settings?: TestSettingsOverride): Promise<ApiResponse<{ task_id: string; status: string }>> => {
  const response = await apiClient.post<ApiResponse<{ task_id: string; status: string }>>('/api/settings/tests/baidu-ocr', settings || {});
  return response.data;
};

/**
 * API (API) 
 * @param settings API (API) 
 * @returns APIID, API getTestStatus API
 */
export const testTextModel = async (settings?: TestSettingsOverride): Promise<ApiResponse<{ task_id: string; status: string }>> => {
  const response = await apiClient.post<ApiResponse<{ task_id: string; status: string }>>('/api/settings/tests/text-model', settings || {});
  return response.data;
};

/**
 * API (API) 
 * @param settings API (API) 
 * @returns APIID, API getTestStatus API
 */
export const testCaptionModel = async (settings?: TestSettingsOverride): Promise<ApiResponse<{ task_id: string; status: string }>> => {
  const response = await apiClient.post<ApiResponse<{ task_id: string; status: string }>>('/api/settings/tests/caption-model', settings || {});
  return response.data;
};

/**
 * API (API) 
 * @param settings API (API) 
 * @returns APIID, API getTestStatus API
 */
export const testBaiduInpaint = async (settings?: TestSettingsOverride): Promise<ApiResponse<{ task_id: string; status: string }>> => {
  const response = await apiClient.post<ApiResponse<{ task_id: string; status: string }>>('/api/settings/tests/baidu-inpaint', settings || {});
  return response.data;
};

/**
 * API (API) 
 * @param settings API (API) 
 * @returns APIID, API getTestStatus API
 */
export const testImageModel = async (settings?: TestSettingsOverride): Promise<ApiResponse<{ task_id: string; status: string }>> => {
  const response = await apiClient.post<ApiResponse<{ task_id: string; status: string }>>('/api/settings/tests/image-model', settings || {});
  return response.data;
};

/**
 * API MinerU PDF API (API) 
 * @param settings API (API) 
 * @returns APIID, API getTestStatus API
 */
export const testMineruPdf = async (settings?: TestSettingsOverride): Promise<ApiResponse<{ task_id: string; status: string }>> => {
  const response = await apiClient.post<ApiResponse<{ task_id: string; status: string }>>('/api/settings/tests/mineru-pdf', settings || {});
  return response.data;
};

/**
 * API
 * @param taskId APIID
 * @returns API
 */
export const getTestStatus = async (taskId: string): Promise<ApiResponse<{
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  result?: any;
  error?: string;
  message?: string;
  openai_oauth_disconnected?: boolean;
}>> => {
  const response = await apiClient.get<ApiResponse<any>>(`/api/settings/tests/${taskId}/status`);
  return response.data;
};

export interface UpdateCheckInfo {
  status: 'up_to_date' | 'update_available' | 'unknown';
  update_available: boolean;
  message: string;
  repository: string;
  current: {
    tag?: string;
    commit_sha?: string;
    short_sha?: string;
    is_docker: boolean;
  };
  latest: null | {
    tag: string;
    sha?: string;
    last_updated: string;
    image: string;
  };
}

export const checkForUpdates = async (): Promise<ApiResponse<UpdateCheckInfo>> => {
  const response = await apiClient.get<ApiResponse<UpdateCheckInfo>>('/api/settings/check-update');
  return response.data;
};


// API client endpoint

/**
 * API PPT API
 * API PDF/PPTX API, API+API
 */
export const createPptRenovationProject = async (
  file: File,
  options?: {
    keepLayout?: boolean;
    templateStyle?: string;
    language?: string;
  }
): Promise<ApiResponse<{ project_id: string; task_id: string; page_count: number }>> => {
  const formData = new FormData();
  formData.append('file', file);
  if (options?.keepLayout) {
    formData.append('keep_layout', 'true');
  }
  if (options?.templateStyle) {
    formData.append('template_style', options.templateStyle);
  }
  if (options?.language) {
    formData.append('language', options.language);
  }

  const response = await apiClient.post<ApiResponse<{ project_id: string; task_id: string; page_count: number }>>(
    '/api/projects/renovation',
    formData
  );
  return response.data;
};

/**
 * API (API, API) 
 */
export const extractStyleFromImage = async (
  imageFile: File
): Promise<ApiResponse<{ style_description: string }>> => {
  const formData = new FormData();
  formData.append('image', imageFile);

  const response = await apiClient.post<ApiResponse<{ style_description: string }>>(
    '/api/extract-style',
    formData
  );
  return response.data;
};

/**
 * API (API, API) 
 */
export const generateStyleFromContent = async (
  content: string,
  language: string = 'zh'
): Promise<ApiResponse<{ style_description: string }>> => {
  const response = await apiClient.post<ApiResponse<{ style_description: string }>>(
    '/api/generate-style-from-content',
    { content, language }
  );
  return response.data;
};

// API client endpoint

/**
 * API
 */
export const listTemplateAssets = async (
  projectId: string
): Promise<ApiResponse<{ assets: TemplateAsset[] }>> => {
  const response = await apiClient.get<ApiResponse<{ assets: TemplateAsset[] }>>(
    `/api/projects/${projectId}/template-assets`
  );
  return response.data;
};

/**
 * API (API) 
 * @param opts.bindToPageId API (PRD §10.3) 
 */
export const uploadTemplateAsset = async (
  projectId: string,
  image: File,
  opts?: { userLabel?: string; bindToPageId?: string }
): Promise<ApiResponse<{ asset: TemplateAsset; analyze_task_id: string }>> => {
  const formData = new FormData();
  formData.append('image', image);
  if (opts?.userLabel) formData.append('user_label', opts.userLabel);
  const query = opts?.bindToPageId
    ? `?bind_to_page=${encodeURIComponent(opts.bindToPageId)}`
    : '';
  const response = await apiClient.post<
    ApiResponse<{ asset: TemplateAsset; analyze_task_id: string }>
  >(`/api/projects/${projectId}/template-assets${query}`, formData);
  return response.data;
};

/**
 * API PDF API (API, API task_id API) 
 */
export const uploadTemplatePdf = async (
  projectId: string,
  pdf: File
): Promise<ApiResponse<{ task_id: string }>> => {
  const formData = new FormData();
  formData.append('pdf', pdf);
  const response = await apiClient.post<ApiResponse<{ task_id: string }>>(
    `/api/projects/${projectId}/template-assets/upload-pdf`,
    formData
  );
  return response.data;
};

/**
 * API (API / API) 
 */
export const updateTemplateAsset = async (
  projectId: string,
  assetId: string,
  patch: {
    user_label?: string | null;
    analysis_json?: TemplateAsset['analysis_json'];
    analysis_notes?: string | null;
    sort_order?: number;
  }
): Promise<ApiResponse<{ asset: TemplateAsset }>> => {
  const response = await apiClient.patch<ApiResponse<{ asset: TemplateAsset }>>(
    `/api/projects/${projectId}/template-assets/${assetId}`,
    patch
  );
  return response.data;
};

/**
 * API (API) 
 */
export const deleteTemplateAsset = async (
  projectId: string,
  assetId: string
): Promise<ApiResponse<{ deleted: boolean; cleared_page_ids: string[] }>> => {
  const response = await apiClient.delete<
    ApiResponse<{ deleted: boolean; cleared_page_ids: string[] }>
  >(`/api/projects/${projectId}/template-assets/${assetId}`);
  return response.data;
};

/**
 * API
 */
export const reanalyzeTemplateAsset = async (
  projectId: string,
  assetId: string
): Promise<ApiResponse<{ analyze_task_id: string }>> => {
  const response = await apiClient.post<ApiResponse<{ analyze_task_id: string }>>(
    `/api/projects/${projectId}/template-assets/${assetId}/reanalyze`
  );
  return response.data;
};

/**
 * API (asset / API / API) 
 */
export const updatePageTemplate = async (
  projectId: string,
  pageId: string,
  patch: {
    template_asset_id?: string | null;
    template_style_text?: string | null;
    selection_source?: 'manual' | 'auto' | 'batch_apply';
  }
): Promise<ApiResponse<{ page: Page }>> => {
  const response = await apiClient.patch<ApiResponse<{ page: Page }>>(
    `/api/projects/${projectId}/pages/${pageId}/template`,
    patch
  );
  return response.data;
};

/**
 * API (JSON API, API 7) 
 * API→API: { mode: 'multi' }
 * API→API: { mode: 'single', unified_asset_id? , unified_style_text? }
 */
export const switchTemplateMode = async (
  projectId: string,
  payload:
    | { mode: 'multi' }
    | { mode: 'single'; unified_asset_id?: string | null; unified_style_text?: string | null }
): Promise<ApiResponse<{ project: Project }>> => {
  const response = await apiClient.patch<ApiResponse<{ project: Project }>>(
    `/api/projects/${projectId}/template-mode`,
    payload
  );
  return response.data;
};

/**
 * API→API + API (multipart API) 
 */
export const switchTemplateModeSingleWithUpload = async (
  projectId: string,
  image: File,
  unifiedStyleText?: string
): Promise<ApiResponse<{ asset: TemplateAsset; project: Project; analyze_task_id: string }>> => {
  const formData = new FormData();
  formData.append('image', image);
  if (unifiedStyleText) formData.append('unified_style_text', unifiedStyleText);
  const response = await apiClient.post<
    ApiResponse<{ asset: TemplateAsset; project: Project; analyze_task_id: string }>
  >(`/api/projects/${projectId}/template-mode/single-with-upload`, formData);
  return response.data;
};

/**
 * API (API 5) 
 */
export const autoMatchAllTemplates = async (
  projectId: string,
  opts?: { overwrite_existing?: boolean; preserve_non_empty?: boolean }
): Promise<ApiResponse<{ task_id: string }>> => {
  const response = await apiClient.post<ApiResponse<{ task_id: string }>>(
    `/api/projects/${projectId}/template-assets/auto-match`,
    {
      overwrite_existing: opts?.overwrite_existing ?? true,
      preserve_non_empty: opts?.preserve_non_empty ?? false,
    }
  );
  return response.data;
};

/**
 * API (PRD §9) 
 */
export const autoMatchPageTemplate = async (
  projectId: string,
  pageId: string
): Promise<ApiResponse<{ task_id: string }>> => {
  const response = await apiClient.post<ApiResponse<{ task_id: string }>>(
    `/api/projects/${projectId}/pages/${pageId}/template/auto-match`
  );
  return response.data;
};