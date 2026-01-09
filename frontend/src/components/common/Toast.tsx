import React from 'react';
import { CheckCircle, XCircle, Info, AlertTriangle, X } from 'lucide-react';
import { clsx } from 'clsx';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

interface ToastProps {
  message: string;
  type: ToastType;
  onClose: () => void;
}

const toastStyles = {
  success: {
    border: 'border-l-emerald-500',
    icon: <CheckCircle className="shrink-0 text-emerald-500" size={20} />,
  },
  error: {
    border: 'border-l-red-500',
    icon: <XCircle className="shrink-0 text-red-500" size={20} />,
  },
  info: {
    border: 'border-l-primary',
    icon: <Info className="shrink-0 text-primary" size={20} />,
  },
  warning: {
    border: 'border-l-amber-500',
    icon: <AlertTriangle className="shrink-0 text-amber-500" size={20} />,
  },
};

export const Toast: React.FC<ToastProps> = ({ message, type, onClose }) => {
  const style = toastStyles[type];

  return (
    <div
      className={clsx(
        'min-w-[300px] max-w-[450px] p-4',
        'bg-white/95 backdrop-blur-sm rounded-xl',
        'shadow-lg border border-slate-200',
        'border-l-4',
        style.border,
        'flex items-center justify-between gap-3',
        'pointer-events-auto',
        'animate-slideInRight'
      )}
    >
      <div className="flex items-center gap-3">
        {style.icon}
        <span className="text-sm font-medium text-slate-900">{message}</span>
      </div>
      <button
        onClick={onClose}
        type="button"
        className="shrink-0 p-1 text-slate-400 hover:text-slate-600 transition-colors bg-transparent border-none cursor-pointer"
      >
        <X size={16} />
      </button>
    </div>
  );
};
