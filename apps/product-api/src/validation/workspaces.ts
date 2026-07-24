import { z } from "zod";

export const organizationIdSchema = z.string().uuid();

export const createWorkspaceSchema = z.object({
  description: z.string().trim().max(2000).optional(),
  name: z.string().trim().min(1).max(120),
  privacyMode: z
    .enum(["local_confidential", "synthetic_demo"])
    .default("local_confidential")
});

