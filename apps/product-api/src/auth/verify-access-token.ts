import {
  createRemoteJWKSet,
  jwtVerify,
  type JWTVerifyGetKey,
  type JWTPayload
} from "jose";
import { z } from "zod";
import { getEnvironment } from "@/config/env";

const verifiedClaimsBrand: unique symbol = Symbol("VerifiedClaims");

export type VerifiedClaims = Readonly<{
  audience: string | readonly string[];
  expiresAt: number;
  issuer: string;
  role: "authenticated";
  subject: string;
  [verifiedClaimsBrand]: true;
}>;

export class AuthenticationError extends Error {
  readonly code:
    | "authentication_required"
    | "invalid_authorization_header"
    | "invalid_access_token";

  constructor(
    code:
      | "authentication_required"
      | "invalid_authorization_header"
      | "invalid_access_token"
  ) {
    super(code);
    this.name = "AuthenticationError";
    this.code = code;
  }
}

const subjectSchema = z.string().uuid();

const keySets = new Map<string, JWTVerifyGetKey>();

function remoteKeySet(url: string): JWTVerifyGetKey {
  const cached = keySets.get(url);
  if (cached) {
    return cached;
  }

  const created = createRemoteJWKSet(new URL(url), {
    cacheMaxAge: 10 * 60 * 1000,
    cooldownDuration: 30_000,
    timeoutDuration: 5_000
  });
  keySets.set(url, created);
  return created;
}

function toVerifiedClaims(
  payload: JWTPayload,
  expectedAudience: string,
  expectedIssuer: string
): VerifiedClaims {
  const subject = subjectSchema.parse(payload.sub);
  const audience = payload.aud;

  if (!audience) {
    throw new AuthenticationError("invalid_access_token");
  }

  const audienceValues = Array.isArray(audience) ? audience : [audience];
  if (!audienceValues.includes(expectedAudience)) {
    throw new AuthenticationError("invalid_access_token");
  }

  if (
    payload.iss !== expectedIssuer ||
    payload.role !== "authenticated" ||
    typeof payload.exp !== "number"
  ) {
    throw new AuthenticationError("invalid_access_token");
  }

  return Object.freeze({
    audience,
    expiresAt: payload.exp,
    issuer: payload.iss,
    role: "authenticated",
    subject,
    [verifiedClaimsBrand]: true as const
  });
}

export function extractBearerToken(request: Request): string {
  const authorization = request.headers.get("authorization");

  if (!authorization) {
    throw new AuthenticationError("authentication_required");
  }

  const match = /^Bearer ([A-Za-z0-9._~-]+)$/.exec(authorization);
  if (!match?.[1]) {
    throw new AuthenticationError("invalid_authorization_header");
  }

  return match[1];
}

export async function verifyAccessToken(
  token: string,
  options?: Readonly<{
    audience?: string;
    issuer?: string;
    keySet?: JWTVerifyGetKey;
  }>
): Promise<VerifiedClaims> {
  const environment = options ? undefined : getEnvironment();
  const audience =
    options?.audience ?? environment?.supabaseJwtAudience ?? "authenticated";
  const issuer = options?.issuer ?? environment?.supabaseJwtIssuer;
  const keySet =
    options?.keySet ??
    remoteKeySet(environment?.supabaseJwksUrl ?? getEnvironment().supabaseJwksUrl);

  if (!issuer) {
    throw new AuthenticationError("invalid_access_token");
  }

  try {
    const { payload } = await jwtVerify(token, keySet, {
      algorithms: ["ES256", "RS256", "EdDSA"],
      audience,
      issuer,
      requiredClaims: ["sub", "role", "exp", "iss", "aud"]
    });
    return toVerifiedClaims(payload, audience, issuer);
  } catch (error) {
    if (error instanceof AuthenticationError) {
      throw error;
    }
    throw new AuthenticationError("invalid_access_token");
  }
}

export async function authenticateRequest(
  request: Request
): Promise<VerifiedClaims> {
  return verifyAccessToken(extractBearerToken(request));
}
