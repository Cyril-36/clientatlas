# ClientAtlas Dependency Risk Register

| Field | Value |
| --- | --- |
| Status | Open, accepted for V1 application |
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

The implemented Next.js application now serves the product UI and route
handlers:

- user-authored CSS is compiled at build time;
- runtime requests cannot submit stylesheets for transformation;
- no image upload or image-optimization route;
- no use of Next.js image optimization for untrusted URLs; and
- no untrusted source maps.

The frontend increases package reachability compared with the original
headless host. The application therefore retains this as an explicit release
risk rather than treating the earlier reduced exposure as sufficient.

### Mitigations

- Keep remote images and runtime stylesheet transformation disabled.
- Use local CSS and Lucide SVG components rather than untrusted image URLs.
- Run `npm audit --omit=dev` on every dependency update.
- CI blocks critical advisories while this documented high-severity exception is
  open.
- Upgrade to the first compatible stable Next.js release that resolves both
  dependency chains.
- Reassess reachability before public deployment and after each Next.js update.

### Closure

Close only when:

1. Next.js resolves to non-vulnerable PostCSS and Sharp versions;
2. `npm audit --omit=dev` reports no corresponding advisories;
3. the production build passes; and
4. API and RLS tests remain green.
