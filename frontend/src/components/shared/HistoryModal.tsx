import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Trash2, AlertTriangle, Inbox } from 'lucide-react';
import { Modal } from './Modal';
import { Button } from './Button';
import { Loading } from './Loading';
import { Card } from './Card';
import { Pagination } from './Pagination';
import { useToast } from './Toast';
import { useConfirm } from './ConfirmDialog';
import { ProjectCard } from '@/components/history/ProjectCard';
import { useProjectStore } from '@/store/useProjectStore';
import { useT } from '@/hooks/useT';
import * as api from '@/api/endpoints';
import { normalizeProject } from '@/utils';
import { getProjectTitle, getProjectRoute } from '@/utils/projectUtils';
import type { Project } from '@/types';

const DEFAULT_PAGE_SIZE = 5;
const PAGE_SIZE_KEY = 'history_page_size';

const historyModalI18n = {
  zh: {
    history: {
      title: 'Lịch sử dự án',
      subtitle: 'Xem và quản lý tất cả các bài thuyết trình của bạn',
      noProjects: 'Chưa có dự án lịch sử nào',
      createFirst: 'Hãy tạo dự án đầu tiên của bạn để bắt đầu',
      createProject: 'Tạo dự án mới',
      selectedCount: 'Đã chọn {{count}} mục',
      cancelSelect: 'Hủy chọn',
      batchDelete: 'Xóa mục đã chọn',
      confirmDelete: 'Bạn có chắc chắn muốn xóa dự án "{{title}}" không? Thao tác này không thể hoàn tác.',
      confirmBatchDelete: 'Bạn có chắc chắn muốn xóa {{count}} dự án đã chọn không? Thao tác này không thể hoàn tác.',
      deleteTitle: 'Xác nhận xóa',
      batchDeleteTitle: 'Xác nhận xóa hàng loạt',
      deleteSuccess: 'Đã xóa {{count}} dự án',
      deletePartial: 'Đã xóa {{success}} dự án thành công, {{fail}} dự án thất bại',
      deleteCurrentProject: 'Đã xóa dự án hiện tại đang mở',
      deleteFailed: 'Xóa dự án thất bại',
      openFailed: 'Mở dự án thất bại',
      loadFailed: 'Tải lịch sử dự án thất bại',
      perPage: '/ trang',
      titleEmpty: 'Tên dự án không được để trống',
      titleUpdated: 'Đã cập nhật tên dự án',
      titleUpdateFailed: 'Cập nhật tên dự án thất bại',
    },
  },
  en: {
    history: {
      title: 'Project History',
      subtitle: 'View and manage all your projects',
      noProjects: 'No projects yet',
      createFirst: 'Create your first project to get started',
      createProject: 'Create New Project',
      selectedCount: '{{count}} selected',
      cancelSelect: 'Cancel Selection',
      batchDelete: 'Batch Delete',
      confirmDelete: 'Are you sure you want to delete project "{{title}}"? This action cannot be undone.',
      confirmBatchDelete: 'Are you sure you want to delete {{count}} selected project(s)? This action cannot be undone.',
      deleteTitle: 'Confirm Delete',
      batchDeleteTitle: 'Confirm Batch Delete',
      deleteSuccess: 'Successfully deleted {{count}} project(s)',
      deletePartial: 'Deleted {{success}} project(s), {{fail}} failed',
      deleteCurrentProject: 'Deleted projects including the currently open one',
      deleteFailed: 'Failed to delete project',
      openFailed: 'Failed to open project',
      loadFailed: 'Failed to load project history',
      perPage: '/ page',
      titleEmpty: 'Project name cannot be empty',
      titleUpdated: 'Project name updated',
      titleUpdateFailed: 'Failed to update project name',
    },
  },
};

export interface HistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HistoryModal: React.FC<HistoryModalProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const { i18n } = useTranslation();
  const t = useT(historyModalI18n);
  const { syncProject, setCurrentProject } = useProjectStore();

  const [projects, setProjects] = useState<Project[]>([]);
  const [totalProjects, setTotalProjects] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(() => {
    const saved = localStorage.getItem(PAGE_SIZE_KEY);
    return saved ? Number(saved) : DEFAULT_PAGE_SIZE;
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedProjects, setSelectedProjects] = useState<Set<string>>(new Set());
  const [isDeleting, setIsDeleting] = useState(false);
  const [editingProjectId, setEditingProjectId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState<string>('');

  const { show, ToastContainer } = useToast();
  const { confirm, ConfirmDialog } = useConfirm();

  const totalPages = Math.ceil(totalProjects / pageSize);

  const loadProjects = useCallback(async (page: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const offset = (page - 1) * pageSize;
      const response = await api.listProjects(pageSize, offset);
      if (response.data?.projects) {
        const normalizedProjects = response.data.projects.map(normalizeProject);
        setProjects(normalizedProjects);
        setTotalProjects(response.data.total ?? 0);
      }
    } catch (err: any) {
      console.error('Tải lịch sử dự án thất bại:', err);
      setError(err.message || t('history.loadFailed'));
    } finally {
      setIsLoading(false);
    }
  }, [pageSize, t]);

  useEffect(() => {
    if (isOpen) {
      loadProjects(currentPage);
    }
  }, [isOpen, currentPage, loadProjects]);

  const handlePageChange = useCallback((page: number) => {
    setSelectedProjects(new Set());
    setCurrentPage(page);
  }, []);

  const handlePageSizeChange = useCallback((size: number) => {
    localStorage.setItem(PAGE_SIZE_KEY, String(size));
    setPageSize(size);
    setCurrentPage(1);
    setSelectedProjects(new Set());
  }, []);

  const handleSelectProject = useCallback(async (project: Project) => {
    const projectId = project.id || project.project_id;
    if (!projectId) return;
    if (selectedProjects.size > 0 || editingProjectId === projectId) return;

    try {
      setCurrentProject(project);
      localStorage.setItem('currentProjectId', projectId);
      await syncProject(projectId);
      onClose();
      const route = getProjectRoute(project);
      navigate(route, { state: { from: 'history' } });
    } catch (err: any) {
      console.error('Mở dự án thất bại:', err);
      show({
        message: t('history.openFailed') + ': ' + (err.message || t('common.unknownError')),
        type: 'error',
      });
    }
  }, [selectedProjects, editingProjectId, setCurrentProject, syncProject, onClose, navigate, show, t]);

  const handleToggleSelect = useCallback((projectId: string) => {
    setSelectedProjects(prev => {
      const newSelected = new Set(prev);
      if (newSelected.has(projectId)) {
        newSelected.delete(projectId);
      } else {
        newSelected.add(projectId);
      }
      return newSelected;
    });
  }, []);

  const handleSelectAll = useCallback(() => {
    setSelectedProjects(prev => {
      if (prev.size === projects.length) {
        return new Set();
      } else {
        const allIds = projects.map(p => p.id || p.project_id).filter(Boolean) as string[];
        return new Set(allIds);
      }
    });
  }, [projects]);

  const deleteProjects = useCallback(async (projectIds: string[]) => {
    setIsDeleting(true);
    const currentProjectId = localStorage.getItem('currentProjectId');
    let deletedCurrentProject = false;

    try {
      const results = await Promise.allSettled(
        projectIds.map(projectId => api.deleteProject(projectId))
      );

      const successIds = projectIds.filter((_, i) => results[i].status === 'fulfilled');
      const failCount = results.filter(r => r.status === 'rejected').length;

      if (currentProjectId && successIds.includes(currentProjectId)) {
        localStorage.removeItem('currentProjectId');
        setCurrentProject(null);
        deletedCurrentProject = true;
      }

      setSelectedProjects(new Set());

      if (successIds.length > 0) {
        const remainingOnPage = projects.length - successIds.length;
        const newPage = remainingOnPage <= 0 && currentPage > 1 ? currentPage - 1 : currentPage;
        if (newPage !== currentPage) {
          setCurrentPage(newPage);
        } else {
          await loadProjects(newPage);
        }
      }

      if (failCount > 0 && successIds.length > 0) {
        show({
          message: t('history.deletePartial', { success: successIds.length, fail: failCount }),
          type: 'warning',
        });
      } else if (deletedCurrentProject) {
        show({
          message: t('history.deleteCurrentProject'),
          type: 'info',
        });
      } else if (successIds.length > 0) {
        show({
          message: t('history.deleteSuccess', { count: successIds.length }),
          type: 'success',
        });
      } else {
        show({
          message: t('history.deleteFailed'),
          type: 'error',
        });
      }
    } catch (err: any) {
      console.error('Xóa dự án thất bại:', err);
      show({
        message: t('history.deleteFailed') + ': ' + (err.message || t('common.unknownError')),
        type: 'error',
      });
    } finally {
      setIsDeleting(false);
    }
  }, [setCurrentProject, show, projects, currentPage, loadProjects, t]);

  const handleDeleteProject = useCallback(async (e: React.MouseEvent, project: Project) => {
    e.stopPropagation();
    const projectId = project.id || project.project_id;
    if (!projectId) return;

    const projectTitle = getProjectTitle(project);
    confirm(
      t('history.confirmDelete', { title: projectTitle }),
      async () => {
        await deleteProjects([projectId]);
      },
      { title: t('history.deleteTitle'), variant: 'danger' }
    );
  }, [confirm, deleteProjects, t]);

  const handleBatchDelete = useCallback(async () => {
    if (selectedProjects.size === 0) return;
    const count = selectedProjects.size;
    confirm(
      t('history.confirmBatchDelete', { count }),
      async () => {
        const projectIds = Array.from(selectedProjects);
        await deleteProjects(projectIds);
      },
      { title: t('history.batchDeleteTitle'), variant: 'danger' }
    );
  }, [selectedProjects, confirm, deleteProjects, t]);

  const handleStartEdit = useCallback((e: React.MouseEvent, project: Project) => {
    e.stopPropagation();
    if (selectedProjects.size > 0) return;
    const projectId = project.id || project.project_id;
    if (!projectId) return;
    const currentTitle = getProjectTitle(project);
    setEditingProjectId(projectId);
    setEditingTitle(currentTitle);
  }, [selectedProjects]);

  const handleCancelEdit = useCallback(() => {
    setEditingProjectId(null);
    setEditingTitle('');
  }, []);

  const handleSaveEdit = useCallback(async (projectId: string) => {
    const nextTitle = editingTitle.trim();
    if (!nextTitle) {
      show({ message: t('history.titleEmpty'), type: 'error' });
      return;
    }

    try {
      const targetProject = projects.find((p) => (p.id || p.project_id) === projectId);
      if (!targetProject) return;
      await api.updateProject(projectId, { project_title: nextTitle });

      setProjects(prev => prev.map(p => {
        const id = p.id || p.project_id;
        if (id === projectId) {
          return { ...p, project_title: nextTitle };
        }
        return p;
      }));

      setEditingProjectId(null);
      setEditingTitle('');
      show({ message: t('history.titleUpdated'), type: 'success' });
    } catch (err: any) {
      console.error('Cập nhật tên dự án thất bại:', err);
      show({
        message: t('history.titleUpdateFailed') + ': ' + (err.message || t('common.unknownError')),
        type: 'error',
      });
    }
  }, [editingTitle, projects, show, t]);

  const handleTitleKeyDown = useCallback((e: React.KeyboardEvent, projectId: string) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSaveEdit(projectId);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancelEdit();
    }
  }, [handleSaveEdit, handleCancelEdit]);

  const modalTitle = !i18n.language?.startsWith('en') ? 'Lịch sử dự án' : 'Project History';

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title={modalTitle}
        size="wide"
      >
        <div className="py-2 space-y-4">
          {projects.length > 0 && selectedProjects.size > 0 && (
            <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 bg-banana-50 dark:bg-background-tertiary rounded-lg border border-banana-200 dark:border-border-primary">
              <span className="text-xs sm:text-sm font-medium text-gray-700 dark:text-foreground-secondary">
                {t('history.selectedCount', { count: selectedProjects.size })}
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedProjects(new Set())}
                  disabled={isDeleting}
                  className="text-xs"
                >
                  {t('history.cancelSelect')}
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<Trash2 size={14} />}
                  onClick={handleBatchDelete}
                  disabled={isDeleting}
                  loading={isDeleting}
                  className="text-xs text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  {t('history.batchDelete')}
                </Button>
              </div>
            </div>
          )}

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loading message={!i18n.language?.startsWith('en') ? 'Đang tải dự án...' : 'Loading projects...'} />
            </div>
          ) : error ? (
            <Card className="p-6 text-center">
              <AlertTriangle size={40} className="mx-auto mb-3 text-amber-500" strokeWidth={1.5} />
              <p className="text-sm text-gray-600 dark:text-foreground-tertiary mb-3">{error}</p>
              <Button variant="primary" size="sm" onClick={() => loadProjects(currentPage)}>
                {!i18n.language?.startsWith('en') ? 'Thử lại' : 'Retry'}
              </Button>
            </Card>
          ) : projects.length === 0 ? (
            <Card className="p-8 sm:p-12 text-center">
              <Inbox size={44} className="mx-auto mb-3 text-gray-400 dark:text-foreground-tertiary" strokeWidth={1.5} />
              <h3 className="text-base sm:text-lg font-semibold text-gray-700 dark:text-foreground-secondary mb-1">
                {t('history.noProjects')}
              </h3>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-foreground-tertiary mb-4">
                {t('history.createFirst')}
              </p>
              <Button variant="primary" size="sm" onClick={onClose}>
                {t('history.createProject')}
              </Button>
            </Card>
          ) : (
            <div className="space-y-3">
              {projects.length > 0 && (
                <div className="flex items-center gap-2 pb-1 border-b border-gray-100 dark:border-border-primary">
                  <label className="flex items-center gap-2 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={selectedProjects.size === projects.length && projects.length > 0}
                      onChange={handleSelectAll}
                      className="w-4 h-4 text-banana-600 border-gray-300 dark:border-border-primary rounded focus:ring-banana-500"
                    />
                    <span className="text-xs sm:text-sm text-gray-600 dark:text-foreground-secondary">
                      {selectedProjects.size === projects.length ? (!i18n.language?.startsWith('en') ? 'Bỏ chọn tất cả' : 'Deselect All') : (!i18n.language?.startsWith('en') ? 'Chọn tất cả' : 'Select All')}
                    </span>
                  </label>
                </div>
              )}

              {projects.map((project) => {
                const projectId = project.id || project.project_id;
                if (!projectId) return null;

                return (
                  <ProjectCard
                    key={projectId}
                    project={project}
                    isSelected={selectedProjects.has(projectId)}
                    isEditing={editingProjectId === projectId}
                    editingTitle={editingTitle}
                    onSelect={handleSelectProject}
                    onToggleSelect={handleToggleSelect}
                    onDelete={handleDeleteProject}
                    onStartEdit={handleStartEdit}
                    onTitleChange={setEditingTitle}
                    onTitleKeyDown={handleTitleKeyDown}
                    onSaveEdit={handleSaveEdit}
                    isBatchMode={selectedProjects.size > 0}
                  />
                );
              })}

              <div className="pt-3">
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
                  pageSize={pageSize}
                  onPageSizeChange={handlePageSizeChange}
                  pageSizeLabel={t('history.perPage')}
                />
              </div>
            </div>
          )}
        </div>
      </Modal>
      <ToastContainer />
      {ConfirmDialog}
    </>
  );
};
