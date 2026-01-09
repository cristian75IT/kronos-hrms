/**
 * KRONOS - Error Handling Utilities
 */

interface ValidationError {
    loc: (string | number)[];
    msg: string;
    type: string;
}

interface ApiErrorResponse {
    detail?: string | ValidationError[] | Record<string, unknown>;
    error?: string | { message: string };
}

/**
 * Formats API error messages, handling both strings and FastAPI validation error objects.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const formatApiError = (error: any): string => {
    if (!error) return 'Errore sconosciuto';


    const data = error?.response?.data as ApiErrorResponse | undefined;

    // 1. Standard KRONOS Error Format ({ error: { message: "..." } })
    if (data?.error && typeof data.error === 'object' && 'message' in data.error) {
        return data.error.message;
    }

    // 2. Simple Error Format ({ error: "..." })
    if (typeof data?.error === 'string') {
        return data.error;
    }

    // 3. FastAPI Default Format ({ detail: ... })
    const detail = data?.detail;

    if (!detail) {

        return (error.message as string) || 'Si è verificato un errore';
    }

    if (typeof detail === 'string') {
        return detail;
    }

    if (Array.isArray(detail)) {
        // Handle FastAPI validation errors (422 Unprocessable Entity)
        return detail
            .map((err: ValidationError) => {
                const loc = err.loc ? err.loc.join('.') : '';
                return `${loc}: ${err.msg}`;
            })
            .join(', ');
    }

    if (typeof detail === 'object') {
        return JSON.stringify(detail);
    }

    return String(detail);
};
