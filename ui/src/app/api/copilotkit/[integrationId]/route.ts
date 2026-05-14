import { handleCopilotRuntimeRequest } from "@/lib/copilot-runtime";
import { NextRequest } from "next/server";

interface IntegrationRouteContext {
  params: Promise<{
    integrationId: string;
  }>;
}

const handleIntegrationRequest = async (
  req: NextRequest,
  context: IntegrationRouteContext,
) => {
  const { integrationId } = await context.params;
  const authorizationHeader = req.headers.get("authorization");
  const accessToken =
    authorizationHeader?.startsWith("Bearer ")
      ? authorizationHeader.slice("Bearer ".length).trim()
      : undefined;
  const authRequired = process.env.ENTRA_AUTH_REQUIRED === "true";

  if (authRequired && !accessToken) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  return handleCopilotRuntimeRequest(
    req,
    integrationId,
    `/api/copilotkit/${integrationId}`,
  );
};

export const GET = handleIntegrationRequest;
export const POST = handleIntegrationRequest;
export const PATCH = handleIntegrationRequest;
export const DELETE = handleIntegrationRequest;
export const OPTIONS = handleIntegrationRequest;
