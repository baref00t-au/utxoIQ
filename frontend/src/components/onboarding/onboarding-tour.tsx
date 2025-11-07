'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { X, ArrowRight, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface OnboardingStep {
  title: string;
  description: string;
  target?: string;
}

const ONBOARDING_STEPS: OnboardingStep[] = [
  {
    title: 'Welcome to utxoIQ!',
    description: 'Let us show you around. This quick tour will help you get started with AI-powered Bitcoin insights.',
  },
  {
    title: 'Live Feed',
    description: 'Your home for real-time blockchain insights. New insights appear here automatically as they are generated.',
    target: 'feed',
  },
  {
    title: 'Daily Brief',
    description: 'Get a curated summary of the top 3-5 blockchain events every day at 07:00 UTC.',
    target: 'brief',
  },
  {
    title: 'Custom Alerts',
    description: 'Set up alerts for specific blockchain metrics and get notified when conditions are met.',
    target: 'alerts',
  },
  {
    title: 'You\'re all set!',
    description: 'Start exploring Bitcoin blockchain insights powered by AI. You can always access help from the menu.',
  },
];

interface OnboardingTourProps {
  onComplete: () => void;
  onSkip: () => void;
}

export function OnboardingTour({ onComplete, onSkip }: OnboardingTourProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(true);

  const handleNext = () => {
    if (currentStep < ONBOARDING_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handleComplete = () => {
    setIsVisible(false);
    setTimeout(() => {
      onComplete();
    }, 300);
  };

  const handleSkip = () => {
    setIsVisible(false);
    setTimeout(() => {
      onSkip();
    }, 300);
  };

  const step = ONBOARDING_STEPS[currentStep];
  const isLastStep = currentStep === ONBOARDING_STEPS.length - 1;

  return (
    <AnimatePresence>
      {isVisible && (
        <>
          {/* Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40"
            onClick={handleSkip}
          />

          {/* Tour Card */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md"
          >
            <div className="rounded-2xl border-2 border-brand bg-card p-8 shadow-2xl">
              {/* Close Button */}
              <button
                onClick={handleSkip}
                className="absolute top-4 right-4 text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="w-5 h-5" />
              </button>

              {/* Content */}
              <div className="mb-6">
                <h2 className="text-2xl font-bold mb-3">{step.title}</h2>
                <p className="text-muted-foreground leading-relaxed">
                  {step.description}
                </p>
              </div>

              {/* Progress */}
              <div className="mb-6">
                <div className="flex gap-2">
                  {ONBOARDING_STEPS.map((_, idx) => (
                    <div
                      key={idx}
                      className={`h-1 flex-1 rounded-full transition-colors ${
                        idx <= currentStep ? 'bg-brand' : 'bg-muted'
                      }`}
                    />
                  ))}
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  Step {currentStep + 1} of {ONBOARDING_STEPS.length}
                </p>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                {!isLastStep && (
                  <Button variant="outline" onClick={handleSkip} className="flex-1">
                    Skip Tour
                  </Button>
                )}
                <Button onClick={handleNext} className="flex-1">
                  {isLastStep ? (
                    <>
                      <Check className="w-4 h-4 mr-2" />
                      Get Started
                    </>
                  ) : (
                    <>
                      Next
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
