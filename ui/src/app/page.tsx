import { redirect } from "next/navigation";

export default function Home() {
  const defaultIntegrationId =
    process.env.COPILOT_DEFAULT_INTEGRATION_ID ??
    process.env.NEXT_PUBLIC_COPILOT_AGENT_ID ??
    "agui_agent";

  redirect(`/${defaultIntegrationId}`);
}
