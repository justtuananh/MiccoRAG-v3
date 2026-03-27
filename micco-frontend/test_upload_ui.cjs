const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();

    page.on('console', msg => console.log('BROWSER_LOG:', msg.text()));
    page.on('pageerror', error => console.log('BROWSER_ERROR:', error));
    page.on('response', response => {
        if (response.url().includes('/upload/')) {
            console.log('UPLOAD_RESPONSE:', response.status(), response.url());
        }
    });

    console.log('Navigating to local react app...');
    // Clear storage just in case + bypass auth
    await page.goto('http://localhost:5173');
    await page.evaluate(() => {
        localStorage.setItem('auth_token', 'fake-admin-token-for-skip-auth');
        localStorage.setItem('user_info', JSON.stringify({ role: 'admin' }));
    });
    
    await page.goto('http://localhost:5173/documents');
    await page.waitForSelector('text=Tải lên');

    console.log('Clicking Tải lên button to open modal...');
    await page.click('button:has-text("Tải lên")');

    // Wait for the modal and input field
    const fileInputSelector = 'input[type="file"]';
    await page.waitForSelector(fileInputSelector, { state: 'attached' });

    console.log('Setting file path...');
    const filePath = 'C:\\Users\\tuana\\Downloads\\01_Kien_Truc_Transformer.docx';
    if (!fs.existsSync(filePath)) {
        console.error('File not found:', filePath);
        await browser.close();
        process.exit(1);
    }

    await page.setInputFiles(fileInputSelector, filePath);

    console.log('Waiting for staged file to appear...');
    await page.waitForTimeout(500); // let react state update

    console.log('Clicking Submit in modal...');
    // There are 2 "Tải lên" buttons now (one to open modal, one to submit)
    // The submit button has the Upload icon and text "Tải lên 1 tệp" or similar.
    // It's the primary button in the modal footer.
    const submitBtn = page.locator('button.bg-primary-600.text-white:not(:disabled)');
    // we want the one inside the modal.
    await page.locator('.fixed.z-50 button.bg-primary-600').click();

    console.log('Waiting for upload to finish...');
    // Wait for either the success screen or error screen
    try {
        await page.waitForSelector('text=Tải lên thành công!', { timeout: 10000 });
        console.log('SUCCESS text found in UI.');
    } catch (e) {
        console.log('SUCCESS text NOT found. Checking for errors...');
        const errorText = await page.locator('.text-red-700, .text-red-400').innerText().catch(() => null);
        if (errorText) console.log('UI ERROR SHOWN:', errorText);
    }

    await page.waitForTimeout(2000);
    await browser.close();
})();
