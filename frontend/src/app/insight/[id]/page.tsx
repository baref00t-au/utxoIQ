import { InsightDetail } from '@/components/insights/insight-detail';

export default function InsightPage({ params }: { params: { id: string } }) {
  return (
    <div className="container mx-auto px-4 py-8">
      <InsightDetail insightId={params.id} />
    </div>
  );
}
