import "./globals.css";

export const metadata = {
  title: "DAMA Dashboard",
  description: "AI Content Automation Platform dashboard"
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
