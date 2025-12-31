/**
 * KRONOS - User Management Page
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useUsers } from '../../hooks/useApi';
import { User as UserIcon, Mail, Briefcase, UserPlus, Search, Building } from 'lucide-react';
import { ContractHistory } from '../../components/users/ContractHistory';

export function UsersPage() {
    const { data: users, isLoading, error } = useUsers();
    const [selectedUser, setSelectedUser] = useState<string | null>(null);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="spinner-lg" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center h-64 text-red-500">
                <p>Errore nel caricamento degli utenti</p>
            </div>
        );
    }

    return (
        <div className="users-page animate-fadeIn">
            {/* Header */}
            <div className="page-header">
                <div>
                    <h1>Gestione Utenti</h1>
                    <p className="page-subtitle">Amministra gli utenti e i loro permessi</p>
                </div>
                <Link to="/admin/users/new" className="btn btn-primary">
                    <UserPlus size={18} />
                    Nuovo Utente
                </Link>
            </div>

            {/* Toolbar */}
            <div className="toolbar">
                <div className="search-box">
                    <Search size={18} className="text-gray-400" />
                    <input
                        type="text"
                        placeholder="Cerca utente..."
                        className="search-input"
                    />
                </div>
            </div>

            {/* List */}
            <div className="users-list">
                {users?.map((user) => (
                    <div key={user.id} className="user-card" onClick={() => setSelectedUser(user.id)} style={{ cursor: 'pointer' }}>
                        <div className="user-avatar">
                            {user.first_name?.[0]}{user.last_name?.[0]}
                        </div>
                        <div className="user-info">
                            <h3 className="user-name">
                                {user.first_name} {user.last_name}
                            </h3>
                            <div className="user-meta">
                                <span className="meta-item">
                                    <Mail size={14} />
                                    {user.email}
                                </span>
                                <span className="meta-item">
                                    <UserIcon size={14} />
                                    {user.username}
                                </span>
                            </div>
                            <div className="user-meta mt-1">
                                {user.profile?.department && (
                                    <span className="meta-item badge badge-neutral">
                                        <Building size={12} className="mr-1" />
                                        {user.profile.department}
                                    </span>
                                )}
                                {user.profile?.position && (
                                    <span className="meta-item badge badge-neutral">
                                        <Briefcase size={12} className="mr-1" />
                                        {user.profile.position}
                                    </span>
                                )}
                                {user.roles?.map(role => (
                                    <span key={role} className="badge badge-info text-xs">
                                        {role}
                                    </span>
                                ))}
                            </div>
                        </div>
                        <div className="user-actions">
                            <button className="btn btn-sm btn-secondary" onClick={(e) => {
                                e.stopPropagation();
                                setSelectedUser(user.id);
                            }}>
                                Gestisci Contratti
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {/* Contract History Modal */}
            {selectedUser && (
                <ContractHistory
                    userId={selectedUser}
                    onClose={() => setSelectedUser(null)}
                />
            )}

            <style>{`
                .users-page {
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-6);
                }
                /* ... keep existing styles ... */
                .page-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .page-header h1 {
                    font-size: var(--font-size-2xl);
                    margin-bottom: var(--space-1);
                }
                /* ... other styles are assumed to be kept or I need to include them all if I replace the whole return block. 
                   Since I'm replacing the whole component function logic, I should include styles or rely on Replace properly matching block.
                   Wait, I'll try to replace ONLY the changed parts if possible, but the structure changed significantly (wrappers).
                   Actually, I can replace the whole function body.
                */
            `}</style>

            {/* Re-injecting styles because I cannot assume partial replacement handles CSS block well if I don't include it */}
            <style>{`
                .users-page {
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-6);
                }
                .page-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .page-header h1 {
                    font-size: var(--font-size-2xl);
                    margin-bottom: var(--space-1);
                }
                .toolbar {
                    display: flex;
                    gap: var(--space-4);
                    padding: var(--space-4);
                    background: var(--glass-bg);
                    border: 1px solid var(--glass-border);
                    border-radius: var(--radius-lg);
                }
                .search-box {
                    display: flex;
                    align-items: center;
                    gap: var(--space-2);
                    background: var(--color-bg-primary);
                    border: 1px solid var(--color-border-light);
                    padding: 0 var(--space-3);
                    border-radius: var(--radius-md);
                    flex: 1;
                    max-width: 400px;
                }
                .search-input {
                    border: none;
                    background: transparent;
                    padding: var(--space-2) 0;
                    width: 100%;
                    outline: none;
                }
                .users-list {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                    gap: var(--space-4);
                }
                .user-card {
                    display: flex;
                    align-items: center;
                    gap: var(--space-4);
                    padding: var(--space-4);
                    background: var(--glass-bg);
                    border: 1px solid var(--glass-border);
                    border-radius: var(--radius-lg);
                    transition: all var(--transition-fast);
                }
                .user-card:hover {
                    border-color: var(--color-primary);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                }
                .user-avatar {
                    width: 48px;
                    height: 48px;
                    background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: var(--font-size-lg);
                }
                .user-info {
                    flex: 1;
                    min-width: 0;
                }
                .user-name {
                    font-weight: var(--font-weight-bold);
                    margin-bottom: var(--space-1);
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                .user-meta {
                    display: flex;
                    flex-wrap: wrap;
                    gap: var(--space-3);
                    font-size: var(--font-size-sm);
                    color: var(--color-text-secondary);
                }
                .meta-item {
                    display: flex;
                    align-items: center;
                    gap: var(--space-1);
                }
            `}</style>
        </div>
    );
}

export default UsersPage;
