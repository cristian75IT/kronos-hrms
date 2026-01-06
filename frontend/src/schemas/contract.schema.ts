
import { z } from 'zod';

export const employeeContractSchema = z.object({
    contract_type_id: z.string().uuid("Seleziona un tipo di contratto valido"),
    national_contract_id: z.string().uuid("Seleziona un CCNL valido").optional().or(z.literal('')),
    level_id: z.string().uuid("Seleziona un livello valido").optional().or(z.literal('')),
    start_date: z.string().refine((val) => !isNaN(Date.parse(val)), {
        message: "Data di inizio non valida",
    }),
    end_date: z.string().optional().refine((val) => !val || !isNaN(Date.parse(val)), {
        message: "Data di fine non valida",
    }),
    weekly_hours: z.number()
        .min(1, "Minimo 1 ora")
        .max(168, "Massimo 168 ore"),
    job_title: z.string().max(100, "Massimo 100 caratteri").optional().or(z.literal('')),
    department: z.string().max(100, "Massimo 100 caratteri").optional().or(z.literal('')),
    document_path: z.string().optional().or(z.literal('')),
});

export type EmployeeContractFormValues = z.infer<typeof employeeContractSchema>;
