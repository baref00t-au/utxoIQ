import Link from 'next/link';

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-border bg-background" role="contentinfo">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <p className="text-sm text-muted-foreground">
          © {currentYear} utxoIQ. AI-powered Bitcoin intelligence.
        </p>
        <nav className="flex items-center gap-6" role="navigation" aria-label="Footer navigation">
          <Link
            href="/privacy"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 rounded px-2 py-1"
            aria-label="Privacy policy"
          >
            Privacy
          </Link>
          <Link
            href="/terms"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 rounded px-2 py-1"
            aria-label="Terms of service"
          >
            Terms
          </Link>
          <Link
            href="/accessibility"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 rounded px-2 py-1"
            aria-label="Accessibility statement"
          >
            Accessibility
          </Link>
        </nav>
      </div>
    </footer>
  );
}
