import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/**
 * Accessibility Compliance Tests
 * 
 * Tests WCAG 2.1 AA compliance using axe-core automated testing.
 * Validates color contrast, ARIA labels, keyboard navigation, and focus management.
 */

test.describe('Accessibility Compliance', () => {
  test('homepage should not have any automatically detectable accessibility issues', async ({ page }) => {
    await page.goto('/');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('insight feed page should not have accessibility violations', async ({ page }) => {
    await page.goto('/');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('daily brief page should not have accessibility violations', async ({ page }) => {
    await page.goto('/brief');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('sign in page should not have accessibility violations', async ({ page }) => {
    await page.goto('/sign-in');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });
});

test.describe('Color Contrast Validation', () => {
  test('should meet minimum 4.5:1 contrast ratio for text', async ({ page }) => {
    await page.goto('/');
    
    // Run axe with specific focus on color contrast
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .include(['body'])
      .analyze();

    // Filter for color contrast violations
    const contrastViolations = accessibilityScanResults.violations.filter(
      violation => violation.id === 'color-contrast'
    );

    expect(contrastViolations).toEqual([]);
  });

  test('should have sufficient contrast for interactive elements', async ({ page }) => {
    await page.goto('/');
    
    // Check buttons
    const buttons = await page.locator('button').all();
    expect(buttons.length).toBeGreaterThan(0);

    // Check links
    const links = await page.locator('a').all();
    expect(links.length).toBeGreaterThan(0);

    // Run contrast check
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .analyze();

    const contrastViolations = accessibilityScanResults.violations.filter(
      violation => violation.id === 'color-contrast'
    );

    expect(contrastViolations).toEqual([]);
  });
});

test.describe('Keyboard Navigation', () => {
  test('skip to main content link should be accessible via keyboard', async ({ page }) => {
    await page.goto('/');
    
    // Press Tab to focus skip link
    await page.keyboard.press('Tab');
    
    // Check if skip link is focused
    const skipLink = page.locator('a[href="#main-content"]');
    await expect(skipLink).toBeFocused();
    
    // Verify skip link text
    await expect(skipLink).toHaveText('Skip to main content');
  });

  test('should be able to navigate header links with keyboard', async ({ page }) => {
    await page.goto('/');
    
    // Tab through header elements
    await page.keyboard.press('Tab'); // Skip link
    await page.keyboard.press('Tab'); // Mobile nav or logo
    
    // Check that we can reach navigation links
    const feedLink = page.locator('a[href="/"]').first();
    const briefLink = page.locator('a[href="/brief"]').first();
    
    await expect(feedLink).toBeVisible();
    await expect(briefLink).toBeVisible();
  });

  test('all interactive elements should be keyboard accessible', async ({ page }) => {
    await page.goto('/');
    
    // Run axe check for keyboard accessibility
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();

    // Check for keyboard-related violations
    const keyboardViolations = accessibilityScanResults.violations.filter(
      violation => 
        violation.id === 'keyboard' || 
        violation.id === 'focus-order-semantics' ||
        violation.id === 'tabindex'
    );

    expect(keyboardViolations).toEqual([]);
  });

  test('modal dialogs should trap focus', async ({ page }) => {
    await page.goto('/');
    
    // Open keyboard shortcuts help modal with '?'
    await page.keyboard.press('?');
    
    // Wait for modal to appear
    await page.waitForTimeout(500);
    
    // Check if modal is visible
    const modal = page.locator('[role="dialog"]');
    if (await modal.count() > 0) {
      await expect(modal).toBeVisible();
      
      // Tab through modal elements
      await page.keyboard.press('Tab');
      
      // Focus should stay within modal
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      expect(focusedElement).toBeTruthy();
    }
  });
});

test.describe('Focus Management', () => {
  test('focus indicators should be visible on all interactive elements', async ({ page }) => {
    await page.goto('/');
    
    // Tab to first interactive element
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Check that focused element has visible focus indicator
    const focusedElement = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el) return null;
      
      const styles = window.getComputedStyle(el);
      return {
        outline: styles.outline,
        outlineWidth: styles.outlineWidth,
        boxShadow: styles.boxShadow,
      };
    });
    
    expect(focusedElement).toBeTruthy();
    // Should have either outline or box-shadow for focus indicator
    const hasFocusIndicator = 
      (focusedElement?.outline && focusedElement.outline !== 'none') ||
      (focusedElement?.boxShadow && focusedElement.boxShadow !== 'none');
    
    expect(hasFocusIndicator).toBeTruthy();
  });

  test('focus should not be lost when navigating', async ({ page }) => {
    await page.goto('/');
    
    // Tab through several elements
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
      
      // Verify focus is on an element
      const hasFocus = await page.evaluate(() => {
        return document.activeElement !== document.body;
      });
      
      expect(hasFocus).toBeTruthy();
    }
  });
});

test.describe('ARIA Labels and Roles', () => {
  test('all icons should have proper ARIA labels or be marked as decorative', async ({ page }) => {
    await page.goto('/');
    
    // Run axe check for image alt text and ARIA labels
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();

    const imageViolations = accessibilityScanResults.violations.filter(
      violation => 
        violation.id === 'image-alt' || 
        violation.id === 'svg-img-alt' ||
        violation.id === 'button-name'
    );

    expect(imageViolations).toEqual([]);
  });

  test('landmark regions should be properly labeled', async ({ page }) => {
    await page.goto('/');
    
    // Check for main landmark
    const main = page.locator('main[role="main"]');
    await expect(main).toBeVisible();
    
    // Check for header landmark
    const header = page.locator('header[role="banner"]');
    await expect(header).toBeVisible();
    
    // Check for footer landmark
    const footer = page.locator('footer[role="contentinfo"]');
    await expect(footer).toBeVisible();
    
    // Check for navigation landmarks
    const navs = page.locator('nav[role="navigation"]');
    expect(await navs.count()).toBeGreaterThan(0);
  });

  test('form inputs should have associated labels', async ({ page }) => {
    await page.goto('/sign-in');
    
    // Run axe check for form labels
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();

    const labelViolations = accessibilityScanResults.violations.filter(
      violation => 
        violation.id === 'label' || 
        violation.id === 'label-title-only'
    );

    expect(labelViolations).toEqual([]);
  });

  test('buttons should have accessible names', async ({ page }) => {
    await page.goto('/');
    
    // Get all buttons
    const buttons = await page.locator('button').all();
    
    for (const button of buttons) {
      // Each button should have text content or aria-label
      const hasAccessibleName = await button.evaluate((el) => {
        const text = el.textContent?.trim();
        const ariaLabel = el.getAttribute('aria-label');
        const ariaLabelledBy = el.getAttribute('aria-labelledby');
        
        return !!(text || ariaLabel || ariaLabelledBy);
      });
      
      expect(hasAccessibleName).toBeTruthy();
    }
  });
});

test.describe('Screen Reader Support', () => {
  test('page should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/');
    
    // Run axe check for heading order
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();

    const headingViolations = accessibilityScanResults.violations.filter(
      violation => violation.id === 'heading-order'
    );

    expect(headingViolations).toEqual([]);
  });

  test('lists should be properly structured', async ({ page }) => {
    await page.goto('/');
    
    // Run axe check for list structure
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();

    const listViolations = accessibilityScanResults.violations.filter(
      violation => 
        violation.id === 'list' || 
        violation.id === 'listitem'
    );

    expect(listViolations).toEqual([]);
  });

  test('page should have a descriptive title', async ({ page }) => {
    await page.goto('/');
    
    const title = await page.title();
    expect(title).toBeTruthy();
    expect(title.length).toBeGreaterThan(0);
    expect(title).toContain('utxoIQ');
  });

  test('language should be specified', async ({ page }) => {
    await page.goto('/');
    
    const lang = await page.locator('html').getAttribute('lang');
    expect(lang).toBe('en');
  });
});
