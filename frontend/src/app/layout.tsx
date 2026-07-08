import type { ReactNode } from "react";

import { AppNav } from "../components/app-nav";
import "./globals.css";

export const metadata = {
  title: "DAMA Dashboard",
  description: "AI Content Automation Platform dashboard"
};

export default function RootLayout({
  children
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AppNav />
        {children}
      </body>
    </html>
  );
}
