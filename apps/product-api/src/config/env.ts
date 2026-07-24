import { z } from "zod";

const environmentSchema = z.object({
  NODE_ENV: z
    .enum(["development", "test", "production"])
    .default("development"),
  SUPABASE_JWT_AUDIENCE: z.string().min(1).default("authenticated"),
  SUPABASE_JWT_ISSUER: z.string().url(),
  SUPABASE_JWKS_URL: z.string().url(),
  USER_DATABASE_URL: z.string().url()
});

export type ApplicationEnvironment = Readonly<{
  nodeEnv: "development" | "test" | "production";
  supabaseJwtAudience: string;
  supabaseJwtIssuer: string;
  supabaseJwksUrl: string;
  userDatabaseUrl: string;
}>;

let cachedEnvironment: ApplicationEnvironment | undefined;

export function getEnvironment(): ApplicationEnvironment {
  if (cachedEnvironment) {
    return cachedEnvironment;
  }

  const parsed = environmentSchema.parse(process.env);
  cachedEnvironment = Object.freeze({
    nodeEnv: parsed.NODE_ENV,
    supabaseJwtAudience: parsed.SUPABASE_JWT_AUDIENCE,
    supabaseJwtIssuer: parsed.SUPABASE_JWT_ISSUER,
    supabaseJwksUrl: parsed.SUPABASE_JWKS_URL,
    userDatabaseUrl: parsed.USER_DATABASE_URL
  });
  return cachedEnvironment;
}

