import { Metadata } from 'next';
import { ProfileSettings } from '@/components/profile/profile-settings';

export const metadata: Metadata = {
  title: 'Profile Settings - utxoIQ',
  description: 'Manage your utxoIQ profile settings',
};

export default function ProfilePage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <ProfileSettings />
    </div>
  );
}
