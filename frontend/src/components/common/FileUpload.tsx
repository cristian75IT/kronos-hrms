/**
 * KRONOS - Modern File Upload Component
 * Features:
 * - Drag & drop support
 * - Multiple file upload
 * - File preview with size info
 * - Max size validation
 * - Beautiful modern design
 */
import { useState, useRef, useCallback } from 'react';
import { Upload, X, FileText, Image, File, AlertCircle } from 'lucide-react';

interface FileUploadProps {
    /** Callback when files change */
    onFilesChange: (files: File[]) => void;
    /** Accepted file types (e.g., ".pdf,.jpg,.png") */
    accept?: string;
    /** Allow multiple files */
    multiple?: boolean;
    /** Max file size in MB */
    maxSizeMB?: number;
    /** Max number of files */
    maxFiles?: number;
    /** Label text */
    label?: string;
    /** Helper text */
    helperText?: string;
    /** Current files (controlled component) */
    files?: File[];
    /** Error message */
    error?: string;
    /** Disabled state */
    disabled?: boolean;
}

const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const getFileIcon = (file: File) => {
    const type = file.type;
    if (type.startsWith('image/')) return Image;
    if (type === 'application/pdf') return FileText;
    return File;
};

export function FileUpload({
    onFilesChange,
    accept = '*',
    multiple = true,
    maxSizeMB = 5,
    maxFiles = 10,
    label,
    helperText,
    files = [],
    error,
    disabled = false,
}: FileUploadProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [validationError, setValidationError] = useState<string | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const validateFiles = useCallback((newFiles: FileList | File[]): File[] => {
        const fileArray = Array.from(newFiles);
        const maxBytes = maxSizeMB * 1024 * 1024;
        const validFiles: File[] = [];
        const errors: string[] = [];

        for (const file of fileArray) {
            if (file.size > maxBytes) {
                errors.push(`"${file.name}" supera ${maxSizeMB}MB`);
                continue;
            }
            if (files.length + validFiles.length >= maxFiles) {
                errors.push(`Massimo ${maxFiles} file consentiti`);
                break;
            }
            validFiles.push(file);
        }

        if (errors.length > 0) {
            setValidationError(errors.join('. '));
            setTimeout(() => setValidationError(null), 5000);
        }

        return validFiles;
    }, [files.length, maxFiles, maxSizeMB]);

    const handleFiles = useCallback((newFiles: FileList | File[]) => {
        const validFiles = validateFiles(newFiles);
        if (validFiles.length > 0) {
            const updatedFiles = multiple ? [...files, ...validFiles] : validFiles.slice(0, 1);
            onFilesChange(updatedFiles);
        }
    }, [files, multiple, onFilesChange, validateFiles]);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        if (!disabled) {
            setIsDragging(true);
        }
    }, [disabled]);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        if (!disabled && e.dataTransfer.files) {
            handleFiles(e.dataTransfer.files);
        }
    }, [disabled, handleFiles]);

    const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            handleFiles(e.target.files);
            e.target.value = ''; // Reset input to allow selecting same file
        }
    }, [handleFiles]);

    const removeFile = useCallback((index: number) => {
        const newFiles = files.filter((_, i) => i !== index);
        onFilesChange(newFiles);
    }, [files, onFilesChange]);

    const openFilePicker = () => {
        if (!disabled) {
            inputRef.current?.click();
        }
    };

    const displayError = validationError || error;

    return (
        <div className="space-y-2">
            {label && (
                <label className="block text-sm font-medium text-gray-700">
                    {label}
                </label>
            )}

            {/* Drop Zone */}
            <div
                onClick={openFilePicker}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`
                    relative group cursor-pointer
                    border-2 border-dashed rounded-xl p-6
                    transition-all duration-200 ease-in-out
                    ${isDragging
                        ? 'border-indigo-500 bg-indigo-50 scale-[1.02]'
                        : disabled
                            ? 'border-gray-200 bg-gray-50 cursor-not-allowed'
                            : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50'
                    }
                    ${displayError ? 'border-red-300 bg-red-50' : ''}
                `}
            >
                <input
                    ref={inputRef}
                    type="file"
                    accept={accept}
                    multiple={multiple}
                    onChange={handleInputChange}
                    disabled={disabled}
                    className="hidden"
                />

                <div className="flex flex-col items-center text-center">
                    <div className={`
                        w-12 h-12 rounded-full flex items-center justify-center mb-3
                        transition-all duration-200
                        ${isDragging
                            ? 'bg-indigo-100 text-indigo-600 scale-110'
                            : disabled
                                ? 'bg-gray-100 text-gray-400'
                                : 'bg-gray-100 text-gray-500 group-hover:bg-indigo-100 group-hover:text-indigo-600'
                        }
                    `}>
                        <Upload size={24} className={isDragging ? 'animate-bounce' : ''} />
                    </div>

                    <p className={`text-sm font-medium mb-1 ${disabled ? 'text-gray-400' : 'text-gray-700'}`}>
                        {isDragging ? 'Rilascia i file qui' : 'Trascina i file qui'}
                    </p>
                    <p className={`text-xs ${disabled ? 'text-gray-400' : 'text-gray-500'}`}>
                        oppure{' '}
                        <span className={disabled ? 'text-gray-400' : 'text-indigo-600 font-medium hover:underline'}>
                            sfoglia
                        </span>
                    </p>
                    {helperText && (
                        <p className="text-xs text-gray-400 mt-2">{helperText}</p>
                    )}
                </div>
            </div>

            {/* Error Message */}
            {displayError && (
                <div className="flex items-center gap-2 text-red-600 text-sm">
                    <AlertCircle size={14} />
                    <span>{displayError}</span>
                </div>
            )}

            {/* File List */}
            {files.length > 0 && (
                <div className="space-y-2 mt-3">
                    {files.map((file, index) => {
                        const IconComponent = getFileIcon(file);
                        const isImage = file.type.startsWith('image/');

                        return (
                            <div
                                key={`${file.name}-${index}`}
                                className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-100 group hover:bg-gray-100 transition-colors"
                            >
                                {/* Preview or Icon */}
                                <div className="w-10 h-10 rounded-lg bg-white border border-gray-200 flex items-center justify-center overflow-hidden flex-shrink-0">
                                    {isImage ? (
                                        <img
                                            src={URL.createObjectURL(file)}
                                            alt={file.name}
                                            className="w-full h-full object-cover"
                                        />
                                    ) : (
                                        <IconComponent size={20} className="text-gray-400" />
                                    )}
                                </div>

                                {/* File Info */}
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-gray-700 truncate">
                                        {file.name}
                                    </p>
                                    <p className="text-xs text-gray-500">
                                        {formatFileSize(file.size)}
                                    </p>
                                </div>

                                {/* Remove Button */}
                                <button
                                    type="button"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        removeFile(index);
                                    }}
                                    className="w-8 h-8 rounded-full flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100"
                                    aria-label="Rimuovi file"
                                >
                                    <X size={16} />
                                </button>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* File Count */}
            {multiple && files.length > 0 && (
                <p className="text-xs text-gray-500 text-right">
                    {files.length} / {maxFiles} file
                </p>
            )}
        </div>
    );
}

export default FileUpload;
