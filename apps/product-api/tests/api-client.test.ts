import { afterEach, describe, expect, it, vi } from "vitest";

import { createApiClient } from "@/frontend/api-client";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("frontend API client", () => {
  it("adds only the authenticated user's bearer token", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(JSON.stringify({ data: { id: "organization-id" } }), {
          headers: { "Content-Type": "application/json" },
          status: 201
        })
      );
    const client = createApiClient({
      getAccessToken: async () => "verified-user-token"
    });

    await client.createOrganization({
      name: "Northstar Studio",
      slug: "northstar-studio"
    });

    const init = fetchMock.mock.calls[0]?.[1];
    expect(init?.headers).toMatchObject({
      Authorization: "Bearer verified-user-token",
      "Content-Type": "application/json"
    });
    expect(init?.body).toBe(
      JSON.stringify({
        name: "Northstar Studio",
        slug: "northstar-studio"
      })
    );
  });

  it("refuses tenant API calls when no user session exists", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    const client = createApiClient({
      getAccessToken: async () => null
    });

    await expect(
      client.createOrganization({
        name: "Northstar Studio",
        slug: "northstar-studio"
      })
    ).rejects.toThrow("authentication_required");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("parses the streamed chat event contract", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        [
          'event: progress\ndata: {"stage":"retrieving"}',
          'event: answer\ndata: {"content":"Supported answer","contentFormat":"plain_text"}',
          'event: complete\ndata: {"conversationId":"00000000-0000-4000-8000-000000000001"}',
          ""
        ].join("\n\n"),
        {
          headers: { "Content-Type": "text/event-stream" },
          status: 200
        }
      )
    );
    const client = createApiClient({
      getAccessToken: async () => "verified-user-token"
    });
    const events: string[] = [];

    await client.streamChat(
      "00000000-0000-4000-8000-000000000010",
      "00000000-0000-4000-8000-000000000020",
      { question: "What is supported?", top_k: 8 },
      (event) => events.push(event.event)
    );

    expect(events).toEqual(["progress", "answer", "complete"]);
  });
});
