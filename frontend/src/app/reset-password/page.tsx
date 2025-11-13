import { Metadata } from 'next';
import { ResetPasswordForm } from '@/components/auth/reset-password-form';

export const metadata: Metadata = {
  title: 'Reset Password - utxoIQ',
  description: 'Reset your utxoIQ password',
};

export default function ResetPasswordPage() {
  return (
    <div className="flex min-h-[calc(100vh-128px)] items-center justify-center px-4 py-12">
      <ResetPasswordForm />
    </div>
  );
}
