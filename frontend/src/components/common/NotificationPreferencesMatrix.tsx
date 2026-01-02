/**
 * KRONOS - Notification Preferences Matrix Component
 * 
 * Matrix UI for configuring per-notification-type channel preferences.
 */
import { useState, useEffect } from 'react';
import { Bell, Mail, Smartphone, Save, RefreshCw } from 'lucide-react';
import notificationService, { NotificationType } from '../../services/notification.service';
import type { UserPreferences } from '../../services/notification.service';

interface NotificationPreferencesMatrixProps {
    onSave?: () => void;
}

const NOTIFICATION_TYPES = [
    { key: NotificationType.LEAVE_REQUEST_SUBMITTED, label: 'Nuova richiesta ferie', category: 'Ferie' },
    { key: NotificationType.LEAVE_REQUEST_APPROVED, label: 'Approvazione ferie', category: 'Ferie' },
    { key: NotificationType.LEAVE_REQUEST_REJECTED, label: 'Rifiuto ferie', category: 'Ferie' },
    { key: NotificationType.CALENDAR_SYSTEM_DEADLINE, label: 'Scadenze di sistema', category: 'Calendario' },
    { key: NotificationType.CALENDAR_PERSONAL_DEADLINE, label: 'Scadenze personali', category: 'Calendario' },
    { key: NotificationType.CALENDAR_SHARED_DEADLINE, label: 'Scadenze calendari condivisi', category: 'Calendario' },
    { key: NotificationType.SYSTEM_ANNOUNCEMENT, label: 'Annunci di sistema', category: 'Sistema' },
    { key: NotificationType.COMPLIANCE_ALERT, label: 'Avvisi compliance', category: 'Sistema' },
];

const CHANNELS = [
    { key: 'in_app', label: 'In-App', icon: Bell },
    { key: 'email', label: 'Email', icon: Mail },
    { key: 'push', label: 'Push', icon: Smartphone },
];

export function NotificationPreferencesMatrix({ onSave }: NotificationPreferencesMatrixProps) {
    const [preferences, setPreferences] = useState<UserPreferences | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [hasChanges, setHasChanges] = useState(false);

    useEffect(() => {
        fetchPreferences();
    }, []);

    const fetchPreferences = async () => {
        setLoading(true);
        try {
            const data = await notificationService.getPreferences();
            setPreferences(data);
        } catch (error) {
            console.error('Failed to fetch preferences:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleGlobalToggle = (channel: 'email' | 'in_app' | 'push') => {
        if (!preferences) return;

        const key = `${channel}_enabled` as keyof UserPreferences;
        setPreferences({
            ...preferences,
            [key]: !preferences[key],
        });
        setHasChanges(true);
    };

    const handleMatrixToggle = (notificationType: string, channel: string) => {
        if (!preferences) return;

        const matrix = { ...preferences.preferences_matrix };
        if (!matrix[notificationType]) {
            matrix[notificationType] = {};
        }
        matrix[notificationType][channel] = !matrix[notificationType]?.[channel];

        setPreferences({
            ...preferences,
            preferences_matrix: matrix,
        });
        setHasChanges(true);
    };

    const getMatrixValue = (notificationType: string, channel: string): boolean => {
        if (!preferences) return true;
        return preferences.preferences_matrix?.[notificationType]?.[channel] ?? true;
    };

    const handleSave = async () => {
        if (!preferences) return;

        setSaving(true);
        try {
            await notificationService.updatePreferences({
                email_enabled: preferences.email_enabled,
                in_app_enabled: preferences.in_app_enabled,
                push_enabled: preferences.push_enabled,
                preferences_matrix: preferences.preferences_matrix,
                digest_frequency: preferences.digest_frequency,
            });
            setHasChanges(false);
            onSave?.();
        } catch (error) {
            console.error('Failed to save preferences:', error);
        } finally {
            setSaving(false);
        }
    };

    // Group notifications by category
    const groupedTypes = NOTIFICATION_TYPES.reduce((acc, type) => {
        if (!acc[type.category]) acc[type.category] = [];
        acc[type.category].push(type);
        return acc;
    }, {} as Record<string, typeof NOTIFICATION_TYPES>);

    if (loading) {
        return (
            <div className="preferences-loading">
                <RefreshCw size={24} className="spinning" />
                <p>Caricamento preferenze...</p>
            </div>
        );
    }

    if (!preferences) {
        return <div className="preferences-error">Impossibile caricare le preferenze</div>;
    }

    return (
        <div className="preferences-matrix-container">
            {/* Global Switches */}
            <div className="preferences-global">
                <h3>Canali di notifica</h3>
                <div className="global-switches">
                    {CHANNELS.map(channel => {
                        const Icon = channel.icon;
                        const enabled = preferences[`${channel.key}_enabled` as keyof UserPreferences] as boolean;
                        return (
                            <label key={channel.key} className={`global-switch ${enabled ? 'active' : ''}`}>
                                <input
                                    type="checkbox"
                                    checked={enabled}
                                    onChange={() => handleGlobalToggle(channel.key as 'email' | 'in_app' | 'push')}
                                />
                                <Icon size={18} />
                                <span>{channel.label}</span>
                            </label>
                        );
                    })}
                </div>
            </div>

            {/* Matrix Table */}
            <div className="preferences-matrix">
                <h3>Preferenze dettagliate</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Tipo notifica</th>
                            {CHANNELS.map(channel => (
                                <th key={channel.key}>
                                    <channel.icon size={16} />
                                    {channel.label}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {Object.entries(groupedTypes).map(([category, types]) => (
                            <>
                                <tr key={category} className="category-row">
                                    <td colSpan={4}>{category}</td>
                                </tr>
                                {types.map(type => (
                                    <tr key={type.key}>
                                        <td>{type.label}</td>
                                        {CHANNELS.map(channel => {
                                            const globalEnabled = preferences[`${channel.key}_enabled` as keyof UserPreferences] as boolean;
                                            const checked = getMatrixValue(type.key, channel.key);
                                            return (
                                                <td key={channel.key}>
                                                    <label className={`matrix-toggle ${!globalEnabled ? 'disabled' : ''}`}>
                                                        <input
                                                            type="checkbox"
                                                            checked={checked && globalEnabled}
                                                            disabled={!globalEnabled}
                                                            onChange={() => handleMatrixToggle(type.key, channel.key)}
                                                        />
                                                        <span className="toggle-track">
                                                            <span className="toggle-thumb" />
                                                        </span>
                                                    </label>
                                                </td>
                                            );
                                        })}
                                    </tr>
                                ))}
                            </>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Digest Frequency */}
            <div className="preferences-digest">
                <h3>Frequenza digest email</h3>
                <div className="digest-options">
                    {['instant', 'daily', 'weekly'].map(freq => (
                        <label
                            key={freq}
                            className={`digest-option ${preferences.digest_frequency === freq ? 'active' : ''}`}
                        >
                            <input
                                type="radio"
                                name="digest"
                                value={freq}
                                checked={preferences.digest_frequency === freq}
                                onChange={() => {
                                    setPreferences({ ...preferences, digest_frequency: freq as UserPreferences['digest_frequency'] });
                                    setHasChanges(true);
                                }}
                            />
                            {freq === 'instant' && 'Istantaneo'}
                            {freq === 'daily' && 'Giornaliero'}
                            {freq === 'weekly' && 'Settimanale'}
                        </label>
                    ))}
                </div>
            </div>

            {/* Save Button */}
            <div className="preferences-actions">
                <button
                    className={`save-btn ${hasChanges ? 'has-changes' : ''}`}
                    onClick={handleSave}
                    disabled={!hasChanges || saving}
                >
                    <Save size={18} />
                    {saving ? 'Salvataggio...' : 'Salva preferenze'}
                </button>
            </div>

            <style>{`
        .preferences-matrix-container {
          max-width: 800px;
        }

        .preferences-loading,
        .preferences-error {
          padding: var(--space-8);
          text-align: center;
          color: var(--color-text-muted);
        }

        .spinning {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .preferences-global,
        .preferences-matrix,
        .preferences-digest {
          margin-bottom: var(--space-6);
          padding: var(--space-4);
          background: var(--color-bg-secondary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-lg);
        }

        .preferences-global h3,
        .preferences-matrix h3,
        .preferences-digest h3 {
          font-size: var(--font-size-base);
          font-weight: 600;
          color: var(--color-text-primary);
          margin: 0 0 var(--space-4);
        }

        .global-switches {
          display: flex;
          gap: var(--space-4);
        }

        .global-switch {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-3) var(--space-4);
          background: var(--color-bg-primary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .global-switch input {
          display: none;
        }

        .global-switch.active {
          background: var(--color-primary-light);
          border-color: var(--color-primary);
          color: var(--color-primary);
        }

        .preferences-matrix table {
          width: 100%;
          border-collapse: collapse;
        }

        .preferences-matrix th,
        .preferences-matrix td {
          padding: var(--space-3);
          text-align: center;
          border-bottom: 1px solid var(--color-border-light);
        }

        .preferences-matrix th {
          font-size: var(--font-size-sm);
          font-weight: 500;
          color: var(--color-text-secondary);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-1);
        }

        .preferences-matrix th:first-child,
        .preferences-matrix td:first-child {
          text-align: left;
        }

        .category-row td {
          font-weight: 600;
          font-size: var(--font-size-sm);
          color: var(--color-text-muted);
          background: var(--color-bg-tertiary);
          padding: var(--space-2) var(--space-3);
        }

        .matrix-toggle {
          display: inline-flex;
          cursor: pointer;
        }

        .matrix-toggle.disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        .matrix-toggle input {
          display: none;
        }

        .toggle-track {
          width: 36px;
          height: 20px;
          background: var(--color-bg-tertiary);
          border-radius: var(--radius-full);
          position: relative;
          transition: background var(--transition-fast);
        }

        .matrix-toggle input:checked + .toggle-track {
          background: var(--color-primary);
        }

        .toggle-thumb {
          position: absolute;
          top: 2px;
          left: 2px;
          width: 16px;
          height: 16px;
          background: white;
          border-radius: var(--radius-full);
          transition: transform var(--transition-fast);
          box-shadow: var(--shadow-sm);
        }

        .matrix-toggle input:checked + .toggle-track .toggle-thumb {
          transform: translateX(16px);
        }

        .digest-options {
          display: flex;
          gap: var(--space-3);
        }

        .digest-option {
          flex: 1;
          padding: var(--space-3);
          background: var(--color-bg-primary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          text-align: center;
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .digest-option input {
          display: none;
        }

        .digest-option.active {
          background: var(--color-primary-light);
          border-color: var(--color-primary);
          color: var(--color-primary);
        }

        .preferences-actions {
          display: flex;
          justify-content: flex-end;
        }

        .save-btn {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-3) var(--space-5);
          background: var(--color-bg-secondary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          color: var(--color-text-secondary);
          font-weight: 500;
          cursor: not-allowed;
          transition: all var(--transition-fast);
        }

        .save-btn.has-changes {
          background: var(--color-primary);
          border-color: var(--color-primary);
          color: white;
          cursor: pointer;
        }

        .save-btn.has-changes:hover {
          background: var(--color-primary-dark);
        }

        .save-btn:disabled {
          opacity: 0.6;
        }
      `}</style>
        </div>
    );
}

export default NotificationPreferencesMatrix;
