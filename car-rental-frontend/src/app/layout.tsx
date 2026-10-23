import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Septum Rental",
  description: "Premium multi-vehicle rental platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de">
      <body>{children}</body>
    </html>
  );
}
