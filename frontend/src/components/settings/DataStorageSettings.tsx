import React, { useEffect, useState } from 'react';
import { FolderOpen, HardDrive, RefreshCw } from 'lucide-react';
import { Button, Input, Modal, Skeleton } from '@/components/shared';
import { useT } from '@/hooks/useT';
import {
  getDataStorageElectronApi,
  type DataStorageInspection,
} from '@/types/dataStorage';

const dataStorageI18n = {
  zh: {
    dataStorage: {
      title: "Data storage location",
      description: "Stores projects, generated images, uploaded assets, and export cache.",
      pathLabel: "Storage path",
      browse: "Browse",
      openCurrent: "Open current folder",
      saveRestart: "Save and restart",
      saving: "Saving",
      loading: "Loading data storage location",
      loadFailed: "Could not load the current data storage location",
      inspectFailed: "The selected folder cannot be used",
      openFailed: "Could not open the current data folder",
      applyFailed: "Could not save the data storage location",
      pathRequired: "Choose or enter a data storage path.",
      unchanged: "This data storage location is already in use.",
      manualMigration: "The app does not move or delete existing data automatically. To migrate, quit Banana Slides completely, then copy data, uploads, and exports in full from the old folder to the new one.",
      restartHint: "The app restarts immediately after this change and reads data from the new location. Regular Save Settings and Reset to Default do not change this path.",
      confirmTitle: "Use a new empty data location?",
      confirmBody: "The selected folder does not contain data/database.db. Banana Slides will appear as a new installation after switching. Existing projects remain in the old folder and will not be moved or deleted.",
      confirmCheck: "I confirm that I copied data, uploads, and exports if needed, and understand that the new folder may not contain my existing projects.",
      cancel: "Hủy",
      confirmRestart: "Confirm and restart",
    },
  },
  en: {
    dataStorage: {
      title: 'Data storage location',
      description: 'Stores projects, generated images, uploaded assets, and export cache.',
      pathLabel: 'Storage path',
      browse: 'Browse',
      openCurrent: 'Open current folder',
      saveRestart: 'Save and restart',
      saving: 'Saving',
      loading: 'Loading data storage location',
      loadFailed: 'Could not load the current data storage location',
      inspectFailed: 'The selected folder cannot be used',
      openFailed: 'Could not open the current data folder',
      applyFailed: 'Could not save the data storage location',
      pathRequired: 'Choose or enter a data storage path.',
      unchanged: 'This data storage location is already in use.',
      manualMigration: 'The app does not move or delete existing data automatically. To migrate, quit Banana Slides completely, then copy data, uploads, and exports in full from the old folder to the new one.',
      restartHint: 'The app restarts immediately after this change and reads data from the new location. Regular Save Settings and Reset to Default do not change this path.',
      confirmTitle: 'Use a new empty data location?',
      confirmBody: 'The selected folder does not contain data/database.db. Banana Slides will appear as a new installation after switching. Existing projects remain in the old folder and will not be moved or deleted.',
      confirmCheck: 'I confirm that I copied data, uploads, and exports if needed, and understand that the new folder may not contain my existing projects.',
      cancel: 'Cancel',
      confirmRestart: 'Confirm and restart',
    },
  },
};

function errorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'string' && error) return `${fallback}: ${error}`;
  if (error && typeof error === 'object' && 'message' in error) {
    const message = (error as { message?: unknown }).message;
    if (typeof message === 'string' && message) return `${fallback}: ${message}`;
  }
  return fallback;
}

export const DataStorageSettings: React.FC = () => {
  const t = useT(dataStorageI18n);
  const api = getDataStorageElectronApi();
  const [currentPath, setCurrentPath] = useState('');
  const [path, setPath] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [configurable, setConfigurable] = useState<boolean | null>(null);
  const [saving, setSaving] = useState(false);
  const [pendingInspection, setPendingInspection] = useState<DataStorageInspection | null>(null);
  const [acknowledged, setAcknowledged] = useState(false);
  const loadFailedMessage = t('dataStorage.loadFailed');

  useEffect(() => {
    if (!api) return;
    let active = true;
    api.getDataStorageInfo()
      .then((info) => {
        if (!active) return;
        setConfigurable(info.configurable);
        setCurrentPath(info.dataRoot);
        setPath(info.dataRoot);
        setLoading(false);
      })
      .catch((loadError) => {
        if (!active) return;
        setConfigurable(true);
        setError(errorMessage(loadError, loadFailedMessage));
        setLoading(false);
      });
    return () => { active = false; };
  }, [api, loadFailedMessage]);

  if (!api || configurable === false) return null;

  if (configurable === null) {
    return (
      <section
        className="min-h-[220px]"
        role="status"
        aria-label={t('dataStorage.loading')}
        aria-busy="true"
      >
        <div className="mb-1 flex items-center gap-2">
          <Skeleton className="h-5 w-5 shrink-0 rounded-md" />
          <Skeleton className="h-6 w-40 rounded-md" />
        </div>
        <Skeleton className="mb-4 h-4 max-w-md rounded-md" />
        <div className="rounded-lg border border-gray-200 p-4 dark:border-border-primary">
          <Skeleton className="h-10 w-full rounded-lg" />
          <Skeleton className="mt-4 h-16 w-full rounded-md" />
        </div>
      </section>
    );
  }

  const chooseDirectory = async () => {
    setError('');
    try {
      const selected = await api.chooseDataStorageDirectory();
      if (selected) setPath(selected);
    } catch (chooseError) {
      setError(errorMessage(chooseError, t('dataStorage.inspectFailed')));
    }
  };

  const openCurrentDirectory = async () => {
    setError('');
    try {
      const result = await api.openDataStorageDirectory();
      if (!result.success) setError(result.error || t('dataStorage.openFailed'));
    } catch (openError) {
      setError(errorMessage(openError, t('dataStorage.openFailed')));
    }
  };

  const apply = async (inspection: DataStorageInspection, allowInitialize: boolean) => {
    setSaving(true);
    setError('');
    try {
      const result = await api.applyDataStorageDirectory(inspection.dataRoot, allowInitialize);
      if (!result.success) {
        setError(t('dataStorage.applyFailed'));
        setSaving(false);
      }
    } catch (applyError) {
      setError(errorMessage(applyError, t('dataStorage.applyFailed')));
      setSaving(false);
    }
  };

  const inspectAndApply = async () => {
    const candidate = path.trim();
    setError('');
    if (!candidate) {
      setError(t('dataStorage.pathRequired'));
      return;
    }
    if (candidate === currentPath) {
      setError(t('dataStorage.unchanged'));
      return;
    }
    setSaving(true);
    try {
      const inspection = await api.inspectDataStorageDirectory(candidate);
      if (inspection.dataRoot === currentPath) {
        setError(t('dataStorage.unchanged'));
        setSaving(false);
        return;
      }
      if (!inspection.hasDatabase) {
        setPendingInspection(inspection);
        setAcknowledged(false);
        setSaving(false);
        return;
      }
      await apply(inspection, false);
    } catch (inspectError) {
      setError(errorMessage(inspectError, t('dataStorage.inspectFailed')));
      setSaving(false);
    }
  };

  const confirmEmptyDirectory = async () => {
    if (!pendingInspection || !acknowledged) return;
    const inspection = pendingInspection;
    setPendingInspection(null);
    await apply(inspection, true);
  };

  return (
    <section aria-labelledby="data-storage-title">
      <h2 id="data-storage-title" className="mb-1 flex items-center text-xl font-semibold text-gray-900 dark:text-foreground-primary">
        <HardDrive size={20} />
        <span className="ml-2">{t('dataStorage.title')}</span>
      </h2>
      <p className="mb-4 text-sm text-gray-500 dark:text-foreground-tertiary">{t('dataStorage.description')}</p>

      <div className="rounded-lg border border-gray-200 p-4 dark:border-border-primary">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="min-w-0 flex-1">
            <Input
              label={t('dataStorage.pathLabel')}
              value={path}
              onChange={(event) => setPath(event.target.value)}
              disabled={loading || saving}
              aria-label={t('dataStorage.pathLabel')}
              className="text-sm"
            />
          </div>
          <Button
            variant="secondary"
            icon={<FolderOpen size={17} />}
            onClick={chooseDirectory}
            disabled={loading || saving}
            className="shrink-0 whitespace-nowrap px-4 text-sm"
          >
            {t('dataStorage.browse')}
          </Button>
        </div>

        <div className="mt-4 space-y-2 border-l-4 border-amber-300 pl-4 text-sm leading-6 text-gray-700 dark:border-amber-700 dark:text-foreground-secondary">
          <p>{t('dataStorage.manualMigration')}</p>
          <p>{t('dataStorage.restartHint')}</p>
        </div>

        {error && <p role="alert" className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>}

        <div className="mt-4 flex flex-wrap justify-end gap-3">
          <Button
            variant="secondary"
            icon={<FolderOpen size={17} />}
            onClick={openCurrentDirectory}
            disabled={loading || saving || !currentPath}
            className="whitespace-nowrap px-4 text-sm"
          >
            {t('dataStorage.openCurrent')}
          </Button>
          <Button
            icon={<RefreshCw size={17} />}
            onClick={inspectAndApply}
            loading={saving}
            disabled={loading}
            className="whitespace-nowrap px-4 text-sm"
          >
            {saving ? t('dataStorage.saving') : t('dataStorage.saveRestart')}
          </Button>
        </div>
      </div>

      <Modal
        isOpen={Boolean(pendingInspection)}
        onClose={() => setPendingInspection(null)}
        title={t('dataStorage.confirmTitle')}
        size="md"
      >
        <div className="space-y-5 px-7 pb-7">
          <p className="text-sm leading-6 text-gray-700 dark:text-foreground-secondary">{t('dataStorage.confirmBody')}</p>
          <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-200">
            <input
              type="checkbox"
              checked={acknowledged}
              onChange={(event) => setAcknowledged(event.target.checked)}
              className="mt-1 h-4 w-4 accent-banana-500"
            />
            <span>{t('dataStorage.confirmCheck')}</span>
          </label>
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setPendingInspection(null)}>{t('dataStorage.cancel')}</Button>
            <Button onClick={confirmEmptyDirectory} disabled={!acknowledged} loading={saving}>{t('dataStorage.confirmRestart')}</Button>
          </div>
        </div>
      </Modal>
    </section>
  );
};