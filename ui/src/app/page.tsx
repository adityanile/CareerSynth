import { AgenticChat } from "@/components/agentic-chat";
import { EntraAuthGate } from "@/components/entra-auth-gate";
import { EntraAuthProvider } from "@/components/entra-auth-provider";

export default function Home() {
  return (
    <EntraAuthProvider>
      <EntraAuthGate>
        <AgenticChat />
      </EntraAuthGate>
    </EntraAuthProvider>
  );
}
