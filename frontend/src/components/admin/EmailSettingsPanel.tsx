import { useState, useEffect } from 'react';
import { Mail, AlertTriangle, Save, Send, RefreshCw, Eye, EyeOff } from 'lucide-react';
import { Card, Button } from '../common';
import notificationService from '../../services/notification.service';
import type { EmailProviderSettings, EmailProviderSettingsCreate, EmailProviderSettingsUpdate } from '../../services/notification.service';
import { useToast } from '../../context/ToastContext';

interface EmailSettingsPanelProps {
    className?: string;
}

export function EmailSettingsPanel({ className }: EmailSettingsPanelProps) {
    const toast = useToast();
    const [settings, setSettings] = useState<EmailProviderSettings | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [testing, setTesting] = useState(false);
    const [showApiKey, setShowApiKey] = useState(false);
    const [isNewSettings, setIsNewSettings] = useState(false);
    const [testEmail, setTestEmail] = useState('');

    // Form state
    const [formData, setFormData] = useState<EmailProviderSettingsCreate>({
        api_key: '',
        sender_email: '',
        sender_name: 'KRONOS HR',
        test_mode: false,
        test_email: '',
    });

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        setLoading(true);
        try {
            const data = await notificationService.getProviderSettings();
            setSettings(data);
            setFormData({
                api_key: '', // Never show actual key
                sender_email: data.sender_email,
                sender_name: data.sender_name,
                reply_to_email: data.reply_to_email,
                reply_to_name: data.reply_to_name,
                test_mode: data.test_mode,
                test_email: data.test_email || '',
                daily_limit: data.daily_limit,
            });
            setIsNewSettings(false);
        } catch (err: any) {
            if (err.response?.status === 404) {
                setIsNewSettings(true);
            } else {
                toast.error('Errore caricamento impostazioni');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            if (isNewSettings) {
                if (!formData.api_key) {
                    toast.error('API Key Brevo richiesta');
                    setSaving(false);
                    return;
                }
                await notificationService.createProviderSettings(formData);
                toast.success('Impostazioni email create');
            } else {
                // Only include api_key if changed
                const updateData: EmailProviderSettingsUpdate = {
                    sender_email: formData.sender_email,
                    sender_name: formData.sender_name,
                    reply_to_email: formData.reply_to_email,
                    reply_to_name: formData.reply_to_name,
                    test_mode: formData.test_mode,
                    test_email: formData.test_email,
                    daily_limit: formData.daily_limit,
                };
                if (formData.api_key) {
                    updateData.api_key = formData.api_key;
                }
                await notificationService.updateProviderSettings(settings!.id, updateData);
                toast.success('Impostazioni aggiornate');
            }
            loadSettings();
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Errore salvataggio');
        } finally {
            setSaving(false);
        }
    };

    const handleTest = async () => {
        if (!testEmail) {
            toast.error('Inserisci email per il test');
            return;
        }
        setTesting(true);
        try {
            const result = await notificationService.testEmailSettings(testEmail);
            if (result.success) {
                toast.success('Email di test inviata!');
            } else {
                toast.error(result.error || 'Errore invio test');
            }
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Errore invio test');
        } finally {
            setTesting(false);
        }
    };

    if (loading) {
        return (
            <Card className={className} title="Impostazioni Email (Brevo)">
                <div className="py-8 text-center text-gray-500">
                    <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
                    Caricamento impostazioni...
                </div>
            </Card>
        );
    }

    return (
        <Card
            className={className}
            title="Impostazioni Email (Brevo)"
            subtitle={settings?.is_active ? 'Attivo' : 'Non configurato'}
            headerAction={
                <Mail className="h-5 w-5 text-indigo-600" />
            }
        >
            <div className="space-y-6">
                {/* API Key */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        API Key Brevo
                    </label>
                    <div className="relative">
                        <input
                            type={showApiKey ? 'text' : 'password'}
                            value={formData.api_key}
                            onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                            placeholder={isNewSettings ? 'Inserisci API Key' : settings?.api_key_masked || '(non modificata)'}
                            className="w-full px-3 py-2 border rounded-lg pr-20"
                        />
                        <button
                            type="button"
                            onClick={() => setShowApiKey(!showApiKey)}
                            className="absolute right-2 top-2 text-gray-500 hover:text-gray-700"
                        >
                            {showApiKey ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                        </button>
                    </div>
                    {!isNewSettings && <p className="text-xs text-gray-500 mt-1">Lascia vuoto per non modificare</p>}
                </div>

                {/* Sender Info */}
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Email Mittente
                        </label>
                        <input
                            type="email"
                            value={formData.sender_email || ''}
                            onChange={(e) => setFormData({ ...formData, sender_email: e.target.value })}
                            className="w-full px-3 py-2 border rounded-lg"
                            placeholder="noreply@azienda.it"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Nome Mittente
                        </label>
                        <input
                            type="text"
                            value={formData.sender_name || ''}
                            onChange={(e) => setFormData({ ...formData, sender_name: e.target.value })}
                            className="w-full px-3 py-2 border rounded-lg"
                            placeholder="KRONOS HR"
                        />
                    </div>
                </div>

                {/* Reply-to */}
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Email Reply-To (opzionale)
                        </label>
                        <input
                            type="email"
                            value={formData.reply_to_email || ''}
                            onChange={(e) => setFormData({ ...formData, reply_to_email: e.target.value })}
                            className="w-full px-3 py-2 border rounded-lg"
                            placeholder="hr@azienda.it"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Nome Reply-To
                        </label>
                        <input
                            type="text"
                            value={formData.reply_to_name || ''}
                            onChange={(e) => setFormData({ ...formData, reply_to_name: e.target.value })}
                            className="w-full px-3 py-2 border rounded-lg"
                            placeholder="Ufficio HR"
                        />
                    </div>
                </div>

                {/* Test Mode */}
                <div className="flex items-center gap-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <AlertTriangle className="h-5 w-5 text-yellow-600" />
                    <div className="flex-1">
                        <label className="flex items-center gap-2">
                            <input
                                type="checkbox"
                                checked={formData.test_mode || false}
                                onChange={(e) => setFormData({ ...formData, test_mode: e.target.checked })}
                                className="rounded"
                            />
                            <span className="font-medium text-yellow-800">Modalità Test</span>
                        </label>
                        <p className="text-sm text-yellow-700 mt-1">
                            Tutte le email verranno reindirizzate all'indirizzo di test.
                        </p>
                    </div>
                    {formData.test_mode && (
                        <input
                            type="email"
                            value={formData.test_email || ''}
                            onChange={(e) => setFormData({ ...formData, test_email: e.target.value })}
                            className="w-48 px-3 py-2 border rounded-lg"
                            placeholder="test@azienda.it"
                        />
                    )}
                </div>

                {/* Daily Limit */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Limite giornaliero (opzionale)
                    </label>
                    <div className="flex items-center gap-4">
                        <input
                            type="number"
                            value={formData.daily_limit || ''}
                            onChange={(e) => setFormData({ ...formData, daily_limit: e.target.value ? parseInt(e.target.value) : undefined })}
                            className="w-32 px-3 py-2 border rounded-lg"
                            placeholder="Nessun limite"
                            min="0"
                        />
                        {settings && (
                            <span className="text-sm text-gray-500">
                                Email inviate oggi: <strong>{settings.emails_sent_today}</strong>
                            </span>
                        )}
                    </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between pt-4 border-t">
                    <div className="flex items-center gap-2">
                        <input
                            type="email"
                            value={testEmail}
                            onChange={(e) => setTestEmail(e.target.value)}
                            className="w-48 px-3 py-2 border rounded-lg text-sm"
                            placeholder="Email per test"
                        />
                        <Button
                            onClick={handleTest}
                            disabled={testing || !settings}
                            variant="secondary"
                            icon={testing ? <RefreshCw size={16} className="animate-spin" /> : <Send size={16} />}
                        >
                            Invia Test
                        </Button>
                    </div>
                    <Button onClick={handleSave} disabled={saving} variant="primary" icon={saving ? <RefreshCw size={16} className="animate-spin" /> : <Save size={16} />}>
                        {isNewSettings ? 'Crea' : 'Salva'}
                    </Button>
                </div>
            </div>
        </Card>
    );
}

export default EmailSettingsPanel;
