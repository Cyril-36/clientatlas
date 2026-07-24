import { describe, expect, it } from "vitest";
import {
  membershipUserIdSchema,
  setMembershipSchema
} from "@/validation/memberships";

describe("membership validation", () => {
  it("accepts an explicit organization role and UUID", () => {
    expect(
      setMembershipSchema.parse({
        role: "editor",
        userId: "9b3b84bc-d195-40f1-a399-049858ff7df6"
      })
    ).toEqual({
      role: "editor",
      userId: "9b3b84bc-d195-40f1-a399-049858ff7df6"
    });
  });

  it("rejects an unknown role", () => {
    expect(() =>
      setMembershipSchema.parse({
        role: "superadmin",
        userId: "9b3b84bc-d195-40f1-a399-049858ff7df6"
      })
    ).toThrow();
  });

  it("rejects malformed user identifiers", () => {
    expect(() => membershipUserIdSchema.parse("../../admin")).toThrow();
  });
});
