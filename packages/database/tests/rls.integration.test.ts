import { randomUUID } from "node:crypto";
import postgres, { type Sql, type TransactionSql } from "postgres";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

const migrationUrl = process.env.TEST_MIGRATION_DATABASE_URL;
const userUrl = process.env.TEST_USER_DATABASE_URL;
const integrationEnabled = Boolean(migrationUrl && userUrl);

const suite = integrationEnabled ? describe : describe.skip;

suite("identity and tenancy RLS", () => {
  let admin: Sql;
  let runtime: Sql;
  const userA = randomUUID();
  const userB = randomUUID();
  const userC = randomUUID();
  let organizationA: string;
  let workspaceA: string;

  async function asUser<T>(
    userId: string,
    operation: (transaction: TransactionSql) => Promise<T>
  ): Promise<T> {
    return runtime.begin(async (transaction) => {
      const claims = JSON.stringify({
        aud: "authenticated",
        exp: Math.floor(Date.now() / 1000) + 300,
        iss: "https://test.supabase.co/auth/v1",
        role: "authenticated",
        sub: userId
      });
      await transaction`select set_config('request.jwt.claims', ${claims}, true)`;
      await transaction`set local role authenticated`;
      return operation(transaction);
    }) as Promise<T>;
  }

  beforeAll(async () => {
    admin = postgres(migrationUrl!, { max: 1 });
    runtime = postgres(userUrl!, { max: 1 });

    await admin`
      insert into auth.users (id, email)
      values
        (${userA}, ${`user-a-${userA}@example.test`}),
        (${userB}, ${`user-b-${userB}@example.test`}),
        (${userC}, ${`user-c-${userC}@example.test`})
    `;

    organizationA = await asUser(userA, async (transaction) => {
      const rows = await transaction<{ id: string }[]>`
        select app.create_organization(
          ${`Tenant ${userA}`},
          ${`tenant-${userA}`}
        ) as id
      `;
      return rows[0]!.id;
    });

    workspaceA = await asUser(userA, async (transaction) => {
      const rows = await transaction<{ id: string }[]>`
        insert into app.workspaces (
          organization_id,
          name,
          privacy_mode,
          created_by
        )
        values (
          ${organizationA},
          'Implementation',
          'local_confidential',
          ${userA}
        )
        returning id
      `;
      return rows[0]!.id;
    });
  });

  afterAll(async () => {
    if (admin) {
      await admin`delete from app.organizations where id = ${organizationA}`;
      await admin`delete from auth.users where id in (${userA}, ${userB}, ${userC})`;
      await admin.end();
    }
    if (runtime) {
      await runtime.end();
    }
  });

  it("exposes organization and workspace only to a member", async () => {
    const visibleToA = await asUser(userA, (transaction) =>
      transaction<{ id: string }[]>`
        select id from app.workspaces where id = ${workspaceA}
      `
    );
    const visibleToB = await asUser(userB, (transaction) =>
      transaction<{ id: string }[]>`
        select id from app.workspaces where id = ${workspaceA}
      `
    );

    expect(visibleToA).toHaveLength(1);
    expect(visibleToB).toHaveLength(0);
  });

  it("prevents a non-member from inserting into another tenant", async () => {
    await expect(
      asUser(userB, (transaction) =>
        transaction`
          insert into app.workspaces (
            organization_id,
            name,
            privacy_mode,
            created_by
          )
          values (
            ${organizationA},
            'Unauthorized',
            'local_confidential',
            ${userB}
          )
        `
      )
    ).rejects.toBeDefined();
  });

  it("sets the claims and effective role only inside the transaction", async () => {
    const context = await asUser(userA, async (transaction) => {
      const rows = await transaction<
        { current_role: string; user_id: string }[]
      >`
        select current_role, auth.uid()::text as user_id
      `;
      return rows[0]!;
    });
    expect(context).toEqual({
      current_role: "authenticated",
      user_id: userA
    });

    const after = await runtime<
      { claims: string | null; current_role: string }[]
    >`
      select
        nullif(current_setting('request.jwt.claims', true), '') as claims,
        current_role
    `;
    expect(after[0]).toEqual({
      claims: null,
      current_role: "clientatlas_runtime"
    });
  });

  it("uses a non-owner NOBYPASSRLS runtime role and forced RLS", async () => {
    const roles = await admin<
      { rolbypassrls: boolean; rolname: string; rolsuper: boolean }[]
    >`
      select rolname, rolsuper, rolbypassrls
      from pg_roles
      where rolname = 'clientatlas_runtime'
    `;
    expect(roles[0]).toEqual({
      rolbypassrls: false,
      rolname: "clientatlas_runtime",
      rolsuper: false
    });

    const tables = await admin<
      { owner: string; relforcerowsecurity: boolean; relname: string }[]
    >`
      select
        class.relname,
        class.relforcerowsecurity,
        pg_get_userbyid(class.relowner) as owner
      from pg_class class
      join pg_namespace namespace on namespace.oid = class.relnamespace
      where namespace.nspname = 'app'
        and class.relkind = 'r'
    `;
    expect(tables.length).toBeGreaterThanOrEqual(4);
    for (const table of tables) {
      expect(table.relforcerowsecurity).toBe(true);
      expect(table.owner).not.toBe("clientatlas_runtime");
    }
  });

  it("enforces the editor and viewer authorization matrix", async () => {
    await asUser(userA, (transaction) =>
      transaction`
        select app.set_organization_membership(
          ${organizationA},
          ${userB},
          'editor'::app.organization_role
        )
      `
    );
    await asUser(userA, (transaction) =>
      transaction`
        select app.set_organization_membership(
          ${organizationA},
          ${userC},
          'viewer'::app.organization_role
        )
      `
    );

    const editorRows = await asUser(userB, (transaction) =>
      transaction<{ id: string }[]>`
        insert into app.workspaces (
          organization_id,
          name,
          privacy_mode,
          created_by
        )
        values (
          ${organizationA},
          'Editor workspace',
          'local_confidential',
          ${userB}
        )
        returning id
      `
    );
    expect(editorRows).toHaveLength(1);

    await expect(
      asUser(userC, (transaction) =>
        transaction`
          insert into app.workspaces (
            organization_id,
            name,
            privacy_mode,
            created_by
          )
          values (
            ${organizationA},
            'Viewer workspace',
            'local_confidential',
            ${userC}
          )
        `
      )
    ).rejects.toBeDefined();
  });

  it("prevents deleting the last owner", async () => {
    await expect(
      asUser(userA, (transaction) =>
        transaction`
          select app.remove_organization_membership(
            ${organizationA},
            ${userA}
          )
        `
      )
    ).rejects.toBeDefined();
  });
});
