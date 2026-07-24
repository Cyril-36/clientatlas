import {
  index,
  jsonb,
  pgSchema,
  primaryKey,
  text,
  timestamp,
  uniqueIndex,
  uuid
} from "drizzle-orm/pg-core";

export const appSchema = pgSchema("app");

export const organizationRole = appSchema.enum("organization_role", [
  "owner",
  "admin",
  "editor",
  "viewer"
]);

export const organizations = appSchema.table(
  "organizations",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    name: text("name").notNull(),
    slug: text("slug").notNull(),
    createdBy: uuid("created_by").notNull(),
    createdAt: timestamp("created_at", {
      mode: "date",
      withTimezone: true
    })
      .notNull()
      .defaultNow(),
    updatedAt: timestamp("updated_at", {
      mode: "date",
      withTimezone: true
    })
      .notNull()
      .defaultNow()
  },
  (table) => [
    uniqueIndex("organizations_slug_key").on(table.slug)
  ]
);

export const organizationMemberships = appSchema.table(
  "organization_memberships",
  {
    organizationId: uuid("organization_id")
      .notNull()
      .references(() => organizations.id, { onDelete: "cascade" }),
    userId: uuid("user_id").notNull(),
    role: organizationRole("role").notNull(),
    invitedBy: uuid("invited_by"),
    createdAt: timestamp("created_at", {
      mode: "date",
      withTimezone: true
    })
      .notNull()
      .defaultNow(),
    updatedAt: timestamp("updated_at", {
      mode: "date",
      withTimezone: true
    })
      .notNull()
      .defaultNow()
  },
  (table) => [
    primaryKey({
      columns: [table.organizationId, table.userId],
      name: "organization_memberships_pkey"
    }),
    index("organization_memberships_user_org_idx").on(
      table.userId,
      table.organizationId
    )
  ]
);

export const workspaces = appSchema.table(
  "workspaces",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    organizationId: uuid("organization_id")
      .notNull()
      .references(() => organizations.id, { onDelete: "cascade" }),
    name: text("name").notNull(),
    description: text("description"),
    privacyMode: text("privacy_mode").notNull().default("local_confidential"),
    createdBy: uuid("created_by").notNull(),
    createdAt: timestamp("created_at", {
      mode: "date",
      withTimezone: true
    })
      .notNull()
      .defaultNow(),
    updatedAt: timestamp("updated_at", {
      mode: "date",
      withTimezone: true
    })
      .notNull()
      .defaultNow()
  },
  (table) => [
    uniqueIndex("workspaces_tenant_key").on(table.organizationId, table.id),
    index("workspaces_org_updated_idx").on(
      table.organizationId,
      table.updatedAt
    )
  ]
);

export const auditEvents = appSchema.table(
  "audit_events",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    organizationId: uuid("organization_id").references(() => organizations.id, {
      onDelete: "set null"
    }),
    workspaceId: uuid("workspace_id"),
    actorUserId: uuid("actor_user_id"),
    actorType: text("actor_type").notNull(),
    eventType: text("event_type").notNull(),
    targetType: text("target_type").notNull(),
    targetId: uuid("target_id"),
    safeDetails: jsonb("safe_details")
      .$type<Record<string, string | number | boolean | null>>()
      .notNull()
      .default({}),
    createdAt: timestamp("created_at", {
      mode: "date",
      withTimezone: true
    })
      .notNull()
      .defaultNow()
  },
  (table) => [
    index("audit_events_org_created_idx").on(
      table.organizationId,
      table.createdAt
    )
  ]
);

export type Organization = typeof organizations.$inferSelect;
export type OrganizationMembership =
  typeof organizationMemberships.$inferSelect;
export type Workspace = typeof workspaces.$inferSelect;
