import { expect, test } from '@playwright/test';
import { mkdir } from 'node:fs/promises';

test("admin reviews a synthetic patient's readings and manages the team", async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /A clearer view/i })).toBeVisible();
  await page.getByLabel('Username').fill('demo-admin');
  await page.getByLabel('Password').fill('DemoAdmin2026!');
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page.getByText('Synthetic environment')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Mina Solberg' })).toBeVisible();
  await page.getByRole('button', { name: /Theo Calder/ }).click();
  await expect(page.getByRole('heading', { name: 'Theo Calder' })).toBeVisible();
  await expect(page.getByRole('heading', { name: /Signals to review/ })).toBeVisible();
  await expect(page.getByRole('img', { name: /Heart rate trend/ })).toBeVisible();
  await mkdir('test-results/screenshots', { recursive: true });
  await page.screenshot({ path: 'test-results/screenshots/patient-dashboard.png', fullPage: true });
  await page.getByRole('button', { name: 'Team access' }).click();
  await expect(page.getByRole('heading', { name: 'Team members' })).toBeVisible();
  await expect(page.getByText('demo-clinician@example.test')).toBeVisible();
  await page.screenshot({ path: 'test-results/screenshots/team-admin.png', fullPage: true });
});

test('researcher sees pseudonyms instead of names', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Username').fill('demo-researcher');
  await page.getByLabel('Password').fill('DemoResearch2026!');
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page.getByRole('heading', { name: /p-/ }).first()).toBeVisible();
  await expect(page.getByText('Mina Solberg')).toHaveCount(0);
  await expect(page.getByRole('button', { name: /Export pseudonymized/ })).toBeVisible();
});
