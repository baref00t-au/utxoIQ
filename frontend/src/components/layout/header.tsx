'use client';

import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Box, Github } from 'lucide-react';

export function Header() {
  const { user, signOut } = useAuth();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2">
            <Box className="h-6 w-6 text-brand" />
            <span className="text-xl font-semibold">utxoIQ</span>
          </Link>
          <nav className="hidden md:flex items-center gap-6">
            <Link
              href="/"
              className="text-sm font-medium transition-colors hover:text-brand"
            >
              Feed
            </Link>
            <Link
              href="/brief"
              className="text-sm font-medium transition-colors hover:text-brand"
            >
              Brief
            </Link>
            {user && (
              <>
                <Link
                  href="/alerts"
                  className="text-sm font-medium transition-colors hover:text-brand"
                >
                  Alerts
                </Link>
                <Link
                  href="/chat"
                  className="text-sm font-medium transition-colors hover:text-brand"
                >
                  Ask
                </Link>
              </>
            )}
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <Button variant="outline" size="sm" asChild>
            <a
              href="https://github.com/utxoiq"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Github className="h-4 w-4" />
            </a>
          </Button>
          {user ? (
            <div className="flex items-center gap-4">
              <Link href="/billing">
                <Button variant="outline" size="sm">
                  Billing
                </Button>
              </Link>
              <Button variant="default" size="sm" onClick={() => signOut()}>
                Sign Out
              </Button>
            </div>
          ) : (
            <Link href="/sign-in">
              <Button variant="default" size="sm">
                Sign In
              </Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
