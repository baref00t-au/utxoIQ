import { Metadata } from 'next';
import { SignInForm } from '@/components/auth/sign-in-form';

export const metadata: Metadata = {
  title: 'Sign In - utxoIQ',
  description: 'Sign in to your utxoIQ account',
};

export default function SignInPage() {
  return (
    <div className="flex min-h-[calc(100vh-128px)] items-center justify-center px-4 py-12">
      <SignInForm />
    </div>
  );
}
