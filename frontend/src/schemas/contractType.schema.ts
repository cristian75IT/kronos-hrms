
import { z } from 'zod';

export const contractTypeSchema = z.object({
    name: z.string().min(1, "Nome obbligatorio").max(100, "Massimo 100 caratteri"),
    code: z.string().optional(),
    is_part_time: z.boolean(),
    part_time_percentage: z.number().min(1, "Minimo 1%").max(100, "Massimo 100%").optional(),
    annual_vacation_days: z.number().min(0, "Non può essere negativo"),
    annual_rol_hours: z.number().min(0, "Non può essere negativo"),
    annual_permit_hours: z.number().min(0, "Non può essere negativo"),
    is_active: z.boolean()
});

export type ContractTypeFormValues = z.infer<typeof contractTypeSchema>;
