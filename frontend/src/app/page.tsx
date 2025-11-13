import { HeroSection } from '@/components/marketing/hero-section';
import { ValueProps } from '@/components/marketing/value-props';
import { ProductPreview } from '@/components/marketing/product-preview';
import { SocialProof } from '@/components/marketing/social-proof';
import { PricingCTA } from '@/components/marketing/pricing-cta';
import { BottomConversion } from '@/components/marketing/bottom-conversion';

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <HeroSection />
      <ValueProps />
      <ProductPreview />
      <SocialProof />
      <PricingCTA />
      <BottomConversion />
    </div>
  );
}
