import { NextRequest } from "next/server";

interface BackendRouteContext {
  params: Promise<{
    path: string[];
  }>;
}

function resolveBackendBaseUrl(): string {
  const baseUrl = process.env.AG_UI_AGENT_URL ?? "http://127.0.0.1:8888/";
  return baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl;
}

function buildTargetUrl(baseUrl: string, pathParts: string[], sourceUrl: string): string {
  const safePath = pathParts
    .map((part) => encodeURIComponent(part))
    .join("/");
  const search = new URL(sourceUrl).search;
  return `${baseUrl}/api/${safePath}${search}`;
}

async function handleBackendProxy(req: NextRequest, context: BackendRouteContext) {
  const { path } = await context.params;
  if (!path || path.length === 0) {
    return Response.json({ error: "Missing backend path." }, { status: 400 });
  }

  const authorizationHeader = req.headers.get("authorization");
  const accessToken =
    authorizationHeader?.startsWith("Bearer ")
      ? authorizationHeader.slice("Bearer ".length).trim()
      : undefined;
  const authRequired = process.env.ENTRA_AUTH_REQUIRED === "true";
  if (authRequired && !accessToken) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  const backendUrl = buildTargetUrl(resolveBackendBaseUrl(), path, req.url);
  const contentType = req.headers.get("content-type");
  const shouldIncludeBody = req.method === "POST" || req.method === "PATCH" || req.method === "PUT";
  const isMultipart = (contentType ?? "").toLowerCase().includes("multipart/form-data");
  const requestBody = shouldIncludeBody
    ? isMultipart
      ? await req.arrayBuffer()
      : await req.text()
    : undefined;

  try {
    const upstreamResponse = await fetch(backendUrl, {
      method: req.method,
      headers: {
        ...(authorizationHeader ? { Authorization: authorizationHeader } : {}),
        ...(contentType ? { "Content-Type": contentType } : {}),
      },
      body: shouldIncludeBody ? requestBody : undefined,
      cache: "no-store",
    });

    const responseText = await upstreamResponse.text();
    const responseHeaders = new Headers();
    const upstreamContentType = upstreamResponse.headers.get("content-type");
    if (upstreamContentType) {
      responseHeaders.set("content-type", upstreamContentType);
    }

    const status = upstreamResponse.status;
    const mustNotHaveBody = status === 204 || status === 205 || status === 304;

    return new Response(mustNotHaveBody ? null : responseText, {
      status,
      headers: responseHeaders,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to reach backend service.";
    return Response.json(
      { error: "Failed to reach backend service.", detail: message, target: backendUrl },
      { status: 502 },
    );
  }
}

export const GET = handleBackendProxy;
export const POST = handleBackendProxy;
export const PATCH = handleBackendProxy;
export const DELETE = handleBackendProxy;
export const OPTIONS = handleBackendProxy;
