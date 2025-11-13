import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/providers';
import { Header } from '@/components/layout/header';
import { Footer } from '@/components/layout/footer';
import { SkipToMain } from '@/components/layout/skip-to-main';
import { Toaster } from 'sonner';
import { PerformanceMonitor } from '@/components/performance-monitor';

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap', // Optimize font loading
  preload: true,
});

export const metadata: Metadata = {
  title: 'utxoIQ - AI-Powered Bitcoin Intelligence',
  description: 'Real-time AI-interpreted blockchain insights for traders, analysts, and researchers',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'utxoIQ',
  },
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#FF5A21',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <SkipToMain />
        <Providers>
          <div className="flex min-h-screen flex-col">
            <Header />
            <main className="flex-1" id="main-content" role="main" aria-label="Main content">
              {children}
            </main>
            <Footer />
          </div>
          <Toaster position="top-right" />
          <PerformanceMonitor />
        </Providers>
      </body>
    </html>
  );
}
