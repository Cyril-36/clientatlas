import * as schema from "@clientatlas/database";
import { drizzle, type PostgresJsDatabase } from "drizzle-orm/postgres-js";
import { sql } from "drizzle-orm";
import postgres from "postgres";
import type { VerifiedClaims } from "@/auth/verify-access-token";
import { getEnvironment } from "@/config/env";

type Database = PostgresJsDatabase<typeof schema>;
export type UserTransaction = Parameters<
  Parameters<Database["transaction"]>[0]
>[0];

let database: Database | undefined;

function getDatabase(): Database {
  if (database) {
    return database;
  }

  const client = postgres(getEnvironment().userDatabaseUrl, {
    max: 10,
    prepare: false
  });
  database = drizzle(client, { schema });
  return database;
}

function databaseClaims(claims: VerifiedClaims): Record<string, unknown> {
  return {
    aud: claims.audience,
    exp: claims.expiresAt,
    iss: claims.issuer,
    role: claims.role,
    sub: claims.subject
  };
}

export async function withUserDatabase<T>(
  claims: VerifiedClaims,
  operation: (transaction: UserTransaction) => Promise<T>
): Promise<T> {
  return getDatabase().transaction(async (transaction) => {
    await transaction.execute(
      sql`select set_config(
        'request.jwt.claims',
        ${JSON.stringify(databaseClaims(claims))},
        true
      )`
    );

    // Fixed SQL identifier. Never interpolate request input into SET ROLE.
    await transaction.execute(sql`set local role authenticated`);

    return operation(transaction);
  });
}

