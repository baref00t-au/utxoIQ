import { Metadata } from 'next';
import { APIKeyManagement } from '@/components/profile/api-key-management';

export const metadata: Metadata = {
  title: 'API Keys - utxoIQ',
  description: 'Manage your utxoIQ API keys',
};

export default function APIKeysPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <APIKeyManagement />
    </div>
  );
}
