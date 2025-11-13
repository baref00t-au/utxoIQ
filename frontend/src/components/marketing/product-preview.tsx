'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';
import { Sparkles, TrendingUp, Activity, BarChart3 } from 'lucide-react';

const features = [
  {
    icon: Sparkles,
    title: 'AI Insights Feed',
    description: 'Real-time blockchain intelligence powered by Gemini AI',
    image: '/screenshots/insights-feed.png',
  },
  {
    icon: TrendingUp,
    title: 'Whale Tracking Heatmap',
    description: 'Monitor large transactions and exchange flows',
    image: '/screenshots/whale-tracking.png',
  },
  {
    icon: Activity,
    title: 'Real-time Mempool Flow',
    description: 'Track fee pressure and transaction congestion',
    image: '/screenshots/mempool-flow.png',
  },
  {
    icon: BarChart3,
    title: 'Macro Bitcoin Signals',
    description: 'UTXO age, miner activity, and network health',
    image: '/screenshots/macro-signals.png',
  },
];

export function ProductPreview() {
  return (
    <section id="features" className="py-20 bg-gradient-to-b from-background to-muted/20">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Everything You Need to Stay Ahead
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Comprehensive Bitcoin intelligence in one powerful platform
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-12">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="group"
            >
              <div className="relative rounded-2xl border border-border bg-card overflow-hidden shadow-lg hover:shadow-2xl transition-shadow duration-300">
                {/* Screenshot placeholder */}
                <div className="aspect-video bg-gradient-to-br from-muted to-muted/50 flex items-center justify-center">
                  <feature.icon className="h-16 w-16 text-muted-foreground/30" />
                </div>

                {/* Content */}
                <div className="p-6">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 rounded-lg bg-brand/10">
                      <feature.icon className="h-5 w-5 text-brand" />
                    </div>
                    <h3 className="text-xl font-semibold">{feature.title}</h3>
                  </div>
                  <p className="text-muted-foreground">{feature.description}</p>
                </div>

                {/* Hover effect */}
                <div className="absolute inset-0 bg-brand/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
