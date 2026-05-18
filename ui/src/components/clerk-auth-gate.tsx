"use client";

import {
  ReactNode,
  useCallback,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import { Show, SignInButton, UserButton, useAuth, useUser } from "@clerk/nextjs";
import { ProfileResourceManager } from "@/components/profile-resource-manager";
import { OPEN_RESUME_PARSE_MODAL_EVENT } from "@/lib/ui-events";
import {
  clearClerkAccessToken,
  setClerkAccessToken,
} from "@/lib/clerk-token-store";
import styles from "./clerk-auth-gate.module.css";

type SessionState = "idle" | "syncing" | "ready" | "error";

function getTokenExpiryMs(token: string): number | null {
  const parts = token.split(".");
  if (parts.length < 2) {
    return null;
  }

  try {
    const payload = JSON.parse(atob(parts[1].replace(/-/g, "+").replace(/_/g, "/"))) as {
      exp?: unknown;
    };
    if (typeof payload.exp !== "number") {
      return null;
    }
    return payload.exp * 1000;
  } catch {
    return null;
  }
}

export function ClerkAuthGate({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const { user } = useUser();
  const hasMounted = useSyncExternalStore(
    () => () => undefined,
    () => true,
    () => false,
  );
  const [sessionState, setSessionState] = useState<SessionState>("idle");
  const [hasSessionReady, setHasSessionReady] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const lastSessionToken = useRef<string | null>(null);
  const refreshTimer = useRef<number | null>(null);
  const forceRefreshSession = useRef<(() => void) | null>(null);

  const clearRefreshTimer = useCallback(() => {
    if (refreshTimer.current !== null) {
      window.clearTimeout(refreshTimer.current);
      refreshTimer.current = null;
    }
  }, []);

  const syncSession = useCallback(
    async (forceRefresh = false) => {
      if (!isLoaded || !isSignedIn) {
        return;
      }

      if (forceRefresh) {
        if (!hasSessionReady) {
          setSessionState("syncing");
        }
      } else {
        setHasSessionReady(false);
        setSessionState("syncing");
      }
      setAuthError(null);

      try {
        const token = forceRefresh
          ? await getToken({ skipCache: true })
          : await getToken();
        if (!token) {
          throw new Error("No Clerk session token was returned.");
        }

        const expiryMs = getTokenExpiryMs(token);
        const defaultDelayMs = 60_000;
        const refreshWindowMs = 30_000;
        const delayMs = expiryMs
          ? Math.max(5_000, expiryMs - Date.now() - refreshWindowMs)
          : defaultDelayMs;

        clearRefreshTimer();
        refreshTimer.current = window.setTimeout(() => {
          forceRefreshSession.current?.();
        }, delayMs);

        if (lastSessionToken.current !== token) {
          lastSessionToken.current = token;
          setClerkAccessToken(token);
        }
        setHasSessionReady(true);
        setSessionState("ready");
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "Failed to synchronize Clerk session.";
        setSessionState(hasSessionReady ? "ready" : "error");
        setAuthError(message);
      }
    },
    [clearRefreshTimer, getToken, hasSessionReady, isLoaded, isSignedIn],
  );

  useEffect(() => {
    forceRefreshSession.current = () => {
      void syncSession(true);
    };
    return () => {
      forceRefreshSession.current = null;
    };
  }, [syncSession]);

  useEffect(() => {
    if (!isLoaded || !isSignedIn) {
      return;
    }

    queueMicrotask(() => {
      void syncSession(false);
    });
  }, [isLoaded, isSignedIn, syncSession]);

  useEffect(() => {
    if (!isSignedIn) {
      clearRefreshTimer();
      clearClerkAccessToken();
      lastSessionToken.current = null;
    }
  }, [clearRefreshTimer, isSignedIn]);

  useEffect(() => {
    return () => {
      clearRefreshTimer();
    };
  }, [clearRefreshTimer]);

  if (!hasMounted || !isLoaded) {
    return <main className={styles.loadingState}>Loading authentication...</main>;
  }

  if (!isSignedIn) {
    return (
      <main className={styles.authPage}>
        <div className={styles.backgroundGlow} aria-hidden="true" />
        <section className={styles.authCard}>
          <p className={styles.kicker}>CareerSynth Workspace</p>
          <h1 className={styles.authTitle}>Sign in to continue</h1>
          <p className={styles.authDescription}>
            Sign in with your Clerk account to access conversations and profile-linked
            context.
          </p>
          <SignInButton mode="modal">
            <button type="button" className={styles.primaryButton}>
              Sign in
            </button>
          </SignInButton>
          {authError && <p className={styles.errorText}>{authError}</p>}
        </section>
      </main>
    );
  }

  const primaryEmail = user?.primaryEmailAddress?.emailAddress ?? user?.username ?? "User";

  return (
    <main className={styles.appShell}>
      <div className={styles.sessionBar}>
        <span className={styles.accountLabel}>
          Signed in as <strong>{primaryEmail}</strong>
        </span>
        <span className={styles.sessionTitle}>CareerSynth Assistant</span>
        <div className={styles.sessionActions}>
          <ProfileResourceManager />
          <button
            type="button"
            className={styles.secondaryButton}
            onClick={() =>
              window.dispatchEvent(new CustomEvent(OPEN_RESUME_PARSE_MODAL_EVENT))
            }
          >
            Parse Resume
          </button>
          <Show when="signed-in">
            <UserButton />
          </Show>
        </div>
      </div>

      {sessionState === "syncing" && !hasSessionReady && (
        <p className={styles.infoBanner}>Establishing secure session...</p>
      )}
      {sessionState === "error" && (
        <p className={styles.errorBanner}>
          {authError ?? "Authentication failed."}
        </p>
      )}
      {hasSessionReady && children}
    </main>
  );
}
