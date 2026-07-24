import { describe, expect, it } from "vitest";
import { createOrganizationSchema } from "@/validation/organizations";
import { createWorkspaceSchema } from "@/validation/workspaces";

describe("organization validation", () => {
  it("accepts a normalized organization", () => {
    expect(
      createOrganizationSchema.parse({
        name: "Acme Consulting",
        slug: "acme-consulting"
      })
    ).toEqual({
      name: "Acme Consulting",
      slug: "acme-consulting"
    });
  });

  it.each(["ACME", "../acme", "acme_", "ab"])(
    "rejects unsafe slug %s",
    (slug) => {
      expect(() =>
        createOrganizationSchema.parse({ name: "Acme", slug })
      ).toThrow();
    }
  );
});

describe("workspace validation", () => {
  it("defaults to local confidential mode", () => {
    expect(
      createWorkspaceSchema.parse({
        name: "Implementation"
      })
    ).toMatchObject({
      name: "Implementation",
      privacyMode: "local_confidential"
    });
  });
});

