# Free Public Demo Runbook

The public deployment is synthetic and read-only.

- Seed only `packages/evaluation/corpus`.
- Disable anonymous uploads, OAuth callbacks, membership mutation, deletion,
  and artifact editing at the deployment gateway.
- Rate-limit chat and generation.
- Use a `synthetic_demo` workspace.
- Never copy real client data into the hosted database.
- Display free-tier cold-start and inactivity limitations.

The backend cannot create a paid resource. The account owner must still verify
that spending is disabled or capped before deployment.

No public URL is recorded because no hosting account or deployment
authorization was provided.
