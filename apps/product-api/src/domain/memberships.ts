import { organizationMemberships } from "@clientatlas/database";
import { and, asc, eq, sql } from "drizzle-orm";
import type { UserTransaction } from "@/db/user-database";

export type OrganizationRole = "owner" | "admin" | "editor" | "viewer";

export async function listMemberships(
  transaction: UserTransaction,
  organizationId: string
) {
  return transaction
    .select({
      createdAt: organizationMemberships.createdAt,
      organizationId: organizationMemberships.organizationId,
      role: organizationMemberships.role,
      updatedAt: organizationMemberships.updatedAt,
      userId: organizationMemberships.userId
    })
    .from(organizationMemberships)
    .where(eq(organizationMemberships.organizationId, organizationId))
    .orderBy(asc(organizationMemberships.createdAt));
}

export async function setMembership(
  transaction: UserTransaction,
  organizationId: string,
  userId: string,
  role: OrganizationRole
) {
  const rows = await transaction.execute<{
    created_at: Date;
    organization_id: string;
    role: OrganizationRole;
    updated_at: Date;
    user_id: string;
  }>(
    sql`select * from app.set_organization_membership(
      ${organizationId},
      ${userId},
      ${role}::app.organization_role
    )`
  );
  const membership = rows[0];
  if (!membership) {
    throw new Error("membership_set_returned_no_row");
  }
  return {
    createdAt: membership.created_at,
    organizationId: membership.organization_id,
    role: membership.role,
    updatedAt: membership.updated_at,
    userId: membership.user_id
  };
}

export async function removeMembership(
  transaction: UserTransaction,
  organizationId: string,
  userId: string
): Promise<boolean> {
  const rows = await transaction.execute<{ removed: boolean }>(
    sql`select app.remove_organization_membership(
      ${organizationId},
      ${userId}
    ) as removed`
  );
  return rows[0]?.removed ?? false;
}

export async function getMembership(
  transaction: UserTransaction,
  organizationId: string,
  userId: string
) {
  const [membership] = await transaction
    .select()
    .from(organizationMemberships)
    .where(
      and(
        eq(organizationMemberships.organizationId, organizationId),
        eq(organizationMemberships.userId, userId)
      )
    )
    .limit(1);
  return membership;
}
