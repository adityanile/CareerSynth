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
import { OPEN_RESUME_PARSE_MODAL_EVENT } from "@/lib/ui-events";
import { entraLoginRequest, entraTokenRequest } from "@/lib/entra-auth";
import {
  clearEntraAccessToken,
  setEntraAccessToken,
} from "@/lib/entra-token-store";
import styles from "./entra-auth-gate.module.css";

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
            Use your Microsoft Entra account to access your conversations and
            profile-linked context.
          </p>
          <button
            type="button"
            className={styles.primaryButton}
            onClick={() => void handleSignIn()}
          >
            Sign in with Microsoft
          </button>
          {authError && <p className={styles.errorText}>{authError}</p>}
        </section>
      </main>
    );
  }

  return (
    <main className={styles.appShell}>
      <div className={styles.sessionBar}>
        <span className={styles.accountLabel}>
          Signed in as <strong>{activeAccount?.username ?? "Entra user"}</strong>
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
          <button
            type="button"
            className={styles.secondaryButton}
            onClick={() => void handleSignOut()}
          >
            Sign out
          </button>
        </div>
      </div>

      {sessionState === "syncing" && (
        <p className={styles.infoBanner}>Establishing secure session...</p>
      )}
      {sessionState === "error" && (
        <p className={styles.errorBanner}>
          {authError ?? "Authentication failed."}
        </p>
      )}
      {missingActiveAccount && (
        <p className={styles.errorBanner}>
          No active Entra account is available. Sign out and sign in again.
        </p>
      )}
      {sessionState === "ready" && children}
    </main>
  );
}
