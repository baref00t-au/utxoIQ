'use client';

import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Check, CreditCard, Zap } from 'lucide-react';
import Link from 'next/link';

const TIERS = [
  {
    name: 'Free',
    price: '$0',
    period: 'forever',
    features: [
      'Access to public insights',
      'Daily brief',
      'Basic charts',
      'Community accuracy ratings',
    ],
    current: true,
  },
  {
    name: 'Pro',
    price: '$29',
    period: 'per month',
    features: [
      'Everything in Free',
      'Real-time insight streaming',
      'Custom alerts (up to 10)',
      'Predictive signals',
      'Priority support',
      'API access',
    ],
    highlight: true,
  },
  {
    name: 'Power',
    price: '$99',
    period: 'per month',
    features: [
      'Everything in Pro',
      'Unlimited custom alerts',
      'Unlimited AI chat queries',
      'Advanced predictive models',
      'White-label API access',
      'Dedicated account manager',
    ],
  },
];

export function BillingPortal() {
  const { user } = useAuth();

  if (!user) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="rounded-lg border border-border bg-card p-8 text-center">
          <CreditCard className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <h2 className="text-2xl font-semibold mb-2">Billing & Subscription</h2>
          <p className="text-muted-foreground mb-4">
            Sign in to manage your subscription
          </p>
          <Link href="/sign-in">
            <Button>Sign In</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Billing & Subscription</h1>
        <p className="text-muted-foreground">
          Manage your subscription and payment methods
        </p>
      </div>

      {/* Current Plan */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold mb-1">Current Plan</h2>
            <p className="text-muted-foreground">You are currently on the Free plan</p>
          </div>
          <Badge variant="secondary" className="text-sm">
            Free
          </Badge>
        </div>
      </div>

      {/* Pricing Tiers */}
      <div>
        <h2 className="text-2xl font-bold mb-6">Upgrade Your Plan</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={`rounded-2xl border p-6 ${
                tier.highlight
                  ? 'border-brand bg-brand/5'
                  : 'border-border bg-card'
              }`}
            >
              {tier.highlight && (
                <Badge className="mb-4">
                  <Zap className="w-3 h-3 mr-1" />
                  Most Popular
                </Badge>
              )}
              <h3 className="text-2xl font-bold mb-2">{tier.name}</h3>
              <div className="mb-4">
                <span className="text-4xl font-bold">{tier.price}</span>
                <span className="text-muted-foreground ml-2">{tier.period}</span>
              </div>
              <ul className="space-y-3 mb-6">
                {tier.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm">
                    <Check className="w-4 h-4 text-success mt-0.5 flex-shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
              {tier.current ? (
                <Button variant="outline" className="w-full" disabled>
                  Current Plan
                </Button>
              ) : (
                <Button
                  variant={tier.highlight ? 'default' : 'outline'}
                  className="w-full"
                >
                  Upgrade to {tier.name}
                </Button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Payment Method */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <h2 className="text-xl font-semibold mb-4">Payment Method</h2>
        <p className="text-sm text-muted-foreground mb-4">
          No payment method on file
        </p>
        <Button variant="outline">
          <CreditCard className="w-4 h-4 mr-2" />
          Add Payment Method
        </Button>
      </div>

      {/* Billing History */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <h2 className="text-xl font-semibold mb-4">Billing History</h2>
        <p className="text-sm text-muted-foreground">
          No billing history available
        </p>
      </div>
    </div>
  );
}
