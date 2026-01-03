import { useState, useEffect } from 'react';
import { FileText, RefreshCw, CloudUpload, CheckCircle, XCircle, Eye } from 'lucide-react';
import { Card, Button } from '../common';
import notificationService from '../../services/notification.service';
import type { EmailTemplate } from '../../services/notification.service';
import { useToast } from '../../context/ToastContext';

interface EmailTemplatesPanelProps {
    className?: string;
}

export function EmailTemplatesPanel({ className }: EmailTemplatesPanelProps) {
    const toast = useToast();
    const [templates, setTemplates] = useState<EmailTemplate[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null);
    const [syncing, setSyncing] = useState<string | null>(null);

    useEffect(() => {
        loadTemplates();
    }, []);

    const loadTemplates = async () => {
        setLoading(true);
        try {
            const data = await notificationService.getTemplates(false); // Include inactive
            setTemplates(data);
        } catch (err) {
            toast.error('Errore caricamento template');
        } finally {
            setLoading(false);
        }
    };

    const handleSync = async (template: EmailTemplate) => {
        setSyncing(template.id);
        try {
            const result = await notificationService.syncTemplateToBrevo(template.id);
            if (result.created) {
                toast.success(`Template creato su Brevo (ID: ${result.brevo_template_id})`);
            } else {
                toast.success('Template aggiornato su Brevo');
            }
            loadTemplates();
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Errore sincronizzazione');
        } finally {
            setSyncing(null);
        }
    };

    const handleToggleActive = async (template: EmailTemplate) => {
        try {
            await notificationService.updateTemplate(template.id, { is_active: !template.is_active });
            toast.success(template.is_active ? 'Template disattivato' : 'Template attivato');
            loadTemplates();
        } catch (err) {
            toast.error('Errore aggiornamento');
        }
    };

    if (loading) {
        return (
            <Card className={className} title="Template Email">
                <div className="py-8 text-center text-gray-500">
                    <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
                    Caricamento template...
                </div>
            </Card>
        );
    }

    return (
        <Card
            className={className}
            title="Template Email"
            subtitle={`${templates.length} template`}
            headerAction={
                <Button size="sm" onClick={loadTemplates} variant="secondary" icon={<RefreshCw size={14} />}>
                    Ricarica
                </Button>
            }
        >
            {templates.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                    <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>Nessun template trovato.</p>
                    <p className="text-sm">Esegui lo script di seeding per creare i template di base.</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {templates.map((template) => (
                        <div
                            key={template.id}
                            className={`border rounded-lg p-4 ${template.is_active ? 'bg-white' : 'bg-gray-50 opacity-75'}`}
                        >
                            <div className="flex items-start justify-between">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <code className="text-sm bg-gray-100 px-2 py-0.5 rounded">
                                            {template.code}
                                        </code>
                                        {template.brevo_template_id ? (
                                            <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                                                <CheckCircle className="h-3 w-3" />
                                                Brevo #{template.brevo_template_id}
                                            </span>
                                        ) : (
                                            <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                                                Non sincronizzato
                                            </span>
                                        )}
                                        {!template.is_active && (
                                            <span className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full">
                                                Disattivo
                                            </span>
                                        )}
                                    </div>
                                    <h4 className="font-medium">{template.name}</h4>
                                    <p className="text-sm text-gray-500">{template.description}</p>
                                    <div className="mt-2 flex items-center gap-2 text-xs text-gray-400">
                                        <span>Tipo: {template.notification_type}</span>
                                        {template.available_variables && template.available_variables.length > 0 && (
                                            <span>| Variabili: {template.available_variables.join(', ')}</span>
                                        )}
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button
                                        size="sm"
                                        variant="secondary"
                                        onClick={() => setSelectedTemplate(template)}
                                        title="Anteprima"
                                        icon={<Eye size={14} />}
                                    />
                                    <Button
                                        size="sm"
                                        variant="secondary"
                                        onClick={() => handleToggleActive(template)}
                                        title={template.is_active ? 'Disattiva' : 'Attiva'}
                                        icon={template.is_active ? <XCircle size={14} className="text-red-500" /> : <CheckCircle size={14} className="text-green-500" />}
                                    />
                                    <Button
                                        size="sm"
                                        variant="secondary"
                                        onClick={() => handleSync(template)}
                                        disabled={syncing === template.id}
                                        title="Sincronizza con Brevo"
                                        icon={syncing === template.id ? <RefreshCw size={14} className="animate-spin" /> : <CloudUpload size={14} />}
                                    />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Template Preview Modal */}
            {selectedTemplate && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[80vh] overflow-hidden">
                        <div className="p-4 border-b flex items-center justify-between">
                            <h3 className="font-semibold">Anteprima: {selectedTemplate.name}</h3>
                            <button
                                onClick={() => setSelectedTemplate(null)}
                                className="text-gray-500 hover:text-gray-700"
                            >
                                ✕
                            </button>
                        </div>
                        <div className="p-4 max-h-[60vh] overflow-auto">
                            <div className="mb-4">
                                <span className="text-sm text-gray-500">Oggetto:</span>
                                <p className="font-medium">{selectedTemplate.subject}</p>
                            </div>
                            {selectedTemplate.html_content && (
                                <div className="border rounded-lg overflow-hidden">
                                    <div className="bg-gray-100 px-3 py-2 text-xs font-medium text-gray-600">
                                        HTML Preview
                                    </div>
                                    <div
                                        className="p-4 bg-white"
                                        dangerouslySetInnerHTML={{ __html: selectedTemplate.html_content }}
                                    />
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </Card>
    );
}

export default EmailTemplatesPanel;
