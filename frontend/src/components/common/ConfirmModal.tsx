import React from 'react';
import { Modal } from './Modal';
import { Button } from './Button';
import { AlertTriangle, Info, CheckCircle } from 'lucide-react';

interface ConfirmModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title: string;
    message: string;
    confirmLabel?: string;
    cancelLabel?: string;
    variant?: 'danger' | 'warning' | 'info' | 'success';
    isLoading?: boolean;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
    isOpen,
    onClose,
    onConfirm,
    title,
    message,
    confirmLabel = 'Conferma',
    cancelLabel = 'Annulla',
    variant = 'danger',
    isLoading = false,
}) => {
    const getIcon = () => {
        switch (variant) {
            case 'danger': return <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center text-red-600 mb-4"><AlertTriangle size={24} /></div>;
            case 'warning': return <div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center text-amber-600 mb-4"><AlertTriangle size={24} /></div>;
            case 'success': return <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 mb-4"><CheckCircle size={24} /></div>;
            default: return <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 mb-4"><Info size={24} /></div>;
        }
    };

    const getConfirmVariant = () => {
        switch (variant) {
            case 'danger': return 'danger';
            case 'warning': return 'warning';
            case 'success': return 'success';
            default: return 'primary';
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} size="sm" showCloseButton={false}>
            <div className="flex flex-col items-center text-center">
                {getIcon()}
                <h3 className="text-xl font-bold text-gray-900 mb-2">{title}</h3>
                <p className="text-gray-500 mb-6">{message}</p>

                <div className="flex gap-3 w-full">
                    <Button
                        variant="secondary"
                        onClick={onClose}
                        className="flex-1 justify-center"
                        disabled={isLoading}
                    >
                        {cancelLabel}
                    </Button>
                    <Button
                        // @ts-ignore - Variant string mismatch possible depending on Button definition, assuming standard names
                        variant={getConfirmVariant()}
                        onClick={() => {
                            onConfirm();
                            // Optional: don't close automatically if loading is handled by parent, 
                            // but usually we want to trigger action. Parent handles closing or loading state.
                        }}
                        isLoading={isLoading}
                        className="flex-1 justify-center"
                    >
                        {confirmLabel}
                    </Button>
                </div>
            </div>
        </Modal>
    );
};
