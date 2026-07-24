# ClientAtlas Backend API

The repository intentionally contains no frontend. The generated FastAPI
contract is committed at `packages/contracts/openapi/ai-service.json`.

All tenant endpoints require a Supabase access token:

```http
Authorization: Bearer <access-token>
```

## Product API

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Product API health |
| GET/POST | `/api/v1/organizations` | List or create organizations |
| GET/POST | `/api/v1/organizations/{organizationId}/workspaces` | List or create workspaces |
| GET/POST | `/api/v1/organizations/{organizationId}/memberships` | List or set memberships |
| DELETE | `/api/v1/organizations/{organizationId}/memberships/{userId}` | Remove a membership |

## AI service

The common prefix below is
`/v1/organizations/{organizationId}/workspaces/{workspaceId}`.

| Method | Route suffix | Purpose |
| --- | --- | --- |
| GET/POST | `/sources` | List sources or upload PDF/DOCX |
| POST | `/sources/{sourceId}/reindex` | Retry or re-index a source |
| DELETE | `/sources/{sourceId}` | Delete active source data |
| POST | `/retrieve` | Return hybrid evidence candidates |
| POST | `/chat/stream` | Stream validated answer and citation SSE events |
| GET | `/artifacts` | List current artifact versions |
| POST | `/artifacts/generate` | Generate a structured artifact |
| GET | `/artifacts/{artifactId}/versions` | Read immutable history |
| POST | `/artifacts/{artifactId}/versions` | Save an edited version |
| POST | `/connectors/google-drive/authorize` | Begin PKCE OAuth |
| POST | `/connectors/google-drive/callback` | Consume state and save credentials |
| POST | `/connectors/google-drive/import` | Import one selected Drive file |
| DELETE | `/connectors/google-drive` | Revoke and remove credentials |

## Streaming contract

`POST /chat/stream` returns `text/event-stream`. Event order is `progress`,
`answer`, zero or more `citation` events, then `complete`.

Answers use `contentFormat: plain_text`. The frontend must not reinterpret this
field as trusted HTML.

## Frontend integration boundary

The frontend may use Supabase Auth and Google Picker, but it must never:

- query tenant tables with a service-role key;
- construct object paths;
- accept citation IDs that were not returned by the backend;
- expose refresh tokens or the server token-encryption key; or
- enable Gemini for a `local_confidential` workspace.
