import React, { useState } from 'react';
import { Card } from '../../components/common';
import { Button } from '../../components/common';
import { leavesService } from '../../services/leaves.service';
import { Loader2, Upload, AlertTriangle, CheckCircle } from 'lucide-react';

export const BalanceImportTool: React.FC = () => {
    const [jsonInput, setJsonInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<{ type: 'success' | 'error', message: string } | null>(null);

    const handleImport = async () => {
        try {
            setLoading(true);
            setResult(null);

            let items;
            try {
                items = JSON.parse(jsonInput);
            } catch (e) {
                setResult({ type: 'error', message: 'Invalid JSON format' });
                setLoading(false);
                return;
            }

            if (!Array.isArray(items)) {
                setResult({ type: 'error', message: 'Input must be a JSON array' });
                setLoading(false);
                return;
            }

            const message = await leavesService.importBalances(items, 'APPEND');
            setResult({ type: 'success', message });
            setJsonInput('');
        } catch (error: any) {
            setResult({
                type: 'error',
                message: error.response?.data?.detail || error.message || 'Import failed'
            });
        } finally {
            setLoading(false);
        }
    };

    const exampleJson = `[
  {
    "email": "mario.rossi@example.com",
    "year": 2023,
    "balance_type": "vacation",
    "amount": 10.5,
    "notes": "Residuo 2023 importato"
  },
  {
    "email": "luigi.verdi@example.com",
    "year": 2023,
    "balance_type": "rol",
    "amount": 20.0,
    "notes": "ROL residui"
  }
]`;

    return (
        <Card className="p-6">
            <div className="flex items-center gap-2 mb-4 border-b pb-4">
                <Upload className="h-5 w-5 text-gray-600" />
                <h3 className="text-lg font-semibold text-gray-900">Importazione Storico Saldi</h3>
            </div>

            <div className="space-y-4">
                <div className="bg-amber-50 border border-amber-200 rounded-md p-4 flex gap-3">
                    <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0" />
                    <p className="text-sm text-amber-800">
                        Questa operazione aggiungerà (APPEND) le voci specificate al ledger dei dipendenti.
                        Assicurati che le email siano corrette.
                    </p>
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700">Dati JSON (Copia e incolla qui)</label>
                    <textarea
                        value={jsonInput}
                        onChange={(e) => setJsonInput(e.target.value)}
                        placeholder={exampleJson}
                        className="w-full h-64 p-3 font-mono text-xs border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                    <p className="text-xs text-gray-500">
                        Formato richiesto: Array di oggetti con email, year, balance_type (vacation, rol, permits), amount.
                    </p>
                </div>

                {result && (
                    <div className={`p-4 rounded-md border flex items-center gap-3 ${result.type === 'success'
                            ? 'bg-green-50 text-green-900 border-green-200'
                            : 'bg-red-50 text-red-900 border-red-200'
                        }`}>
                        {result.type === 'success' ? <CheckCircle className="h-5 w-5 text-green-600" /> : <AlertTriangle className="h-5 w-5 text-red-600" />}
                        <p className="text-sm font-medium">{result.message}</p>
                    </div>
                )}

                <Button
                    onClick={handleImport}
                    disabled={!jsonInput.trim() || loading}
                    className="w-full sm:w-auto"
                >
                    {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Esegui Importazione
                </Button>
            </div>
        </Card>
    );
};
