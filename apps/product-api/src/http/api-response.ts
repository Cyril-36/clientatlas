import { ZodError } from "zod";
import { AuthenticationError } from "@/auth/verify-access-token";

type ErrorCode =
  | "authentication_required"
  | "invalid_authorization_header"
  | "invalid_access_token"
  | "invalid_request"
  | "not_found"
  | "conflict"
  | "internal_error";

const headers = {
  "cache-control": "no-store",
  "content-type": "application/json",
  "x-content-type-options": "nosniff"
};

export function dataResponse<T>(data: T, status = 200): Response {
  return Response.json({ data }, { headers, status });
}

export function errorResponse(
  code: ErrorCode,
  status: number,
  message: string
): Response {
  return Response.json(
    {
      error: {
        code,
        message
      }
    },
    { headers, status }
  );
}

export async function parseJson<T>(
  request: Request,
  parser: (value: unknown) => T
): Promise<T> {
  let value: unknown;
  try {
    value = await request.json();
  } catch {
    throw new ZodError([]);
  }
  return parser(value);
}

export async function handleApiRequest(
  operation: () => Promise<Response>
): Promise<Response> {
  try {
    return await operation();
  } catch (error) {
    if (error instanceof AuthenticationError) {
      const status = error.code === "authentication_required" ? 401 : 403;
      return errorResponse(error.code, status, "Authentication failed");
    }

    if (error instanceof ZodError) {
      return errorResponse("invalid_request", 400, "Request validation failed");
    }

    // Full error details belong in structured server logs, not responses.
    console.error("api_request_failed", {
      errorName: error instanceof Error ? error.name : "UnknownError"
    });
    return errorResponse("internal_error", 500, "Request failed");
  }
}

