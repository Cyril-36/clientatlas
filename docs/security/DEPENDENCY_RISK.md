# ClientAtlas Dependency Risk Register

| Field | Value |
| --- | --- |
| Status | Open, accepted for backend foundation only |
| Recorded | 2026-07-24 |
| Revisit | Every Next.js stable release and before public deployment |

## DR-001: Next.js transitive PostCSS and Sharp advisories

### Evidence

`npm audit --omit=dev` reports three high-severity advisories through the current
stable Next.js 16.2.11 dependency tree:

- PostCSS at 8.4.31
- Sharp at 0.34.5

The audit tool's automatic `--force` remediation proposes Next.js 9.3.3. That
downgrade is rejected because it is a major, unsupported architecture change
and would not be a safe remediation.

### Current exposure

The implemented Next.js application is a headless route-handler host:

- no pages or user-authored CSS;
- no stylesheet transformation endpoint;
- no image upload or image-optimization route;
- no frontend assets; and
- no untrusted source maps.

This reduces reachability but does not remove the vulnerable packages.

### Mitigations

- Do not add CSS, image handling, or frontend features in this repository.
- Keep the Node API container and dependencies minimal.
- Run `npm audit --omit=dev` on every dependency update.
- CI blocks critical advisories while this documented high-severity exception is
  open.
- Upgrade to the first compatible stable Next.js release that resolves both
  dependency chains.
- Reassess reachability before any public deployment.

### Closure

Close only when:

1. Next.js resolves to non-vulnerable PostCSS and Sharp versions;
2. `npm audit --omit=dev` reports no corresponding advisories;
3. the production build passes; and
4. API and RLS tests remain green.

