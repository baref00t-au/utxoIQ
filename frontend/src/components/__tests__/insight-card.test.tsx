import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { InsightCard } from '../insights/insight-card';
import { Insight } from '@/types';

const mockInsight: Insight = {
  id: '1',
  signal_type: 'mempool',
  headline: 'Test Insight Headline',
  summary: 'This is a test summary',
  confidence: 0.85,
  timestamp: new Date().toISOString(),
  block_height: 800000,
  evidence: [
    {
      type: 'block',
      id: '00000000000000000001',
      description: 'Test block',
      url: 'https://example.com',
    },
  ],
  tags: ['test'],
};

describe('InsightCard', () => {
  it('renders insight headline', () => {
    render(<InsightCard insight={mockInsight} />);
    expect(screen.getByText('Test Insight Headline')).toBeInTheDocument();
  });

  it('renders insight summary', () => {
    render(<InsightCard insight={mockInsight} />);
    expect(screen.getByText('This is a test summary')).toBeInTheDocument();
  });

  it('displays confidence score', () => {
    render(<InsightCard insight={mockInsight} />);
    expect(screen.getByText('85% confidence')).toBeInTheDocument();
  });

  it('shows guest mode CTA when isGuest is true', () => {
    render(<InsightCard insight={mockInsight} isGuest={true} />);
    expect(screen.getByText(/Sign up/)).toBeInTheDocument();
  });
});
