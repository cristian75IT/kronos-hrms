import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Plus,
    Search,
    ChevronRight,
    Briefcase,
    X,
    FileText
} from 'lucide-react';
import { configService } from '../../services/config.service';
import type { NationalContract } from '../../types';
import { useToast } from '../../context/ToastContext';

export function NationalContractsPage() {
    const navigate = useNavigate();
    const toast = useToast();
    const [contracts, setContracts] = useState<NationalContract[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isCreating, setIsCreating] = useState(false);
    const [newContract, setNewContract] = useState({ name: '', code: '', description: '' });

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsCreating(true);
        try {
            await configService.createNationalContract(newContract);
            await loadContracts();
            setIsModalOpen(false);
            setNewContract({ name: '', code: '', description: '' });
            toast.success('CCNL creato con successo');
        } catch (error) {
            console.error(error);
            toast.error('Errore nella creazione del CCNL');
        } finally {
            setIsCreating(false);
        }
    };

    useEffect(() => {
        loadContracts();
    }, []);

    const loadContracts = async () => {
        try {
            const data = await configService.getNationalContracts();
            setContracts(data);
        } catch (error) {
            console.error('Failed to load national contracts', error);
            toast.error('Errore nel caricamento dei contratti nazionali');
        } finally {
            setIsLoading(false);
        }
    };

    const filteredContracts = contracts.filter(c =>
        c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.code.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-screen">
                <div className="spinner-lg" />
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-fadeIn p-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Briefcase className="text-indigo-600" />
                        Contratti Collettivi Nazionali (CCNL)
                    </h1>
                    <p className="text-gray-500 mt-1">Gestisci i modelli contrattuali, i livelli e le regole di calcolo ferie/ROL.</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="btn btn-primary flex items-center gap-2"
                >
                    <Plus size={18} />
                    Nuovo CCNL
                </button>
            </div>

            {/* Search */}
            <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Search size={18} className="text-gray-400" />
                </div>
                <input
                    type="text"
                    placeholder="Cerca per nome o codice..."
                    className="block w-full pl-10 pr-3 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all shadow-sm"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
            </div>

            {/* Contracts Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredContracts.map(contract => (
                    <div
                        key={contract.id}
                        className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all duration-300 hover:border-indigo-300 overflow-hidden cursor-pointer group"
                        onClick={() => navigate(`/admin/national-contracts/${contract.id}`)}
                    >
                        <div className="p-6">
                            <div className="flex justify-between items-start mb-4">
                                <div className="p-3 bg-indigo-50 rounded-lg text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                                    <FileText size={24} />
                                </div>
                                <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${contract.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                                    {contract.is_active ? 'Attivo' : 'Inattivo'}
                                </span>
                            </div>

                            <h3 className="text-lg font-bold text-gray-900 mb-1 group-hover:text-indigo-600 transition-colors">{contract.name}</h3>
                            <p className="text-sm text-gray-500 font-mono mb-4">{contract.code}</p>

                            <p className="text-sm text-gray-600 line-clamp-2 mb-4 h-10">
                                {contract.description || 'Nessuna descrizione disponibile.'}
                            </p>

                            <div className="pt-4 border-t border-gray-100 flex items-center justify-between text-sm text-gray-500">
                                <div className="flex items-center gap-1">
                                    <span className="font-medium text-gray-700">Gestisci Parametri</span>
                                </div>
                                <ChevronRight size={16} className="text-gray-400 group-hover:translate-x-1 transition-transform" />
                            </div>
                        </div>
                    </div>
                ))}

                {filteredContracts.length === 0 && (
                    <div className="col-span-full py-12 text-center bg-gray-50 rounded-xl border border-dashed border-gray-300">
                        <p className="text-gray-500">Nessun CCNL trovato.</p>
                    </div>
                )}
            </div>

            {/* Create Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-scaleIn">
                        <div className="p-5 border-b border-gray-100 flex justify-between items-center">
                            <h3 className="font-bold text-lg text-gray-900">Nuovo CCNL</h3>
                            <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600 transition-colors">
                                <X size={20} />
                            </button>
                        </div>

                        <form onSubmit={handleCreate}>
                            <div className="p-6 space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Nome Contratto</label>
                                    <input
                                        type="text"
                                        required
                                        className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                        placeholder="es. Commercio, Metalmeccanico"
                                        value={newContract.name}
                                        onChange={e => setNewContract({ ...newContract, name: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Codice Identificativo</label>
                                    <input
                                        type="text"
                                        required
                                        className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm uppercase"
                                        placeholder="es. CCNL_COMMERCIO"
                                        value={newContract.code}
                                        onChange={e => setNewContract({ ...newContract, code: e.target.value.toUpperCase() })}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
                                    <textarea
                                        className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                        rows={3}
                                        placeholder="Breve descrizione..."
                                        value={newContract.description}
                                        onChange={e => setNewContract({ ...newContract, description: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div className="p-5 border-t border-gray-100 flex justify-end gap-3 bg-gray-50">
                                <button type="button" onClick={() => setIsModalOpen(false)} className="btn btn-ghost hover:bg-gray-200" disabled={isCreating}>Annulla</button>
                                <button type="submit" className="btn btn-primary" disabled={isCreating}>
                                    {isCreating ? <span className="spinner spinner-white spinner-sm" /> : 'Crea CCNL'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

export default NationalContractsPage;
