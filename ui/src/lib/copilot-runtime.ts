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
type RuntimeCacheEntry = {
  createdAt: number;
  expiresAt: number;
  handler: RuntimeHandler;
};

const runtimeHandlerCache = new Map<string, RuntimeCacheEntry>();
const HANDLER_TTL_MS = 5 * 60 * 1000;
const MAX_RUNTIME_CACHE_ENTRIES = 200;

function normalizePath(path: string): string {
  if (path.length > 1 && path.endsWith("/")) {
    return path.slice(0, -1);
  }
  return path;
}

function buildCacheKey(integrationId: string, basePath: string): string {
  const normalizedBasePath = normalizePath(basePath);
  return `${integrationId}::${normalizedBasePath}`;
}

function evictExpiredEntries(now: number) {
  for (const [key, entry] of runtimeHandlerCache) {
    if (entry.expiresAt <= now) {
      runtimeHandlerCache.delete(key);
    }
  }
}

function ensureCacheCapacity() {
  if (runtimeHandlerCache.size <= MAX_RUNTIME_CACHE_ENTRIES) {
    return;
  }

  const oldestEntry = runtimeHandlerCache.entries().next().value as
    | [string, RuntimeCacheEntry]
    | undefined;
  if (oldestEntry) {
    runtimeHandlerCache.delete(oldestEntry[0]);
  }
}

function getRuntimeHandler(integrationId: string, basePath: string): RuntimeHandler {
  const now = Date.now();
  evictExpiredEntries(now);

  const cacheKey = buildCacheKey(integrationId, basePath);
  const existing = runtimeHandlerCache.get(cacheKey);
  if (existing && existing.expiresAt > now) {
    return existing.handler;
  }

  const { agentId, agentUrl } = resolveIntegrationConfig(integrationId);
  const serviceAdapter = new ExperimentalEmptyAdapter();
  const runtime = new CopilotRuntime({
    agents: {
      [agentId]: new HttpAgent({ url: agentUrl }),
    },
  });

  runtime.handleServiceAdapter(serviceAdapter);

  const app = createCopilotHonoHandler({
    runtime: runtime.instance,
    basePath,
    mode: "single-route",
  });

  const handler = honoHandle(app);

  runtimeHandlerCache.set(cacheKey, {
    createdAt: now,
    expiresAt: now + HANDLER_TTL_MS,
    handler,
  });
  ensureCacheCapacity();

  return handler;
}

export async function handleCopilotRuntimeRequest(
  req: NextRequest,
  integrationId: string,
  basePath: string,
) {
  const handler = getRuntimeHandler(integrationId, basePath);
  return handler(req);
}
