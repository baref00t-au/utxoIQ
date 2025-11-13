import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Terms of Service - utxoIQ',
  description: 'Terms of service for utxoIQ Bitcoin intelligence platform',
};

export default function TermsPage() {
  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-12 max-w-4xl">
      <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>
      <p className="text-muted-foreground mb-8">Last updated: November 12, 2025</p>

      <div className="prose prose-zinc dark:prose-invert max-w-none space-y-8">
        <section>
          <h2 className="text-2xl font-semibold mb-4">1. Agreement to Terms</h2>
          <p className="text-muted-foreground mb-4">
            By accessing or using utxoIQ ("Service"), you agree to be bound by these Terms of Service
            ("Terms"). If you disagree with any part of these terms, you may not access the Service.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">2. Description of Service</h2>
          <p className="text-muted-foreground mb-4">
            utxoIQ is an AI-powered Bitcoin blockchain intelligence platform that provides real-time
            insights, analytics, and alerts based on on-chain data. The Service includes:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-muted-foreground mb-4">
            <li>AI-generated blockchain insights and analysis</li>
            <li>Real-time mempool monitoring and whale tracking</li>
            <li>Custom alerts and notifications</li>
            <li>Data export and API access (paid tiers)</li>
            <li>Daily intelligence briefs</li>
          </ul>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">3. User Accounts</h2>
          <h3 className="text-xl font-semibold mb-3">3.1 Account Creation</h3>
          <p className="text-muted-foreground mb-4">
            You must create an account to access certain features. You agree to provide accurate,
            current, and complete information during registration and to update such information to
            keep it accurate, current, and complete.
          </p>

          <h3 className="text-xl font-semibold mb-3">3.2 Account Security</h3>
          <p className="text-muted-foreground mb-4">
            You are responsible for maintaining the confidentiality of your account credentials and
            for all activities that occur under your account. You agree to notify us immediately of
            any unauthorized use of your account.
          </p>

          <h3 className="text-xl font-semibold mb-3">3.3 Account Termination</h3>
          <p className="text-muted-foreground mb-4">
            We reserve the right to suspend or terminate your account at any time for violations of
            these Terms or for any other reason at our sole discretion.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">4. Subscription Plans and Billing</h2>
          <h3 className="text-xl font-semibold mb-3">4.1 Subscription Tiers</h3>
          <p className="text-muted-foreground mb-4">
            We offer multiple subscription tiers: Free, Pro Trader ($39/mo), Analyst ($99/mo), and
            Enterprise (custom pricing). Features and limitations vary by tier.
          </p>

          <h3 className="text-xl font-semibold mb-3">4.2 Payment Terms</h3>
          <ul className="list-disc pl-6 space-y-2 text-muted-foreground mb-4">
            <li>Subscriptions are billed monthly or annually in advance</li>
            <li>All payments are processed securely through Stripe</li>
            <li>Prices are subject to change with 30 days notice</li>
            <li>Annual plans offer approximately 20% savings</li>
          </ul>

          <h3 className="text-xl font-semibold mb-3">4.3 Refunds</h3>
          <p className="text-muted-foreground mb-4">
            We offer a 14-day money-back guarantee for first-time subscribers. Refunds are not
            available for renewals or after 14 days of initial purchase.
          </p>

          <h3 className="text-xl font-semibold mb-3">4.4 Cancellation</h3>
          <p className="text-muted-foreground mb-4">
            You may cancel your subscription at any time. Cancellations take effect at the end of the
            current billing period. No partial refunds are provided for unused time.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">5. Acceptable Use</h2>
          <p className="text-muted-foreground mb-4">You agree not to:</p>
          <ul className="list-disc pl-6 space-y-2 text-muted-foreground mb-4">
            <li>Use the Service for any illegal purpose or in violation of any laws</li>
            <li>Attempt to gain unauthorized access to the Service or related systems</li>
            <li>Interfere with or disrupt the Service or servers</li>
            <li>Use automated systems (bots, scrapers) without written permission</li>
            <li>Resell, redistribute, or sublicense the Service or data</li>
            <li>Reverse engineer or attempt to extract source code</li>
            <li>Remove or modify any proprietary notices or labels</li>
            <li>Use the Service to transmit malware or harmful code</li>
          </ul>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">6. Intellectual Property</h2>
          <h3 className="text-xl font-semibold mb-3">6.1 Our Content</h3>
          <p className="text-muted-foreground mb-4">
            The Service and its original content, features, and functionality are owned by utxoIQ and
            are protected by international copyright, trademark, patent, trade secret, and other
            intellectual property laws.
          </p>

          <h3 className="text-xl font-semibold mb-3">6.2 Your Content</h3>
          <p className="text-muted-foreground mb-4">
            You retain ownership of any content you submit to the Service (feedback, comments). By
            submitting content, you grant us a worldwide, non-exclusive, royalty-free license to use,
            reproduce, and display such content in connection with the Service.
          </p>

          <h3 className="text-xl font-semibold mb-3">6.3 Blockchain Data</h3>
          <p className="text-muted-foreground mb-4">
            Bitcoin blockchain data is public information. Our AI-generated insights, analysis, and
            interpretations of this data are proprietary to utxoIQ.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">7. API Usage</h2>
          <p className="text-muted-foreground mb-4">
            API access is available to Analyst and Enterprise tier subscribers. API usage is subject
            to rate limits and fair use policies. Abuse of API access may result in suspension or
            termination.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">8. Disclaimers and Limitations</h2>
          <h3 className="text-xl font-semibold mb-3">8.1 No Investment Advice</h3>
          <p className="text-muted-foreground mb-4">
            <strong>IMPORTANT:</strong> utxoIQ provides informational and analytical tools only. We
            do not provide investment, financial, legal, or tax advice. All insights and analysis are
            for informational purposes only and should not be construed as investment recommendations.
            You are solely responsible for your investment decisions.
          </p>

          <h3 className="text-xl font-semibold mb-3">8.2 No Guarantees</h3>
          <p className="text-muted-foreground mb-4">
            We do not guarantee the accuracy, completeness, or timeliness of any information provided
            through the Service. AI-generated insights may contain errors or inaccuracies. Past
            performance does not indicate future results.
          </p>

          <h3 className="text-xl font-semibold mb-3">8.3 Service Availability</h3>
          <p className="text-muted-foreground mb-4">
            We strive for 99.9% uptime but do not guarantee uninterrupted access to the Service. We
            may suspend or discontinue the Service at any time without notice.
          </p>

          <h3 className="text-xl font-semibold mb-3">8.4 Limitation of Liability</h3>
          <p className="text-muted-foreground mb-4">
            TO THE MAXIMUM EXTENT PERMITTED BY LAW, UTXOIQ SHALL NOT BE LIABLE FOR ANY INDIRECT,
            INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS OR
            REVENUES, WHETHER INCURRED DIRECTLY OR INDIRECTLY, OR ANY LOSS OF DATA, USE, GOODWILL, OR
            OTHER INTANGIBLE LOSSES.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">9. Indemnification</h2>
          <p className="text-muted-foreground mb-4">
            You agree to indemnify and hold harmless utxoIQ and its officers, directors, employees,
            and agents from any claims, damages, losses, liabilities, and expenses (including
            attorneys' fees) arising out of your use of the Service or violation of these Terms.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">10. Privacy</h2>
          <p className="text-muted-foreground mb-4">
            Your use of the Service is also governed by our Privacy Policy. Please review our Privacy
            Policy to understand our practices regarding your personal information.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">11. Changes to Terms</h2>
          <p className="text-muted-foreground mb-4">
            We reserve the right to modify these Terms at any time. We will notify users of material
            changes via email or through the Service. Your continued use of the Service after changes
            constitutes acceptance of the modified Terms.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">12. Governing Law</h2>
          <p className="text-muted-foreground mb-4">
            These Terms shall be governed by and construed in accordance with the laws of the United
            States, without regard to its conflict of law provisions.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">13. Dispute Resolution</h2>
          <p className="text-muted-foreground mb-4">
            Any disputes arising out of or relating to these Terms or the Service shall be resolved
            through binding arbitration in accordance with the rules of the American Arbitration
            Association.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">14. Severability</h2>
          <p className="text-muted-foreground mb-4">
            If any provision of these Terms is found to be unenforceable or invalid, that provision
            shall be limited or eliminated to the minimum extent necessary so that these Terms shall
            otherwise remain in full force and effect.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">15. Contact Information</h2>
          <p className="text-muted-foreground mb-4">
            If you have any questions about these Terms, please contact us:
          </p>
          <ul className="list-none space-y-2 text-muted-foreground mb-4">
            <li>Email: legal@utxoiq.com</li>
            <li>Website: utxoiq.com/contact</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
