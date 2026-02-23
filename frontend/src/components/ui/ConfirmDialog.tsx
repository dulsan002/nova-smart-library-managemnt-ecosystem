/**
 * ConfirmDialog — confirmation modal for destructive actions.
 */

import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { Button } from './Button';
import { Modal, ModalFooter } from './Modal';

export interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message?: string;
  /** Alias for message */
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'info';
  loading?: boolean;
}

const iconColors = {
  danger: 'text-red-500 bg-red-100 dark:bg-red-900/30',
  warning: 'text-amber-500 bg-amber-100 dark:bg-amber-900/30',
  info: 'text-blue-500 bg-blue-100 dark:bg-blue-900/30',
};

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  message,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger',
  loading = false,
}: ConfirmDialogProps) {
  const displayMessage = message ?? description ?? '';
  return (
    <Modal open={open} onClose={onClose} size="sm" showClose={false}>
      <div className="flex gap-4">
        <div
          className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full ${iconColors[variant]}`}
        >
          <ExclamationTriangleIcon className="h-5 w-5" />
        </div>
        <div className="flex-1">
          <h3 className="text-base font-semibold text-nova-text">{title}</h3>
          <p className="mt-1.5 text-sm text-nova-text-secondary">{displayMessage}</p>
        </div>
      </div>
      <ModalFooter>
        <Button variant="secondary" size="sm" onClick={onClose} disabled={loading}>
          {cancelLabel}
        </Button>
        <Button
          variant={variant === 'danger' ? 'danger' : 'primary'}
          size="sm"
          onClick={onConfirm}
          isLoading={loading}
        >
          {confirmLabel}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
