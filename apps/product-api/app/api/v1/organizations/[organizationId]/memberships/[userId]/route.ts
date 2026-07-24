import { authenticateRequest } from "@/auth/verify-access-token";
import { withUserDatabase } from "@/db/user-database";
import { removeMembership } from "@/domain/memberships";
import { dataResponse, handleApiRequest } from "@/http/api-response";
import { membershipUserIdSchema } from "@/validation/memberships";
import { organizationIdSchema } from "@/validation/workspaces";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type Context = {
  params: Promise<{ organizationId: string; userId: string }>;
};

export async function DELETE(
  request: Request,
  context: Context
): Promise<Response> {
  return handleApiRequest(async () => {
    const claims = await authenticateRequest(request);
    const params = await context.params;
    const organizationId = organizationIdSchema.parse(params.organizationId);
    const userId = membershipUserIdSchema.parse(params.userId);
    const removed = await withUserDatabase(claims, (transaction) =>
      removeMembership(transaction, organizationId, userId)
    );
    return dataResponse({ removed });
  });
}
