/**
 * KRONOS - System Calendars Page (Refactored)
 *
 * Enterprise admin page for managing holidays, closures and exceptions.
 * Uses extracted hooks and components for better maintainability.
 */
import { useState, useCallback } from 'react';
import {
    Calendar,
    Flag,
    Building,
    MapPin,
    Loader,
    ChevronLeft,
    ChevronRight,
    Download,
    Link,
    AlertCircle,
} from 'lucide-react';
import { useToast } from '../../context/ToastContext';
import { calendarService } from '../../services/calendar.service';
import type { Holiday, Closure } from '../../services/calendar.service';
import {
    useSystemCalendars,
    useSubscriptionUrls,
    type HolidayForm,
    type ClosureForm,
    type ExceptionForm,
} from '../../hooks/domain/useSystemCalendars';
import {
    HolidaysTab,
    ClosuresTab,
    ExceptionsTab,
    SystemCalendarModals,
} from '../../components/admin/calendars';

type TabType = 'holidays' | 'closures' | 'exceptions';

export function SystemCalendarsPage() {
    const toast = useToast();
    const [year, setYear] = useState(new Date().getFullYear());
    const [activeTab, setActiveTab] = useState<TabType>('holidays');

    // Data and mutations from hook
    const {
        holidays,
        closures,
        exceptions,
        isLoading,
        createHoliday,
        updateHoliday,
        deleteHoliday,
        confirmHoliday,
        generateHolidays,
        copyHolidays,
        createClosure,
        updateClosure,
        deleteClosure,
        createException,
        deleteException,
        isGenerating,
        isSavingHoliday,
        isSavingClosure,
        isSavingException,
    } = useSystemCalendars(year);

    const { urls: subscriptionUrls, fetchUrls } = useSubscriptionUrls(year);

    // Modal states
    const [showHolidayModal, setShowHolidayModal] = useState(false);
    const [showClosureModal, setShowClosureModal] = useState(false);
    const [showExceptionModal, setShowExceptionModal] = useState(false);
    const [showSyncModal, setShowSyncModal] = useState(false);
    const [showCopyConfirm, setShowCopyConfirm] = useState(false);
    const [deleteConfirm, setDeleteConfirm] = useState<{ type: 'holiday' | 'closure' | 'exception'; id: string } | null>(null);

    // Editing states
    const [editingHoliday, setEditingHoliday] = useState<Holiday | null>(null);
    const [editingClosure, setEditingClosure] = useState<Closure | null>(null);

    // Form states
    const [holidayForm, setHolidayForm] = useState<HolidayForm>({
        date: '',
        name: '',
        scope: 'national',
    });

    const [closureForm, setClosureForm] = useState<ClosureForm>({
        name: '',
        description: '',
        start_date: '',
        end_date: '',
        closure_type: 'total',
        is_paid: true,
        consumes_leave_balance: false,
    });

    const [exceptionForm, setExceptionForm] = useState<ExceptionForm>({
        date: '',
        exception_type: 'working',
        reason: '',
    });

    // Handlers
    const openNewHoliday = useCallback(() => {
        setEditingHoliday(null);
        setHolidayForm({ date: '', name: '', scope: 'national' });
        setShowHolidayModal(true);
    }, []);

    const openEditHoliday = useCallback((holiday: Holiday) => {
        setEditingHoliday(holiday);
        setHolidayForm({
            date: holiday.date,
            name: holiday.name,
            scope: holiday.scope,
        });
        setShowHolidayModal(true);
    }, []);

    const openNewClosure = useCallback(() => {
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
    }, []);

    const openEditClosure = useCallback((closure: Closure) => {
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
    }, []);

    const openNewException = useCallback(() => {
        setExceptionForm({ date: '', exception_type: 'working', reason: '' });
        setShowExceptionModal(true);
    }, []);

    const handleSaveHoliday = useCallback(() => {
        if (editingHoliday) {
            updateHoliday({ id: editingHoliday.id, data: holidayForm });
        } else {
            createHoliday(holidayForm);
        }
        setShowHolidayModal(false);
        setEditingHoliday(null);
    }, [editingHoliday, holidayForm, createHoliday, updateHoliday]);

    const handleSaveClosure = useCallback(() => {
        if (editingClosure) {
            updateClosure({ id: editingClosure.id, data: closureForm });
        } else {
            createClosure(closureForm);
        }
        setShowClosureModal(false);
        setEditingClosure(null);
    }, [editingClosure, closureForm, createClosure, updateClosure]);

    const handleSaveException = useCallback(() => {
        createException(exceptionForm);
        setShowExceptionModal(false);
    }, [exceptionForm, createException]);

    const handleDeleteRequest = useCallback((id: string, type: 'holiday' | 'closure' | 'exception') => {
        setDeleteConfirm({ type, id });
    }, []);

    const performDelete = useCallback(() => {
        if (!deleteConfirm) return;
        if (deleteConfirm.type === 'holiday') {
            deleteHoliday(deleteConfirm.id);
        } else if (deleteConfirm.type === 'closure') {
            deleteClosure(deleteConfirm.id);
        } else {
            deleteException(deleteConfirm.id);
        }
        setDeleteConfirm(null);
    }, [deleteConfirm, deleteHoliday, deleteClosure, deleteException]);

    const handleCopyHolidays = useCallback(() => {
        copyHolidays();
        setShowCopyConfirm(false);
    }, [copyHolidays]);

    const handleOpenSyncModal = useCallback(() => {
        setShowSyncModal(true);
        fetchUrls();
    }, [fetchUrls]);

    const copyToClipboard = useCallback((text: string) => {
        navigator.clipboard.writeText(text);
        toast.success('Link copiato negli appunti!');
    }, [toast]);

    // Derived data
    const unconfirmedCount = holidays.filter(h => !h.is_confirmed).length;

    if (isLoading) {
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
                <ExportDropdown year={year} onOpenSyncModal={handleOpenSyncModal} />
            </div>

            {/* Summary Dashboard */}
            <SummaryDashboard
                holidays={holidays}
                closures={closures}
                exceptions={exceptions}
            />

            {/* Tabs */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200">
                <div className="flex gap-2">
                    <TabButton
                        active={activeTab === 'holidays'}
                        onClick={() => setActiveTab('holidays')}
                        icon={<Flag size={18} />}
                        label="Festività"
                        count={holidays.length}
                        hasNotification={unconfirmedCount > 0}
                    />
                    <TabButton
                        active={activeTab === 'closures'}
                        onClick={() => setActiveTab('closures')}
                        icon={<Building size={18} />}
                        label="Chiusure"
                        count={closures.length}
                    />
                    <TabButton
                        active={activeTab === 'exceptions'}
                        onClick={() => setActiveTab('exceptions')}
                        icon={<AlertCircle size={18} />}
                        label="Eccezioni"
                        count={exceptions.length}
                    />
                </div>
            </div>

            {/* Content */}
            <div className="min-h-[400px]">
                {activeTab === 'holidays' && (
                    <HolidaysTab
                        holidays={holidays}
                        year={year}
                        onAdd={openNewHoliday}
                        onEdit={openEditHoliday}
                        onDelete={(id) => handleDeleteRequest(id, 'holiday')}
                        onConfirm={confirmHoliday}
                        onGenerate={generateHolidays}
                        onCopy={() => setShowCopyConfirm(true)}
                        isGenerating={isGenerating}
                    />
                )}

                {activeTab === 'closures' && (
                    <ClosuresTab
                        closures={closures}
                        onAdd={openNewClosure}
                        onEdit={openEditClosure}
                        onDelete={(id) => handleDeleteRequest(id, 'closure')}
                    />
                )}

                {activeTab === 'exceptions' && (
                    <ExceptionsTab
                        exceptions={exceptions}
                        onAdd={openNewException}
                        onDelete={(id) => handleDeleteRequest(id, 'exception')}
                    />
                )}
            </div>

            {/* Modals */}
            <SystemCalendarModals
                showHolidayModal={showHolidayModal}
                setShowHolidayModal={setShowHolidayModal}
                editingHoliday={editingHoliday}
                holidayForm={holidayForm}
                setHolidayForm={setHolidayForm}
                onSaveHoliday={handleSaveHoliday}
                isSavingHoliday={isSavingHoliday}
                showClosureModal={showClosureModal}
                setShowClosureModal={setShowClosureModal}
                editingClosure={editingClosure}
                closureForm={closureForm}
                setClosureForm={setClosureForm}
                onSaveClosure={handleSaveClosure}
                isSavingClosure={isSavingClosure}
                showExceptionModal={showExceptionModal}
                setShowExceptionModal={setShowExceptionModal}
                exceptionForm={exceptionForm}
                setExceptionForm={setExceptionForm}
                onSaveException={handleSaveException}
                isSavingException={isSavingException}
                deleteConfirm={deleteConfirm}
                setDeleteConfirm={setDeleteConfirm}
                onConfirmDelete={performDelete}
                showCopyConfirm={showCopyConfirm}
                setShowCopyConfirm={setShowCopyConfirm}
                onConfirmCopy={handleCopyHolidays}
                year={year}
                isGenerating={isGenerating}
                showSyncModal={showSyncModal}
                setShowSyncModal={setShowSyncModal}
                subscriptionUrls={subscriptionUrls}
                onCopyToClipboard={copyToClipboard}
            />
        </div>
    );
}

// ============================================================================
// Sub-components
// ============================================================================

interface TabButtonProps {
    active: boolean;
    onClick: () => void;
    icon: React.ReactNode;
    label: string;
    count: number;
    hasNotification?: boolean;
}

function TabButton({ active, onClick, icon, label, count, hasNotification }: TabButtonProps) {
    return (
        <button
            onClick={onClick}
            className={`px-4 py-4 font-semibold text-sm border-b-2 transition-all flex items-center gap-2 ${active
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-900'
                }`}
        >
            {icon}
            <span>{label}</span>
            <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${active ? 'bg-indigo-100 text-indigo-600' : 'bg-gray-100 text-gray-500'
                    }`}
            >
                {count}
            </span>
            {hasNotification && <span className="flex h-2 w-2 rounded-full bg-amber-500 animate-pulse"></span>}
        </button>
    );
}

interface SummaryDashboardProps {
    holidays: Holiday[];
    closures: Closure[];
    exceptions: { id: string }[];
}

function SummaryDashboard({ holidays, closures, exceptions }: SummaryDashboardProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <SummaryCard
                icon={<Flag size={20} />}
                iconBg="bg-red-50 text-red-600"
                badge="Nazionali"
                badgeColor="text-red-600 bg-red-50"
                value={holidays.filter(h => h.scope === 'national').length}
                label="Festività Nazionali"
            />
            <SummaryCard
                icon={<MapPin size={20} />}
                iconBg="bg-orange-50 text-orange-600"
                badge="Locali"
                badgeColor="text-orange-600 bg-orange-50"
                value={holidays.filter(h => h.scope === 'local' || h.scope === 'regional').length}
                label="Festività Locali"
            />
            <SummaryCard
                icon={<Building size={20} />}
                iconBg="bg-purple-50 text-purple-600"
                badge="Pianificate"
                badgeColor="text-purple-600 bg-purple-50"
                value={closures.length}
                label="Chiusure Aziendali"
            />
            <SummaryCard
                icon={<AlertCircle size={20} />}
                iconBg="bg-amber-50 text-amber-600"
                badge="Eccezioni"
                badgeColor="text-amber-600 bg-amber-50"
                value={exceptions.length}
                label="Eccezioni Calendario"
            />
        </div>
    );
}

interface SummaryCardProps {
    icon: React.ReactNode;
    iconBg: string;
    badge: string;
    badgeColor: string;
    value: number;
    label: string;
}

function SummaryCard({ icon, iconBg, badge, badgeColor, value, label }: SummaryCardProps) {
    return (
        <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all group">
            <div className="flex items-center justify-between mb-2">
                <div className={`p-2 rounded-xl group-hover:scale-110 transition-transform ${iconBg}`}>{icon}</div>
                <span className={`text-xs font-semibold px-2 py-1 rounded-full ${badgeColor}`}>{badge}</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">{value}</div>
            <div className="text-xs text-gray-500 font-medium uppercase tracking-wider mt-1">{label}</div>
        </div>
    );
}

interface ExportDropdownProps {
    year: number;
    onOpenSyncModal: () => void;
}

function ExportDropdown({ year, onOpenSyncModal }: ExportDropdownProps) {
    return (
        <div className="relative group">
            <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 text-sm font-medium rounded-lg transition-colors shadow-sm">
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
                        onClick={onOpenSyncModal}
                        className="w-full flex items-center gap-2 text-xs text-indigo-600 hover:text-indigo-700 font-medium transition-colors"
                    >
                        <Link size={12} />
                        <span>Ottieni link di sincronizzazione</span>
                    </button>
                </div>
            </div>
        </div>
    );
}

export default SystemCalendarsPage;
