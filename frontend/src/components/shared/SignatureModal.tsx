import { useState } from 'react';
import { X, Lock, ShieldCheck, FileCheck } from 'lucide-react';
import { useToast } from '../../context/ToastContext';

interface SignatureModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSign: (otp: string) => Promise<void>;
    documentTitle: string;
}

export function SignatureModal({ isOpen, onClose, onSign, documentTitle }: SignatureModalProps) {
    const [otp, setOtp] = useState('');
    const [isSigning, setIsSigning] = useState(false);
    const toast = useToast();

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (otp.length !== 6) {
            toast.error('Il codice OTP deve essere di 6 cifre');
            return;
        }

        setIsSigning(true);
        try {
            await onSign(otp);
            toast.success('Documento firmato con successo');
            onClose();
        } catch (error) {
            console.error(error);
            const message = error instanceof Error ? error.message : 'Errore durante la firma';
            toast.error(message);
        } finally {
            setIsSigning(false);
            setOtp('');
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-scaleIn">
                {/* Header */}
                <div className="bg-slate-900 text-white p-6 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10">
                        <ShieldCheck size={120} />
                    </div>
                    <button
                        onClick={onClose}
                        className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
                    >
                        <X size={20} />
                    </button>

                    <div className="flex items-center gap-3 mb-2 relative z-10">
                        <div className="p-2 bg-teal-500 rounded-lg shadow-lg shadow-teal-500/30">
                            <Lock size={24} className="text-white" />
                        </div>
                        <h2 className="text-xl font-bold">Firma Digitale</h2>
                    </div>
                    <p className="text-slate-400 text-sm relative z-10">
                        Autenticazione richiesta per finalizzare il documento.
                    </p>
                </div>

                {/* Body */}
                <div className="p-6 space-y-6">
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex items-start gap-3">
                        <FileCheck className="text-teal-600 mt-1" size={20} />
                        <div>
                            <p className="text-xs font-bold text-slate-500 uppercase">Documento</p>
                            <p className="text-slate-900 font-medium">{documentTitle}</p>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700 flex justify-between">
                                Codice OTP
                                <span className="text-xs text-slate-400">Dalla tua app Authenticator</span>
                            </label>
                            <div className="relative">
                                <input
                                    type="text"
                                    maxLength={6}
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value.replace(/[^0-9]/g, ''))}
                                    className="w-full text-center text-3xl font-mono tracking-[0.5em] py-3 border-2 border-slate-200 rounded-xl focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 outline-none transition-all placeholder:tracking-normal placeholder:text-sm placeholder:text-gray-300"
                                    placeholder="000000"
                                    autoFocus
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isSigning || otp.length !== 6}
                            className={`w-full py-3.5 rounded-xl font-bold text-white shadow-lg transition-all transform active:scale-[0.98] ${isSigning || otp.length !== 6
                                ? 'bg-slate-300 cursor-not-allowed shadow-none'
                                : 'bg-teal-600 hover:bg-teal-700 shadow-teal-500/30'
                                }`}
                        >
                            {isSigning ? (
                                <span className="flex items-center justify-center gap-2">
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    Verifica in corso...
                                </span>
                            ) : (
                                'Firma Documento'
                            )}
                        </button>
                    </form>

                    <p className="text-center text-xs text-slate-400">
                        La firma via OTP ha valore legale come <br />Firma Elettronica Avanzata (FEA).
                    </p>
                </div>
            </div>
        </div>
    );
}
