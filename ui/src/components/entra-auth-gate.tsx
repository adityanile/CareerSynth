"use client";

import {
  ReactNode,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import {
  AccountInfo,
  AuthenticationResult,
  InteractionRequiredAuthError,
  InteractionStatus,
} from "@azure/msal-browser";
import { useMsal } from "@azure/msal-react";
import { ProfileResourceManager } from "@/components/profile-resource-manager";
import { entraLoginRequest, entraTokenRequest } from "@/lib/entra-auth";
import {
  clearEntraAccessToken,
  setEntraAccessToken,
} from "@/lib/entra-token-store";

type SessionState = "idle" | "syncing" | "ready" | "error";

function getAccount(instanceAccounts: AccountInfo[], activeAccount: AccountInfo | null) {
  return activeAccount ?? instanceAccounts[0] ?? null;
}

export function EntraAuthGate({ children }: { children: ReactNode }) {
  const { instance, accounts, inProgress } = useMsal();
  const hasMounted = useSyncExternalStore(
    () => () => undefined,
    () => true,
    () => false,
  );
  const [sessionState, setSessionState] = useState<SessionState>("idle");
  const [authError, setAuthError] = useState<string | null>(null);
  const lastSessionToken = useRef<string | null>(null);
  const unauthenticatedSessionCleared = useRef(false);
  const activeAccount = getAccount(accounts, instance.getActiveAccount());
  const isSignedIn = Boolean(activeAccount);

  useEffect(() => {
    if (isSignedIn || unauthenticatedSessionCleared.current) {
      return;
    }

    unauthenticatedSessionCleared.current = true;
    lastSessionToken.current = null;
    clearEntraAccessToken();
    setSessionState("idle");
    setAuthError(null);
  }, [isSignedIn]);

  useEffect(() => {
    if (!isSignedIn || inProgress !== InteractionStatus.None) {
      return;
    }

    const account = activeAccount;
    if (!account) {
      return;
    }

    if (!instance.getActiveAccount()) {
      instance.setActiveAccount(account);
    }

    let cancelled = false;

    const syncSession = async () => {
      setSessionState("syncing");
      setAuthError(null);

      try {
        const tokenResult: AuthenticationResult =
          await instance.acquireTokenSilent({
            ...entraTokenRequest,
            account,
          }).catch(async (error) => {
          if (error instanceof InteractionRequiredAuthError) {
            return instance.acquireTokenPopup(entraTokenRequest);
          }
          throw error;
        });

        const bearerToken = tokenResult.accessToken;
        if (!bearerToken) {
          throw new Error(
            "No access token returned. Configure NEXT_PUBLIC_ENTRA_API_SCOPES for your protected API scope.",
          );
        }

        if (lastSessionToken.current === bearerToken) {
          if (!cancelled) {
            setSessionState("ready");
          }
          return;
        }

        if (!cancelled) {
          lastSessionToken.current = bearerToken;
          setEntraAccessToken(bearerToken);
          setSessionState("ready");
        }
      } catch (error) {
        if (!cancelled) {
          const message =
            error instanceof Error
              ? error.message
              : "Failed to synchronize auth session.";
          setSessionState("error");
          setAuthError(message);
        }
      }
    };

    void syncSession();

    return () => {
      cancelled = true;
    };
  }, [activeAccount, inProgress, instance, isSignedIn]);

  const handleSignIn = async () => {
    try {
      setAuthError(null);
      const loginResult = await instance.loginPopup(entraLoginRequest);
      if (loginResult.account) {
        instance.setActiveAccount(loginResult.account);
      }
      unauthenticatedSessionCleared.current = false;
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to sign in.";
      setAuthError(message);
    }
  };

  const handleSignOut = async () => {
    lastSessionToken.current = null;
    clearEntraAccessToken();
    unauthenticatedSessionCleared.current = true;
    await instance.logoutPopup();
  };

  const missingActiveAccount =
    isSignedIn &&
    inProgress === InteractionStatus.None &&
    !activeAccount;

  if (!hasMounted) {
    return <main style={{ padding: "2rem" }}>Loading authentication...</main>;
  }

  if (!isSignedIn) {
    return (
      <main style={{ padding: "2rem", maxWidth: "40rem", margin: "0 auto" }}>
        <h1>Sign in required</h1>
        <p>Use your Microsoft Entra account to access CareerSynth.</p>
        <button type="button" onClick={() => void handleSignIn()}>
          Sign in with Microsoft
        </button>
        {authError && <p style={{ color: "#b00020" }}>{authError}</p>}
      </main>
    );
  }

  return (
    <main>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "1rem",
          padding: "0.75rem 1rem",
          borderBottom: "1px solid #d5d7db",
          background: "#f8fafc",
        }}
      >
        <span style={{ fontSize: "0.95rem", color: "#1f2937" }}>
          Signed in as <strong>{activeAccount?.username ?? "Entra user"}</strong>
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <ProfileResourceManager />
          <button type="button" onClick={() => void handleSignOut()}>
            Sign out
          </button>
        </div>
      </div>

      {sessionState === "syncing" && (
        <p style={{ padding: "1rem" }}>Establishing secure session...</p>
      )}
      {sessionState === "error" && (
        <p style={{ padding: "1rem", color: "#b00020" }}>
          {authError ?? "Authentication failed."}
        </p>
      )}
      {missingActiveAccount && (
        <p style={{ padding: "1rem", color: "#b00020" }}>
          No active Entra account is available. Sign out and sign in again.
        </p>
      )}
      {sessionState === "ready" && children}
    </main>
  );
}
