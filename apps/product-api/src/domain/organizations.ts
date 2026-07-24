import { organizations, organizationMemberships } from "@clientatlas/database";
import { asc, eq, sql } from "drizzle-orm";
import type { UserTransaction } from "@/db/user-database";

export type CreateOrganizationInput = Readonly<{
  name: string;
  slug: string;
}>;

export async function createOrganization(
  transaction: UserTransaction,
  input: CreateOrganizationInput
): Promise<{ id: string }> {
  const rows = await transaction.execute<{ id: string }>(
    sql`select app.create_organization(${input.name}, ${input.slug}) as id`
  );
  const created = rows[0];
  if (!created) {
    throw new Error("organization_create_returned_no_row");
  }
  return created;
}

export async function listOrganizations(
  transaction: UserTransaction,
  userId: string
) {
  return transaction
    .select({
      createdAt: organizations.createdAt,
      id: organizations.id,
      name: organizations.name,
      role: organizationMemberships.role,
      slug: organizations.slug,
      updatedAt: organizations.updatedAt
    })
    .from(organizations)
    .innerJoin(
      organizationMemberships,
      eq(organizations.id, organizationMemberships.organizationId)
    )
    .where(eq(organizationMemberships.userId, userId))
    .orderBy(asc(organizations.name));
}

