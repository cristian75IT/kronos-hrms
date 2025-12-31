/**
 * KRONOS - Error Handling Utilities
 */

/**
 * Formats API error messages, handling both strings and FastAPI validation error objects.
 */
export const formatApiError = (error: any): string => {
    if (!error) return 'Errore sconosciuto';

    const detail = error?.response?.data?.detail;

    if (!detail) {
        return error.message || 'Si è verificato un errore';
    }

    if (typeof detail === 'string') {
        return detail;
    }

    if (Array.isArray(detail)) {
        // Handle FastAPI validation errors (422 Unprocessable Entity)
        return detail
            .map((err: any) => {
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
