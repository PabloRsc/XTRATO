import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { chromium } from 'playwright';

const baseURL = process.env.XTRATO_BASE_URL || 'http://127.0.0.1:8000';
const username = process.env.XTRATO_TEST_USERNAME;
const password = process.env.XTRATO_TEST_PASSWORD;

assert.ok(username, 'XTRATO_TEST_USERNAME is required');
assert.ok(password, 'XTRATO_TEST_PASSWORD is required');

await mkdir('artifacts', { recursive: true });
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const pageErrors = [];

page.on('pageerror', error => pageErrors.push(error.message));

try {
  await page.goto(baseURL, { waitUntil: 'domcontentloaded' });
  await page.locator('#loginView').waitFor({ state: 'visible' });
  await page.locator('#loginForm input[name="username"]').fill(username);
  await page.locator('#loginForm input[name="password"]').fill(password);
  await page.locator('#loginForm button[type="submit"]').click();

  await page.locator('#appView').waitFor({ state: 'visible', timeout: 15000 });
  await page.locator('#page-dashboard').waitFor({ state: 'visible' });
  await page.locator('#walletCards').waitFor({ state: 'visible' });
  await page.locator('#statementEntries').waitFor({ state: 'visible' });
  await page.locator('#forecastChart').waitFor({ state: 'visible' });

  const desktopOverflow = await page.evaluate(() =>
    document.documentElement.scrollWidth > document.documentElement.clientWidth
  );
  assert.equal(desktopOverflow, false, 'Desktop layout has horizontal overflow');
  await page.screenshot({ path: 'artifacts/xtrato-desktop.png', fullPage: true });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(250);
  const mobileOverflow = await page.evaluate(() =>
    document.documentElement.scrollWidth > document.documentElement.clientWidth
  );
  assert.equal(mobileOverflow, false, 'Mobile layout has horizontal overflow');
  await page.screenshot({ path: 'artifacts/xtrato-mobile.png', fullPage: true });

  assert.deepEqual(pageErrors, [], `Browser runtime errors: ${pageErrors.join('; ')}`);
  console.log('Browser smoke test passed: login, dashboard, forecast, desktop and mobile layouts.');
} finally {
  await browser.close();
}
