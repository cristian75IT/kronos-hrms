import { useState, useEffect } from 'react';
import { FileCheck, ShieldCheck, Eye, Hash, Calendar, Loader2, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { signatureService, type SignatureTransaction } from '../../../services/signature.service';
import { useToast } from '../../../context/ToastContext';

export function UserSignaturesTab() {
    const toast = useToast();
    const [signatures, setSignatures] = useState<SignatureTransaction[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedSig, setSelectedSig] = useState<SignatureTransaction | null>(null);

    useEffect(() => {
        loadSignatures();
    }, []);

    const loadSignatures = async () => {
        setIsLoading(true);
        try {
            const data = await signatureService.getMySignatures();
            setSignatures(data);
        } catch (error) {
            console.error(error);
            toast.error('Errore nel caricamento delle firme');
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center py-12">
                <Loader2 size={32} className="animate-spin text-indigo-600 mb-3" />
                <p className="text-sm text-gray-500">Recupero firme digitali...</p>
            </div>
        );
    }

    if (signatures.length === 0) {
        return (
            <div className="text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-200">
                <ShieldCheck className="mx-auto text-gray-300 mb-3" size={40} />
                <p className="text-gray-500 font-medium">Nessuna firma digitale trovata</p>
                <p className="text-sm text-gray-400 mt-1">Le tue firme digitali appariranno qui una volta effettuate.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50 uppercase text-[10px] font-bold tracking-wider text-gray-500">
                            <tr>
                                <th className="px-6 py-4 text-left">Data Firma</th>
                                <th className="px-6 py-4 text-left">Documento</th>
                                <th className="px-6 py-4 text-left">Metodo</th>
                                <th className="px-6 py-4 text-left">Impronta Digitale (Hash)</th>
                                <th className="px-6 py-4 text-left">Stato</th>
                                <th className="px-6 py-4 text-right"></th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 bg-white">
                            {signatures.map((sig) => (
                                <tr key={sig.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center gap-2 text-sm font-medium text-gray-900">
                                            <Calendar size={14} className="text-gray-400" />
                                            {format(new Date(sig.signed_at), 'dd MMM yyyy, HH:mm', { locale: it })}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                                                <FileCheck size={16} />
                                            </div>
                                            <div>
                                                <div className="text-sm font-bold text-gray-900">{sig.document_type}</div>
                                                <div className="text-xs text-gray-500 font-mono">ID: {sig.document_id.substring(0, 8)}...</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className="px-2 py-1 text-xs font-bold bg-slate-100 text-slate-600 rounded">
                                            {sig.signature_method}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center gap-2 text-xs font-mono text-gray-500 bg-gray-50 px-2 py-1 rounded border border-gray-100 max-w-[150px] truncate" title={sig.document_hash}>
                                            <Hash size={10} />
                                            {sig.document_hash.substring(0, 16)}...
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        {sig.is_valid ? (
                                            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                                                <ShieldCheck size={12} /> Verificata
                                            </span>
                                        ) : (
                                            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                                <AlertCircle size={12} /> Non Valida
                                            </span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button
                                            onClick={() => setSelectedSig(sig)}
                                            className="text-indigo-600 hover:text-indigo-900 p-2 hover:bg-indigo-50 rounded-lg transition-colors"
                                            title="Visualizza certificato"
                                        >
                                            <Eye size={18} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Signature Certificate Modal */}
            {selectedSig && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden animate-scaleIn">
                        <div className="bg-slate-900 text-white p-6 relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-4 opacity-10">
                                <ShieldCheck size={120} />
                            </div>
                            <h3 className="text-lg font-bold relative z-10 flex items-center gap-2">
                                <ShieldCheck className="text-emerald-400" />
                                Certificato di Firma
                            </h3>
                            <p className="text-slate-400 text-sm mt-1 relative z-10">
                                ID Transazione: {selectedSig.id}
                            </p>
                        </div>

                        <div className="p-6 space-y-6">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-gray-50 p-3 rounded-xl border border-gray-100">
                                    <p className="text-[10px] font-bold text-gray-400 uppercase">Data Firma</p>
                                    <p className="text-sm font-medium text-gray-900">
                                        {format(new Date(selectedSig.signed_at), 'dd MMM yyyy', { locale: it })}
                                    </p>
                                    <p className="text-xs text-gray-500">
                                        {format(new Date(selectedSig.signed_at), 'HH:mm:ss', { locale: it })}
                                    </p>
                                </div>
                                <div className="bg-gray-50 p-3 rounded-xl border border-gray-100">
                                    <p className="text-[10px] font-bold text-gray-400 uppercase">Metodo</p>
                                    <p className="text-sm font-medium text-gray-900">{selectedSig.signature_method}</p>
                                    <p className="text-xs text-gray-500">OTP Verified</p>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <p className="text-xs font-bold text-gray-500 uppercase flex items-center gap-2">
                                    <FileCheck size={12} /> Impronta Digitale Documento (SHA-256)
                                </p>
                                <div className="p-3 bg-slate-100 rounded-lg font-mono text-[10px] text-slate-600 break-all border border-slate-200">
                                    {selectedSig.document_hash}
                                </div>
                            </div>

                            <div className="border-t border-gray-100 pt-4">
                                <div className="flex items-center justify-between text-xs text-gray-500">
                                    <span>IP: {selectedSig.metadata?.ip_address || 'N/D'}</span>
                                    {selectedSig.is_valid && (
                                        <span className="flex items-center gap-1 text-emerald-600 font-bold">
                                            <ShieldCheck size={12} /> FEA Validata
                                        </span>
                                    )}
                                </div>
                            </div>

                            <button
                                onClick={() => setSelectedSig(null)}
                                className="w-full py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold rounded-xl transition-colors"
                            >
                                Chiudi Certificato
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
