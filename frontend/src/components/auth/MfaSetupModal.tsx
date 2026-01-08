
import { useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { authService } from '../../services/authService';
import { useToast } from '../../context/ToastContext';
import { tokenStorage } from '../../utils/tokenStorage';
import { Shield, Key } from 'lucide-react';

interface MfaSetupModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export function MfaSetupModal({ isOpen, onClose }: MfaSetupModalProps) {
    const toast = useToast();
    const [step, setStep] = useState<1 | 2>(1);
    const [secretData, setSecretData] = useState<{ secret: string; otp_url: string } | null>(null);
    const [code, setCode] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    if (!isOpen) return null;

    const handleStart = async () => {
        setIsLoading(true);
        try {
            const token = tokenStorage.getAccessToken();
            if (!token) throw new Error("No session");
            const data = await authService.setupMfa(token);
            setSecretData(data);
            setStep(2);
        } catch (error) {
            console.error(error);
            toast.error("Errore avvio configurazione 2FA");
        } finally {
            setIsLoading(false);
        }
    };

    const handleVerify = async () => {
        if (!secretData || code.length !== 6) return;
        setIsLoading(true);
        try {
            const token = tokenStorage.getAccessToken();
            if (!token) throw new Error("No session");

            await authService.enableMfa(token, secretData.secret, code);

            toast.success("Autenticazione a due fattori attivata con successo!");
            onClose();
        } catch (error: any) {
            console.error(error);
            toast.error(error.message || "Codice non valido");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden animate-fadeIn">
                <div className="p-6">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600">
                            <Shield size={20} />
                        </div>
                        <h2 className="text-xl font-bold text-gray-900">Configura 2FA</h2>
                    </div>

                    {step === 1 ? (
                        <div className="space-y-6">
                            <p className="text-gray-600">
                                L'autenticazione a due fattori (2FA) aumenta la sicurezza del tuo account richiedendo un codice temporaneo (OTP) oltre alla password.
                            </p>
                            <div className="bg-blue-50 p-4 rounded-xl text-sm text-blue-800 flex gap-3">
                                <Key className="shrink-0" size={20} />
                                <div>
                                    Avrai bisogno di un'app come <strong>Google Authenticator</strong> o <strong>Authy</strong> sul tuo smartphone.
                                </div>
                            </div>
                            <div className="flex justify-end gap-3 pt-4">
                                <button onClick={onClose} className="btn btn-ghost text-gray-500">Annulla</button>
                                <button
                                    onClick={handleStart}
                                    className="btn btn-primary"
                                    disabled={isLoading}
                                >
                                    {isLoading ? 'Caricamento...' : 'Inizia Configurazione'}
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            <div className="flex flex-col items-center gap-4 py-4 bg-gray-50 rounded-xl border border-gray-100">
                                {secretData && (
                                    <div className="bg-white p-2 rounded-lg shadow-sm">
                                        <QRCodeSVG value={secretData.otp_url} size={180} />
                                    </div>
                                )}
                                <p className="text-xs text-gray-500 font-mono bg-white px-2 py-1 rounded border">
                                    {secretData?.secret}
                                </p>
                                <p className="text-sm text-center text-gray-600 px-4">
                                    Scansiona il QR Code con la tua app Authenticator
                                </p>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium text-gray-700">Inserisci il codice a 6 cifre</label>
                                <input
                                    type="text"
                                    value={code}
                                    onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                    placeholder="000000"
                                    className="input input-lg text-center tracking-[0.5em] font-mono text-xl"
                                    autoFocus
                                />
                            </div>

                            <div className="flex justify-end gap-3 pt-4">
                                <button onClick={() => setStep(1)} className="btn btn-ghost text-gray-500">Indietro</button>
                                <button
                                    onClick={handleVerify}
                                    className="btn btn-primary"
                                    disabled={isLoading || code.length !== 6}
                                >
                                    {isLoading ? 'Verifica...' : 'Attiva 2FA'}
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
