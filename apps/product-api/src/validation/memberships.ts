import { z } from "zod";

export const membershipUserIdSchema = z.string().uuid();

export const setMembershipSchema = z.object({
  role: z.enum(["owner", "admin", "editor", "viewer"]),
  userId: membershipUserIdSchema
});
