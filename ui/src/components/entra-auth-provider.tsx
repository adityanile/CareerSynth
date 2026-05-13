"use client";

import { ReactNode, useEffect } from "react";
import { PublicClientApplication } from "@azure/msal-browser";
import { MsalProvider } from "@azure/msal-react";
import { getMsalConfiguration } from "@/lib/entra-auth";

let instance: PublicClientApplication | null = null;

function getMsalInstance(): PublicClientApplication {
  if (!instance) {
    instance = new PublicClientApplication(getMsalConfiguration());
  }

  return instance;
}

export function EntraAuthProvider({ children }: { children: ReactNode }) {
  const msalInstance = getMsalInstance();

  useEffect(() => {
    let cancelled = false;

    const hasAuthHashParams = () =>
      window.location.hash.includes("code=") ||
      window.location.hash.includes("error=");

    const clearAuthHash = () => {
      const cleanUrl = `${window.location.pathname}${window.location.search}`;
      window.history.replaceState({}, document.title, cleanUrl);
    };

    const initializeMsal = async () => {
      await msalInstance.initialize();
      let redirectResult = null;

      if (hasAuthHashParams()) {
        try {
          redirectResult = await msalInstance.handleRedirectPromise();
        } catch (error) {
          const message = error instanceof Error ? error.message : String(error);
          if (!message.includes("no_token_request_cache_error")) {
            throw error;
          }
        }
      }

      if (cancelled) {
        return;
      }

      if (redirectResult?.account) {
        msalInstance.setActiveAccount(redirectResult.account);
      } else {
        const activeAccount = msalInstance.getActiveAccount();
        if (!activeAccount) {
          const [firstAccount] = msalInstance.getAllAccounts();
          if (firstAccount) {
            msalInstance.setActiveAccount(firstAccount);
          }
        }
      }

      if (hasAuthHashParams()) {
        clearAuthHash();
      }
    };

    void initializeMsal();

    return () => {
      cancelled = true;
    };
  }, [msalInstance]);

  return <MsalProvider instance={msalInstance}>{children}</MsalProvider>;
}
