import {
  createLocalJWKSet,
  exportJWK,
  generateKeyPair,
  SignJWT
} from "jose";
import { describe, expect, it } from "vitest";
import {
  AuthenticationError,
  extractBearerToken,
  verifyAccessToken
} from "@/auth/verify-access-token";

const issuer = "https://example.supabase.co/auth/v1";
const audience = "authenticated";

async function tokenFixture(
  overrides: Readonly<{
    audience?: string;
    expiresAt?: number;
    issuer?: string;
    role?: string;
    subject?: string;
  }> = {}
) {
  const { privateKey, publicKey } = await generateKeyPair("RS256");
  const publicJwk = await exportJWK(publicKey);
  publicJwk.alg = "RS256";
  publicJwk.kid = "test-key";
  publicJwk.use = "sig";

  const now = Math.floor(Date.now() / 1000);
  const token = await new SignJWT({
    role: overrides.role ?? "authenticated"
  })
    .setProtectedHeader({ alg: "RS256", kid: "test-key", typ: "JWT" })
    .setAudience(overrides.audience ?? audience)
    .setExpirationTime(overrides.expiresAt ?? now + 300)
    .setIssuedAt(now)
    .setIssuer(overrides.issuer ?? issuer)
    .setSubject(
      overrides.subject ?? "50f10f9f-ff74-4cc0-9ca2-da246ae5d593"
    )
    .sign(privateKey);

  return {
    keySet: createLocalJWKSet({ keys: [publicJwk] }),
    token
  };
}

describe("extractBearerToken", () => {
  it("extracts a strict bearer token", () => {
    const request = new Request("https://example.test", {
      headers: {
        authorization: "Bearer a.b.c"
      }
    });
    expect(extractBearerToken(request)).toBe("a.b.c");
  });

  it.each([
    undefined,
    "bearer a.b.c",
    "Bearer",
    "Bearer a.b.c extra"
  ])("rejects malformed authorization: %s", (authorization) => {
    const request = new Request(
      "https://example.test",
      authorization ? { headers: { authorization } } : {}
    );
    expect(() => extractBearerToken(request)).toThrow(AuthenticationError);
  });
});


describe("verifyAccessToken", () => {
  it("returns branded verified claims for a valid token", async () => {
    const fixture = await tokenFixture();
    const claims = await verifyAccessToken(fixture.token, {
      audience,
      issuer,
      keySet: fixture.keySet
    });

    expect(claims).toMatchObject({
      issuer,
      role: "authenticated",
      subject: "50f10f9f-ff74-4cc0-9ca2-da246ae5d593"
    });
  });

  it.each([
    { audience: "wrong" },
    { issuer: "https://attacker.invalid/auth/v1" },
    { role: "service_role" },
    { subject: "not-a-uuid" },
    { expiresAt: 1 }
  ])("rejects invalid claims: %o", async (overrides) => {
    const fixture = await tokenFixture(overrides);
    await expect(
      verifyAccessToken(fixture.token, {
        audience,
        issuer,
        keySet: fixture.keySet
      })
    ).rejects.toMatchObject({
      code: "invalid_access_token"
    });
  });
});
