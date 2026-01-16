import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import MobileNav from "@/components/MobileNav";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "DeepTutor - AI-Powered Learning Assistant",
  description: "Your intelligent learning companion for research, problem-solving, and knowledge management",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <div className="h-screen flex overflow-hidden bg-zinc-50 dark:bg-black">
          <Sidebar />
          <div className="flex flex-col w-0 flex-1 overflow-hidden md:ml-64">
            <MobileNav />
            <main className="flex-1 relative overflow-y-auto focus:outline-none bg-zinc-50 dark:bg-black">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
