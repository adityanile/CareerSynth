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
