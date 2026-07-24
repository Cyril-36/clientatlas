import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  description:
    "Evidence-backed client onboarding briefs, readiness reports, and cited answers.",
  title: {
    default: "ClientAtlas",
    template: "%s · ClientAtlas"
  }
};

export default function RootLayout({
  children
}: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">
          Skip to main content
        </a>
        {children}
      </body>
    </html>
  );
}
