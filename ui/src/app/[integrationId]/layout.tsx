import { ReactNode } from "react";
import { ClerkAuthGate } from "@/components/clerk-auth-gate";

export default function IntegrationLayout({ children }: { children: ReactNode }) {
  return <ClerkAuthGate>{children}</ClerkAuthGate>;
}
