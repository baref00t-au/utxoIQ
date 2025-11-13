import type { Metadata } from 'next';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, Keyboard, Eye, MousePointer, Smartphone } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Accessibility Statement - utxoIQ',
  description: 'Learn about utxoIQ\'s commitment to accessibility and how we ensure our platform is usable by everyone.',
};

export default function AccessibilityPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-4">Accessibility Statement</h1>
        <p className="text-lg text-muted-foreground">
          utxoIQ is committed to ensuring digital accessibility for people with disabilities. 
          We are continually improving the user experience for everyone and applying the relevant 
          accessibility standards.
        </p>
      </div>

      {/* Compliance Status */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-success" aria-hidden="true" />
            WCAG 2.1 Level AA Compliance
          </CardTitle>
          <CardDescription>
            Our platform conforms to the Web Content Accessibility Guidelines (WCAG) 2.1 at Level AA.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold mb-2">Standards We Follow</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                <li>Web Content Accessibility Guidelines (WCAG) 2.1 Level AA</li>
                <li>Section 508 of the Rehabilitation Act</li>
                <li>Americans with Disabilities Act (ADA) Title III</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Accessibility Features */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Accessibility Features</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Keyboard className="h-5 w-5 text-brand" aria-hidden="true" />
                Keyboard Navigation
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>Full keyboard navigation support for all interactive elements.</p>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li>Tab through all interactive elements</li>
                <li>Skip to main content link</li>
                <li>Keyboard shortcuts for common actions</li>
                <li>Focus indicators on all elements</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Eye className="h-5 w-5 text-brand" aria-hidden="true" />
                Screen Reader Support
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>Compatible with popular screen readers including NVDA, JAWS, and VoiceOver.</p>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li>Semantic HTML structure</li>
                <li>ARIA labels and landmarks</li>
                <li>Descriptive alt text for images</li>
                <li>Proper heading hierarchy</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <MousePointer className="h-5 w-5 text-brand" aria-hidden="true" />
                Visual Design
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>High contrast and readable design for users with visual impairments.</p>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li>4.5:1 minimum contrast ratio for text</li>
                <li>Resizable text up to 200%</li>
                <li>Dark and light theme options</li>
                <li>Clear focus indicators</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Smartphone className="h-5 w-5 text-brand" aria-hidden="true" />
                Mobile Accessibility
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>Touch-friendly interface optimized for mobile devices.</p>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li>44px minimum touch target size</li>
                <li>Responsive design for all screen sizes</li>
                <li>Gesture alternatives available</li>
                <li>Reduced motion support</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Keyboard Shortcuts */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Keyboard Shortcuts</CardTitle>
          <CardDescription>
            Use these keyboard shortcuts to navigate utxoIQ more efficiently.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-border">
              <span className="text-sm">Focus search</span>
              <Badge variant="secondary" className="font-mono">/</Badge>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-border">
              <span className="text-sm">Show keyboard shortcuts</span>
              <Badge variant="secondary" className="font-mono">?</Badge>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-border">
              <span className="text-sm">Close modal/dialog</span>
              <Badge variant="secondary" className="font-mono">Esc</Badge>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-border">
              <span className="text-sm">Navigate lists</span>
              <Badge variant="secondary" className="font-mono">↑ ↓</Badge>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-border">
              <span className="text-sm">Navigate between elements</span>
              <Badge variant="secondary" className="font-mono">Tab</Badge>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-sm">Activate focused element</span>
              <Badge variant="secondary" className="font-mono">Enter / Space</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Testing and Validation */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Testing and Validation</CardTitle>
          <CardDescription>
            We regularly test our platform to ensure accessibility compliance.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="font-semibold mb-2">Automated Testing</h3>
            <p className="text-sm text-muted-foreground">
              We use axe-core and other automated testing tools to continuously monitor for 
              accessibility issues during development.
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Manual Testing</h3>
            <p className="text-sm text-muted-foreground">
              Our team regularly tests the platform with:
            </p>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground mt-2">
              <li>Screen readers (NVDA, JAWS, VoiceOver)</li>
              <li>Keyboard-only navigation</li>
              <li>Various assistive technologies</li>
              <li>Different browsers and devices</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Known Issues */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Known Issues and Limitations</CardTitle>
          <CardDescription>
            We are actively working to address the following accessibility limitations.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Currently, there are no known accessibility issues. If you encounter any problems, 
            please let us know using the feedback form below.
          </p>
        </CardContent>
      </Card>

      {/* Feedback */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Accessibility Feedback</CardTitle>
          <CardDescription>
            We welcome your feedback on the accessibility of utxoIQ.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm">
            If you encounter any accessibility barriers while using our platform, please contact us:
          </p>
          <div className="space-y-2 text-sm">
            <div>
              <span className="font-semibold">Email:</span>{' '}
              <a href="mailto:accessibility@utxoiq.com" className="text-brand hover:underline">
                accessibility@utxoiq.com
              </a>
            </div>
            <div>
              <span className="font-semibold">Response Time:</span> We aim to respond within 2 business days
            </div>
          </div>
          <p className="text-sm text-muted-foreground">
            When reporting an accessibility issue, please include:
          </p>
          <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
            <li>The page or feature where you encountered the issue</li>
            <li>A description of the problem</li>
            <li>The assistive technology you were using (if applicable)</li>
            <li>Your browser and operating system</li>
          </ul>
        </CardContent>
      </Card>

      {/* Last Updated */}
      <div className="text-center text-sm text-muted-foreground">
        <p>This accessibility statement was last updated on November 12, 2025.</p>
        <p className="mt-2">
          <Link href="/" className="text-brand hover:underline">
            Return to Home
          </Link>
        </p>
      </div>
    </div>
  );
}
