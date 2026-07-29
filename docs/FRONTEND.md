# ClientAtlas Frontend

The frontend is implemented in `apps/product-api` using Next.js, React,
TypeScript, local CSS design tokens, Lucide icons, and the Supabase browser
client.

## Routes

| Route | Screen |
| --- | --- |
| `/overview` | Workspace readiness and activity |
| `/knowledge` | PDF/DOCX source library and document details |
| `/ask` | Streamed cited answers and extracted evidence |
| `/onboarding-brief` | Editable evidence-linked brief |
| `/readiness-report` | Readiness categories and missing information |
| `/action-plan` | Structured versioned actions |
| `/integrations` | Google Drive status and deferred connectors |
| `/members` | Owner/admin/editor/viewer administration |
| `/settings` | Workspace privacy and deletion statements |
| `/sign-in`, `/sign-up` | Supabase authentication |
| `/recover-password`, `/verify-email` | Authentication recovery states |
| `/onboarding/*` | Organization, workspace, member, and document setup |
| `/permission-denied`, `/system-error` | Safe system states |

Loading and empty-state variants are available at `/overview/loading`,
`/knowledge/loading`, `/knowledge/empty`, and `/ask/empty`.

## Synthetic demonstration

`NEXT_PUBLIC_DEMO_MODE` defaults to `true`. In this mode:

- all displayed names and documents are fictional;
- uploads, connector changes, administrative actions, generation, and deletion
  are disabled;
- chat uses a deterministic local demonstration response; and
- no Supabase, FastAPI, Gemini, or local-model call is made from the demo
  question.

## Authenticated mode

Set `NEXT_PUBLIC_DEMO_MODE=false` and configure the browser-safe Supabase URL
and anonymous key. The anonymous key is public by design; a service-role key
must never be used.

The frontend sends the authenticated access token to the product API and AI
service. The server remains responsible for JWT verification, RLS, workspace
privacy routing, citation validation, and authorization.

`NEXT_PUBLIC_*` values are compiled into the browser bundle. Docker deployments
must provide them as build arguments rather than expecting runtime changes.

## Accessibility

The application includes:

- a skip link and landmark-based layout;
- labelled inputs and icon buttons;
- visible focus indicators;
- keyboard and Escape handling for navigation and dialogs;
- live regions for streaming and form feedback;
- reduced-motion and increased-contrast preferences; and
- responsive reflow down to a 320-pixel viewport.

Automated `jest-axe` checks cover every implemented screen. Manual browser
checks cover desktop and mobile navigation, focus restoration, overflow, and
dialog dismissal.
