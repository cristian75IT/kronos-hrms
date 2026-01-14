/**
 * KRONOS - Notification Preferences Settings Component
 */
import { Mail, Monitor, Smartphone, Save } from 'lucide-react';
import type { UserPreferences } from '../../services/notification.service';

interface NotificationPreferencesProps {
    preferences: UserPreferences;
    onUpdatePreference: (key: keyof UserPreferences, value: boolean | string) => void;
    onSave: () => void;
    isSaving: boolean;
}

export function NotificationPreferences({
    preferences,
    onUpdatePreference,
    onSave,
    isSaving
}: NotificationPreferencesProps) {
    const digestOptions = [
        { value: 'instant', label: 'Istantanea' },
        { value: 'daily', label: 'Giornaliero' },
        { value: 'weekly', label: 'Settimanale' },
    ];

    return (
        <div className="settings-section">
            <div className="settings-card">
                <h3>Canali di Notifica</h3>
                <p className="settings-description">
                    Scegli come vuoi ricevere le notifiche
                </p>

                <div className="settings-toggles">
                    <div className="toggle-row">
                        <div className="toggle-info">
                            <Mail size={20} />
                            <div>
                                <span className="toggle-label">Email</span>
                                <span className="toggle-desc">Ricevi notifiche via email</span>
                            </div>
                        </div>
                        <label className="toggle-switch">
                            <input
                                type="checkbox"
                                checked={preferences.email_enabled}
                                onChange={(e) => onUpdatePreference('email_enabled', e.target.checked)}
                            />
                            <span className="slider"></span>
                        </label>
                    </div>

                    <div className="toggle-row">
                        <div className="toggle-info">
                            <Monitor size={20} />
                            <div>
                                <span className="toggle-label">In-App</span>
                                <span className="toggle-desc">Notifiche nell'applicazione</span>
                            </div>
                        </div>
                        <label className="toggle-switch">
                            <input
                                type="checkbox"
                                checked={preferences.in_app_enabled}
                                onChange={(e) => onUpdatePreference('in_app_enabled', e.target.checked)}
                            />
                            <span className="slider"></span>
                        </label>
                    </div>

                    <div className="toggle-row">
                        <div className="toggle-info">
                            <Smartphone size={20} />
                            <div>
                                <span className="toggle-label">Push</span>
                                <span className="toggle-desc">Notifiche push sul browser</span>
                            </div>
                        </div>
                        <label className="toggle-switch">
                            <input
                                type="checkbox"
                                checked={preferences.push_enabled}
                                onChange={(e) => onUpdatePreference('push_enabled', e.target.checked)}
                            />
                            <span className="slider"></span>
                        </label>
                    </div>
                </div>
            </div>

            <div className="settings-card">
                <h3>Frequenza Digest</h3>
                <p className="settings-description">
                    Scegli quando ricevere il riepilogo delle notifiche email
                </p>

                <div className="digest-options">
                    {digestOptions.map(opt => (
                        <label key={opt.value} className="digest-option">
                            <input
                                type="radio"
                                name="digest"
                                value={opt.value}
                                checked={preferences.digest_frequency === opt.value}
                                onChange={(e) => onUpdatePreference('digest_frequency', e.target.value)}
                            />
                            <span className="radio-custom"></span>
                            <span>{opt.label}</span>
                        </label>
                    ))}
                </div>
            </div>

            <div className="settings-actions">
                <button
                    className="save-btn"
                    onClick={onSave}
                    disabled={isSaving}
                >
                    <Save size={18} />
                    {isSaving ? 'Salvataggio...' : 'Salva Preferenze'}
                </button>
            </div>
        </div>
    );
}
