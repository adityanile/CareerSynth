import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CareerSynth Agent UI",
  description: "Multi-conversation chat UI for AG-UI + Clerk authentication",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        <ClerkProvider
          signInForceRedirectUrl="/workspace"
          signInFallbackRedirectUrl="/workspace"
          signUpForceRedirectUrl="/workspace"
          signUpFallbackRedirectUrl="/workspace"
        >
          {children}
        </ClerkProvider>
      </body>
    </html>
  );
}
