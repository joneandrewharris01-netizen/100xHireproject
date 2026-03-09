import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "../components/Sidebar";

export const metadata: Metadata = {
  title: "Content Factory",
  description: "Video content pipeline dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-surface text-white min-h-screen flex">
        <Sidebar />
        <main className="flex-1 ml-56 p-6 overflow-auto min-h-screen">
          {children}
        </main>
      </body>
    </html>
  );
}
