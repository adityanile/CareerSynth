"use client";

import { useMemo, useSyncExternalStore } from "react";
import "@copilotkit/react-core/v2/styles.css";
import { CopilotKit } from "@copilotkit/react-core";
import { MultiConversationChat } from "@/components/multi-conversation-chat";
import {
  getClerkAccessToken,
  subscribeToClerkAccessToken,
} from "@/lib/clerk-token-store";
import { resolveDefaultIntegrationId } from "@/lib/integration-config";

interface AgenticChatProps {
  integrationId?: string;
}

export function AgenticChat({ integrationId }: AgenticChatProps) {
  const resolvedIntegrationId = integrationId ?? resolveDefaultIntegrationId();
  const publicApiKey =
    process.env.NEXT_PUBLIC_COPILOT_PUBLIC_API_KEY ??
    process.env.NEXT_PUBLIC_COPILOT_PUBLIC_LICENSE_KEY;
  const agentId = process.env.NEXT_PUBLIC_COPILOT_AGENT_ID ?? resolvedIntegrationId;
  const providerConfig = publicApiKey ? { publicApiKey } : {};
  const accessToken = useSyncExternalStore(
    subscribeToClerkAccessToken,
    getClerkAccessToken,
    () => null,
  );
  const headers = useMemo(
    () => (accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    [accessToken],
  );

  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      agent={agentId}
      headers={headers}
      useSingleEndpoint
      {...providerConfig}
    >
      <MultiConversationChat agentId={agentId} hasPublicKey={Boolean(publicApiKey)} />
    </CopilotKit>
  );
}
