export function resolveDefaultIntegrationId(): string {
  return (
    process.env.COPILOT_DEFAULT_INTEGRATION_ID ??
    process.env.NEXT_PUBLIC_COPILOT_AGENT_ID ??
    "agui_agent"
  );
}

