import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/providers';
import { Sidebar } from '@/components/sidebar';
import { Bell, Settings } from 'lucide-react';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Optima AI Supply Chain',
  description: 'Advanced supply chain management platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen bg-[#111111] flex">
            <Sidebar />
            <div className="flex-1 ml-64">
              {/* Top bar */}
              <header className="h-16 bg-[#1a1a1a] border-b border-gray-700 flex items-center justify-end px-6">
                <div className="flex items-center space-x-4">
                  <button className="p-2 text-gray-400 hover:text-white">
                    <Bell className="w-5 h-5" />
                  </button>
                  <button className="p-2 text-gray-400 hover:text-white">
                    <Settings className="w-5 h-5" />
                  </button>
                </div>
              </header>
              {/* Main content */}
              <main className="p-8">
                {children}
              </main>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
