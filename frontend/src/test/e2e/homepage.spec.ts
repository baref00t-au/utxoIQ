import { test, expect } from '@playwright/test';

test.describe('Homepage', () => {
  test('should display the header', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('header')).toBeVisible();
    await expect(page.getByText('utxoIQ')).toBeVisible();
  });

  test('should show guest mode prompt when not authenticated', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Welcome to utxoIQ')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible();
  });

  test('should navigate to sign in page', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Sign In' }).first().click();
    await expect(page).toHaveURL(/\/sign-in/);
  });

  test('should have responsive navigation', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Feed')).toBeVisible();
    await expect(page.getByText('Brief')).toBeVisible();
  });
});
