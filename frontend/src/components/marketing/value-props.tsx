'use client';

import { motion } from 'framer-motion';
import { Brain, Zap, Eye } from 'lucide-react';

const props = [
  {
    icon: Brain,
    title: 'Smart',
    description: 'AI interprets blockchain data, highlights anomalies',
    color: 'text-brand',
  },
  {
    icon: Zap,
    title: 'Fast',
    description: 'Real-time UTXO analytics',
    color: 'text-sky-500',
  },
  {
    icon: Eye,
    title: 'Transparent',
    description: 'No black-box predictions, full explainability',
    color: 'text-emerald-500',
  },
];

export function ValueProps() {
  return (
    <section className="py-20 bg-background">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid md:grid-cols-3 gap-8">
          {props.map((prop, index) => (
            <motion.div
              key={prop.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="text-center"
            >
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-card border border-border mb-6">
                <prop.icon className={`h-8 w-8 ${prop.color}`} />
              </div>
              <h3 className="text-2xl font-bold mb-3">{prop.title}</h3>
              <p className="text-muted-foreground">{prop.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
