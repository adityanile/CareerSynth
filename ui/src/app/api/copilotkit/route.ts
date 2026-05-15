import { handleCopilotRuntimeRequest } from "@/lib/copilot-runtime";
import { resolveDefaultIntegrationId } from "@/lib/integration-config";
import { NextRequest } from "next/server";

const handleIntegrationRequest = async (req: NextRequest) => {
  const authorizationHeader = req.headers.get("authorization");
  const accessToken =
    authorizationHeader?.startsWith("Bearer ")
      ? authorizationHeader.slice("Bearer ".length).trim()
      : undefined;
  const authRequired = process.env.ENTRA_AUTH_REQUIRED === "true";

  if (authRequired && !accessToken) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  const integrationId = resolveDefaultIntegrationId();
  return handleCopilotRuntimeRequest(req, integrationId, "/api/copilotkit");
};

export const GET = handleIntegrationRequest;
export const POST = handleIntegrationRequest;
export const PATCH = handleIntegrationRequest;
export const DELETE = handleIntegrationRequest;
export const OPTIONS = handleIntegrationRequest;

