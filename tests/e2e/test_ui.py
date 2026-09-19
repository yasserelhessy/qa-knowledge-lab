import os
import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e
BASE = os.getenv("BASE_URL", "http://127.0.0.1:8000")

def test_answer_and_evidence(page):
    page.goto(BASE)
    expect(page.get_by_text("● Offline demo")).to_be_visible()
    page.get_by_role("button", name="Release gates").click()
    page.get_by_role("button", name="Find an answer").click()
    expect(page.locator("#answer")).to_contain_text("Playwright smoke tests")
    page.get_by_text("Evidence · Release gates").click()
    expect(page.locator("details p")).to_contain_text("golden dataset")


def test_unknown_has_no_citation(page):
    page.goto(BASE)
    page.get_by_role("button", name="Try an unknown").click()
    page.get_by_role("button", name="Find an answer").click()
    expect(page.locator("#status")).to_have_text("Not in the playbook")
    expect(page.locator("#sources details")).to_have_count(0)


def test_error_recovery(page):
    page.goto(BASE)
    page.route("**/api/ask", lambda route: route.fulfill(status=502, body="{}"))
    page.get_by_label("Your question").fill("release gates")
    page.get_by_role("button", name="Find an answer").click()
    expect(page.get_by_role("alert")).to_contain_text("unavailable")
    expect(page.get_by_role("button", name="Find an answer")).to_be_enabled()
    page.unroute("**/api/ask")
    page.get_by_role("button", name="Find an answer").click()
    expect(page.locator("#answer")).to_contain_text("Playwright")
    expect(page.get_by_role("alert")).to_be_hidden()


def test_mobile_and_untrusted_text(page):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(BASE)
    page.route("**/api/ask", lambda route: route.fulfill(json={
        "answer": "<img src=x onerror=alert(1)>", "status": "answered", "sources": []}))
    page.get_by_label("Your question").fill("release gates")
    page.get_by_role("button", name="Find an answer").click()
    expect(page.locator("#answer")).to_have_text("<img src=x onerror=alert(1)>")
    expect(page.locator("#answer img")).to_have_count(0)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
