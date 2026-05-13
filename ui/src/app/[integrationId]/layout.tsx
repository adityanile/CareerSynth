import { ReactNode } from "react";
import { EntraAuthProvider } from "@/components/entra-auth-provider";

export default function IntegrationLayout({ children }: { children: ReactNode }) {
  return <EntraAuthProvider>{children}</EntraAuthProvider>;
}

