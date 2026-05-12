import { AgenticChat } from "@/components/agentic-chat";

interface IntegrationPageProps {
  params: Promise<{
    integrationId: string;
  }>;
}

export default async function IntegrationPage({ params }: IntegrationPageProps) {
  const { integrationId } = await params;

  return <AgenticChat integrationId={integrationId} />;
}
