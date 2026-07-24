import { authenticateRequest } from "@/auth/verify-access-token";
import { withUserDatabase } from "@/db/user-database";
import { listMemberships, setMembership } from "@/domain/memberships";
import {
  dataResponse,
  handleApiRequest,
  parseJson
} from "@/http/api-response";
import { setMembershipSchema } from "@/validation/memberships";
import { organizationIdSchema } from "@/validation/workspaces";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type Context = {
  params: Promise<{ organizationId: string }>;
};

export async function GET(
  request: Request,
  context: Context
): Promise<Response> {
  return handleApiRequest(async () => {
    const claims = await authenticateRequest(request);
    const { organizationId: rawOrganizationId } = await context.params;
    const organizationId = organizationIdSchema.parse(rawOrganizationId);
    const memberships = await withUserDatabase(claims, (transaction) =>
      listMemberships(transaction, organizationId)
    );
    return dataResponse(memberships);
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
      setMembershipSchema.parse(value)
    );
    const membership = await withUserDatabase(claims, (transaction) =>
      setMembership(transaction, organizationId, input.userId, input.role)
    );
    return dataResponse(membership, 201);
  });
}
