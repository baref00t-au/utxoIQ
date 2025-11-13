import { Metadata } from 'next';
import { SignUpForm } from '@/components/auth/sign-up-form';

export const metadata: Metadata = {
  title: 'Sign Up - utxoIQ',
  description: 'Create your utxoIQ account',
};

export default function SignUpPage() {
  return (
    <div className="flex min-h-[calc(100vh-128px)] items-center justify-center px-4 py-12">
      <SignUpForm />
    </div>
  );
}
