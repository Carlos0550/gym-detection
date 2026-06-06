import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Gym Detection",
  description: "Sistema de reconocimiento facial para gimnasios",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
