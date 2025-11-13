'use client';

import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { Check } from 'lucide-react';

const plans = [
  {
    name: 'Free',
    price: '$0',
    period: 'forever',
    features: [
      'AI summaries (24h delay)',
      'Limited insights',
      'No alerts',
      'Community support',
    ],
    cta: 'Start Free',
    href: '/sign-up',
    highlighted: false,
  },
  {
    name: 'Pro Trader',
    price: '$39',
    period: 'per month',
    annual: '$399/yr (save $69)',
    features: [
      'Real-time AI insights',
      'Whale alerts',
      'Mempool analysis',
      'Custom alerts',
      'Priority support',
    ],
    cta: 'Start Free Trial',
    href: '/sign-up?plan=pro',
    highlighted: true,
  },
  {
    name: 'Analyst',
    price: '$99',
    period: 'per month',
    annual: '$999/yr (save $189)',
    features: [
      'Everything in Pro Trader',
      'Full AI reasoning feed',
      'CSV/JSON export',
      'API access',
      'Advanced analytics',
      'Dedicated support',
    ],
    cta: 'Start Free Trial',
    href: '/sign-up?plan=analyst',
    highlighted: false,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: 'starting at $299/mo',
    features: [
      'Everything in Analyst',
      'Dedicated model access',
      'Integration support',
      'Private dashboard',
      'SLA guarantee',
      'Team collaboration',
    ],
    cta: 'Contact Sales',
    href: '/contact',
    highlighted: false,
  },
];

export function PricingCTA() {
  return (
    <section id="pricing" className="py-20 bg-gradient-to-b from-muted/20 to-background">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Pricing Built for Every Trader
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            From curious beginners to professional analysts — start free, scale as you grow
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-7xl mx-auto">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className={`relative rounded-2xl border p-6 ${
                plan.highlighted
                  ? 'border-brand bg-card shadow-2xl lg:scale-105'
                  : 'border-border bg-card'
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <span className="bg-brand text-white px-4 py-1 rounded-full text-sm font-semibold">
                    Most Popular
                  </span>
                </div>
              )}

              <div className="text-center mb-6">
                <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
                <div className="mb-2">
                  <span className="text-3xl font-bold">{plan.price}</span>
                  {plan.price !== 'Custom' && (
                    <span className="text-muted-foreground text-sm ml-1">/ mo</span>
                  )}
                </div>
                {plan.annual && (
                  <p className="text-xs text-muted-foreground">{plan.annual}</p>
                )}
                {plan.price === 'Custom' && (
                  <p className="text-xs text-muted-foreground">{plan.period}</p>
                )}
              </div>

              <ul className="space-y-3 mb-8">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-3">
                    <Check className="h-5 w-5 text-brand flex-shrink-0 mt-0.5" />
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>

              <Link href={plan.href} className="block">
                <Button
                  className="w-full"
                  variant={plan.highlighted ? 'default' : 'outline'}
                  size="lg"
                >
                  {plan.cta}
                </Button>
              </Link>
            </motion.div>
          ))}
        </div>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 }}
          className="text-center text-sm text-muted-foreground mt-8"
        >
          No credit card required • Cancel anytime • 14-day money-back guarantee
        </motion.p>
      </div>
    </section>
  );
}
