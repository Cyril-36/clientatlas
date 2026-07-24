import { authenticateRequest } from "@/auth/verify-access-token";
import { withUserDatabase } from "@/db/user-database";
import {
  createOrganization,
  listOrganizations
} from "@/domain/organizations";
import {
  dataResponse,
  handleApiRequest,
  parseJson
} from "@/http/api-response";
import { createOrganizationSchema } from "@/validation/organizations";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request): Promise<Response> {
  return handleApiRequest(async () => {
    const claims = await authenticateRequest(request);
    const result = await withUserDatabase(claims, (transaction) =>
      listOrganizations(transaction, claims.subject)
    );
    return dataResponse(result);
  });
}

export async function POST(request: Request): Promise<Response> {
  return handleApiRequest(async () => {
    const claims = await authenticateRequest(request);
    const input = await parseJson(request, (value) =>
      createOrganizationSchema.parse(value)
    );
    const result = await withUserDatabase(claims, (transaction) =>
      createOrganization(transaction, input)
    );
    return dataResponse(result, 201);
  });
}

