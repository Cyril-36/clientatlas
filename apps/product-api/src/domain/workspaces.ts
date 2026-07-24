import { workspaces } from "@clientatlas/database";
import { and, asc, eq } from "drizzle-orm";
import type { UserTransaction } from "@/db/user-database";

export type CreateWorkspaceInput = Readonly<{
  description?: string | undefined;
  name: string;
  privacyMode: "local_confidential" | "synthetic_demo";
}>;

export async function createWorkspace(
  transaction: UserTransaction,
  organizationId: string,
  userId: string,
  input: CreateWorkspaceInput
) {
  const [created] = await transaction
    .insert(workspaces)
    .values({
      createdBy: userId,
      description: input.description,
      name: input.name,
      organizationId,
      privacyMode: input.privacyMode
    })
    .returning({
      createdAt: workspaces.createdAt,
      description: workspaces.description,
      id: workspaces.id,
      name: workspaces.name,
      organizationId: workspaces.organizationId,
      privacyMode: workspaces.privacyMode,
      updatedAt: workspaces.updatedAt
    });

  if (!created) {
    throw new Error("workspace_create_returned_no_row");
  }
  return created;
}

export async function listWorkspaces(
  transaction: UserTransaction,
  organizationId: string
) {
  return transaction
    .select({
      createdAt: workspaces.createdAt,
      description: workspaces.description,
      id: workspaces.id,
      name: workspaces.name,
      organizationId: workspaces.organizationId,
      privacyMode: workspaces.privacyMode,
      updatedAt: workspaces.updatedAt
    })
    .from(workspaces)
    .where(and(eq(workspaces.organizationId, organizationId)))
    .orderBy(asc(workspaces.name));
}
