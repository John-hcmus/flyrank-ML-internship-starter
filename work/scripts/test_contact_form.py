"""End-to-end test for the portfolio contact form.

Outbound network is blocked in this environment, so the real Web3Forms endpoint
is replaced by a local mock that speaks the same JSON protocol. Everything else
under test is the real shipped file: the same HTML, the same CSS, the same
JavaScript, driven by a real Chromium through Playwright.

Only two values are swapped, and they are exactly the two values a deploy swaps:
  * the access key placeholder -> a fake key
  * the form action            -> the local mock URL

Run:  python3 work/scripts/test_contact_form.py
"""

import json
import pathlib
import re
import shutil
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs" / "portfolio" / "index.html"
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"
FAKE_KEY = "11111111-2222-3333-4444-555555555555"
CHROMIUM = "/opt/pw-browsers/chromium"

received = []          # every POST the mock backend accepted
failures = []          # assertion failures, collected so all tests run


def check(name, condition, detail=""):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}" + (f"\n        {detail}" if detail else ""))
        failures.append(name)


class Handler(SimpleHTTPRequestHandler):
    """Static files + a stand-in for POST https://api.web3forms.com/submit."""

    def log_message(self, *args):
        pass

    def _json(self, code, body):
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        if self.path not in ("/submit", "/submit-badkey"):
            return self._json(404, {"success": False, "message": "no such endpoint"})

        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")

        # Mirror the real API's failure mode for a rejected key.
        if self.path == "/submit-badkey":
            return self._json(401, {"success": False, "message": "Invalid access key"})

        # Mirror the real API's silent-drop behaviour for a tripped honeypot.
        if payload.get("botcheck"):
            return self._json(200, {"success": False, "message": "Bot detected"})

        received.append(payload)
        return self._json(200, {"success": True, "message": "Email sent successfully!"})


def build_serve_dir(tmp):
    html = SOURCE.read_text(encoding="utf-8")

    # Rewrite ONLY the hidden input's value, whatever it currently holds, so these
    # tests behave the same before and after the real key is pasted in -- and so the
    # real key is never sent anywhere during a test run. The identical placeholder
    # string also appears as the PLACEHOLDER constant in the page's JavaScript, and
    # that one must stay exactly as it is.
    key_input = re.compile(r'(<input type="hidden" name="access_key" value=")[^"]*(")')

    configured, n = key_input.subn(rf'\g<1>{FAKE_KEY}\g<2>', html)
    assert n == 1, f"expected exactly one access_key input, found {n}"
    assert "PLACEHOLDER = 'PASTE_YOUR_WEB3FORMS_ACCESS_KEY_HERE'" in configured, \
        "the JS placeholder constant must survive the swap"
    assert FAKE_KEY in configured and "88690ebb" not in configured, \
        "the real access key must never reach the test server"

    swapped = configured.replace(
        'action="https://api.web3forms.com/submit"', 'action="/submit"'
    )
    assert swapped != configured, "form action not found in the page"

    (tmp / "index.html").write_text(swapped, encoding="utf-8")
    (tmp / "badkey.html").write_text(
        configured.replace(
            'action="https://api.web3forms.com/submit"', 'action="/submit-badkey"'
        ),
        encoding="utf-8",
    )
    # Unconfigured variant: force the key back to the placeholder, so the
    # "not connected yet" path stays covered once the real key is in the page.
    unconfigured, n = key_input.subn(
        r"\g<1>PASTE_YOUR_WEB3FORMS_ACCESS_KEY_HERE\g<2>", html
    )
    assert n == 1
    (tmp / "pristine.html").write_text(unconfigured, encoding="utf-8")


def fill(page, name, email, message):
    page.fill("#cf-name", name)
    page.fill("#cf-email", email)
    page.fill("#cf-message", message)


def main():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="cf-test-"))
    build_serve_dir(tmp)

    handler = lambda *a, **k: Handler(*a, directory=str(tmp), **k)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                executable_path=CHROMIUM,
                args=["--no-sandbox", "--disable-background-networking",
                      "--disable-component-update", "--no-first-run"],
            )
            page = browser.new_page()
            console_errors = []
            page.on("pageerror", lambda e: console_errors.append(str(e)))

            # ---- 1. page renders, form is present, no setup banner once configured
            print("\n[1] Page loads with a configured key")
            page.goto(f"{BASE}/index.html")
            check("contact form is on the page", page.locator("#cf-form").is_visible())
            check("setup warning hidden when key is set",
                  page.locator("#cf-setup").is_hidden())
            hp = page.evaluate(
                "() => { const el = document.querySelector('input[name=botcheck]');"
                "  const r = el.getBoundingClientRect();"
                "  return { left: r.left, opacity: getComputedStyle(el).opacity,"
                "           tabindex: el.getAttribute('tabindex') }; }"
            )
            check("honeypot is parked off-screen", hp["left"] < 0, str(hp))
            check("honeypot is transparent", hp["opacity"] == "0", str(hp))
            check("honeypot is not tabbable", hp["tabindex"] == "-1", str(hp))

            # ---- 2. empty submit is blocked client-side
            print("\n[2] Empty submit is rejected before any network call")
            before = len(received)
            page.click("#cf-submit")
            page.wait_for_timeout(300)
            check("name error shown", page.locator("#cf-name-err").is_visible())
            check("email error shown", page.locator("#cf-email-err").is_visible())
            check("message error shown", page.locator("#cf-message-err").is_visible())
            check("nothing was sent", len(received) == before)

            # ---- 3. field-level validation
            print("\n[3] Field-level validation")
            page.reload()
            fill(page, "Tu Nguyen", "not-an-email", "This is a long enough message.")
            page.click("#cf-submit")
            page.wait_for_timeout(300)
            check("bad email is caught", page.locator("#cf-email-err").is_visible())
            check("valid name passes", page.locator("#cf-name-err").is_hidden())

            page.fill("#cf-email", "tu@example.com")
            page.fill("#cf-message", "too short")
            page.click("#cf-submit")
            page.wait_for_timeout(300)
            check("short message is caught", page.locator("#cf-message-err").is_visible())
            check("email error cleared once fixed", page.locator("#cf-email-err").is_hidden())

            # ---- 4. the happy path
            print("\n[4] A real submission reaches the backend")
            page.reload()
            before = len(received)
            fill(page, "Alex Recruiter", "alex@example.com",
                 "Saw your volatility Transformer write-up. Are you open to an internship chat?")
            page.click("#cf-submit")
            page.wait_for_selector("#cf-status.is-ok", timeout=8000)

            check("backend received exactly one new submission", len(received) == before + 1)
            got = received[-1] if received else {}
            check("name arrived intact", got.get("name") == "Alex Recruiter", repr(got.get("name")))
            check("email arrived intact", got.get("email") == "alex@example.com", repr(got.get("email")))
            check("message arrived intact",
                  "volatility Transformer" in (got.get("message") or ""), repr(got.get("message")))
            check("access key was sent", got.get("access_key") == FAKE_KEY)
            check("subject line was sent", bool(got.get("subject")))
            check("honeypot was NOT sent for a human", "botcheck" not in got)
            check("success message shown to the visitor",
                  "on its way" in page.locator("#cf-status").inner_text())
            check("form cleared after success", page.input_value("#cf-name") == "")
            check("button re-enabled", page.locator("#cf-submit").is_enabled())
            check("button label restored",
                  page.locator("#cf-submit").inner_text().strip() == "Send message")

            # ---- 5. honeypot
            print("\n[5] A bot that fills the honeypot is rejected")
            page.reload()
            before = len(received)
            fill(page, "Spam Bot", "bot@example.com", "Cheap backlinks for your site, click here.")
            page.evaluate("document.querySelector('input[name=botcheck]').checked = true")
            page.click("#cf-submit")
            page.wait_for_selector("#cf-status.is-err", timeout=8000)
            check("bot submission not delivered", len(received) == before)

            # ---- 6. backend rejects the key
            print("\n[6] Backend error is surfaced, not swallowed")
            page.goto(f"{BASE}/badkey.html")
            fill(page, "Tu Nguyen", "tu@example.com", "Testing the failure path end to end.")
            page.click("#cf-submit")
            page.wait_for_selector("#cf-status.is-err", timeout=8000)
            text = page.locator("#cf-status").inner_text()
            check("real reason from the server is shown", "Invalid access key" in text, text)
            check("button usable again after an error", page.locator("#cf-submit").is_enabled())

            # ---- 7. network is down
            print("\n[7] Network failure degrades gracefully")
            page.goto(f"{BASE}/index.html")
            page.route("**/submit", lambda route: route.abort())
            fill(page, "Tu Nguyen", "tu@example.com", "Testing the offline path end to end.")
            page.click("#cf-submit")
            page.wait_for_selector("#cf-status.is-err", timeout=8000)
            check("offline message shown",
                  "Could not reach" in page.locator("#cf-status").inner_text())
            page.unroute("**/submit")

            # ---- 8. unconfigured page warns instead of pretending
            print("\n[8] Unconfigured key warns loudly")
            page.goto(f"{BASE}/pristine.html")
            check("setup banner visible", page.locator("#cf-setup").is_visible())
            before = len(received)
            fill(page, "Tu Nguyen", "tu@example.com", "This should not be delivered anywhere.")
            page.click("#cf-submit")
            page.wait_for_selector("#cf-status.is-err", timeout=8000)
            check("not-connected message shown",
                  "not connected" in page.locator("#cf-status").inner_text())
            check("nothing delivered while unconfigured", len(received) == before)

            # ---- 9. no stray JS errors anywhere in the run
            print("\n[9] No JavaScript errors during the whole run")
            check("clean console", not console_errors, "; ".join(console_errors))

            browser.close()
    finally:
        server.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + "=" * 60)
    if failures:
        print(f"{len(failures)} CHECK(S) FAILED: " + ", ".join(failures))
        raise SystemExit(1)
    print("ALL CHECKS PASSED")
    print(f"{len(received)} message(s) delivered to the mock backend:")
    for r in received:
        print(f"  - {r['name']} <{r['email']}>: {r['message'][:60]}...")


if __name__ == "__main__":
    main()
