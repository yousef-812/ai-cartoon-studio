import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Cartoon Studio",
  description: "Production dashboard for original AI cartoon episodes",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
