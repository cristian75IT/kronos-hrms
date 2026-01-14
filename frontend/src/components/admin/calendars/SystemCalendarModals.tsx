/**
 * KRONOS - System Calendars Modals Component
 * 
 * Contains all modals for the system calendars page.
 */
import { X, Loader, Calendar, Download, Link } from 'lucide-react';
import { ConfirmModal } from '../../common';
import type { Holiday, Closure } from '../../../services/calendar.service';
import type { HolidayForm, ClosureForm, ExceptionForm } from '../../../hooks/domain/useSystemCalendars';

interface SystemCalendarModalsProps {
    // Holiday Modal
    showHolidayModal: boolean;
    setShowHolidayModal: (show: boolean) => void;
    editingHoliday: Holiday | null;
    holidayForm: HolidayForm;
    setHolidayForm: (form: HolidayForm) => void;
    onSaveHoliday: () => void;
    isSavingHoliday: boolean;

    // Closure Modal
    showClosureModal: boolean;
    setShowClosureModal: (show: boolean) => void;
    editingClosure: Closure | null;
    closureForm: ClosureForm;
    setClosureForm: (form: ClosureForm) => void;
    onSaveClosure: () => void;
    isSavingClosure: boolean;

    // Exception Modal
    showExceptionModal: boolean;
    setShowExceptionModal: (show: boolean) => void;
    exceptionForm: ExceptionForm;
    setExceptionForm: (form: ExceptionForm) => void;
    onSaveException: () => void;
    isSavingException: boolean;

    // Delete Confirm
    deleteConfirm: { type: 'holiday' | 'closure' | 'exception'; id: string } | null;
    setDeleteConfirm: (confirm: { type: 'holiday' | 'closure' | 'exception'; id: string } | null) => void;
    onConfirmDelete: () => void;

    // Copy Confirm
    showCopyConfirm: boolean;
    setShowCopyConfirm: (show: boolean) => void;
    onConfirmCopy: () => void;
    year: number;
    isGenerating: boolean;

    // Sync Modal
    showSyncModal: boolean;
    setShowSyncModal: (show: boolean) => void;
    subscriptionUrls: {
        holidays: { url: string; description: string };
        closures: { url: string; description: string };
        combined: { url: string; description: string };
    } | null;
    onCopyToClipboard: (text: string) => void;
}

export function SystemCalendarModals({
    showHolidayModal,
    setShowHolidayModal,
    editingHoliday,
    holidayForm,
    setHolidayForm,
    onSaveHoliday,
    isSavingHoliday,
    showClosureModal,
    setShowClosureModal,
    editingClosure,
    closureForm,
    setClosureForm,
    onSaveClosure,
    isSavingClosure,
    showExceptionModal,
    setShowExceptionModal,
    exceptionForm,
    setExceptionForm,
    onSaveException,
    isSavingException,
    deleteConfirm,
    setDeleteConfirm,
    onConfirmDelete,
    showCopyConfirm,
    setShowCopyConfirm,
    onConfirmCopy,
    year,
    isGenerating,
    showSyncModal,
    setShowSyncModal,
    subscriptionUrls,
    onCopyToClipboard,
}: SystemCalendarModalsProps) {
    return (
        <>
            {/* Holiday Modal */}
            {showHolidayModal && (
                <ModalWrapper onClose={() => setShowHolidayModal(false)}>
                    <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50">
                        <h3 className="font-bold text-gray-900">
                            {editingHoliday ? 'Modifica Festività' : 'Nuova Festività'}
                        </h3>
                        <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowHolidayModal(false)}>
                            <X size={20} />
                        </button>
                    </div>
                    <div className="p-6 space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Data *</label>
                            <input
                                type="date"
                                value={holidayForm.date}
                                onChange={e => setHolidayForm({ ...holidayForm, date: e.target.value })}
                                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Nome Festività *</label>
                            <input
                                type="text"
                                value={holidayForm.name}
                                onChange={e => setHolidayForm({ ...holidayForm, name: e.target.value })}
                                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                placeholder="es. Santo Patrono"
                            />
                        </div>
                        <div className="space-y-3">
                            <label className="block text-sm font-medium text-gray-700">Tipo</label>
                            <div className="space-y-2">
                                {[
                                    { value: 'national', label: '🇮🇹 Festività Nazionale' },
                                    { value: 'regional', label: '🏛️ Festività Regionale' },
                                    { value: 'local', label: '🏘️ Festività Locale/Aziendale' },
                                ].map(option => (
                                    <label key={option.value} className="flex items-center gap-3 cursor-pointer">
                                        <input
                                            type="radio"
                                            name="holidayType"
                                            checked={holidayForm.scope === option.value || (option.value === 'local' && holidayForm.scope === 'company')}
                                            onChange={() => setHolidayForm({ ...holidayForm, scope: option.value as HolidayForm['scope'] })}
                                            className="border-gray-300 text-indigo-600"
                                        />
                                        <span className="text-sm">{option.label}</span>
                                    </label>
                                ))}
                            </div>
                        </div>
                    </div>
                    <div className="flex justify-end gap-3 p-4 bg-gray-50 border-t border-gray-100">
                        <button
                            className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                            onClick={() => setShowHolidayModal(false)}
                        >
                            Annulla
                        </button>
                        <button
                            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                            onClick={onSaveHoliday}
                            disabled={isSavingHoliday || !holidayForm.date || !holidayForm.name}
                        >
                            {isSavingHoliday && <Loader size={16} className="animate-spin" />}
                            {editingHoliday ? 'Salva Modifiche' : 'Crea Festività'}
                        </button>
                    </div>
                </ModalWrapper>
            )}

            {/* Closure Modal */}
            {showClosureModal && (
                <ModalWrapper onClose={() => setShowClosureModal(false)} maxWidth="max-w-xl">
                    <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50">
                        <h3 className="font-bold text-gray-900">
                            {editingClosure ? 'Modifica Chiusura' : 'Pianifica Chiusura'}
                        </h3>
                        <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowClosureModal(false)}>
                            <X size={20} />
                        </button>
                    </div>
                    <div className="p-6 space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
                            <input
                                type="text"
                                value={closureForm.name}
                                onChange={e => setClosureForm({ ...closureForm, name: e.target.value })}
                                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                placeholder="es. Ponte 2 Giugno"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
                            <textarea
                                value={closureForm.description}
                                onChange={e => setClosureForm({ ...closureForm, description: e.target.value })}
                                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                rows={2}
                                placeholder="Motivazione opzionale..."
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Data Inizio *</label>
                                <input
                                    type="date"
                                    value={closureForm.start_date}
                                    onChange={e => setClosureForm({ ...closureForm, start_date: e.target.value })}
                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Data Fine *</label>
                                <input
                                    type="date"
                                    value={closureForm.end_date}
                                    onChange={e => setClosureForm({ ...closureForm, end_date: e.target.value })}
                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Tipo di Chiusura</label>
                            <div className="flex gap-4">
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="radio"
                                        checked={closureForm.closure_type === 'total'}
                                        onChange={() => setClosureForm({ ...closureForm, closure_type: 'total' })}
                                        className="border-gray-300 text-indigo-600"
                                    />
                                    <span className="text-sm">Totale</span>
                                </label>
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="radio"
                                        checked={closureForm.closure_type === 'partial'}
                                        onChange={() => setClosureForm({ ...closureForm, closure_type: 'partial' })}
                                        className="border-gray-300 text-indigo-600"
                                    />
                                    <span className="text-sm">Parziale</span>
                                </label>
                            </div>
                        </div>
                        <div className="space-y-3 pt-2">
                            <label className="flex items-center gap-3 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={closureForm.is_paid}
                                    onChange={e => setClosureForm({ ...closureForm, is_paid: e.target.checked })}
                                    className="rounded border-gray-300 text-indigo-600"
                                />
                                <span className="text-sm">Chiusura pagata dall'azienda</span>
                            </label>
                            <label className="flex items-center gap-3 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={closureForm.consumes_leave_balance}
                                    onChange={e => setClosureForm({ ...closureForm, consumes_leave_balance: e.target.checked })}
                                    className="rounded border-gray-300 text-indigo-600"
                                />
                                <span className="text-sm">Scala dal monte ferie</span>
                            </label>
                        </div>
                    </div>
                    <div className="flex justify-end gap-3 p-4 bg-gray-50 border-t border-gray-100">
                        <button
                            className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                            onClick={() => setShowClosureModal(false)}
                        >
                            Annulla
                        </button>
                        <button
                            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                            onClick={onSaveClosure}
                            disabled={isSavingClosure || !closureForm.name || !closureForm.start_date || !closureForm.end_date}
                        >
                            {isSavingClosure && <Loader size={16} className="animate-spin" />}
                            {editingClosure ? 'Salva Modifiche' : 'Pianifica'}
                        </button>
                    </div>
                </ModalWrapper>
            )}

            {/* Exception Modal */}
            {showExceptionModal && (
                <ModalWrapper onClose={() => setShowExceptionModal(false)}>
                    <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50">
                        <h3 className="font-bold text-gray-900">Nuova Eccezione</h3>
                        <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowExceptionModal(false)}>
                            <X size={20} />
                        </button>
                    </div>
                    <div className="p-6 space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Data *</label>
                            <input
                                type="date"
                                value={exceptionForm.date}
                                onChange={e => setExceptionForm({ ...exceptionForm, date: e.target.value })}
                                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Motivazione</label>
                            <input
                                type="text"
                                value={exceptionForm.reason}
                                onChange={e => setExceptionForm({ ...exceptionForm, reason: e.target.value })}
                                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                placeholder="es. Recupero festività lavorata"
                            />
                        </div>
                    </div>
                    <div className="flex justify-end gap-3 p-4 bg-gray-50 border-t border-gray-100">
                        <button
                            className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                            onClick={() => setShowExceptionModal(false)}
                        >
                            Annulla
                        </button>
                        <button
                            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                            onClick={onSaveException}
                            disabled={isSavingException || !exceptionForm.date}
                        >
                            {isSavingException && <Loader size={16} className="animate-spin" />}
                            Salva Eccezione
                        </button>
                    </div>
                </ModalWrapper>
            )}

            {/* Sync Modal */}
            {showSyncModal && (
                <ModalWrapper onClose={() => setShowSyncModal(false)} maxWidth="max-w-lg">
                    <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50">
                        <h3 className="font-bold text-gray-900 flex items-center gap-2">
                            <Link size={18} className="text-indigo-500" />
                            Link di Sincronizzazione
                        </h3>
                        <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowSyncModal(false)}>
                            <X size={20} />
                        </button>
                    </div>
                    <div className="p-6 space-y-4">
                        <p className="text-sm text-gray-500">
                            Usa questi link per sincronizzare automaticamente il calendario con Google Calendar, Outlook o altre applicazioni.
                        </p>
                        {subscriptionUrls ? (
                            <div className="space-y-3">
                                {Object.entries(subscriptionUrls).map(([key, value]) => (
                                    <div key={key} className="bg-gray-50 rounded-xl p-4 border border-gray-100">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-sm font-bold text-gray-900 capitalize flex items-center gap-2">
                                                <Calendar size={14} className="text-indigo-500" />
                                                {value.description}
                                            </span>
                                            <button
                                                onClick={() => onCopyToClipboard(value.url)}
                                                className="text-xs text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-1"
                                            >
                                                <Download size={12} />
                                                Copia
                                            </button>
                                        </div>
                                        <code className="text-xs text-gray-500 break-all block">{value.url}</code>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="py-8 text-center">
                                <Loader size={24} className="animate-spin text-indigo-500 mx-auto" />
                                <p className="text-sm text-gray-400 mt-2">Caricamento URL...</p>
                            </div>
                        )}
                    </div>
                    <div className="flex justify-end p-4 bg-gray-50 border-t border-gray-100">
                        <button
                            className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                            onClick={() => setShowSyncModal(false)}
                        >
                            Chiudi
                        </button>
                    </div>
                </ModalWrapper>
            )}

            {/* Delete Confirm Modal */}
            <ConfirmModal
                isOpen={deleteConfirm !== null}
                onClose={() => setDeleteConfirm(null)}
                onConfirm={onConfirmDelete}
                title="Conferma Eliminazione"
                message={`Sei sicuro di voler eliminare questo elemento? L'azione è irreversibile.`}
                confirmLabel="Elimina"
                variant="danger"
            />

            {/* Copy Confirm Modal */}
            <ConfirmModal
                isOpen={showCopyConfirm}
                onClose={() => setShowCopyConfirm(false)}
                onConfirm={onConfirmCopy}
                title="Copia Festività"
                message={`Vuoi copiare tutte le festività dal ${year - 1} al ${year}?`}
                confirmLabel={isGenerating ? 'Copia in corso...' : 'Copia'}
                variant="info"
            />
        </>
    );
}

// Helper component for modal wrapper
function ModalWrapper({
    children,
    onClose,
    maxWidth = 'max-w-lg',
}: {
    children: React.ReactNode;
    onClose: () => void;
    maxWidth?: string;
}) {
    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn"
            onClick={onClose}
        >
            <div
                className={`bg-white rounded-xl shadow-2xl w-full ${maxWidth} overflow-hidden animate-scaleIn`}
                onClick={e => e.stopPropagation()}
            >
                {children}
            </div>
        </div>
    );
}
