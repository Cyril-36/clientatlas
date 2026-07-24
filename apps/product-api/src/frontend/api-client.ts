export type AccessTokenProvider = () => Promise<string | null>;

export type ApiClientOptions = Readonly<{
  aiBaseUrl?: string;
  getAccessToken: AccessTokenProvider;
}>;

export type SseEvent =
  | Readonly<{ event: "progress"; data: Record<string, unknown> }>
  | Readonly<{ event: "answer"; data: Record<string, unknown> }>
  | Readonly<{ event: "citation"; data: Record<string, unknown> }>
  | Readonly<{ event: "complete"; data: Record<string, unknown> }>;

async function authorizedHeaders(
  getAccessToken: AccessTokenProvider,
  contentType = true
): Promise<HeadersInit> {
  const token = await getAccessToken();
  if (!token) {
    throw new Error("authentication_required");
  }
  return {
    Authorization: `Bearer ${token}`,
    ...(contentType ? { "Content-Type": "application/json" } : {})
  };
}

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as
      | { error?: { code?: string } }
      | null;
    throw new Error(body?.error?.code ?? `request_failed_${response.status}`);
  }
  return (await response.json()) as T;
}

export function createApiClient(options: ApiClientOptions) {
  const aiBaseUrl = options.aiBaseUrl ?? "http://127.0.0.1:8000";

  return {
    async createOrganization(input: { name: string; slug: string }) {
      return readJson<unknown>(
        await fetch("/api/v1/organizations", {
          body: JSON.stringify(input),
          headers: await authorizedHeaders(options.getAccessToken),
          method: "POST"
        })
      );
    },

    async createWorkspace(
      organizationId: string,
      input: {
        description?: string;
        name: string;
        privacyMode: "local_confidential" | "synthetic_demo";
      }
    ) {
      return readJson<unknown>(
        await fetch(`/api/v1/organizations/${organizationId}/workspaces`, {
          body: JSON.stringify(input),
          headers: await authorizedHeaders(options.getAccessToken),
          method: "POST"
        })
      );
    },

    async setMembership(
      organizationId: string,
      input: {
        role: "admin" | "editor" | "owner" | "viewer";
        userId: string;
      }
    ) {
      return readJson<unknown>(
        await fetch(`/api/v1/organizations/${organizationId}/memberships`, {
          body: JSON.stringify(input),
          headers: await authorizedHeaders(options.getAccessToken),
          method: "POST"
        })
      );
    },

    async listSources(organizationId: string, workspaceId: string) {
      return readJson<unknown>(
        await fetch(
          `${aiBaseUrl}/v1/organizations/${organizationId}/workspaces/${workspaceId}/sources`,
          { headers: await authorizedHeaders(options.getAccessToken, false) }
        )
      );
    },

    async uploadSource(
      organizationId: string,
      workspaceId: string,
      file: File
    ) {
      const form = new FormData();
      form.set("file", file);
      return readJson<unknown>(
        await fetch(
          `${aiBaseUrl}/v1/organizations/${organizationId}/workspaces/${workspaceId}/sources`,
          {
            body: form,
            headers: await authorizedHeaders(options.getAccessToken, false),
            method: "POST"
          }
        )
      );
    },

    async streamChat(
      organizationId: string,
      workspaceId: string,
      body: Record<string, unknown>,
      onEvent: (event: SseEvent) => void,
      signal?: AbortSignal
    ) {
      const response = await fetch(
        `${aiBaseUrl}/v1/organizations/${organizationId}/workspaces/${workspaceId}/chat/stream`,
        {
          body: JSON.stringify(body),
          headers: await authorizedHeaders(options.getAccessToken),
          method: "POST",
          ...(signal ? { signal } : {})
        }
      );
      if (!response.ok || !response.body) {
        throw new Error(`chat_stream_failed_${response.status}`);
      }

      const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += value;
        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() ?? "";
        for (const block of blocks) {
          const eventLine = block
            .split("\n")
            .find((line) => line.startsWith("event:"));
          const dataLine = block
            .split("\n")
            .find((line) => line.startsWith("data:"));
          if (!eventLine || !dataLine) continue;
          const event = eventLine.slice(6).trim() as SseEvent["event"];
          const data = JSON.parse(dataLine.slice(5).trim()) as Record<
            string,
            unknown
          >;
          onEvent({ data, event } as SseEvent);
        }
      }
    }
  };
}
