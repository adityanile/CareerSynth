import { AgenticChat } from "@/components/agentic-chat";
import { EntraAuthGate } from "@/components/entra-auth-gate";

interface IntegrationPageProps {
  params: Promise<{
    integrationId: string;
  }>;
}

export default async function IntegrationPage({ params }: IntegrationPageProps) {
  const { integrationId } = await params;

  return (
    <EntraAuthGate>
      <AgenticChat integrationId={integrationId} />
    </EntraAuthGate>
  );
}
