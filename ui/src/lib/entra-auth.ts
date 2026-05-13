import type { Configuration, PopupRequest } from "@azure/msal-browser";

function parseScopes(rawScopes: string | undefined): string[] {
  if (!rawScopes) {
    return [];
  }

  return rawScopes
    .split(",")
    .map((scope) => scope.trim())
    .filter(Boolean);
}

function resolveAppOrigin(): string {
  if (typeof window !== "undefined") {
    return window.location.origin;
  }

  return "http://localhost:3000";
}

export function getMsalConfiguration(): Configuration {
  const clientId = process.env.NEXT_PUBLIC_ENTRA_CLIENT_ID;
  const tenantId = process.env.NEXT_PUBLIC_ENTRA_TENANT_ID;
  const authorityFromEnv = process.env.NEXT_PUBLIC_ENTRA_AUTHORITY;

  if (!clientId) {
    throw new Error("Missing NEXT_PUBLIC_ENTRA_CLIENT_ID.");
  }

  if (!authorityFromEnv && !tenantId) {
    throw new Error(
      "Missing Entra authority configuration. Set NEXT_PUBLIC_ENTRA_AUTHORITY or NEXT_PUBLIC_ENTRA_TENANT_ID.",
    );
  }

  const appOrigin = resolveAppOrigin();
  const authority =
    authorityFromEnv ?? `https://login.microsoftonline.com/${tenantId}`;
  const redirectUri =
    process.env.NEXT_PUBLIC_ENTRA_REDIRECT_URI ??
    appOrigin;
  const postLogoutRedirectUri =
    process.env.NEXT_PUBLIC_ENTRA_POST_LOGOUT_REDIRECT_URI ??
    appOrigin;

  return {
    auth: {
      clientId,
      authority,
      redirectUri,
      postLogoutRedirectUri,
      navigateToLoginRequestUrl: true,
    },
    cache: {
      cacheLocation: "sessionStorage",
      storeAuthStateInCookie: false,
    },
  };
}

const oidcScopes = ["openid", "profile", "email"];
const apiScopes = parseScopes(process.env.NEXT_PUBLIC_ENTRA_API_SCOPES);
const loginScopes = parseScopes(process.env.NEXT_PUBLIC_ENTRA_LOGIN_SCOPES);
function uniqueScopes(scopes: string[]): string[] {
  return [...new Set(scopes)];
}

const defaultApiScopes = ["User.Read"];

function resolveApiScopes(): string[] {
  return apiScopes.length > 0 ? apiScopes : defaultApiScopes;
}

const resolvedApiScopes = resolveApiScopes();

export const entraLoginRequest: PopupRequest = {
  scopes: uniqueScopes(
    loginScopes.length > 0
      ? [...loginScopes, ...resolvedApiScopes]
      : [...oidcScopes, ...resolvedApiScopes],
  ),
};

export const entraTokenRequest: PopupRequest = {
  scopes: uniqueScopes(resolvedApiScopes),
};
