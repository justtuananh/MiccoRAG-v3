const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();

    const TARGET_URL = 'https://propose-montana-refuse-rubber.trycloudflare.com';

    try {
        // 1. Login directly
        console.log('1. Logging in...');
        await page.goto(`${TARGET_URL}/login`, { timeout: 30000, waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        // Check if page loaded
        const title = await page.title();
        console.log('   Page title:', title);

        const loginForm = await page.locator('form').first();
        if (await loginForm.count() > 0) {
            await page.fill('input[type="email"]', 'admin@micco.vn');
            await page.fill('input[type="password"]', 'admin123');
            await page.click('button[type="submit"]');
            await page.waitForTimeout(3000);
            console.log('✅ Login form submitted');
        } else {
            console.log('❌ No login form found');
            await page.screenshot({ path: '/tmp/login-page.png' });
        }

        // Check current URL
        console.log('   Current URL:', page.url());

        // 2. Go to Admin
        if (page.url().includes('dashboard') || page.url().includes('login')) {
            console.log('2. Navigating to /admin...');
            await page.goto(`${TARGET_URL}/admin`, { waitUntil: 'domcontentloaded' });
            await page.waitForTimeout(2000);
            console.log('   Admin URL:', page.url());

            // 3. Try to add user
            const addBtn = page.locator('button:has-text("Thêm người dùng")');
            if (await addBtn.count() > 0) {
                console.log('3. Found Add User button, clicking...');
                await addBtn.click();
                await page.waitForTimeout(1000);

                // Fill form
                const nameInput = page.locator('input[placeholder="Nguyễn Văn A"]');
                if (await nameInput.count() > 0) {
                    await nameInput.fill('API Test User');
                    await page.fill('input[type="email"]', `apitest${Date.now()}@micco.vn`);

                    // Select department
                    const deptSelect = page.locator('select').last();
                    const options = await deptSelect.locator('option').count();
                    console.log('   Department options:', options);

                    if (options > 1) {
                        await deptSelect.selectOption({ index: 1 });
                    }

                    // Submit
                    console.log('4. Submitting...');
                    await page.locator('button[type="submit"]').click();
                    await page.waitForTimeout(3000);

                    // Check for success/failure
                    const url = page.url();
                    console.log('   Final URL:', url);
                    console.log('✅ Form submitted');
                } else {
                    console.log('❌ Name input not found');
                }
            } else {
                console.log('❌ Add User button not found');
                await page.screenshot({ path: '/tmp/admin-page.png' });
            }
        }

    } catch (error) {
        console.error('❌ Error:', error.message);
        await page.screenshot({ path: '/tmp/error-page.png' }).catch(() => {});
    } finally {
        await browser.close();
    }
})();
