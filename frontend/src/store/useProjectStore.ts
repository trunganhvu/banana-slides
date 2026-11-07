import { create } from 'zustand';
import type { Project, TemplateAsset, Task } from '@/types';
import * as api from '@/api/endpoints';
import {
  debounce,
  normalizeProject,
  normalizeErrorMessage,
} from '@/utils';
import { devLog } from '@/utils/logger';
import { triggerDownload } from '@/api/client';
import { getT } from '@/utils/i18nHelper';

const storeI18n = {
  zh: {
    store: {
      createFailed: 'Tạo dự án thất bại',
      createNoId: 'Tạo dự án thất bại: Máy chủ không trả về ID dự án',
      syncFailed: 'Đồng bộ dự án thất bại',
      projectNotFound: 'Dự án không tồn tại, có thể đã bị xóa',
      requestFailed: 'Yêu cầu thất bại',
      requestFailedStatus: 'Yêu cầu thất bại: {{status}}',
      networkError: 'Lỗi kết nối mạng, vui lòng kiểm tra xem dịch vụ backend đã chạy chưa',
      updateOrderFailed: 'Cập nhật thứ tự thất bại',
      newPage: 'Trang mới',
      addPageFailed: 'Thêm trang thất bại',
      deletePageFailed: 'Xóa trang thất bại',
      taskStartFailed: 'Khởi động tác vụ thất bại',
      taskFailed: 'Tác vụ thất bại',
      unknownTaskStatus: 'Trạng thái tác vụ không xác định: {{status}}',
      taskQueryFailed: 'Truy vấn tác vụ thất bại',
      generateOutlineFailed: 'Tạo dàn ý thất bại',
      generateFromDescFailed: 'Tạo từ mô tả thất bại',
      projectIdMissing: 'ID dự án không tồn tại',
      noTaskId: 'Không nhận được ID tác vụ',
      generateDescFailed: 'Tạo mô tả thất bại',
      generateDescTimeout: 'Tạo mô tả thất bại: Hết thời gian chờ',
      startGenerationFailed: 'Khởi động tác vụ tạo thất bại',
      regenerateFailed: 'Tạo lại thất bại',
      batchGenerateFailed: 'Tạo hàng loạt thất bại',
      editImageFailed: 'Chỉnh sửa ảnh thất bại',
      exportLinkFailed: 'Lấy liên kết xuất thất bại',
      exportFailed: 'Xuất thất bại',
      exportEditableFailed: 'Xuất PPTX có thể chỉnh sửa thất bại',
    }
  },
  en: {
    store: {
      createFailed: 'Failed to create project',
      createNoId: 'Project creation failed: no project ID returned',
      syncFailed: 'Failed to sync project',
      projectNotFound: 'Project not found, it may have been deleted',
      requestFailed: 'Request failed',
      requestFailedStatus: 'Request failed: {{status}}',
      networkError: 'Network error, please check if the backend service is running',
      updateOrderFailed: 'Failed to update page order',
      newPage: 'New Page',
      addPageFailed: 'Failed to add page',
      deletePageFailed: 'Failed to delete page',
      taskStartFailed: 'Failed to start task',
      taskFailed: 'Task failed',
      unknownTaskStatus: 'Unknown task status: {{status}}',
      taskQueryFailed: 'Failed to query task',
      generateOutlineFailed: 'Failed to generate outline',
      generateFromDescFailed: 'Failed to generate from description',
      projectIdMissing: 'Project ID not found',
      noTaskId: 'No task ID received',
      generateDescFailed: 'Failed to generate description',
      generateDescTimeout: 'Failed to generate description: polling timeout',
      startGenerationFailed: 'Failed to start generation task',
      regenerateFailed: 'Failed to regenerate',
      batchGenerateFailed: 'Batch generation failed',
      editImageFailed: 'Failed to edit image',
      exportLinkFailed: 'Failed to get export link',
      exportFailed: 'Export failed',
      exportEditableFailed: 'Failed to export editable PPTX',
    }
  }
};
const t = getT(storeI18n);

// Project store logic
// Project store logic
(function cleanupLegacyTemplateLocalStorageKeys() {
  if (typeof window === 'undefined' || !window.localStorage) return;
  const legacyPrefixes = ['template_mode_', 'template_assets_', 'page_template_assign_'];
  try {
    const toRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && legacyPrefixes.some((prefix) => key.startsWith(prefix))) {
        toRemove.push(key);
      }
    }
    toRemove.forEach((key) => localStorage.removeItem(key));

    // Also migrate any legacy Chinese extra fields in localStorage
    const rawFields = localStorage.getItem('banana-available-extra-fields');
    if (rawFields) {
      const arr = JSON.parse(rawFields);
      if (Array.isArray(arr)) {
        const fieldMap: Record<string, string> = {
          '\u914d\u56fe\u4e0e\u7d20\u6750': 'Hình ảnh & Tư liệu',
          '\u7248\u5f0f\u4e0e\u91cd\u70b9': 'Bố cục & Trọng tâm',
          '\u6f14\u8bb2\u8005\u5907\u6ce8': 'Ghi chú thuyết trình',
          '\u89c6\u89c9\u5143\u7d20': 'Yếu tố thị giác',
          '\u89c6\u89c9\u7126\u70b9': 'Điểm nhấn thị giác',
          '\u6392\u7248\u5e03\u5c40': 'Bố cục trình bày',
          '\u6392\u7248\u5efa\u8bae': 'Gợi ý bố cục',
        };
        const updated = [...new Set(arr.map((item: string) => fieldMap[item] || item))];
        localStorage.setItem('banana-available-extra-fields', JSON.stringify(updated));
      }
    }
  } catch {
    // Project store logic
  }
})();

interface ProjectState {
  // Project store logic
  currentProject: Project | null;
  isGlobalLoading: boolean;
  // Project store logic
  isSavingPages: boolean;
  activeTaskId: string | null;
  taskProgress: { total: number; completed: number } | null;
  error: string | null;
  // Project store logic
  pageGeneratingTasks: Record<string, string>;
  // Project store logic
  warningMessage: string | null;
  // Project store logic
  isOutlineStreaming: boolean;
  // Project store logic
  outlineStreamingProjectIds: string[];
  // Project store logic
  isDescriptionStreaming: boolean;
  // Project store logic
  templateAssets: TemplateAsset[];

  // Actions
  setCurrentProject: (project: Project | null) => void;
  setGlobalLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Project store logic
  initializeProject: (type: 'idea' | 'outline' | 'description' | 'blank', content: string, templateImage?: File, templateStyle?: string, referenceFileIds?: string[], aspectRatio?: string) => Promise<void>;
  syncProject: (projectId?: string) => Promise<void>;
  
  // Project store logic
  updatePageLocal: (pageId: string, data: any) => void;
  saveAllPages: () => Promise<void>;
  reorderPages: (newOrder: string[]) => Promise<void>;
  addNewPage: () => Promise<void>;
  deletePageById: (pageId: string) => Promise<void>;
  
  // Project store logic
  startAsyncTask: (apiCall: () => Promise<any>) => Promise<void>;
  pollTask: (taskId: string) => Promise<void>;
  pollImageTask: (taskId: string, pageIds: string[]) => void;

  // Project store logic
  generateOutline: () => Promise<void>;
  generateOutlineStream: (lockPageCount?: boolean) => Promise<{ complete: boolean; active: boolean } | undefined>;
  generateFromDescription: () => Promise<void>;
  generateDescriptions: (detailLevel?: string) => Promise<void>;
  generatePageDescription: (pageId: string, detailLevel?: string) => Promise<void>;
  regenerateRenovationPage: (pageId: string, keepLayout?: boolean) => Promise<void>;
  generatePageImage: (pageId: string, forceRegenerate?: boolean) => Promise<void>;
  generateImages: (pageIds?: string[]) => Promise<void>;
  editPageImage: (
    pageId: string,
    editPrompt: string,
    contextImages?: {
      useTemplate?: boolean;
      descImageUrls?: string[];
      uploadedFiles?: File[];
    }
  ) => Promise<void>;
  
  // Project store logic
  exportPPTX: (pageIds?: string[]) => Promise<void>;
  exportPDF: (pageIds?: string[]) => Promise<void>;
  exportEditablePPTX: (filename?: string, pageIds?: string[]) => Promise<void>;

  // Project store logic
  loadTemplateAssets: (projectId: string) => Promise<TemplateAsset[]>;
  uploadTemplateAsset: (projectId: string, file: File, opts?: { userLabel?: string; bindToPageId?: string }) => Promise<TemplateAsset>;
  uploadTemplatePdf: (projectId: string, file: File) => Promise<string>;
  updateTemplateAsset: (projectId: string, assetId: string, patch: { user_label?: string | null; analysis_json?: TemplateAsset['analysis_json']; analysis_notes?: string | null; sort_order?: number }) => Promise<TemplateAsset>;
  deleteTemplateAsset: (projectId: string, assetId: string) => Promise<string[]>;
  reanalyzeTemplateAsset: (projectId: string, assetId: string) => Promise<string>;
  updatePageTemplate: (projectId: string, pageId: string, patch: { template_asset_id?: string | null; template_style_text?: string | null; selection_source?: 'manual' | 'auto' | 'batch_apply' }) => Promise<void>;
  switchTemplateMode: (projectId: string, payload: { mode: 'multi' } | { mode: 'single'; unified_asset_id?: string | null; unified_style_text?: string | null }) => Promise<void>;
  switchTemplateModeWithUpload: (projectId: string, file: File, unifiedStyleText?: string) => Promise<void>;
  autoMatchAll: (projectId: string, opts?: { overwrite_existing?: boolean; preserve_non_empty?: boolean }) => Promise<string>;
  autoMatchPage: (projectId: string, pageId: string) => Promise<string>;
  pollTemplateTask: (taskId: string, projectId: string, onProgress?: (task: Task) => void) => Promise<Task>;
}

export const useProjectStore = create<ProjectState>((set, get) => {
  // Project store logic
  const savePageFields = async (projectId: string, pageId: string, data: any) => {
    const promises: Promise<any>[] = [];

    // Project store logic
    if (data.description_content) {
      promises.push(api.updatePageDescription(projectId, pageId, data.description_content));
    }

    // Project store logic
    if (data.outline_content) {
      promises.push(api.updatePageOutline(projectId, pageId, data.outline_content));
    }

    // Project store logic
    // Project store logic
    if ('narration_text' in data) {
      promises.push(api.updatePageNarration(projectId, pageId, data.narration_text ?? ''));
    }

    // Project store logic
    if ('part' in data) {
      promises.push(api.updatePage(projectId, pageId, { part: data.part }));
    }

    // Project store logic
    if (promises.length === 0) {
      await api.updatePage(projectId, pageId, data);
    } else {
      // Project store logic
      await Promise.all(promises);
    }
  };

  // Project store logic
  // Project store logic
  // Project store logic
  const pendingPageUpdates = new Map<string, { projectId: string; data: any }>();

  const flushPageUpdates = async () => {
    const entries = Array.from(pendingPageUpdates.entries());
    pendingPageUpdates.clear();
    if (entries.length === 0) return;

    try {
      await Promise.all(
        entries.map(([pageId, { projectId, data }]) => savePageFields(projectId, pageId, data))
      );

      // Project store logic
      // Project store logic
      // Project store logic
      // Project store logic
      // Project store logic
      const { syncProject, pageGeneratingTasks, currentProject } = get();
      const touchedCurrentProject =
        !!currentProject && entries.some(([, update]) => update.projectId === currentProject.id);
      if (touchedCurrentProject && Object.keys(pageGeneratingTasks).length === 0) {
        await syncProject(currentProject!.id);
      }
    } catch (error: any) {
      console.error('Lưu trang thất bại:', error);
      // Project store logic
      // Project store logic
    } finally {
      // Project store logic
      if (pendingPageUpdates.size === 0) set({ isSavingPages: false });
    }
  };

  const debouncedFlushPageUpdates = debounce(flushPageUpdates, 1000);

  const debouncedUpdatePage = (projectId: string, pageId: string, data: any) => {
    const existing = pendingPageUpdates.get(pageId);
    pendingPageUpdates.set(pageId, {
      projectId,
      data: { ...(existing?.data ?? {}), ...data },
    });
    // Project store logic
    if (!get().isSavingPages) set({ isSavingPages: true });
    debouncedFlushPageUpdates();
  };

  return {
  // Project store logic
  currentProject: null,
  isGlobalLoading: false,
  isSavingPages: false,
  activeTaskId: null,
  taskProgress: null,
  error: null,
  pageGeneratingTasks: {},
  warningMessage: null,
  isOutlineStreaming: false,
  outlineStreamingProjectIds: [],
  isDescriptionStreaming: false,
  templateAssets: [],

  // Setters
  setCurrentProject: (project) => set({ currentProject: project }),
  setGlobalLoading: (loading) => set({ isGlobalLoading: loading }),
  setError: (error) => set({ error }),

  // Project store logic
  initializeProject: async (type, content, templateImage, templateStyle, referenceFileIds, aspectRatio) => {
    set({ isGlobalLoading: true, error: null });
    try {
      const request: any = {};
      const normalizedContent = typeof content === 'string' ? content.trim() : '';

      if (type === 'blank') {
        // Project store logic
        request.creation_type = 'blank';
      } else if (type === 'idea') {
        request.idea_prompt = normalizedContent;
      } else if (type === 'outline') {
        request.outline_text = normalizedContent;
      } else if (type === 'description') {
        request.description_text = normalizedContent;
      }

      // Project store logic
      if (templateStyle && templateStyle.trim()) {
        request.template_style = templateStyle.trim();
      }

      // Project store logic
      if (aspectRatio) {
        request.image_aspect_ratio = aspectRatio;
      }

      // Project store logic
      const response = await api.createProject(request);
      const projectId = response.data?.project_id;

      if (!projectId) {
        throw new Error(t('store.createNoId'));
      }

      // Project store logic
      if (referenceFileIds && referenceFileIds.length > 0) {
        try {
          await Promise.all(
            referenceFileIds.map(fileId => api.associateFileToProject(fileId, projectId))
          );
          devLog(`[Khởi tạo dự án] Đã liên kết ${referenceFileIds.length} tệp tham khảo`);
        } catch (error) {
          console.warn('[Khởi tạo dự án] Liên kết tệp tham khảo thất bại:', error);
        }
      }

      // Project store logic
      if (templateImage) {
        try {
          await api.uploadTemplate(projectId, templateImage);
        } catch (error) {
          console.warn('Tải lên mẫu thất bại:', error);
          // Project store logic
        }
      }

      // Project store logic
      const projectResponse = await api.getProject(projectId);
      const project = normalizeProject(projectResponse.data);

      if (project) {
        set({ currentProject: project });
        // Project store logic
        localStorage.setItem('currentProjectId', project.id!);
      }
    } catch (error: any) {
      set({ error: normalizeErrorMessage(error.message || t('store.createFailed')) });
      throw error;
    } finally {
      set({ isGlobalLoading: false });
    }
  },

  // Project store logic
  syncProject: async (projectId?: string) => {
    const { currentProject } = get();

    // Project store logic
    let targetProjectId = projectId;
    if (!targetProjectId) {
      if (currentProject?.id) {
        targetProjectId = currentProject.id;
      } else {
        targetProjectId = localStorage.getItem('currentProjectId') || undefined;
      }
    }

    if (!targetProjectId) {
      console.warn('syncProject: Không có ID dự án khả dụng');
      return;
    }

    try {
      const response = await api.getProject(targetProjectId);
      if (response.data) {
        const project = normalizeProject(response.data);
        devLog('[syncProject] Đồng bộ dữ liệu dự án:', {
          projectId: project.id,
          pagesCount: project.pages?.length || 0,
          status: project.status
        });
        set({ currentProject: project });
        // Project store logic
        localStorage.setItem('currentProjectId', project.id!);
      }
    } catch (error: any) {
      // Project store logic
      let errorMessage = t('store.syncFailed');
      let shouldClearStorage = false;
      
      if (error.response) {
        // Project store logic
        const errorData = error.response.data;
        if (error.response.status === 404) {
          // Project store logic
          errorMessage = errorData?.error?.message || t('store.projectNotFound');
          shouldClearStorage = true;
        } else if (errorData?.error?.message) {
          // Project store logic
          errorMessage = errorData.error.message;
        } else if (errorData?.message) {
          errorMessage = errorData.message;
        } else if (errorData?.error) {
          errorMessage = typeof errorData.error === 'string' ? errorData.error : errorData.error.message || t('store.requestFailed');
        } else {
          errorMessage = t('store.requestFailedStatus', { status: error.response.status });
        }
      } else if (error.request) {
        // Project store logic
        errorMessage = t('store.networkError');
      } else if (error.message) {
        // Project store logic
        errorMessage = error.message;
      }
      
      // Project store logic
      // Project store logic
      if (shouldClearStorage) {
        console.warn('[syncProject] Dự án không tồn tại, xóa localStorage');
        localStorage.removeItem('currentProjectId');
        set({ currentProject: null });
      } else {
        set({ error: normalizeErrorMessage(errorMessage) });
      }
    }
  },

  // Project store logic
  updatePageLocal: (pageId, data) => {
    const { currentProject } = get();
    if (!currentProject) return;

    const updatedPages = currentProject.pages.map((page) =>
      page.id === pageId ? { ...page, ...data } : page
    );

    set({
      currentProject: {
        ...currentProject,
        pages: updatedPages,
      },
    });

    // Project store logic
    debouncedUpdatePage(currentProject.id, pageId, data);
  },

  // Project store logic
  // Project store logic
  saveAllPages: async () => {
    const { currentProject } = get();
    if (!currentProject) return;

    // Project store logic
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Project store logic
    await get().syncProject(currentProject.id);
  },

  // Project store logic
  reorderPages: async (newOrder) => {
    const { currentProject } = get();
    if (!currentProject) return;

    // Project store logic
    const reorderedPages = newOrder
      .map((id) => currentProject.pages.find((p) => p.id === id))
      .filter(Boolean) as any[];

    set({
      currentProject: {
        ...currentProject,
        pages: reorderedPages,
      },
    });

    try {
      await api.updatePagesOrder(currentProject.id, newOrder);
    } catch (error: any) {
      set({ error: error.message || t('store.updateOrderFailed') });
      // Project store logic
      await get().syncProject();
    }
  },

  // Project store logic
  addNewPage: async () => {
    const { currentProject } = get();
    if (!currentProject) return;

    try {
      const newPage = {
        outline_content: { title: t('store.newPage'), points: [] },
        order_index: currentProject.pages.length,
      };

      const response = await api.addPage(currentProject.id, newPage);
      if (response.data) {
        await get().syncProject();
      }
    } catch (error: any) {
      set({ error: error.message || t('store.addPageFailed') });
    }
  },

  // Project store logic
  deletePageById: async (pageId) => {
    const { currentProject } = get();
    if (!currentProject) return;

    try {
      await api.deletePage(currentProject.id, pageId);
      await get().syncProject();
    } catch (error: any) {
      set({ error: error.message || t('store.deletePageFailed') });
    }
  },

  // Project store logic
  startAsyncTask: async (apiCall) => {
    devLog('[Tác vụ bất đồng bộ] Bắt đầu tác vụ...');
    set({ isGlobalLoading: true, error: null });
    try {
      const response = await apiCall();
      devLog('[Tác vụ bất đồng bộ] Phản hồi API:', response);
      
      // Project store logic
      const taskId = response.data?.task_id;
      if (taskId) {
        devLog('[Tác vụ bất đồng bộ] Nhận được task_id:', taskId, 'bắt đầu truy vấn...');
        set({ activeTaskId: taskId });
        await get().pollTask(taskId);
      } else {
        console.warn('[Tác vụ bất đồng bộ] Phản hồi không có task_id:', response);
        // Project store logic
        await get().syncProject();
        set({ isGlobalLoading: false });
      }
    } catch (error: any) {
      console.error('[Tác vụ bất đồng bộ] Khởi động thất bại:', error);
      set({ error: error.message || t('store.taskStartFailed'), isGlobalLoading: false });
      throw error;
    }
  },

  // Project store logic
  pollTask: async (taskId) => {
    devLog(`[Truy vấn] Bắt đầu truy vấn tác vụ: ${taskId}`);
    const { currentProject } = get();
    if (!currentProject) {
      console.warn('[Truy vấn] Không có dự án hiện tại, dừng truy vấn');
      return;
    }
    const projectId = currentProject.id!;

    const poll = async () => {
      try {
        devLog(`[Truy vấn] Kiểm tra trạng thái tác vụ: ${taskId}`);
        const response = await api.getTaskStatus(projectId, taskId);
        const task = response.data;
        
        if (!task) {
      console.warn('[Polling] Không có dự án hiện tại, dừng polling');
          return;
        }

        // Project store logic
        if (task.progress) {
          set({ taskProgress: task.progress });
        }

        devLog(`[Polling] Task ${taskId} trạng thái: ${task.status}`, task);

        // Project store logic
        if (task.status === 'COMPLETED') {
          devLog(`[Polling] Task ${taskId} đã hoàn tất, Làm mới dữ liệu dự án`);
          
          // Project store logic
          if (task.task_type === 'EXPORT_EDITABLE_PPTX' && task.progress) {
            const progress = typeof task.progress === 'string' 
              ? JSON.parse(task.progress) 
              : task.progress;
            
            const downloadUrl = progress?.download_url;
            if (downloadUrl) {
              devLog('[Xuất tệp có thể chỉnh sửaPPTX] Lấy liên kết tải xuống từ phản hồi tác vụ:', downloadUrl);
              // Project store logic
              setTimeout(() => {
                triggerDownload(downloadUrl);
              }, 500);
            } else {
              console.warn('[Xuất tệp có thể chỉnh sửaPPTX] Tác vụ hoàn tất nhưng không có liên kết tải xuống');
            }
          }
          
          set({ 
            activeTaskId: null, 
            taskProgress: null, 
            isGlobalLoading: false 
          });
          // Project store logic
          await get().syncProject();
        } else if (task.status === 'FAILED') {
          console.error(`[Polling] Task ${taskId} thất bại:`, task.error_message || task.error);
          set({ 
            error: normalizeErrorMessage(task.error_message || task.error || t('store.taskFailed')),
            activeTaskId: null,
            taskProgress: null,
            isGlobalLoading: false
          });
        } else if (task.status === 'PENDING' || task.status === 'PROCESSING') {
          // Project store logic
          devLog(`[Polling] Task ${taskId} Đang xử lý, 2giây sau sẽ tiếp tục polling...`);
          setTimeout(poll, 2000);
        } else {
          // Project store logic
          console.warn(`[Polling] Task ${taskId} Trạng thái không xác định: ${task.status}, dừng polling`);
          set({ 
            error: `${t('store.unknownTaskStatus', { status: task.status })}`,
            activeTaskId: null,
            taskProgress: null,
            isGlobalLoading: false
          });
        }
      } catch (error: any) {
      console.error('Lưu trang thất bại:', error);
        set({ 
          error: normalizeErrorMessage(error.message || t('store.taskQueryFailed')),
          activeTaskId: null,
          isGlobalLoading: false
        });
      }
    };

    await poll();
  },

  // Project store logic
  generateOutline: async () => {
    const { currentProject } = get();
    if (!currentProject) return;

    set({ isGlobalLoading: true, error: null });
    try {
      const response = await api.generateOutline(currentProject.id!);
      devLog('[Tác vụ bất đồng bộ] APIphản hồi:', response);
      
      // Project store logic
      await get().syncProject();
      
      // Project store logic
      const { currentProject: updatedProject } = get();
      devLog('[Tạo dàn ý] Dự án sau khi làm mới:', updatedProject?.pages.length, 'trang');
    } catch (error: any) {
      console.error('[] :', error);
      const message =
        error.response?.data?.error?.message ||
        error.response?.data?.message ||
        error.message ||
        t('store.generateOutlineFailed');
      set({ error: normalizeErrorMessage(message) });
      throw error;
    } finally {
      set({ isGlobalLoading: false });
    }
  },

  // Project store logic
  generateOutlineStream: async (lockPageCount?: boolean) => {
    const { currentProject } = get();
    const projectId = currentProject?.id;
    if (!currentProject || !projectId) return;

    if (get().outlineStreamingProjectIds.includes(projectId)) return;

    const finishStream = () => {
      set((state) => {
        const outlineStreamingProjectIds = state.outlineStreamingProjectIds.filter((id) => id !== projectId);
        return {
          outlineStreamingProjectIds,
          isOutlineStreaming: outlineStreamingProjectIds.length > 0,
        };
      });
    };
    const isViewingTargetProject = () => get().currentProject?.id === projectId;

    set((state) => ({
      outlineStreamingProjectIds: [...state.outlineStreamingProjectIds, projectId],
      isOutlineStreaming: true,
      error: null,
    }));

    // Clear existing pages for fresh streaming display
    set((state) => ({
      currentProject: state.currentProject?.id === projectId
        ? { ...state.currentProject, pages: [] }
        : state.currentProject,
    }));

    // Concurrent queue: pages are pushed by SSE callbacks, drained by a timer loop
    const pageQueue: any[] = [];
    let streamDone = false;
    let doneData: { total: number; pages: any[]; complete?: boolean } | null = null;
    const STAGGER_MS = 150;

    // Start the render loop — runs concurrently with the SSE stream
    const renderPromise = new Promise<void>((resolve) => {
      const tick = () => {
        if (pageQueue.length > 0) {
          const page = pageQueue.shift()!;
          const { currentProject: proj } = get();
          if (proj?.id === projectId) {
            const tempPage: any = {
              id: `streaming-${page.index}`,
              order_index: page.index,
              outline_content: { title: page.title, points: page.points },
              description_content: page.description_text
                ? { text: page.description_text, ...(page.extra_fields ? { extra_fields: page.extra_fields } : {}) }
                : undefined,
              part: page.part,
              status: page.description_text ? 'DESCRIPTION_GENERATED' : 'DRAFT',
            };
            set({
              currentProject: { ...proj, pages: [...proj.pages, tempPage] },
            });
          }
          setTimeout(tick, STAGGER_MS);
        } else if (streamDone) {
          resolve();
        } else {
          // Queue empty but stream still going — poll quickly
          setTimeout(tick, 30);
        }
      };
      tick();
    });

    try {
      await api.generateOutlineStream(projectId, {
        onPage: (page) => { pageQueue.push(page); },
        onDone: (data) => { doneData = data; },
        onError: (message) => {
          console.error('[Dàn ý luồng] Lỗi:', message);
          if (isViewingTargetProject()) {
            set({ error: normalizeErrorMessage(message) });
          }
          streamDone = true;
        },
      }, undefined /* language */, lockPageCount);

      streamDone = true;
      await renderPromise;

      // Replace temp pages with real persisted pages
      if (doneData) {
        const { currentProject: proj } = get();
        if (proj?.id === projectId) {
          const normalized = normalizeProject({ ...proj, pages: doneData.pages });
          set({ currentProject: normalized });
        }
        devLog('[Dàn ý luồng] Hoàn tất:', doneData.total, 'trang');
        return { complete: doneData.complete ?? false, active: isViewingTargetProject() };
      } else {
        return { complete: false, active: isViewingTargetProject() };
      }
    } catch (error: any) {
      console.error('[] :', error);
      streamDone = true;
      if (!isViewingTargetProject()) {
        // Project store logic
        return { complete: false, active: false };
      }
      set({ error: normalizeErrorMessage(error.message || t('store.generateOutlineFailed')) });
      throw error;
    } finally {
      finishStream();
    }
  },

  // Project store logic
  generateFromDescription: async () => {
    const { currentProject } = get();
    if (!currentProject) return;

    set({ isGlobalLoading: true, error: null });
    try {
      const response = await api.generateFromDescription(currentProject.id!);
      devLog('[Tác vụ bất đồng bộ] APIphản hồi:', response);
      
      // Project store logic
      await get().syncProject();
      
      // Project store logic
      const { currentProject: updatedProject } = get();
      devLog('[Tạo dàn ý] Dự án sau khi làm mới:', updatedProject?.pages.length, 'trang');
    } catch (error: any) {
      console.error('[] :', error);
      set({ error: error.message || t('store.generateFromDescFailed') });
      throw error;
    } finally {
      set({ isGlobalLoading: false });
    }
  },

  // Project store logic
  generateDescriptions: async (detailLevel?: string) => {
    const { currentProject } = get();
    if (!currentProject || !currentProject.id) return;

    const pages = currentProject.pages.filter((p) => p.id);
    if (pages.length === 0) return;

    // Project store logic
    let mode: string = 'streaming';
    try {
      const cached = sessionStorage.getItem('banana-settings');
      if (cached) {
        const parsed = JSON.parse(cached);
        if (parsed?.description_generation_mode) {
          mode = parsed.description_generation_mode;
        }
      }
    } catch { /* ignore */ }

    if (mode === 'streaming') {
      // Project store logic
      set({ isDescriptionStreaming: true, error: null });

      const updatedPages = currentProject.pages.map((page) =>
        page.id ? { ...page, status: 'GENERATING_DESCRIPTION' as const } : page
      );
      set({ currentProject: { ...currentProject, pages: updatedPages } });

      // Concurrent queue + render loop (like outline streaming)
      const descQueue: api.DescriptionStreamEvent[] = [];
      let streamDone = false;
      let doneData: { total: number; pages: any[]; warning?: string } | null = null;
      const STAGGER_MS = 100;

      const renderPromise = new Promise<void>((resolve) => {
        const tick = () => {
          if (descQueue.length > 0) {
            const desc = descQueue.shift()!;
            const { currentProject: proj } = get();
            if (proj) {
              const updatedPages = proj.pages.map((page) => {
                if (page.id === desc.page_id) {
                  return {
                    ...page,
                    status: 'DESCRIPTION_GENERATED' as const,
                    description_content: {
                      text: desc.text,
                      ...(desc.extra_fields ? { extra_fields: desc.extra_fields } : {}),
                    },
                  };
                }
                return page;
              });
              set({ currentProject: { ...proj, pages: updatedPages } });
            }
            setTimeout(tick, STAGGER_MS);
          } else if (streamDone) {
            resolve();
          } else {
            setTimeout(tick, 30);
          }
        };
        tick();
      });

      try {
        await api.generateDescriptionsStream(currentProject.id, {
          onDescription: (data) => { descQueue.push(data); },
          onDone: (data) => { doneData = data; },
          onError: (message) => {
          console.error('[Dàn ý luồng] Lỗi:', message);
            set({ error: normalizeErrorMessage(message) });
            streamDone = true;
          },
        }, undefined, detailLevel);

        streamDone = true;
        await renderPromise;

        if (doneData) {
          const { currentProject: proj } = get();
          if (proj) {
            const normalized = normalizeProject({ ...proj, pages: doneData.pages });
            set({
              currentProject: normalized,
              isDescriptionStreaming: false,
              ...(doneData.warning ? { error: doneData.warning } : {}),
            });
          }
        devLog('[Dàn ý luồng] Hoàn tất:', doneData.total, 'trang');
        } else {
          // Project store logic
          await get().syncProject();
          set({ isDescriptionStreaming: false });
        }
      } catch (error: any) {
        console.error('[] :', error);
        streamDone = true;
        await get().syncProject();
        set({
          error: normalizeErrorMessage(error.message || t('store.generateDescFailed')),
          isDescriptionStreaming: false,
        });
        throw error;
      }
    } else {
      // Project store logic
      set({ error: null });

      const updatedPages = currentProject.pages.map((page) =>
        page.id ? { ...page, status: 'GENERATING_DESCRIPTION' as const } : page
      );
      set({ currentProject: { ...currentProject, pages: updatedPages } });

      try {
        const projectId = currentProject.id;
        if (!projectId) {
          throw new Error(t('store.projectIdMissing'));
        }

        const response = await api.generateDescriptions(projectId, undefined, detailLevel);
        const taskId = response.data?.task_id;

        if (!taskId) {
          throw new Error(t('store.noTaskId'));
        }

        let pollErrors = 0;
        const pollAndSync = async () => {
          try {
            const taskResponse = await api.getTaskStatus(projectId, taskId);
            const task = taskResponse.data;

            if (task) {
              if (task.progress) {
                set({ taskProgress: task.progress });
              }

              await get().syncProject();

              if (task.status === 'COMPLETED') {
                set({ taskProgress: null, activeTaskId: null });
                await get().syncProject();
              } else if (task.status === 'FAILED') {
                set({
                  taskProgress: null,
                  activeTaskId: null,
                  error: normalizeErrorMessage(task.error_message || task.error || t('store.generateDescFailed'))
                });
                await get().syncProject();
              } else if (task.status === 'PENDING' || task.status === 'PROCESSING') {
                setTimeout(pollAndSync, 2000);
              }
            }
          } catch (error: any) {
            console.error('[] :', error);
            pollErrors++;
            if (pollErrors >= 10) {
              console.error('[Tạo mô tả] Quá nhiều lỗi polling, dừng polling');
              set({
                taskProgress: null,
                activeTaskId: null,
                error: normalizeErrorMessage(error.message || t('store.generateDescTimeout'))
              });
              await get().syncProject();
              return;
            }
            await get().syncProject();
            setTimeout(pollAndSync, 2000);
          }
        };

        setTimeout(pollAndSync, 2000);

      } catch (error: any) {
        console.error('[] :', error);
        await get().syncProject();
        set({ error: normalizeErrorMessage(error.message || t('store.startGenerationFailed')) });
        throw error;
      }
    }
  },

  // Project store logic
  generatePageDescription: async (pageId: string, detailLevel?: string) => {
    const { currentProject } = get();
    if (!currentProject) return;

    // Project store logic
    const targetPage = currentProject.pages.find((p) => p.id === pageId);
    if (targetPage?.status === 'GENERATING_DESCRIPTION') {
      devLog(`[Tạo mô tả] Trang ${pageId} đang được tạo, bỏ qua yêu cầu trùng lặp`);
      return;
    }

    set({ error: null });

    // Project store logic
    const updatedPages = currentProject.pages.map((page) =>
      page.id === pageId ? { ...page, status: 'GENERATING_DESCRIPTION' as const } : page
    );
    set({ currentProject: { ...currentProject, pages: updatedPages } });

    try {
      const response = await api.generatePageDescription(currentProject.id, pageId, true, undefined, detailLevel);

      if (response.data) {
        const updatedPageData = response.data;
        const { currentProject: latestProject } = get();
        if (latestProject) {
          const newPages = latestProject.pages.map((page) =>
            page.id === pageId ? { ...page, ...updatedPageData } : page
          );
          set({ currentProject: { ...latestProject, pages: newPages } });
          devLog(`[Tạo mô tả] Trang ${pageId} đã cập nhật mô tả, Dữ liệu từ API phản hồi`);
        }
      }
    } catch (error: any) {
      // Project store logic
      await get().syncProject();
      set({ error: normalizeErrorMessage(error.message || t('store.generateDescFailed')) });
      throw error;
    }
  },

  // Project store logic
  regenerateRenovationPage: async (pageId: string, keepLayout: boolean = false) => {
    const { currentProject } = get();
    if (!currentProject) return;

    // Project store logic
    const targetPage = currentProject.pages.find((p) => p.id === pageId);
    if (targetPage?.status === 'GENERATING_DESCRIPTION') {
      devLog(`[PPTLàm mới] Trang ${pageId} đang được tạo, bỏ qua yêu cầu trùng lặp`);
      return;
    }

    set({ error: null });

    // Project store logic
    const updatedPages = currentProject.pages.map((page) =>
      page.id === pageId ? { ...page, status: 'GENERATING_DESCRIPTION' as const } : page
    );
    set({ currentProject: { ...currentProject, pages: updatedPages } });

    try {
      const response = await api.regenerateRenovationPage(currentProject.id, pageId, keepLayout);

      if (response.data) {
        const updatedPageData = response.data;
        const { currentProject: latestProject } = get();
        if (latestProject) {
          const newPages = latestProject.pages.map((page) =>
            page.id === pageId ? { ...page, ...updatedPageData } : page
          );
          set({ currentProject: { ...latestProject, pages: newPages } });
          devLog(`[PPT]  ${pageId} `);
        }
      }
    } catch (error: any) {
      await get().syncProject();
      set({ error: normalizeErrorMessage(error.message || t('store.regenerateFailed')) });
      throw error;
    }
  },

  // Project store logic
  generatePageImage: async (pageId: string, forceRegenerate: boolean = false) => {
    const { currentProject } = get();
    if (!currentProject) return;

    if (get().pageGeneratingTasks[pageId]) {
      devLog(`[Tạo mô tả] Trang ${pageId} đang được tạo, bỏ qua yêu cầu trùng lặp`);
      return;
    }

    set({ error: null, warningMessage: null });

    try {
      const response = await api.generatePageImage(currentProject.id, pageId, forceRegenerate);
      const taskId = response.data?.task_id;

      if (taskId) {
        devLog(`[Tạo trang đơn] nhận được task_id: ${taskId}, Bắt đầu polling trang ${pageId}`);
        set((state) => ({
          pageGeneratingTasks: {
            ...state.pageGeneratingTasks,
            [pageId]: taskId,
          },
        }));

        await get().syncProject();
        get().pollImageTask(taskId, [pageId]);
      } else {
        await get().syncProject();
      }
    } catch (error: any) {
      console.error('[] :', error);
      await get().syncProject();
      throw error;
    }
  },

  // Project store logic
  generateImages: async (pageIds?: string[]) => {
    const { currentProject, pageGeneratingTasks } = get();
    if (!currentProject) return;

    // Project store logic
    const targetPageIds = pageIds || currentProject.pages.map(p => p.id).filter((id): id is string => !!id);
    
    // Project store logic
    const alreadyGenerating = targetPageIds.filter(id => pageGeneratingTasks[id]);
    if (alreadyGenerating.length > 0) {
      devLog(`[Tạo hàng loạt] ${alreadyGenerating.length} trang đang được tạo, bỏ qua`);
      // Project store logic
      const newPageIds = targetPageIds.filter(id => !pageGeneratingTasks[id]);
      if (newPageIds.length === 0) {
    devLog('[Tác vụ bất đồng bộ] Khởi chạy tác vụ bất đồng bộ...');
        return;
      }
    }

    set({ error: null, warningMessage: null });
    
    try {
      // Project store logic
      const response = await api.generateImages(currentProject.id, undefined, pageIds);
      const taskId = response.data?.task_id;
      
      if (taskId) {
        devLog(`[Tạo hàng loạt] nhận được task_id: ${taskId}, đánh dấu ${targetPageIds.length} trang sang trạng thái đang tạo`);
        
        // Project store logic
        const newPageGeneratingTasks = { ...pageGeneratingTasks };
        targetPageIds.forEach(id => {
          newPageGeneratingTasks[id] = taskId;
        });
        set({ pageGeneratingTasks: newPageGeneratingTasks });
        
        // Project store logic
        await get().syncProject();

        // Project store logic
        get().pollImageTask(taskId, targetPageIds);
      } else {
        // Project store logic
        await get().syncProject();
      }
    } catch (error: any) {
      console.error('[] :', error);
      throw error;
    }
  },

  // Project store logic
  pollImageTask: async (taskId: string, pageIds: string[]) => {
    const { currentProject } = get();
    if (!currentProject) {
      console.warn('[] , ');
      return;
    }
    const projectId = currentProject.id!;

    const poll = async () => {
      try {
        const response = await api.getTaskStatus(projectId, taskId);
        const task = response.data;
        
        if (!task) {
      console.warn('[Polling] Không có dự án hiện tại, dừng polling');
          return;
        }

        devLog(`[Polling hàng loạt] Task ${taskId} trạng thái: ${task.status}`, task.progress);

        // Project store logic
        if (task.status === 'COMPLETED') {
          devLog(`[Polling] Task ${taskId} đã hoàn tất, Làm mới dữ liệu dự án`);
          // Project store logic
          const { pageGeneratingTasks } = get();
          const newTasks = { ...pageGeneratingTasks };
          pageIds.forEach(id => {
            if (newTasks[id] === taskId) {
              delete newTasks[id];
            }
          });
          
          // Project store logic
          const warningMessage = task.progress?.warning_message || null;
          
          set({ pageGeneratingTasks: newTasks, warningMessage });

          // Project store logic
          // Project store logic
          let retryCount = 0;
          const maxRetries = 5;
          const retryDelay = 1000; // Project store logic

          const syncWithRetry = async (): Promise<void> => {
            await get().syncProject();

            // Project store logic
            const { currentProject: updatedProject } = get();
            if (updatedProject) {
              const allImagesReady = pageIds.every(pageId => {
                const page = updatedProject.pages.find(p => p.id === pageId);
                return page?.generated_image_path;
              });

              if (allImagesReady) {
                devLog(`[] `);
                return;
              }

              if (retryCount < maxRetries) {
                retryCount++;
                devLog(`[Polling hàng loạt] Đường dẫn ảnh vẫn chưa đồng bộ hoàn toàn, ${retryDelay}ms rồi thử lại (${retryCount}/${maxRetries})`);
                await new Promise(resolve => setTimeout(resolve, retryDelay));
                return syncWithRetry();
              } else {
                console.warn(`[] , `);
              }
            }
          };

          await syncWithRetry();
        } else if (task.status === 'FAILED') {
          console.error(`[Polling] Task ${taskId} thất bại:`, task.error_message || task.error);
          // Project store logic
          const { pageGeneratingTasks } = get();
          const newTasks = { ...pageGeneratingTasks };
          pageIds.forEach(id => {
            if (newTasks[id] === taskId) {
              delete newTasks[id];
            }
          });
          set({ 
            pageGeneratingTasks: newTasks,
            error: normalizeErrorMessage(task.error_message || task.error || t('store.batchGenerateFailed'))
          });
          // Project store logic
          await get().syncProject();
        } else if (task.status === 'PENDING' || task.status === 'PROCESSING') {
          // Project store logic
          const newWarning = task.progress?.warning_message;
          if (newWarning && get().warningMessage !== newWarning) {
            set({ warningMessage: newWarning });
          }
          // Project store logic
          devLog(`[] Task ${taskId} , ...`);
          await get().syncProject();

          // Project store logic
          const { currentProject: proj, pageGeneratingTasks: pgt } = get();
          if (proj) {
            const updated = { ...pgt };
            let changed = false;
            pageIds.forEach(id => {
              if (updated[id] === taskId) {
                const page = proj.pages.find(p => p.id === id);
                // Project store logic
                // Project store logic
                if (page && (page.status === 'COMPLETED' || page.status === 'FAILED')) {
                  delete updated[id];
                  changed = true;
                }
              }
            });
            if (changed) set({ pageGeneratingTasks: updated });
          }

          devLog(`[Polling] Task ${taskId} Đang xử lý, 2giây sau sẽ tiếp tục polling...`);
          setTimeout(poll, 2000);
        } else {
          // Project store logic
          console.warn(`[Polling] Task ${taskId} Trạng thái không xác định: ${task.status}, dừng polling`);
          const { pageGeneratingTasks } = get();
          const newTasks = { ...pageGeneratingTasks };
          pageIds.forEach(id => {
            if (newTasks[id] === taskId) {
              delete newTasks[id];
            }
          });
          set({ pageGeneratingTasks: newTasks });
        }
      } catch (error: any) {
        console.error('[] :', error);
        // Project store logic
        const { pageGeneratingTasks } = get();
        const newTasks = { ...pageGeneratingTasks };
        pageIds.forEach(id => {
          if (newTasks[id] === taskId) {
            delete newTasks[id];
          }
        });
        set({ pageGeneratingTasks: newTasks });
      }
    };

    // Project store logic
    poll();
  },

  // Project store logic
  editPageImage: async (pageId, editPrompt, contextImages) => {
    const { currentProject, pageGeneratingTasks } = get();
    if (!currentProject) return;

    // Project store logic
    if (pageGeneratingTasks[pageId]) {
      devLog(`[Tạo trang đơn] Trang ${pageId} đang được tạo, bỏ qua yêu cầu trùng lặp`);
      return;
    }

    set({ error: null });
    try {
      const response = await api.editPageImage(currentProject.id, pageId, editPrompt, contextImages);
      const taskId = response.data?.task_id;
      
      if (taskId) {
        // Project store logic
        set({ 
          pageGeneratingTasks: { ...pageGeneratingTasks, [pageId]: taskId }
        });
        
        // Project store logic
        await get().syncProject();
        
        // Project store logic
        get().pollImageTask(taskId, [pageId]);
      } else {
        // Project store logic
        await get().syncProject();
      }
    } catch (error: any) {
      // Project store logic
      const { pageGeneratingTasks } = get();
      const newTasks = { ...pageGeneratingTasks };
      delete newTasks[pageId];
      set({ pageGeneratingTasks: newTasks, error: normalizeErrorMessage(error.message || t('store.editImageFailed')) });
      throw error;
    }
  },

  // Project store logic
  exportPPTX: async (pageIds?: string[]) => {
    const { currentProject } = get();
    if (!currentProject) return;

    set({ isGlobalLoading: true, error: null });
    try {
      const response = await api.exportPPTX(currentProject.id, pageIds);
      // Project store logic
      const downloadUrl =
        response.data?.download_url || response.data?.download_url_absolute;

      if (!downloadUrl) {
        throw new Error(t('store.exportLinkFailed'));
      }

      const filename = downloadUrl.split('/').pop()?.split('?')[0] || 'presentation.pptx';
      // Project store logic
      triggerDownload(downloadUrl, filename);
    } catch (error: any) {
      set({ error: error.message || t('store.exportFailed') });
    } finally {
      set({ isGlobalLoading: false });
    }
  },

  // Project store logic
  exportPDF: async (pageIds?: string[]) => {
    const { currentProject } = get();
    if (!currentProject) return;

    set({ isGlobalLoading: true, error: null });
    try {
      const response = await api.exportPDF(currentProject.id, pageIds);
      // Project store logic
      const downloadUrl =
        response.data?.download_url || response.data?.download_url_absolute;

      if (!downloadUrl) {
        throw new Error(t('store.exportLinkFailed'));
      }

      const filename = downloadUrl.split('/').pop()?.split('?')[0] || 'presentation.pdf';
      // Project store logic
      triggerDownload(downloadUrl, filename);
    } catch (error: any) {
      set({ error: error.message || t('store.exportFailed') });
    } finally {
      set({ isGlobalLoading: false });
    }
  },

  // Project store logic
  exportEditablePPTX: async (filename?: string, pageIds?: string[]) => {
    const { currentProject, startAsyncTask } = get();
    if (!currentProject) return;

    try {
      devLog('[Xuất tệp có thể chỉnh sửaPPTX] Khởi chạy tác vụ xuất bất đồng bộ...');
      // Project store logic
      await startAsyncTask(() => api.exportEditablePPTX(currentProject.id, filename, pageIds));
      devLog('[PPTX] ');
    } catch (error: any) {
      console.error('[Xuất tệp có thể chỉnh sửaPPTX] Xuất thất bại:', error);
      set({ error: error.message || t('store.exportEditableFailed') });
    }
  },

  // Project store logic

  loadTemplateAssets: async (projectId) => {
    const response = await api.listTemplateAssets(projectId);
    const assets = response.data?.assets || [];
    set({ templateAssets: assets });
    return assets;
  },

  uploadTemplateAsset: async (projectId, file, opts) => {
    const response = await api.uploadTemplateAsset(projectId, file, opts);
    const asset = response.data!.asset;
    const analyzeTaskId = response.data!.analyze_task_id;
    set((state) => ({ templateAssets: [...state.templateAssets, asset] }));
    // Project store logic
    // Project store logic
    if (analyzeTaskId) {
      const refreshIfCurrent = () => {
        const cur = get().currentProject;
        if (cur && cur.id === projectId) {
          get().loadTemplateAssets(projectId).catch(() => {});
        }
      };
      get()
        .pollTemplateTask(analyzeTaskId, projectId)
        .then(refreshIfCurrent)
        .catch(refreshIfCurrent);
    }
    // Project store logic
    if (opts?.bindToPageId) {
      const { currentProject } = get();
      if (currentProject) {
        set({
          currentProject: {
            ...currentProject,
            pages: currentProject.pages.map((p) =>
              (p.id === opts.bindToPageId || p.page_id === opts.bindToPageId)
                ? {
                    ...p,
                    template_asset_id: asset.id,
                    template_selection_source: 'manual',
                    template_match_reason: null,
                    template_match_confidence: null,
                  }
                : p
            ),
          },
        });
      }
    }
    return asset;
  },

  uploadTemplatePdf: async (projectId, file) => {
    const response = await api.uploadTemplatePdf(projectId, file);
    return response.data!.task_id;
  },

  updateTemplateAsset: async (projectId, assetId, patch) => {
    const response = await api.updateTemplateAsset(projectId, assetId, patch);
    const updated = response.data!.asset;
    set((state) => ({
      templateAssets: state.templateAssets.map((a) => (a.id === assetId ? updated : a)),
    }));
    return updated;
  },

  deleteTemplateAsset: async (projectId, assetId) => {
    const response = await api.deleteTemplateAsset(projectId, assetId);
    const clearedPageIds = response.data?.cleared_page_ids || [];
    set((state) => ({
      templateAssets: state.templateAssets.filter((a) => a.id !== assetId),
    }));
    // Project store logic
    if (clearedPageIds.length > 0) {
      const { currentProject } = get();
      if (currentProject) {
        const cleared = new Set(clearedPageIds);
        set({
          currentProject: {
            ...currentProject,
            pages: currentProject.pages.map((p) => {
              const pid = p.id || p.page_id;
              return pid && cleared.has(pid)
                ? {
                    ...p,
                    template_asset_id: null,
                    template_selection_source: null,
                    template_match_reason: null,
                    template_match_confidence: null,
                  }
                : p;
            }),
          },
        });
      }
    }
    return clearedPageIds;
  },

  reanalyzeTemplateAsset: async (projectId, assetId) => {
    const response = await api.reanalyzeTemplateAsset(projectId, assetId);
    // Project store logic
    set((state) => ({
      templateAssets: state.templateAssets.map((a) =>
        a.id === assetId ? { ...a, analysis_status: 'pending', analysis_error: null } : a
      ),
    }));
    return response.data!.analyze_task_id;
  },

  updatePageTemplate: async (projectId, pageId, patch) => {
    const response = await api.updatePageTemplate(projectId, pageId, patch);
    const updatedPage = response.data?.page;
    const { currentProject } = get();
    if (currentProject && updatedPage) {
      set({
        currentProject: {
          ...currentProject,
          pages: currentProject.pages.map((p) =>
            (p.id === pageId || p.page_id === pageId)
              ? { ...p, ...updatedPage, id: p.id, page_id: p.page_id }
              : p
          ),
        },
      });
    }
  },

  switchTemplateMode: async (projectId, payload) => {
    await api.switchTemplateMode(projectId, payload);
    // Project store logic
    await get().syncProject(projectId);
  },

  switchTemplateModeWithUpload: async (projectId, file, unifiedStyleText) => {
    const response = await api.switchTemplateModeSingleWithUpload(projectId, file, unifiedStyleText);
    const asset = response.data?.asset;
    if (asset) {
      set((state) => ({ templateAssets: [...state.templateAssets, asset] }));
    }
    await get().syncProject(projectId);
  },

  autoMatchAll: async (projectId, opts) => {
    const response = await api.autoMatchAllTemplates(projectId, opts);
    return response.data!.task_id;
  },

  autoMatchPage: async (projectId, pageId) => {
    const response = await api.autoMatchPageTemplate(projectId, pageId);
    return response.data!.task_id;
  },

  // Project store logic
  // Project store logic
  pollTemplateTask: async (taskId, projectId, onProgress) => {
    // Cap the loop so a stuck/dead worker can't poll forever (~15 min).
    const MAX_ATTEMPTS = 450;
    // Tolerate a few transient network errors before giving up.
    const MAX_CONSECUTIVE_ERRORS = 5;
    return new Promise<Task>((resolve, reject) => {
      let attempts = 0;
      let consecutiveErrors = 0;
      const poll = async () => {
        // Stop polling if the user navigated to a different project so we
        // don't keep firing requests for a screen that's no longer visible.
        const { currentProject } = get();
        if (!currentProject || currentProject.id !== projectId) {
          reject(new Error('Project changed, polling stopped'));
          return;
        }
        if (attempts++ >= MAX_ATTEMPTS) {
          reject(new Error(t('store.taskFailed')));
          return;
        }
        try {
          const response = await api.getTaskStatus(projectId, taskId);
          consecutiveErrors = 0;
          const task = response.data;
          if (!task) {
            setTimeout(poll, 2000);
            return;
          }
          if (onProgress) onProgress(task);
          if (task.status === 'COMPLETED') {
            resolve(task);
          } else if (task.status === 'FAILED') {
            reject(new Error(task.error_message || task.error || t('store.taskFailed')));
          } else {
            setTimeout(poll, 2000);
          }
        } catch (error: any) {
          consecutiveErrors++;
          if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
            reject(error);
          } else {
            setTimeout(poll, 2000);
          }
        }
      };
      poll();
    });
  },
};});
