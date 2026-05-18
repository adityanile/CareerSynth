import { AgenticChat } from "@/components/agentic-chat";
import { ClerkAuthGate } from "@/components/clerk-auth-gate";
import { auth } from "@clerk/nextjs/server";

export default async function WorkspacePage() {
  await auth();

  return (
    <ClerkAuthGate>
      <AgenticChat />
    </ClerkAuthGate>
  );
}
