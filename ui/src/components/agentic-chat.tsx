"use client";

import "@copilotkit/react-core/v2/styles.css";
import { CopilotKit } from "@copilotkit/react-core";
import { MultiConversationChat } from "@/components/multi-conversation-chat";

interface AgenticChatProps {
  integrationId: string;
}

export function AgenticChat({ integrationId }: AgenticChatProps) {
  const publicApiKey =
    process.env.NEXT_PUBLIC_COPILOT_PUBLIC_API_KEY ??
    process.env.NEXT_PUBLIC_COPILOT_PUBLIC_LICENSE_KEY;
  const agentId = process.env.NEXT_PUBLIC_COPILOT_AGENT_ID ?? integrationId;
  const providerConfig = publicApiKey ? { publicApiKey } : {};

  return (
    <CopilotKit
      runtimeUrl={`/api/copilotkit/${integrationId}`}
      agent={agentId}
      {...providerConfig}
    >
      <MultiConversationChat agentId={agentId} hasPublicKey={Boolean(publicApiKey)} />
    </CopilotKit>
  );
}
