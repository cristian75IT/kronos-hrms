/**
 * KRONOS - FormField Component
 * Unified form field with label, input, error handling, and helper text
 */
import React, { forwardRef } from 'react';
import { clsx } from 'clsx';
import { AlertCircle } from 'lucide-react';

export interface FormFieldProps extends React.InputHTMLAttributes<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement> {
    /** Field label */
    label: string;
    /** Field name (required for form binding) */
    name: string;
    /** Error message to display */
    error?: string;
    /** Helper text shown below input */
    helperText?: string;
    /** Input type - extends to textarea and select */
    as?: 'input' | 'textarea' | 'select';
    /** Select options when as="select" */
    options?: Array<{ value: string; label: string }>;
    /** Icon to show on the left side */
    leftIcon?: React.ReactNode;
    /** Make the field full width */
    fullWidth?: boolean;
    /** Additional wrapper class */
    wrapperClassName?: string;
}

export const FormField = forwardRef<
    HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement,
    FormFieldProps
>(({
    label,
    name,
    error,
    helperText,
    as = 'input',
    options = [],
    leftIcon,
    required,
    disabled,
    fullWidth = true,
    wrapperClassName,
    className,
    ...props
}, ref) => {
    const hasError = !!error;

    const baseInputClasses = clsx(
        'w-full rounded-lg border text-sm transition-all duration-150',
        'placeholder-slate-400 text-slate-900',
        'focus:outline-none focus:ring-2',
        leftIcon ? 'pl-10 pr-3' : 'px-3',
        as === 'textarea' ? 'py-3 min-h-[100px] resize-y' : 'py-2.5 h-10',
        hasError
            ? 'border-red-300 focus:border-red-500 focus:ring-red-100'
            : 'border-slate-200 focus:border-primary focus:ring-primary/20',
        disabled && 'bg-slate-50 text-slate-400 cursor-not-allowed',
        className
    );

    const renderInput = () => {
        const commonProps = {
            id: name,
            name,
            disabled,
            className: baseInputClasses,
            'aria-invalid': hasError,
            'aria-describedby': hasError ? `${name}-error` : helperText ? `${name}-helper` : undefined,
        };

        if (as === 'textarea') {
            return (
                <textarea
                    {...commonProps}
                    {...(props as React.TextareaHTMLAttributes<HTMLTextAreaElement>)}
                    ref={ref as React.Ref<HTMLTextAreaElement>}
                />
            );
        }

        if (as === 'select') {
            return (
                <select
                    {...commonProps}
                    {...(props as React.SelectHTMLAttributes<HTMLSelectElement>)}
                    ref={ref as React.Ref<HTMLSelectElement>}
                    className={clsx(baseInputClasses, 'appearance-none cursor-pointer bg-no-repeat bg-right pr-10')}
                    style={{
                        backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%2394a3b8' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
                        backgroundPosition: 'right 0.75rem center',
                        backgroundSize: '1.25rem',
                    }}
                >
                    {options.map((option) => (
                        <option key={option.value} value={option.value}>
                            {option.label}
                        </option>
                    ))}
                </select>
            );
        }

        return (
            <input
                {...commonProps}
                {...(props as React.InputHTMLAttributes<HTMLInputElement>)}
                ref={ref as React.Ref<HTMLInputElement>}
            />
        );
    };

    return (
        <div className={clsx('flex flex-col gap-1.5', fullWidth && 'w-full', wrapperClassName)}>
            {/* Label */}
            <label
                htmlFor={name}
                className="text-sm font-medium text-slate-700 flex items-center gap-1"
            >
                {label}
                {required && <span className="text-red-500">*</span>}
            </label>

            {/* Input Container */}
            <div className="relative">
                {leftIcon && (
                    <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
                        {leftIcon}
                    </div>
                )}
                {renderInput()}
            </div>

            {/* Error or Helper Text */}
            {hasError ? (
                <div
                    id={`${name}-error`}
                    className="flex items-center gap-1.5 text-xs text-red-600"
                    role="alert"
                >
                    <AlertCircle size={14} />
                    {error}
                </div>
            ) : helperText ? (
                <p
                    id={`${name}-helper`}
                    className="text-xs text-slate-500"
                >
                    {helperText}
                </p>
            ) : null}
        </div>
    );
});

FormField.displayName = 'FormField';

export default FormField;
