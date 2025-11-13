import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Privacy Policy - utxoIQ',
  description: 'Privacy policy for utxoIQ Bitcoin intelligence platform',
};

export default function PrivacyPage() {
  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-12 max-w-4xl">
      <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>
      <p className="text-muted-foreground mb-8">Last updated: November 12, 2025</p>

      <div className="prose prose-zinc dark:prose-invert max-w-none space-y-8">
        <section>
          <h2 className="text-2xl font-semibold mb-4">1. Introduction</h2>
          <p className="text-muted-foreground mb-4">
            Welcome to utxoIQ ("we," "our," or "us"). We are committed to protecting your personal
            information and your right to privacy. This Privacy Policy explains how we collect, use,
            disclose, and safeguard your information when you use our Bitcoin intelligence platform.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">2. Information We Collect</h2>
          <h3 className="text-xl font-semibold mb-3">2.1 Information You Provide</h3>
          <ul className="list-disc pl-6 space-y-2 text-muted-foreground mb-4">
            <li>Account information (email address, password)</li>
            <li>Profile information (display name, preferences)</li>
            <li>Payment information (processed securely through Stripe)</li>
            <li>Communication data (support requests, feedback)</li>
          </ul>

          <h3 className="text-xl font-semibold mb-3">2.2 Automatically Collected Information</h3>
          <ul className="list-disc pl-6 space-y-2 text-muted-foreground mb-4">
            <li>Usage data (features accessed, time spent, interactions)</li>
            <li>Device information (browser type, operating system, IP address)</li>
            <li>Analytics data (page views, click patterns, performance metrics)</li>
            <li>Cookies and similar tracking technologies</li>
          </ul>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">3. How We Use Your Information</h2>
          <ul className="list-disc pl-6 space-y-2 text-muted-foreground mb-4">
            <li>Provide, maintain, and improve our services</li>
            <li>Process transactions and send related information</li>
            <li>Send administrative information, updates, and security alerts</li>
            <li>Respond to your comments, questions, and customer service requests</li>
            <li>Generate AI-powered insights and personalized recommendations</li>
            <li>Monitor and analyze usage patterns and trends</li>
            <li>Detect, prevent, and address technical issues and security threats</li>
            <li>Comply with legal obligations</li>
          </ul>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">4. Data Sharing and Disclosure</h2>
          <p className="text-muted-foreground mb-4">
            We do not sell your personal information. We may share your information in the following
            circumstances:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-muted-foreground mb-4">
            <li>
              <strong>Service Providers:</strong> Third-party vendors who perform services on our
              behalf (Firebase, Google Cloud, Stripe)
            </li>
            <li>
              <strong>Legal Requirements:</strong> When required by law or to protect our rights
            </li>
            <li>
              <strong>Business Transfers:</strong> In connection with a merger, acquisition, or sale
              of assets
            </li>
            <li>
              <strong>With Your Consent:</strong> When you explicitly agree to share information
            </li>
          </ul>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">5. Data Security</h2>
          <p className="text-muted-foreground mb-4">
            We implement appropriate technical and organizational security measures to protect your
            personal information, including:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-muted-foreground mb-4">
            <li>Encryption of data in transit and at rest</li>
            <li>Regular security audits and vulnerability assessments</li>
            <li>Access controls and authentication mechanisms</li>
            <li>Secure cloud infrastructure (Google Cloud Platform)</li>
            <li>Regular backups and disaster recovery procedures</li>
          </ul>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">6. Data Retention</h2>
          <p className="text-muted-foreground mb-4">
            We retain your personal information for as long as necessary to provide our services and
            fulfill the purposes outlined in this Privacy Policy. When you delete your account, we
            will delete or anonymize your personal information within 30 days, except where we are
            required to retain it for legal or regulatory purposes.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">7. Your Privacy Rights</h2>
          <p className="text-muted-foreground mb-4">Depending on your location, you may have the following rights:</p>
          <ul className="list-disc pl-6 space-y-2 text-muted-foreground mb-4">
            <li>Access and receive a copy of your personal information</li>
            <li>Correct inaccurate or incomplete information</li>
            <li>Delete your personal information</li>
            <li>Object to or restrict processing of your information</li>
            <li>Data portability (receive your data in a structured format)</li>
            <li>Withdraw consent at any time</li>
            <li>Lodge a complaint with a supervisory authority</li>
          </ul>
          <p className="text-muted-foreground mb-4">
            To exercise these rights, please contact us at privacy@utxoiq.com
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">8. Cookies and Tracking</h2>
          <p className="text-muted-foreground mb-4">
            We use cookies and similar tracking technologies to track activity on our service and
            store certain information. You can instruct your browser to refuse all cookies or to
            indicate when a cookie is being sent. However, if you do not accept cookies, you may not
            be able to use some portions of our service.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">9. Third-Party Services</h2>
          <p className="text-muted-foreground mb-4">
            Our service may contain links to third-party websites or services. We are not responsible
            for the privacy practices of these third parties. We encourage you to review their
            privacy policies.
          </p>
          <p className="text-muted-foreground mb-4">Third-party services we use:</p>
          <ul className="list-disc pl-6 space-y-2 text-muted-foreground mb-4">
            <li>Firebase Authentication (Google)</li>
            <li>Google Cloud Platform</li>
            <li>Stripe (payment processing)</li>
            <li>Vertex AI (Google)</li>
          </ul>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">10. Children's Privacy</h2>
          <p className="text-muted-foreground mb-4">
            Our service is not intended for children under 18 years of age. We do not knowingly
            collect personal information from children under 18. If you are a parent or guardian and
            believe your child has provided us with personal information, please contact us.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">11. International Data Transfers</h2>
          <p className="text-muted-foreground mb-4">
            Your information may be transferred to and processed in countries other than your country
            of residence. These countries may have data protection laws that are different from the
            laws of your country. We ensure appropriate safeguards are in place to protect your
            information in accordance with this Privacy Policy.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">12. Changes to This Privacy Policy</h2>
          <p className="text-muted-foreground mb-4">
            We may update our Privacy Policy from time to time. We will notify you of any changes by
            posting the new Privacy Policy on this page and updating the "Last updated" date. You are
            advised to review this Privacy Policy periodically for any changes.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4">13. Contact Us</h2>
          <p className="text-muted-foreground mb-4">
            If you have any questions about this Privacy Policy, please contact us:
          </p>
          <ul className="list-none space-y-2 text-muted-foreground mb-4">
            <li>Email: privacy@utxoiq.com</li>
            <li>Website: utxoiq.com/contact</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
