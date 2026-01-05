import { useState, useEffect } from 'react';
import {
    Building2,
    Briefcase,
    Layers,
    Plus,
    Loader,
    Edit,
    Shield,
    UserCircle,
    Trash2
} from 'lucide-react';
import { useToast } from '../../context/ToastContext';
import { organizationService } from '../../services/organization.service';
import { Button } from '../../components/common';
import type {
    Department,
    OrganizationalService,
    ExecutiveLevel
} from '../../types';

import { DepartmentModal, ServiceModal, ExecutiveLevelModal } from './OrganizationModals';

export default function OrganizationPage() {
    const toast = useToast();
    const [activeTab, setActiveTab] = useState<'departments' | 'services' | 'executive'>('departments');

    // Data State
    const [departments, setDepartments] = useState<Department[]>([]);
    const [flatDepartments, setFlatDepartments] = useState<Department[]>([]); // For selects
    const [services, setServices] = useState<OrganizationalService[]>([]);
    const [executiveLevels, setExecutiveLevels] = useState<ExecutiveLevel[]>([]);

    const [isLoading, setIsLoading] = useState(false);

    // Modal State
    const [execModal, setExecModal] = useState<{ isOpen: boolean, data?: ExecutiveLevel | null }>({ isOpen: false });
    const [deptModal, setDeptModal] = useState<{ isOpen: boolean, data?: Department | null }>({ isOpen: false });
    const [serviceModal, setServiceModal] = useState<{ isOpen: boolean, data?: OrganizationalService | null }>({ isOpen: false });

    useEffect(() => {
        loadData();
    }, [activeTab]);

    const loadData = async () => {
        setIsLoading(true);
        try {
            // Always fetch flat departments for selects if we are in relevant tabs
            const flatDepts = await organizationService.getDepartments(false);
            setFlatDepartments(flatDepts);

            if (activeTab === 'departments') {
                const data = await organizationService.getDepartmentTree(false);
                setDepartments(data);
            } else if (activeTab === 'services') {
                const data = await organizationService.getServices(false);
                setServices(data);
            } else if (activeTab === 'executive') {
                const data = await organizationService.getExecutiveLevels(false);
                setExecutiveLevels(data.sort((a, b) => a.hierarchy_level - b.hierarchy_level));
            }
        } catch (error) {
            console.error('Failed to load organization data:', error);
            toast.error('Errore nel caricamento dei dati');
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteExecutive = async (id: string) => {
        if (!window.confirm('Sei sicuro di voler eliminare questo livello?')) return;
        try {
            await organizationService.deleteExecutiveLevel(id);
            toast.success('Livello eliminato');
            loadData();
        } catch (error) {
            toast.error('Errore durante l\'eliminazione');
        }
    };

    const handleDeleteDepartment = async (id: string) => {
        if (!window.confirm('Sei sicuro di voler eliminare questo dipartimento? Attenzione: i sottodipartimenti potrebbero essere eliminati o scollegati.')) return;
        try {
            await organizationService.deleteDepartment(id);
            toast.success('Dipartimento eliminato');
            loadData();
        } catch (error) {
            toast.error('Errore durante l\'eliminazione');
        }
    };

    const handleDeleteService = async (id: string) => {
        if (!window.confirm('Sei sicuro di voler eliminare questo servizio?')) return;
        try {
            await organizationService.deleteService(id);
            toast.success('Servizio eliminato');
            loadData();
        } catch (error) {
            toast.error('Errore durante l\'eliminazione');
        }
    };

    return (
        <div className="space-y-6 animate-fadeIn pb-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start border-b border-gray-200 pb-6 gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2 mb-1">
                        <Building2 className="text-indigo-600" size={24} />
                        Struttura Organizzativa
                    </h1>
                    <p className="text-sm text-gray-500">Gestisci dipartimenti, servizi e livelli esecutivi</p>
                </div>
                <div className="flex bg-gray-100 p-1 rounded-lg">
                    <button
                        onClick={() => setActiveTab('departments')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'departments' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        <Layers size={16} /> Dipartimenti
                    </button>
                    <button
                        onClick={() => setActiveTab('services')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'services' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        <Briefcase size={16} /> Servizi
                    </button>
                    <button
                        onClick={() => setActiveTab('executive')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'executive' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        <Shield size={16} /> Livelli Executive
                    </button>
                </div>
            </div>

            {/* Content */}
            {/* Content */}
            {isLoading ? (
                <div className="flex items-center justify-center py-12">
                    <Loader className="animate-spin text-indigo-600" size={32} />
                </div>
            ) : (
                <>
                    {activeTab === 'executive' && (
                        <ExecutiveLevelsTab
                            levels={executiveLevels}
                            onRefresh={loadData}
                            onNew={() => setExecModal({ isOpen: true })}
                            onEdit={(l) => setExecModal({ isOpen: true, data: l })}
                            onDelete={handleDeleteExecutive}
                        />
                    )}
                    {activeTab === 'departments' && (
                        <DepartmentsTab
                            departments={departments}
                            onRefresh={loadData}
                            onNew={() => setDeptModal({ isOpen: true })}
                            onEdit={(d) => setDeptModal({ isOpen: true, data: d })}
                            onDelete={handleDeleteDepartment}
                        />
                    )}
                    {activeTab === 'services' && (
                        <ServicesTab
                            services={services}
                            onRefresh={loadData}
                            onNew={() => setServiceModal({ isOpen: true })}
                            onEdit={(s) => setServiceModal({ isOpen: true, data: s })}
                            onDelete={handleDeleteService}
                        />
                    )}

                    {/* Modals */}
                    <ExecutiveLevelModal
                        isOpen={execModal.isOpen}
                        onClose={() => setExecModal({ isOpen: false })}
                        onSuccess={loadData}
                        initialData={execModal.data}
                    />
                    <DepartmentModal
                        isOpen={deptModal.isOpen}
                        onClose={() => setDeptModal({ isOpen: false })}
                        onSuccess={loadData}
                        initialData={deptModal.data}
                        parentDepartments={flatDepartments}
                    />
                    <ServiceModal
                        isOpen={serviceModal.isOpen}
                        onClose={() => setServiceModal({ isOpen: false })}
                        onSuccess={loadData}
                        initialData={serviceModal.data}
                        departments={flatDepartments}
                    />
                </>
            )}
        </div>
    );
}

// ═══════════════════════════════════════════════════════════
// Executive Levels Tab
// ═══════════════════════════════════════════════════════════

interface ExecutiveLevelsTabProps {
    levels: ExecutiveLevel[];
    onRefresh: () => void;
    onNew: () => void;
    onEdit: (level: ExecutiveLevel) => void;
    onDelete: (id: string) => void;
}

function ExecutiveLevelsTab({ levels, onNew, onEdit, onDelete }: ExecutiveLevelsTabProps) {
    return (
        <div className="space-y-4">
            <div className="flex justify-end">
                <Button variant="primary" icon={<Plus size={16} />} onClick={onNew}>nuovo Livello</Button>
            </div>
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Livello</th>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Codice</th>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Titolo</th>
                            <th className="px-6 py-3 text-center text-xs font-semibold text-gray-500 uppercase">Limit Spesa</th>
                            <th className="px-6 py-3 text-center text-xs font-semibold text-gray-500 uppercase">Status</th>
                            <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">Azioni</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {levels.map((level) => (
                            <tr key={level.id} className="hover:bg-gray-50">
                                <td className="px-6 py-4 text-sm font-medium text-gray-900">{level.hierarchy_level}</td>
                                <td className="px-6 py-4 text-sm font-mono text-gray-600">{level.code}</td>
                                <td className="px-6 py-4 text-sm text-gray-900">{level.title}</td>
                                <td className="px-6 py-4 text-center text-sm text-gray-600">
                                    {level.max_approval_amount ? `€ ${level.max_approval_amount.toLocaleString()}` : '-'}
                                </td>
                                <td className="px-6 py-4 text-center">
                                    <span className={`px-2 py-1 text-xs rounded-full ${level.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-600'}`}>
                                        {level.is_active ? 'Attivo' : 'Inattivo'}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <div className="flex justify-end gap-1">
                                        <button onClick={() => onEdit(level)} className="text-gray-400 hover:text-indigo-600 p-1">
                                            <Edit size={16} />
                                        </button>
                                        <button onClick={() => onDelete(level.id)} className="text-gray-400 hover:text-red-600 p-1">
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                        {levels.length === 0 && (
                            <tr>
                                <td colSpan={6} className="px-6 py-8 text-center text-gray-500">Nessun livello configurato</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

// ═══════════════════════════════════════════════════════════
// Departments Tab
// ═══════════════════════════════════════════════════════════

interface DepartmentsTabProps {
    departments: Department[];
    onRefresh: () => void;
    onNew: () => void;
    onEdit: (dept: Department) => void;
    onDelete: (id: string) => void;
}

function DepartmentsTab({ departments, onNew, onEdit, onDelete }: DepartmentsTabProps) {
    const renderTree = (depts: Department[], level = 0): React.ReactNode => {
        return depts.map(dept => (
            <>
                <tr key={dept.id} className="hover:bg-gray-50 group">
                    <td className="px-6 py-3">
                        <div className="flex items-center" style={{ paddingLeft: `${level * 24}px` }}>
                            {level > 0 && <div className="w-4 h-px bg-gray-300 mr-2"></div>}
                            <div className="flex items-center gap-2">
                                <Building2 size={16} className={level === 0 ? 'text-indigo-600' : 'text-gray-400'} />
                                <span className={`text-sm ${level === 0 ? 'font-semibold text-gray-900' : 'text-gray-700'}`}>
                                    {dept.name}
                                </span>
                            </div>
                        </div>
                    </td>
                    <td className="px-6 py-3 text-sm font-mono text-gray-500">{dept.code}</td>
                    <td className="px-6 py-3">
                        {dept.manager ? (
                            <div className="flex items-center gap-2 text-sm text-gray-700">
                                <UserCircle size={16} className="text-gray-400" />
                                {dept.manager.first_name} {dept.manager.last_name}
                            </div>
                        ) : <span className="text-gray-400 text-sm">-</span>}
                    </td>
                    <td className="px-6 py-3 text-center">
                        <span className={`px-2 py-1 text-xs rounded-full ${dept.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-600'}`}>
                            {dept.is_active ? 'Attivo' : 'Inattivo'}
                        </span>
                    </td>
                    <td className="px-6 py-3 text-right opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="flex justify-end gap-1">
                            <button onClick={() => onEdit(dept)} className="p-1 text-gray-400 hover:text-indigo-600" title="Modifica"><Edit size={16} /></button>
                            <button onClick={() => onDelete(dept.id)} className="p-1 text-gray-400 hover:text-red-600" title="Elimina"><Trash2 size={16} /></button>
                        </div>
                    </td>
                </tr>
                {dept.children && dept.children.length > 0 && renderTree(dept.children, level + 1)}
            </>
        ));
    };

    return (
        <div className="space-y-4">
            <div className="flex justify-end">
                <Button variant="primary" icon={<Plus size={16} />} onClick={onNew}>Nuovo Dipartimento</Button>
            </div>
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Nome Dipartimento</th>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Codice</th>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Responsabile</th>
                            <th className="px-6 py-3 text-center text-xs font-semibold text-gray-500 uppercase">Status</th>
                            <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">Azioni</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {departments.length > 0 ? renderTree(departments) : (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                                    <Building2 className="mx-auto text-gray-300 mb-2" size={32} />
                                    Nessun dipartimento configurato
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

// ═══════════════════════════════════════════════════════════
// Services Tab
// ═══════════════════════════════════════════════════════════

interface ServicesTabProps {
    services: OrganizationalService[];
    onRefresh: () => void;
    onNew: () => void;
    onEdit: (service: OrganizationalService) => void;
    onDelete: (id: string) => void;
}

function ServicesTab({ services, onNew, onEdit, onDelete }: ServicesTabProps) {
    return (
        <div className="space-y-4">
            <div className="flex justify-end">
                <Button variant="primary" icon={<Plus size={16} />} onClick={onNew}>Nuovo Servizio</Button>
            </div>
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Servizio</th>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Dipartimento</th>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Coordinatore</th>
                            <th className="px-6 py-3 text-center text-xs font-semibold text-gray-500 uppercase">Status</th>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Azioni</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {services.map((service) => (
                            <tr key={service.id} className="hover:bg-gray-50">
                                <td className="px-6 py-4">
                                    <div className="font-medium text-gray-900">{service.name}</div>
                                    <div className="text-xs text-gray-500 font-mono">{service.code}</div>
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-600">
                                    {service.department_name}
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-600">
                                    {service.coordinator ? (
                                        <div className="flex items-center gap-2">
                                            <UserCircle size={16} className="text-gray-400" />
                                            {service.coordinator.first_name} {service.coordinator.last_name}
                                        </div>
                                    ) : '-'}
                                </td>
                                <td className="px-6 py-4 text-center">
                                    <span className={`px-2 py-1 text-xs rounded-full ${service.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-600'}`}>
                                        {service.is_active ? 'Attivo' : 'Inattivo'}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <div className="flex justify-end gap-1">
                                        <button onClick={() => onEdit(service)} className="text-gray-400 hover:text-indigo-600 p-1">
                                            <Edit size={16} />
                                        </button>
                                        <button onClick={() => onDelete(service.id)} className="text-gray-400 hover:text-red-600 p-1">
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                        {services.length === 0 && (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                                    <Briefcase className="mx-auto text-gray-300 mb-2" size={32} />
                                    Nessun servizio configurato
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
