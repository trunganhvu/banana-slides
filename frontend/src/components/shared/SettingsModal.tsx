import React from 'react';
import { Modal } from './Modal';
import { Settings } from '@/pages/Settings';
import { useTranslation } from 'react-i18next';

export interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const { i18n } = useTranslation();
  const title = !i18n.language?.startsWith('en') ? 'Cài đặt hệ thống' : 'Settings';

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="wide"
    >
      <div className="py-1">
        <Settings />
      </div>
    </Modal>
  );
};
