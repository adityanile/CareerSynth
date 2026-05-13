"use client";

import { useEffect } from "react";
import { broadcastResponseToMainFrame } from "@azure/msal-browser/redirect-bridge";

export default function RedirectBridgePage() {
  useEffect(() => {
    void broadcastResponseToMainFrame().catch((error) => {
      console.error("MSAL redirect bridge failed:", error);
    });
  }, []);

  return <p style={{ padding: "1rem" }}>Processing authentication...</p>;
}

