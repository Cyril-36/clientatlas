import { createHash } from "node:crypto";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import postgres from "postgres";

const migrationDatabaseUrl = process.env.MIGRATION_DATABASE_URL;

if (!migrationDatabaseUrl) {
  throw new Error("MIGRATION_DATABASE_URL is required");
}

const packageDirectory = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  ".."
);
const migrationsDirectory = path.join(packageDirectory, "migrations", "manual");

const sql = postgres(migrationDatabaseUrl, {
  max: 1,
  onnotice: () => undefined
});

try {
  await sql`
    create table if not exists public.clientatlas_schema_migrations (
      name text primary key,
      checksum text not null,
      applied_at timestamptz not null default now()
    )
  `;

  const files = (await readdir(migrationsDirectory))
    .filter((file) => file.endsWith(".sql"))
    .sort();

  for (const file of files) {
    const migration = await readFile(
      path.join(migrationsDirectory, file),
      "utf8"
    );
    const checksum = createHash("sha256").update(migration).digest("hex");
    const applied = await sql<
      { checksum: string }[]
    >`select checksum from public.clientatlas_schema_migrations where name = ${file}`;

    if (applied[0]) {
      if (applied[0].checksum !== checksum) {
        throw new Error(`Applied migration checksum changed: ${file}`);
      }
      continue;
    }

    await sql.begin(async (transaction) => {
      await transaction.unsafe(migration);
      await transaction`
        insert into public.clientatlas_schema_migrations (name, checksum)
        values (${file}, ${checksum})
      `;
    });
  }
} finally {
  await sql.end();
}

