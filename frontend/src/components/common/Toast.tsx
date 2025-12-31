import React from 'react';
import { CheckCircle, XCircle, Info, AlertTriangle, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

interface ToastProps {
    message: string;
    type: ToastType;
    onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({ message, type, onClose }) => {
    const icons = {
        success: <CheckCircle className="toast-icon text-success" size={20} />,
        error: <XCircle className="toast-icon text-danger" size={20} />,
        info: <Info className="toast-icon text-primary" size={20} />,
        warning: <AlertTriangle className="toast-icon text-warning" size={20} />,
    };

    return (
        <div className={`toast-item toast-${type} animate-slideInRight`}>
            <div className="toast-content">
                {icons[type]}
                <span className="toast-message">{message}</span>
            </div>
            <button onClick={onClose} className="toast-close" type="button">
                <X size={16} />
            </button>

            <style>{`
        .toast-item {
          min-width: 300px;
          max-width: 450px;
          padding: 16px;
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(8px);
          border-radius: 12px;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
          border: 1px solid var(--color-border);
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          pointer-events: auto;
        }
        
        .toast-success { border-left: 4px solid var(--color-success); }
        .toast-error { border-left: 4px solid var(--color-danger); }
        .toast-info { border-left: 4px solid var(--color-primary); }
        .toast-warning { border-left: 4px solid var(--color-warning); }

        .toast-content {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .toast-message {
          font-size: 14px;
          font-weight: 500;
          color: var(--color-text-primary);
        }

        .toast-close {
          color: var(--color-text-secondary);
          opacity: 0.6;
          transition: opacity 0.2s;
          background: none;
          border: none;
          padding: 4px;
          cursor: pointer;
        }

        .toast-close:hover {
          opacity: 1;
        }

        @keyframes slideInRight {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }

        .animate-slideInRight {
          animation: slideInRight 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
      `}</style>
        </div>
    );
};
