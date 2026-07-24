import { authenticateRequest } from "@/auth/verify-access-token";
import { withUserDatabase } from "@/db/user-database";
import {
  createWorkspace,
  listWorkspaces
} from "@/domain/workspaces";
import {
  dataResponse,
  handleApiRequest,
  parseJson
} from "@/http/api-response";
import {
  createWorkspaceSchema,
  organizationIdSchema
} from "@/validation/workspaces";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type Context = {
  params: Promise<{
    organizationId: string;
  }>;
};

export async function GET(
  request: Request,
  context: Context
): Promise<Response> {
  return handleApiRequest(async () => {
    const claims = await authenticateRequest(request);
    const { organizationId: rawOrganizationId } = await context.params;
    const organizationId = organizationIdSchema.parse(rawOrganizationId);
    const result = await withUserDatabase(claims, (transaction) =>
      listWorkspaces(transaction, organizationId)
    );
    return dataResponse(result);
  });
}

export async function POST(
  request: Request,
  context: Context
): Promise<Response> {
  return handleApiRequest(async () => {
    const claims = await authenticateRequest(request);
    const { organizationId: rawOrganizationId } = await context.params;
    const organizationId = organizationIdSchema.parse(rawOrganizationId);
    const input = await parseJson(request, (value) =>
      createWorkspaceSchema.parse(value)
    );
    const result = await withUserDatabase(claims, (transaction) =>
      createWorkspace(
        transaction,
        organizationId,
        claims.subject,
        input
      )
    );
    return dataResponse(result, 201);
  });
}

