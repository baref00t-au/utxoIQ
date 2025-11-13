'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { User, Settings, CreditCard, Key, LogOut } from 'lucide-react';
import { ThemeToggle } from './theme-toggle';
import { MobileNav } from './mobile-nav';

export function Header() {
  const { user, signOut, loading } = useAuth();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60" role="banner">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-4 md:gap-8">
          <MobileNav />
          <Link href="/" className="flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 rounded-lg" aria-label="utxoIQ Home">
            <Image
              src="/logo-square.png"
              alt="utxoIQ Logo"
              width={40}
              height={40}
              priority
              className="h-10 w-10"
            />
            <span className="text-xl font-semibold">utxoIQ</span>
          </Link>
          <nav className="hidden md:flex items-center gap-6" role="navigation" aria-label="Main navigation">
            {user ? (
              <>
                <Link
                  href="/feed"
                  className="text-sm font-medium transition-colors hover:text-brand min-h-[44px] flex items-center focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 rounded-lg px-2"
                  aria-label="View insight feed"
                >
                  Feed
                </Link>
                <Link
                  href="/brief"
                  className="text-sm font-medium transition-colors hover:text-brand min-h-[44px] flex items-center focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 rounded-lg px-2"
                  aria-label="View daily brief"
                >
                  Brief
                </Link>
                <Link
                  href="/alerts"
                  className="text-sm font-medium transition-colors hover:text-brand min-h-[44px] flex items-center focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 rounded-lg px-2"
                  aria-label="Manage alerts"
                >
                  Alerts
                </Link>
                <Link
                  href="/chat"
                  className="text-sm font-medium transition-colors hover:text-brand min-h-[44px] flex items-center focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 rounded-lg px-2"
                  aria-label="Ask AI assistant"
                >
                  Ask
                </Link>
              </>
            ) : (
              <>
                <Link
                  href="#features"
                  className="text-sm font-medium transition-colors hover:text-brand min-h-[44px] flex items-center focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 rounded-lg px-2"
                >
                  Features
                </Link>
                <Link
                  href="#pricing"
                  className="text-sm font-medium transition-colors hover:text-brand min-h-[44px] flex items-center focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 rounded-lg px-2"
                >
                  Pricing
                </Link>
                <Link
                  href="/docs"
                  className="text-sm font-medium transition-colors hover:text-brand min-h-[44px] flex items-center focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 rounded-lg px-2"
                >
                  Docs
                </Link>
              </>
            )}
          </nav>
        </div>
        <div className="flex items-center gap-2 md:gap-4">
          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2 min-h-[44px]" aria-label={`User menu for ${user.email}`}>
                  <User className="h-4 w-4" aria-hidden="true" />
                  <span className="hidden sm:inline">{user.email}</span>
                  <span className="ml-1 rounded bg-orange-500/10 px-1.5 py-0.5 text-xs font-medium text-orange-500" aria-label={`Subscription tier: ${user.subscriptionTier}`}>
                    {user.subscriptionTier}
                  </span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56" role="menu" aria-label="User account menu">
                <DropdownMenuLabel>
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">{user.displayName || 'User'}</p>
                    <p className="text-xs leading-none text-muted-foreground">
                      {user.email}
                    </p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link href="/profile" className="cursor-pointer min-h-[44px] flex items-center" role="menuitem">
                    <Settings className="mr-2 h-4 w-4" aria-hidden="true" />
                    Profile Settings
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link href="/profile/api-keys" className="cursor-pointer min-h-[44px] flex items-center" role="menuitem">
                    <Key className="mr-2 h-4 w-4" aria-hidden="true" />
                    API Keys
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link href="/billing" className="cursor-pointer min-h-[44px] flex items-center" role="menuitem">
                    <CreditCard className="mr-2 h-4 w-4" aria-hidden="true" />
                    Billing & Subscription
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => signOut()} className="cursor-pointer min-h-[44px] flex items-center" role="menuitem">
                  <LogOut className="mr-2 h-4 w-4" aria-hidden="true" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : !loading ? (
            <div className="flex items-center gap-2">
              <Link href="/sign-in">
                <Button variant="ghost" size="sm" className="min-h-[44px]">
                  Sign In
                </Button>
              </Link>
              <Link href="/sign-up">
                <Button variant="default" size="sm" className="min-h-[44px]">
                  Start Free
                </Button>
              </Link>
            </div>
          ) : null}
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
