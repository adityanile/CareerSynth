import { HttpAgent } from "@ag-ui/client";
import { CopilotRuntime, ExperimentalEmptyAdapter } from "@copilotkit/runtime";
import { createCopilotHonoHandler } from "@copilotkit/runtime/v2";
import { handle as honoHandle } from "hono/vercel";
import { NextRequest } from "next/server";

function toEnvSuffix(value: string): string {
  return value.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase();
}

function resolveIntegrationConfig(integrationId: string) {
  const suffix = toEnvSuffix(integrationId);
  const integrationAgentUrl = process.env[`AG_UI_AGENT_URL_${suffix}`];
  const integrationAgentId = process.env[`COPILOT_AGENT_ID_${suffix}`];

  return {
    agentUrl:
      integrationAgentUrl ??
      process.env.AG_UI_AGENT_URL ??
      "http://127.0.0.1:8888/",
    agentId:
      integrationAgentId ??
      process.env.COPILOT_AGENT_ID ??
      process.env.NEXT_PUBLIC_COPILOT_AGENT_ID ??
      integrationId,
  };
}

type RuntimeHandler = (req: Request) => Response | Promise<Response>;
type RuntimeHandlers = {
  multiRoute: RuntimeHandler;
  singleRoute: RuntimeHandler;
};

const runtimeHandlerCache = new Map<string, RuntimeHandlers>();

function normalizePath(path: string): string {
  if (path.length > 1 && path.endsWith("/")) {
    return path.slice(0, -1);
  }
  return path;
}

function getRuntimeHandlers(
  integrationId: string,
  basePath: string,
): RuntimeHandlers {
  const cacheKey = `${integrationId}::${basePath}`;
  const existing = runtimeHandlerCache.get(cacheKey);
  if (existing) {
    return existing;
  }

  const { agentId, agentUrl } = resolveIntegrationConfig(integrationId);
  const serviceAdapter = new ExperimentalEmptyAdapter();
  const runtime = new CopilotRuntime({
    agents: {
      [agentId]: new HttpAgent({ url: agentUrl }),
    },
  });

  runtime.handleServiceAdapter(serviceAdapter);

  const multiRouteApp = createCopilotHonoHandler({
    runtime: runtime.instance,
    basePath,
    mode: "multi-route",
  });

  const singleRouteApp = createCopilotHonoHandler({
    runtime: runtime.instance,
    basePath,
    mode: "single-route",
  });

  const handlers = {
    multiRoute: honoHandle(multiRouteApp),
    singleRoute: honoHandle(singleRouteApp),
  };

  runtimeHandlerCache.set(cacheKey, handlers);
  return handlers;
}

function shouldFallbackToSingleRoute(
  req: NextRequest,
  response: Response,
  basePath: string,
): boolean {
  if (req.method.toUpperCase() !== "POST") {
    return false;
  }

  if (response.status !== 404 && response.status !== 405) {
    return false;
  }

  const requestPath = normalizePath(new URL(req.url).pathname);
  const normalizedBasePath = normalizePath(basePath);

  return requestPath === normalizedBasePath;
}

export async function handleCopilotRuntimeRequest(
  req: NextRequest,
  integrationId: string,
  basePath: string,
) {
  const handlers = getRuntimeHandlers(integrationId, basePath);
  const singleRouteRequest = req.clone();
  const response = await handlers.multiRoute(req);

  if (shouldFallbackToSingleRoute(req, response, basePath)) {
    return handlers.singleRoute(singleRouteRequest);
  }

  return response;
}
