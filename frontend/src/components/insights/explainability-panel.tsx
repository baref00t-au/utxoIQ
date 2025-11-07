'use client';

import { ExplainabilitySummary } from '@/types';
import { Progress } from '@/components/ui/progress';

interface ExplainabilityPanelProps {
  explainability: ExplainabilitySummary;
}

export function ExplainabilityPanel({ explainability }: ExplainabilityPanelProps) {
  const factors = explainability.confidence_factors;

  return (
    <div className="space-y-6">
      {/* Explanation */}
      <div>
        <h3 className="text-sm font-medium mb-2">Explanation</h3>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {explainability.explanation}
        </p>
      </div>

      {/* Confidence Factors */}
      <div>
        <h3 className="text-sm font-medium mb-4">Confidence Breakdown</h3>
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">Signal Strength</span>
              <span className="text-sm font-medium">
                {Math.round(factors.signal_strength * 100)}%
              </span>
            </div>
            <Progress value={factors.signal_strength * 100} className="h-2" />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">Historical Accuracy</span>
              <span className="text-sm font-medium">
                {Math.round(factors.historical_accuracy * 100)}%
              </span>
            </div>
            <Progress value={factors.historical_accuracy * 100} className="h-2" />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">Data Quality</span>
              <span className="text-sm font-medium">
                {Math.round(factors.data_quality * 100)}%
              </span>
            </div>
            <Progress value={factors.data_quality * 100} className="h-2" />
          </div>
        </div>
      </div>

      {/* Supporting Evidence */}
      {explainability.supporting_evidence.length > 0 && (
        <div>
          <h3 className="text-sm font-medium mb-2">Supporting Evidence</h3>
          <ul className="space-y-2">
            {explainability.supporting_evidence.map((evidence, idx) => (
              <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                <span className="text-brand mt-1">•</span>
                <span>{evidence}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
