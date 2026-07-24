// @vitest-environment jsdom

import "@testing-library/jest-dom/vitest";

import { cleanup, render } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ClientAtlasApp } from "@/frontend/clientatlas-app";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() })
}));

expect.extend(toHaveNoViolations);

afterEach(cleanup);

describe("frontend accessibility", () => {
  it.each(
    [
      "overview",
      "overview/loading",
      "knowledge",
      "knowledge/loading",
      "knowledge/empty",
      "ask",
      "ask/empty",
      "onboarding-brief",
      "readiness-report",
      "action-plan",
      "integrations",
      "members",
      "settings",
      "permission-denied",
      "system-error"
    ] as const
  )(
    "has no automated WCAG violations on %s",
    async (route) => {
      const { container } = render(<ClientAtlasApp route={route} />);
      expect(await axe(container)).toHaveNoViolations();
    }
  );

  it.each(
    [
      "sign-in",
      "sign-up",
      "recover-password",
      "verify-email",
      "onboarding/organization",
      "onboarding/workspace",
      "onboarding/members",
      "onboarding/documents"
    ] as const
  )("has no automated WCAG violations on %s", async (route) => {
    const { container } = render(<ClientAtlasApp route={route} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
