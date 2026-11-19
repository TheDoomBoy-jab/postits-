from playwright.sync_api import sync_playwright

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto("http://127.0.0.1:8000/demo/apply")

    page.get_by_label("Full name").fill("Demo Applicant")
    page.get_by_label("Email", exact=True).fill("demo@example.com")
    page.get_by_label("Phone number").fill("9876543210")
    page.get_by_label("GitHub URL (optional)").fill("https://github.com/octocat")

    print("Name read back from the form:", page.get_by_label("Full name").input_value())

    input("Press Enter to close the browser...")
    browser.close()