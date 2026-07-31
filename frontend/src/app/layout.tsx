import type { Metadata } from 'next';
import '@/styles/globals.css';
import { Sidebar } from '@/components/dashboard/Sidebar';
import { Header } from '@/components/dashboard/Header';

export const metadata: Metadata = {
  title: 'AI Employee OS - Dashboard & Analytics',
  description: 'AI-Powered Business Operating System with real-time analytics, automated reporting, and AI employee workforce management.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#0b0f19] text-slate-100 antialiased selection:bg-indigo-500 selection:text-white">
        <div className="flex min-h-screen">
          {/* Main Sidebar */}
          <Sidebar />

          {/* Right Main Content Area */}
          <div className="flex-1 flex flex-col min-w-0">
            <Header />
            <main className="flex-1 p-6 space-y-6 overflow-y-auto">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
