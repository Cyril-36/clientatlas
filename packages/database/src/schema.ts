import {
  index,
  jsonb,
  pgSchema,
  primaryKey,
  text,
  bigint,
  integer,
  timestamp,
  uniqueIndex,
  uuid,
  vector
} from "drizzle-orm/pg-core";

export const appSchema = pgSchema("app");

export const organizationRole = appSchema.enum("organization_role", [
  "owner",
  "admin",
  "editor",
  "viewer"
]);

export const sourceKind = appSchema.enum("source_kind", [
  "upload",
  "google_drive"
]);

export const ingestionState = appSchema.enum("ingestion_state", [
  "queued",
  "parsing",
  "chunking",
  "embedding",
  "ready",
  "failed",
  "deleting",
  "deleted"
]);

export const ingestionJobState = appSchema.enum("ingestion_job_state", [
  "queued",
  "running",
  "retry",
  "complete",
  "failed"
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

export const sources = appSchema.table(
  "sources",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    organizationId: uuid("organization_id")
      .notNull()
      .references(() => organizations.id, { onDelete: "cascade" }),
    workspaceId: uuid("workspace_id")
      .notNull()
      .references(() => workspaces.id, { onDelete: "cascade" }),
    kind: sourceKind("kind").notNull(),
    displayName: text("display_name").notNull(),
    externalFileId: text("external_file_id"),
    objectPath: text("object_path").notNull(),
    state: ingestionState("state").notNull().default("queued"),
    activeVersionId: uuid("active_version_id"),
    safeErrorCode: text("safe_error_code"),
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
      .defaultNow(),
    deletedAt: timestamp("deleted_at", {
      mode: "date",
      withTimezone: true
    })
  },
  (table) => [
    uniqueIndex("sources_tenant_key").on(
      table.organizationId,
      table.workspaceId,
      table.id
    ),
    index("sources_workspace_updated_idx").on(
      table.organizationId,
      table.workspaceId,
      table.updatedAt
    )
  ]
);

export const documentVersions = appSchema.table(
  "document_versions",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    organizationId: uuid("organization_id").notNull(),
    workspaceId: uuid("workspace_id").notNull(),
    sourceId: uuid("source_id")
      .notNull()
      .references(() => sources.id, { onDelete: "cascade" }),
    checksumSha256: text("checksum_sha256").notNull(),
    mimeType: text("mime_type").notNull(),
    byteSize: bigint("byte_size", { mode: "number" }).notNull(),
    parserVersion: text("parser_version").notNull(),
    embeddingProvider: text("embedding_provider").notNull(),
    embeddingModel: text("embedding_model").notNull(),
    state: ingestionState("state").notNull().default("queued"),
    pageCount: integer("page_count"),
    chunkCount: integer("chunk_count").notNull().default(0),
    safeErrorCode: text("safe_error_code"),
    createdBy: uuid("created_by").notNull(),
    createdAt: timestamp("created_at", {
      mode: "date",
      withTimezone: true
    })
      .notNull()
      .defaultNow(),
    readyAt: timestamp("ready_at", { mode: "date", withTimezone: true })
  },
  (table) => [
    uniqueIndex("document_versions_source_checksum_key").on(
      table.sourceId,
      table.checksumSha256
    ),
    index("document_versions_source_created_idx").on(
      table.sourceId,
      table.createdAt
    )
  ]
);

export const documentChunks = appSchema.table(
  "document_chunks",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    organizationId: uuid("organization_id").notNull(),
    workspaceId: uuid("workspace_id").notNull(),
    sourceId: uuid("source_id").notNull(),
    documentVersionId: uuid("document_version_id")
      .notNull()
      .references(() => documentVersions.id, { onDelete: "cascade" }),
    ordinal: integer("ordinal").notNull(),
    content: text("content").notNull(),
    tokenCount: integer("token_count").notNull(),
    locator: jsonb("locator")
      .$type<Record<string, string | number | boolean | null>>()
      .notNull(),
    embedding: vector("embedding", { dimensions: 384 }).notNull(),
    createdAt: timestamp("created_at", {
      mode: "date",
      withTimezone: true
    })
      .notNull()
      .defaultNow()
  },
  (table) => [
    uniqueIndex("document_chunks_version_ordinal_key").on(
      table.documentVersionId,
      table.ordinal
    ),
    index("document_chunks_tenant_idx").on(
      table.organizationId,
      table.workspaceId,
      table.sourceId,
      table.documentVersionId
    )
  ]
);

export const ingestionJobs = appSchema.table(
  "ingestion_jobs",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    organizationId: uuid("organization_id").notNull(),
    workspaceId: uuid("workspace_id").notNull(),
    sourceId: uuid("source_id").notNull(),
    documentVersionId: uuid("document_version_id")
      .notNull()
      .references(() => documentVersions.id, { onDelete: "cascade" }),
    state: ingestionJobState("state").notNull().default("queued"),
    attemptCount: integer("attempt_count").notNull().default(0),
    runAfter: timestamp("run_after", {
      mode: "date",
      withTimezone: true
    })
      .notNull()
      .defaultNow(),
    lockedAt: timestamp("locked_at", { mode: "date", withTimezone: true }),
    lockedBy: text("locked_by"),
    safeErrorCode: text("safe_error_code"),
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
    uniqueIndex("ingestion_jobs_document_version_key").on(
      table.documentVersionId
    )
  ]
);

export type Organization = typeof organizations.$inferSelect;
export type OrganizationMembership =
  typeof organizationMemberships.$inferSelect;
export type Workspace = typeof workspaces.$inferSelect;
export type Source = typeof sources.$inferSelect;
export type DocumentVersion = typeof documentVersions.$inferSelect;
export type DocumentChunk = typeof documentChunks.$inferSelect;
