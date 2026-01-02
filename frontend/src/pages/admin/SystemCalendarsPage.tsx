/**
 * KRONOS - Holidays & Closures Management Page
 * Enterprise admin page for managing holidays (national, regional, local) and company closures
 * 
 * Now uses the Calendar microservice API instead of config-service
 */
import { useState, useEffect } from 'react';
import {
    Calendar,
    Flag,
    Building,
    MapPin,
    Plus,
    Edit,
    Trash2,
    Check,
    X,
    Loader,
    ChevronLeft,
    ChevronRight,
    Copy,
    AlertCircle,
    Sparkles,
    Download,
    Link,
} from 'lucide-react';
import { format, parseISO, differenceInDays } from 'date-fns';
import { it } from 'date-fns/locale';
import { useToast } from '../../context/ToastContext';
import { ConfirmModal } from '../../components/common';
import { calendarService } from '../../services/calendar.service';
import type { Holiday, Closure, WorkingDayException } from '../../services/calendar.service';

type TabType = 'holidays' | 'closures' | 'exceptions';
type HolidayFilter = 'all' | 'national' | 'local';


export function SystemCalendarsPage() {
    const toast = useToast();
    const [activeTab, setActiveTab] = useState<TabType>('holidays');
    const [year, setYear] = useState(new Date().getFullYear());
    const [holidays, setHolidays] = useState<Holiday[]>([]);
    const [closures, setClosures] = useState<Closure[]>([]);
    const [exceptions, setExceptions] = useState<WorkingDayException[]>([]);
    const [loading, setLoading] = useState(true);
    const [holidayFilter, setHolidayFilter] = useState<HolidayFilter>('all');

    // Modal states
    const [showHolidayModal, setShowHolidayModal] = useState(false);
    const [showClosureModal, setShowClosureModal] = useState(false);
    const [showExceptionModal, setShowExceptionModal] = useState(false);
    const [showSyncModal, setShowSyncModal] = useState(false);
    const [subscriptionUrls, setSubscriptionUrls] = useState<{
        holidays: { url: string; description: string };
        closures: { url: string; description: string };
        combined: { url: string; description: string };
    } | null>(null);
    const [editingHoliday, setEditingHoliday] = useState<Holiday | null>(null);
    const [editingClosure, setEditingClosure] = useState<Closure | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);

    // Confirm states
    const [deleteConfirm, setDeleteConfirm] = useState<{ type: 'holiday' | 'closure' | 'exception', id: string } | null>(null);
    const [showCopyConfirm, setShowCopyConfirm] = useState(false);

    // Holiday form
    const [holidayForm, setHolidayForm] = useState({
        date: '',
        name: '',
        scope: 'national' as 'national' | 'regional' | 'local' | 'company',
    });

    // Closure form
    const [closureForm, setClosureForm] = useState({
        name: '',
        description: '',
        start_date: '',
        end_date: '',
        closure_type: 'total' as 'total' | 'partial',
        is_paid: true,
        consumes_leave_balance: false,
    });

    // Exception form
    const [exceptionForm, setExceptionForm] = useState({
        date: '',
        exception_type: 'working' as 'working' | 'non_working',
        reason: '',
    });


    useEffect(() => {
        loadData();
    }, [year]);

    const loadData = async () => {
        setLoading(true);
        try {
            const [holidaysData, closuresData, exceptionsData] = await Promise.all([
                calendarService.getHolidays({ year }),
                calendarService.getClosures({ year }),
                calendarService.getWorkingDayExceptions(year),
            ]);
            setHolidays(holidaysData || []);
            setClosures(closuresData || []);
            setExceptions(exceptionsData || []);
        } catch (error) {
            console.error('Failed to load data:', error);
            toast.error('Errore nel caricamento dei dati');
        } finally {
            setLoading(false);
        }
    };

    const generateNationalHolidays = async () => {
        setIsGenerating(true);
        try {
            const created = await calendarService.generateHolidaysForYear(year);
            toast.success(`${created.length} festività nazionali ${year} generate con successo`);
            loadData();
        } catch (error: unknown) {
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(err.response?.data?.detail || 'Errore nella generazione');
        } finally {
            setIsGenerating(false);
        }
    };

    const handleCopyRequest = () => {
        setShowCopyConfirm(true);
    };

    const performCopyHolidays = async () => {
        setIsGenerating(true);
        try {
            const copied = await calendarService.copyHolidaysFromYear(year - 1, year);
            toast.success(`${copied} festività copiate dal ${year - 1}`);
            loadData();
        } catch {
            toast.error('Errore nella copia');
        } finally {
            setIsGenerating(false);
            setShowCopyConfirm(false);
        }
    };

    const confirmHoliday = async (holiday: Holiday) => {
        try {
            await calendarService.updateHoliday(holiday.id, { is_confirmed: true });
            toast.success('Festività confermata');
            loadData();
        } catch {
            toast.error('Errore nella conferma');
        }
    };

    const handleSaveHoliday = async () => {
        setIsSaving(true);
        try {
            if (editingHoliday) {
                await calendarService.updateHoliday(editingHoliday.id, {
                    date: holidayForm.date,
                    name: holidayForm.name,
                    scope: holidayForm.scope,
                });
                toast.success('Festività aggiornata');
            } else {
                await calendarService.createHoliday({
                    date: holidayForm.date,
                    name: holidayForm.name,
                    year,
                    scope: holidayForm.scope,
                });
                toast.success('Festività aggiunta');
            }
            setShowHolidayModal(false);
            setEditingHoliday(null);
            loadData();
        } catch (error: unknown) {
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(err.response?.data?.detail || 'Errore');
        } finally {
            setIsSaving(false);
        }
    };

    const handleSaveClosure = async () => {
        setIsSaving(true);
        try {
            if (editingClosure) {
                await calendarService.updateClosure(editingClosure.id, closureForm);
                toast.success('Chiusura aggiornata');
            } else {
                await calendarService.createClosure({
                    ...closureForm,
                    year,
                });
                toast.success('Chiusura pianificata');
            }
            setShowClosureModal(false);
            setEditingClosure(null);
            loadData();
        } catch (error: unknown) {
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(err.response?.data?.detail || 'Errore');
        } finally {
            setIsSaving(false);
        }
    };

    const handleSaveException = async () => {
        setIsSaving(true);
        try {
            await calendarService.createWorkingDayException({
                ...exceptionForm,
                year,
            });
            toast.success('Eccezione salvata');
            setShowExceptionModal(false);
            loadData();
        } catch (error: unknown) {
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(err.response?.data?.detail || 'Errore');
        } finally {
            setIsSaving(false);
        }
    };


    const handleDeleteRequest = (id: string, type: 'holiday' | 'closure' | 'exception') => {
        setDeleteConfirm({ type, id });
    };

    const performDelete = async () => {
        if (!deleteConfirm) return;
        try {
            if (deleteConfirm.type === 'holiday') {
                await calendarService.deleteHoliday(deleteConfirm.id);
                toast.success('Festività eliminata');
            } else if (deleteConfirm.type === 'closure') {
                await calendarService.deleteClosure(deleteConfirm.id);
                toast.success('Chiusura eliminata');
            } else {
                await calendarService.deleteWorkingDayException(deleteConfirm.id);
                toast.success('Eccezione eliminata');
            }
            loadData();
        } catch {
            toast.error('Errore');
        } finally {
            setDeleteConfirm(null);
        }
    };

    const openNewHoliday = () => {
        setEditingHoliday(null);
        setHolidayForm({ date: '', name: '', scope: 'national' });
        setShowHolidayModal(true);
    };

    const openEditHoliday = (holiday: Holiday) => {
        setEditingHoliday(holiday);
        setHolidayForm({
            date: holiday.date,
            name: holiday.name,
            scope: holiday.scope,
        });
        setShowHolidayModal(true);
    };

    const openNewClosure = () => {
        setEditingClosure(null);
        setClosureForm({
            name: '',
            description: '',
            start_date: '',
            end_date: '',
            closure_type: 'total',
            is_paid: true,
            consumes_leave_balance: false,
        });
        setShowClosureModal(true);
    };

    const openEditClosure = (closure: Closure) => {
        setEditingClosure(closure);
        setClosureForm({
            name: closure.name,
            description: closure.description || '',
            start_date: closure.start_date,
            end_date: closure.end_date,
            closure_type: closure.closure_type,
            is_paid: closure.is_paid,
            consumes_leave_balance: closure.consumes_leave_balance,
        });
        setShowClosureModal(true);
    };

    const openNewException = () => {
        setExceptionForm({
            date: '',
            exception_type: 'working',
            reason: '',
        });
        setShowExceptionModal(true);
    };


    const handleOpenSyncModal = async () => {
        setShowSyncModal(true);
        if (!subscriptionUrls) {
            try {
                const urls = await calendarService.getSubscriptionUrls(year);
                setSubscriptionUrls(urls);
            } catch (error) {
                console.error("Failed to load subscription urls", error);
                toast.error("Impossibile caricare gli URL di sincronizzazione");
            }
        }
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        toast.success("Link copiato negli appunti!");
    };



    const filteredHolidays = holidays.filter(h => {
        if (holidayFilter === 'all') return true;
        if (holidayFilter === 'national') return h.scope === 'national';
        if (holidayFilter === 'local') return h.scope !== 'national';
        return true;
    }).sort((a, b) => a.date.localeCompare(b.date));

    const unconfirmedCount = holidays.filter(h => !h.is_confirmed).length;

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px]">
                <Loader size={40} className="text-indigo-600 animate-spin mb-4" />
                <p className="text-gray-500 font-medium">Caricamento calendario...</p>
            </div>
        );
    }

    return (
        <div className="space-y-6 max-w-[1400px] mx-auto pb-8 animate-fadeIn">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200 pb-6">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Calendar className="text-indigo-600" size={24} />
                        Calendari di Sistema
                    </h1>
                    <p className="text-sm text-gray-500 mt-1">
                        Gestisci festività (nazionali, regionali, locali) e chiusure aziendali
                    </p>
                </div>

                {/* Year Selector */}
                <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-xl px-2 py-1 shadow-sm">
                    <button
                        onClick={() => setYear(y => y - 1)}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <ChevronLeft size={18} />
                    </button>
                    <span className="px-4 py-1 font-bold text-lg text-gray-900 min-w-[80px] text-center">{year}</span>
                    <button
                        onClick={() => setYear(y => y + 1)}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <ChevronRight size={18} />
                    </button>
                </div>

                {/* Export Dropdown */}
                <div className="relative group">
                    <button
                        className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 text-sm font-medium rounded-lg transition-colors shadow-sm"
                    >
                        <Download size={16} />
                        Esporta iCal
                    </button>
                    <div className="absolute right-0 mt-2 w-72 bg-white border border-gray-200 rounded-xl shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                        <div className="p-3 border-b border-gray-100">
                            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Sincronizza con Calendar</p>
                        </div>
                        <div className="p-2 space-y-1">
                            <button
                                onClick={() => calendarService.downloadHolidaysIcs(year)}
                                className="w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-700 hover:bg-indigo-50 hover:text-indigo-700 rounded-lg transition-colors text-left"
                            >
                                <Flag size={16} className="text-red-500" />
                                <div>
                                    <div className="font-medium">Festività {year}</div>
                                    <div className="text-xs text-gray-400">Scarica file .ics</div>
                                </div>
                            </button>
                            <button
                                onClick={() => calendarService.downloadClosuresIcs(year)}
                                className="w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-700 hover:bg-indigo-50 hover:text-indigo-700 rounded-lg transition-colors text-left"
                            >
                                <Building size={16} className="text-purple-500" />
                                <div>
                                    <div className="font-medium">Chiusure {year}</div>
                                    <div className="text-xs text-gray-400">Scarica file .ics</div>
                                </div>
                            </button>
                            <button
                                onClick={() => calendarService.downloadCombinedIcs(year)}
                                className="w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-700 hover:bg-indigo-50 hover:text-indigo-700 rounded-lg transition-colors text-left"
                            >
                                <Calendar size={16} className="text-indigo-500" />
                                <div>
                                    <div className="font-medium">Calendario Completo {year}</div>
                                    <div className="text-xs text-gray-400">Festività + Chiusure</div>
                                </div>
                            </button>
                        </div>
                        <div className="p-3 border-t border-gray-100 bg-gray-50/50 rounded-b-xl">
                            <button
                                onClick={handleOpenSyncModal}
                                className="w-full flex items-center gap-2 text-xs text-indigo-600 hover:text-indigo-700 font-medium transition-colors"
                            >
                                <Link size={12} />
                                <span>Ottieni link di sincronizzazione</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 border-b border-gray-200">
                <button
                    onClick={() => setActiveTab('holidays')}
                    className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors ${activeTab === 'holidays'
                        ? 'border-indigo-600 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-900'
                        }`}
                >
                    <div className="flex items-center gap-2">
                        <Flag size={16} />
                        Festività
                        <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">{holidays.length}</span>
                        {unconfirmedCount > 0 && (
                            <span className="px-2 py-0.5 rounded-full text-xs bg-amber-100 text-amber-700">{unconfirmedCount} da confermare</span>
                        )}
                    </div>
                </button>
                <button
                    onClick={() => setActiveTab('closures')}
                    className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors ${activeTab === 'closures'
                        ? 'border-indigo-600 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-900'
                        }`}
                >
                    <div className="flex items-center gap-2">
                        <Building size={16} />
                        Chiusure Aziendali
                        <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">{closures.length}</span>
                    </div>
                </button>
                <button
                    onClick={() => setActiveTab('exceptions')}
                    className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors ${activeTab === 'exceptions'
                        ? 'border-indigo-600 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-900'
                        }`}
                >
                    <div className="flex items-center gap-2">
                        <AlertCircle size={16} />
                        Eccezioni Lavorative
                        <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">{exceptions.length}</span>
                    </div>
                </button>
            </div>


            {/* Holidays Tab */}
            {
                activeTab === 'holidays' && (
                    <div className="space-y-4">
                        {/* Actions Bar */}
                        <div className="flex flex-wrap gap-3 p-4 bg-gray-50 rounded-xl border border-gray-100">
                            <button
                                onClick={generateNationalHolidays}
                                disabled={isGenerating}
                                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                title="Ripristina le festività nazionali ufficiali (mantiene le locali esistenti)"
                            >
                                {isGenerating ? <Loader size={16} className="animate-spin" /> : <Sparkles size={16} />}
                                Rigenera Festività Nazionali
                            </button>
                            <button
                                onClick={handleCopyRequest}
                                disabled={isGenerating}
                                className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                title={`Copia tutte le festività dal ${year - 1} al ${year}`}
                            >
                                <Copy size={16} />
                                Copia da anno precedente
                            </button>
                            <div className="flex-1" />
                            <button
                                onClick={openNewHoliday}
                                className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg transition-colors"
                            >
                                <Plus size={16} />
                                Aggiungi Festività
                            </button>
                        </div>

                        {/* Filters */}
                        <div className="flex gap-2">
                            {(['all', 'national', 'local'] as HolidayFilter[]).map(filter => (
                                <button
                                    key={filter}
                                    onClick={() => setHolidayFilter(filter)}
                                    className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${holidayFilter === filter
                                        ? 'bg-indigo-100 text-indigo-700 font-medium'
                                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                        }`}
                                >
                                    {filter === 'all' && 'Tutte'}
                                    {filter === 'national' && '🇮🇹 Nazionali'}
                                    {filter === 'local' && '📍 Locali'}
                                </button>
                            ))}
                        </div>

                        {/* Holidays List */}
                        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                            <div className="divide-y divide-gray-100">
                                {filteredHolidays.map(holiday => (
                                    <div key={holiday.id} className="flex items-center gap-4 px-5 py-4 hover:bg-gray-50 transition-colors">
                                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${holiday.scope === 'national'
                                            ? 'bg-red-100 text-red-600'
                                            : 'bg-orange-100 text-orange-600'
                                            }`}>
                                            {holiday.scope === 'national' ? <Flag size={20} /> : <MapPin size={20} />}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2">
                                                <span className="font-semibold text-gray-900">{holiday.name}</span>
                                                {holiday.scope === 'national' && <span className="px-2 py-0.5 text-xs bg-red-100 text-red-700 rounded">Nazionale</span>}
                                                {holiday.scope === 'regional' && <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">Regionale</span>}
                                                {(holiday.scope === 'local' || holiday.scope === 'company') && <span className="px-2 py-0.5 text-xs bg-orange-100 text-orange-700 rounded">Locale</span>}
                                                {!holiday.is_confirmed && (
                                                    <span className="px-2 py-0.5 text-xs bg-amber-100 text-amber-700 rounded flex items-center gap-1">
                                                        <AlertCircle size={10} />
                                                        Da confermare
                                                    </span>
                                                )}
                                            </div>
                                            <div className="text-sm text-gray-500 mt-0.5">
                                                {format(parseISO(holiday.date), 'EEEE d MMMM yyyy', { locale: it })}
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {!holiday.is_confirmed && (
                                                <button
                                                    onClick={() => confirmHoliday(holiday)}
                                                    className="p-2 text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                                                    title="Conferma"
                                                >
                                                    <Check size={16} />
                                                </button>
                                            )}
                                            <button
                                                onClick={() => openEditHoliday(holiday)}
                                                className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                                            >
                                                <Edit size={16} />
                                            </button>
                                            <button
                                                onClick={() => handleDeleteRequest(holiday.id, 'holiday')}
                                                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </div>
                                ))}

                                {filteredHolidays.length === 0 && (
                                    <div className="text-center py-12 text-gray-400">
                                        <Calendar size={48} className="mx-auto mb-4 opacity-50" />
                                        <p className="font-medium">Nessuna festività per il {year}</p>
                                        <p className="text-sm mt-1">Genera le festività nazionali o aggiungile manualmente.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )
            }

            {/* Closures Tab */}
            {
                activeTab === 'closures' && (
                    <div className="space-y-4">
                        {/* Actions Bar */}
                        <div className="flex justify-between items-center">
                            <p className="text-sm text-gray-500">
                                Pianifica le chiusure aziendali (es. ferie collettive, ponti, etc.)
                            </p>
                            <button
                                onClick={openNewClosure}
                                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors"
                            >
                                <Plus size={16} />
                                Nuova Chiusura
                            </button>
                        </div>

                        {/* Closures List */}
                        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                            <div className="divide-y divide-gray-100">
                                {closures.map(closure => {
                                    const days = differenceInDays(parseISO(closure.end_date), parseISO(closure.start_date)) + 1;
                                    return (
                                        <div key={closure.id} className="flex items-center gap-4 px-5 py-4 hover:bg-gray-50 transition-colors">
                                            <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${closure.closure_type === 'total' ? 'bg-purple-100 text-purple-600' : 'bg-violet-100 text-violet-600'
                                                }`}>
                                                <Building size={20} />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-semibold text-gray-900">{closure.name}</span>
                                                    <span className={`px-2 py-0.5 text-xs rounded ${closure.closure_type === 'total'
                                                        ? 'bg-purple-100 text-purple-700'
                                                        : 'bg-violet-100 text-violet-700'
                                                        }`}>
                                                        {closure.closure_type === 'total' ? 'Chiusura totale' : 'Parziale'}
                                                    </span>
                                                    {closure.is_paid && <span className="px-2 py-0.5 text-xs bg-emerald-100 text-emerald-700 rounded">Retribuita</span>}
                                                    {closure.consumes_leave_balance && <span className="px-2 py-0.5 text-xs bg-amber-100 text-amber-700 rounded">Scala ferie</span>}
                                                </div>
                                                <div className="text-sm text-gray-500 mt-0.5">
                                                    {format(parseISO(closure.start_date), 'd MMM', { locale: it })} - {format(parseISO(closure.end_date), 'd MMM yyyy', { locale: it })}
                                                    <span className="ml-2 text-gray-400">({days} {days === 1 ? 'giorno' : 'giorni'})</span>
                                                </div>
                                                {closure.description && (
                                                    <div className="text-xs text-gray-400 mt-1">{closure.description}</div>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <button
                                                    onClick={() => openEditClosure(closure)}
                                                    className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                                                >
                                                    <Edit size={16} />
                                                </button>
                                                <button
                                                    onClick={() => handleDeleteRequest(closure.id, 'closure')}
                                                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        </div>
                                    );
                                })}

                                {closures.length === 0 && (
                                    <div className="text-center py-12 text-gray-400">
                                        <Building size={48} className="mx-auto mb-4 opacity-50" />
                                        <p className="font-medium">Nessuna chiusura pianificata per il {year}</p>
                                        <p className="text-sm mt-1">Pianifica le chiusure aziendali per questo anno.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )
            }

            {/* Exceptions Tab */}
            {
                activeTab === 'exceptions' && (
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <p className="text-sm text-gray-500">
                                Gestisci giorni lavorativi straordinari o festivi lavorati (es. sabati di recupero o festività lavorate)
                            </p>
                            <button
                                onClick={openNewException}
                                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors"
                            >
                                <Plus size={16} />
                                Nuova Eccezione
                            </button>
                        </div>

                        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                            <div className="divide-y divide-gray-100">
                                {exceptions.map(exception => (
                                    <div key={exception.id} className="flex items-center gap-4 px-5 py-4 hover:bg-gray-50 transition-colors">
                                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${exception.exception_type === 'working' ? 'bg-emerald-100 text-emerald-600' : 'bg-red-100 text-red-600'
                                            }`}>
                                            <AlertCircle size={20} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2">
                                                <span className="font-semibold text-gray-900">
                                                    {format(parseISO(exception.date), 'EEEE d MMMM yyyy', { locale: it })}
                                                </span>
                                                <span className={`px-2 py-0.5 text-xs rounded ${exception.exception_type === 'working' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                                                    }`}>
                                                    {exception.exception_type === 'working' ? 'Lavorativo' : 'Non lavorativo'}
                                                </span>
                                            </div>
                                            {exception.reason && (
                                                <div className="text-sm text-gray-500 mt-1">{exception.reason}</div>
                                            )}
                                        </div>
                                        <button
                                            onClick={() => handleDeleteRequest(exception.id, 'exception')}
                                            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                ))}

                                {exceptions.length === 0 && (
                                    <div className="text-center py-12 text-gray-400">
                                        <AlertCircle size={48} className="mx-auto mb-4 opacity-50" />
                                        <p className="font-medium">Nessuna eccezione pianificata per il {year}</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )
            }


            {/* Holiday Modal */}
            {
                showHolidayModal && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn" onClick={() => setShowHolidayModal(false)}>
                        <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-scaleIn" onClick={e => e.stopPropagation()}>
                            <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50">
                                <h3 className="font-bold text-gray-900">{editingHoliday ? 'Modifica Festività' : 'Nuova Festività'}</h3>
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
                                        <label className="flex items-center gap-3 cursor-pointer">
                                            <input
                                                type="radio"
                                                name="holidayType"
                                                checked={holidayForm.scope === 'national'}
                                                onChange={() => setHolidayForm({ ...holidayForm, scope: 'national' })}
                                                className="border-gray-300 text-indigo-600"
                                            />
                                            <span className="text-sm">🇮🇹 Festività Nazionale</span>
                                        </label>
                                        <label className="flex items-center gap-3 cursor-pointer">
                                            <input
                                                type="radio"
                                                name="holidayType"
                                                checked={holidayForm.scope === 'regional'}
                                                onChange={() => setHolidayForm({ ...holidayForm, scope: 'regional' })}
                                                className="border-gray-300 text-indigo-600"
                                            />
                                            <span className="text-sm">🏛️ Festività Regionale</span>
                                        </label>
                                        <label className="flex items-center gap-3 cursor-pointer">
                                            <input
                                                type="radio"
                                                name="holidayType"
                                                checked={holidayForm.scope === 'local' || holidayForm.scope === 'company'}
                                                onChange={() => setHolidayForm({ ...holidayForm, scope: 'local' })}
                                                className="border-gray-300 text-indigo-600"
                                            />
                                            <span className="text-sm">📍 Festività Locale (es. Santo Patrono)</span>
                                        </label>
                                    </div>
                                </div>
                            </div>
                            <div className="flex justify-end gap-3 p-4 bg-gray-50 border-t border-gray-100">
                                <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors" onClick={() => setShowHolidayModal(false)}>
                                    Annulla
                                </button>
                                <button
                                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                    onClick={handleSaveHoliday}
                                    disabled={isSaving || !holidayForm.date || !holidayForm.name}
                                >
                                    {isSaving ? <Loader size={16} className="animate-spin" /> : <Check size={16} />}
                                    Salva
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }

            {/* Closure Modal */}
            {
                showClosureModal && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn" onClick={() => setShowClosureModal(false)}>
                        <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-scaleIn" onClick={e => e.stopPropagation()}>
                            <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50">
                                <h3 className="font-bold text-gray-900">{editingClosure ? 'Modifica Chiusura' : 'Nuova Chiusura Aziendale'}</h3>
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
                                        placeholder="es. Ferie Estive Collettive"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
                                    <textarea
                                        value={closureForm.description}
                                        onChange={e => setClosureForm({ ...closureForm, description: e.target.value })}
                                        className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 min-h-[60px]"
                                        placeholder="Note aggiuntive..."
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
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Tipo Chiusura</label>
                                    <div className="flex gap-4">
                                        <label className="flex items-center gap-2 cursor-pointer">
                                            <input
                                                type="radio"
                                                checked={closureForm.closure_type === 'total'}
                                                onChange={() => setClosureForm({ ...closureForm, closure_type: 'total' })}
                                                className="border-gray-300 text-indigo-600"
                                            />
                                            <span className="text-sm">Chiusura Totale</span>
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
                                <div className="space-y-3 pt-2 border-t border-gray-100">
                                    <label className="flex items-center gap-3 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={closureForm.is_paid}
                                            onChange={e => {
                                                const checked = e.target.checked;
                                                setClosureForm({
                                                    ...closureForm,
                                                    is_paid: checked,
                                                    consumes_leave_balance: checked ? false : closureForm.consumes_leave_balance
                                                });
                                            }}
                                            className="rounded border-gray-300 text-indigo-600"
                                        />
                                        <span className="text-sm text-gray-700">Giorni retribuiti dall'azienda</span>
                                    </label>
                                    <label className="flex items-center gap-3 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={closureForm.consumes_leave_balance}
                                            onChange={e => {
                                                const checked = e.target.checked;
                                                setClosureForm({
                                                    ...closureForm,
                                                    consumes_leave_balance: checked,
                                                    is_paid: checked ? false : closureForm.is_paid
                                                });
                                            }}
                                            className="rounded border-gray-300 text-indigo-600"
                                        />
                                        <span className="text-sm text-gray-700">Scala dal saldo ferie dipendenti</span>
                                    </label>
                                </div>
                            </div>
                            <div className="flex justify-end gap-3 p-4 bg-gray-50 border-t border-gray-100">
                                <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors" onClick={() => setShowClosureModal(false)}>
                                    Annulla
                                </button>
                                <button
                                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                    onClick={handleSaveClosure}
                                    disabled={isSaving || !closureForm.name || !closureForm.start_date || !closureForm.end_date}
                                >
                                    {isSaving ? <Loader size={16} className="animate-spin" /> : <Check size={16} />}
                                    Salva
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }

            {/* Sync Modal */}
            {
                showSyncModal && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn" onClick={() => setShowSyncModal(false)}>
                        <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden animate-scaleIn" onClick={e => e.stopPropagation()}>
                            <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50">
                                <h3 className="font-bold text-gray-900 flex items-center gap-2">
                                    <Sparkles size={18} className="text-indigo-600" />
                                    Sincronizza Calendario
                                </h3>
                                <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowSyncModal(false)}>
                                    <X size={20} />
                                </button>
                            </div>
                            <div className="p-6 space-y-6">
                                <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-4 text-sm text-indigo-800">
                                    <p className="font-medium mb-1">Come funziona?</p>
                                    <p>Copia i link sottostanti e incollali nel tuo calendario (Google Calendar, Outlook, Apple Calendar) usando la funzione <strong>"Aggiungi calendario da URL"</strong>. Gli eventi verranno aggiornati automaticamente.</p>
                                </div>

                                {!subscriptionUrls ? (
                                    <div className="flex justify-center py-8">
                                        <Loader size={32} className="animate-spin text-indigo-600" />
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {[
                                            { key: 'combined', label: 'Calendario Completo (Consigliato)', icon: <Calendar size={18} className="text-indigo-600" />, desc: 'Include tutte le festività e le chiusure aziendali.' },
                                            { key: 'holidays', label: 'Solo Festività', icon: <Flag size={18} className="text-red-500" />, desc: 'Solo le festività nazionali e locali.' },
                                            { key: 'closures', label: 'Solo Chiusure', icon: <Building size={18} className="text-purple-500" />, desc: 'Solo le chiusure aziendali pianificate.' }
                                        ].map((item) => {
                                            // @ts-ignore
                                            const data = (subscriptionUrls as any)[item.key];
                                            if (!data) return null;
                                            return (
                                                <div key={item.key} className="border border-gray-200 rounded-xl p-4 hover:border-indigo-300 transition-colors">
                                                    <div className="flex items-start justify-between gap-4 mb-3">
                                                        <div className="flex items-center gap-2">
                                                            <div className="p-2 bg-gray-50 rounded-lg">
                                                                {item.icon}
                                                            </div>
                                                            <div>
                                                                <h4 className="font-semibold text-gray-900">{item.label}</h4>
                                                                <p className="text-xs text-gray-500">{item.desc}</p>
                                                            </div>
                                                        </div>
                                                        <button
                                                            onClick={() => copyToClipboard(data.url)}
                                                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors"
                                                        >
                                                            <Copy size={14} />
                                                            Copia Link
                                                        </button>
                                                    </div>
                                                    <div className="relative">
                                                        <input
                                                            type="text"
                                                            readOnly
                                                            value={data.url}
                                                            className="w-full text-xs text-gray-500 bg-gray-50 border-none rounded-lg py-2 pl-3 pr-10 font-mono"
                                                        />
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                            <div className="flex justify-end p-4 bg-gray-50 border-t border-gray-100">
                                <button className="px-5 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors" onClick={() => setShowSyncModal(false)}>
                                    Chiudi
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }

            {/* Exception Modal */}
            {
                showExceptionModal && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn" onClick={() => setShowExceptionModal(false)}>
                        <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-scaleIn" onClick={e => e.stopPropagation()}>
                            <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50">
                                <h3 className="font-bold text-gray-900">Nuova Eccezione Calendario</h3>
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
                                <div className="space-y-3">
                                    <label className="block text-sm font-medium text-gray-700">Tipo Eccezione</label>
                                    <div className="flex gap-4">
                                        <label className="flex items-center gap-2 cursor-pointer">
                                            <input
                                                type="radio"
                                                checked={exceptionForm.exception_type === 'working'}
                                                onChange={() => setExceptionForm({ ...exceptionForm, exception_type: 'working' })}
                                                className="border-gray-300 text-indigo-600"
                                            />
                                            <span className="text-sm">Giorno Lavorativo (es. recupero)</span>
                                        </label>
                                        <label className="flex items-center gap-2 cursor-pointer">
                                            <input
                                                type="radio"
                                                checked={exceptionForm.exception_type === 'non_working'}
                                                onChange={() => setExceptionForm({ ...exceptionForm, exception_type: 'non_working' })}
                                                className="border-gray-300 text-indigo-600"
                                            />
                                            <span className="text-sm">Non Lavorativo (es. ponte extra)</span>
                                        </label>
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Motivazione / Note</label>
                                    <textarea
                                        value={exceptionForm.reason}
                                        onChange={e => setExceptionForm({ ...exceptionForm, reason: e.target.value })}
                                        className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 min-h-[80px]"
                                        placeholder="es. Recupero inventario sabato..."
                                    />
                                </div>
                            </div>
                            <div className="flex justify-end gap-3 p-4 bg-gray-50 border-t border-gray-100">
                                <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors" onClick={() => setShowExceptionModal(false)}>
                                    Annulla
                                </button>
                                <button
                                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                    onClick={handleSaveException}
                                    disabled={isSaving || !exceptionForm.date}
                                >
                                    {isSaving ? <Loader size={16} className="animate-spin" /> : <Check size={16} />}
                                    Salva
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }

            <ConfirmModal
                isOpen={!!deleteConfirm}
                onClose={() => setDeleteConfirm(null)}
                onConfirm={performDelete}
                title={
                    deleteConfirm?.type === 'holiday' ? "Elimina Festività" :
                        deleteConfirm?.type === 'closure' ? "Elimina Chiusura" :
                            "Elimina Eccezione"
                }
                message={
                    deleteConfirm?.type === 'holiday' ? "Sei sicuro di voler eliminare questa festività? L'azione è irreversibile." :
                        deleteConfirm?.type === 'closure' ? "Sei sicuro di voler eliminare questa chiusura? L'azione è irreversibile." :
                            "Sei sicuro di voler eliminare questa eccezione lavorativa?"
                }
                confirmLabel="Elimina"
                variant="danger"
            />


            <ConfirmModal
                isOpen={showCopyConfirm}
                onClose={() => setShowCopyConfirm(false)}
                onConfirm={performCopyHolidays}
                title="Copia Festività"
                message={`Vuoi copiare le festività dal ${year - 1} al ${year}? Le festività esistenti non saranno duplicate.`}
                confirmLabel="Copia"
                variant="info"
                isLoading={isGenerating}
            />
        </div>
    );
}

export default SystemCalendarsPage;
