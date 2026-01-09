import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertCircle } from 'lucide-react';

interface Props {
    children?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Uncaught error:', error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            return (
                <div className="flex flex-col items-center justify-center min-h-screen bg-base-100 p-4">
                    <div className="card w-full max-w-lg bg-base-200 shadow-xl">
                        <div className="card-body items-center text-center">
                            <AlertCircle className="w-16 h-16 text-error mb-4" />
                            <h2 className="card-title text-2xl mb-2">Qualcosa è andato storto</h2>
                            <p className="text-base-content/70 mb-6">
                                Si è verificato un errore inaspettato. Ricarica la pagina o contatta il supporto.
                            </p>

                            {this.state.error && import.meta.env.DEV && (
                                <div className="mockup-code bg-base-300 text-left w-full mb-6 max-h-48 overflow-auto">
                                    <pre className="px-4 py-2 text-xs text-error">
                                        <code>{this.state.error.toString()}</code>
                                    </pre>
                                </div>
                            )}

                            <div className="card-actions flex gap-4">
                                <button
                                    className="btn btn-outline"
                                    onClick={() => window.location.reload()}
                                >
                                    Ricarica
                                </button>
                                <a href="/" className="btn btn-primary">
                                    Torna alla Dashboard
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
