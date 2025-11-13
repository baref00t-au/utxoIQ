'use client';

import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { TrendingUp, Zap, Activity } from 'lucide-react';

export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-background to-background/80 pt-20 pb-32">
      {/* Animated background grid */}
      <div className="absolute inset-0 bg-grid-white/[0.02] -z-10" />
      
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left: Copy */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center lg:text-left"
          >
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-6">
              See What's Happening on Bitcoin —{' '}
              <span className="text-brand">Before Everyone Else</span>
            </h1>
            <p className="text-xl text-muted-foreground mb-8 max-w-2xl">
              utxoIQ turns blockchain data into actionable intelligence powered by AI.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <Link href="/sign-up">
                <Button size="lg" className="text-lg px-8 py-6">
                  Start Free
                </Button>
              </Link>
              <Link href="#demo">
                <Button size="lg" variant="outline" className="text-lg px-8 py-6">
                  Watch Demo
                </Button>
              </Link>
            </div>
          </motion.div>

          {/* Right: Animated Dashboard Preview */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative"
          >
            <div className="relative rounded-2xl border border-border bg-card p-6 shadow-2xl">
              {/* Live metrics flowing */}
              <div className="space-y-4">
                <MetricCard
                  icon={<TrendingUp className="h-5 w-5" />}
                  label="Mempool Activity"
                  value="High"
                  trend="+32%"
                  color="orange"
                  delay={0}
                />
                <MetricCard
                  icon={<Zap className="h-5 w-5" />}
                  label="Whale Alert"
                  value="1,633 BTC"
                  trend="Exchange Outflow"
                  color="violet"
                  delay={0.2}
                />
                <MetricCard
                  icon={<Activity className="h-5 w-5" />}
                  label="AI Insight"
                  value="92% Confidence"
                  trend="Low Network Demand"
                  color="emerald"
                  delay={0.4}
                />
              </div>

              {/* Pulse indicator */}
              <div className="absolute -top-2 -right-2">
                <span className="relative flex h-4 w-4">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-4 w-4 bg-brand"></span>
                </span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

function MetricCard({
  icon,
  label,
  value,
  trend,
  color,
  delay,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  trend: string;
  color: 'orange' | 'violet' | 'emerald';
  delay: number;
}) {
  const colorClasses = {
    orange: 'text-orange-500 bg-orange-500/10',
    violet: 'text-violet-500 bg-violet-500/10',
    emerald: 'text-emerald-500 bg-emerald-500/10',
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: delay + 0.6 }}
      className="flex items-center gap-4 p-4 rounded-lg border border-border bg-background/50"
    >
      <div className={`p-2 rounded-lg ${colorClasses[color]}`}>{icon}</div>
      <div className="flex-1">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="text-lg font-semibold">{value}</p>
      </div>
      <div className="text-sm text-muted-foreground">{trend}</div>
    </motion.div>
  );
}
