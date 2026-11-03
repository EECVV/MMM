"""Fetch a TXT channel list and atomically publish an extended M3U playlist."""
import os
from pathlib import Path
import sys
import time
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

MAX_BYTES = 10 * 1024 * 1024
SCHEMES = {"http", "https", "rtsp", "rtmp", "rtmps", "udp", "rtp"}


def is_html(text):
    return text.lstrip().lower().startswith(("<!doctype html", "<html", "<script"))


def decode_source(data):
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise ValueError("Unsupported text encoding")


def convert(text):
    if is_html(text):
        raise ValueError("Source returned an HTML page instead of a channel list")
    if text.lstrip().startswith("#EXTM3U"):
        raise ValueError("Source is already M3U; this converter expects TXT")
    result = ["#EXTM3U"]
    group = ""
    count = 0
    skipped = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, separator, address = line.partition(",")
        name, address = name.strip(), address.strip()
        if not separator:
            skipped += 1
            continue
        if address.casefold() == "#genre#":
            group = name
            continue
        try:
            valid = urlsplit(address).scheme.lower() in SCHEMES
        except ValueError:
            valid = False
        if not name or not valid:
            skipped += 1
            continue
        # Quotes inside a group name would break the M3U attribute syntax.
        safe_group = group.replace('"', "'")
        attribute = f' group-title="{safe_group}"' if group else ""
        result.extend((f"#EXTINF:-1{attribute},{name}", address))
        count += 1
    if not count:
        raise ValueError("No valid channels found; existing output is preserved")
    return "\n".join(result) + "\n", count, skipped


def fetch_http(url):
    if urlsplit(url).scheme.lower() not in {"http", "https"}:
        raise ValueError("TXT_URL must be an HTTP or HTTPS URL")
    for attempt in range(3):
        try:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0 TXT-to-M3U"})
            with urlopen(request, timeout=45) as response:
                data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ValueError("Source exceeds 10 MiB")
            return decode_source(data)
        except Exception:
            if attempt == 2:
                # Do not include a potentially private subscription URL in logs.
                raise RuntimeError("Unable to fetch/decode TXT source after 3 attempts") from None
            time.sleep(2 * (attempt + 1))


def fetch_browser(url):
    """Read the rendered text through an ordinary, isolated Chromium session.

    No stored cookies, stealth flags, fingerprint changes, or CAPTCHA solving.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                try:
                    # Browser text viewers normally put a text/plain file in PRE.
                    viewer = page.locator("pre")
                    if viewer.count() == 1:
                        text = viewer.inner_text(timeout=2000)
                        if len(text.encode("utf-8")) > MAX_BYTES:
                            raise ValueError("Rendered source exceeds 10 MiB")
                        convert(text)
                        return text
                    body = page.locator("body").inner_text(timeout=2000).lower()
                    if any(marker in body for marker in (
                        "verify you are human", "complete the captcha", "access denied"
                    )):
                        raise RuntimeError("Browser access requires manual verification or was denied")
                except ValueError:
                    raise
                except RuntimeError:
                    raise
                except Exception:
                    # An automatic page navigation can replace the document.
                    pass
                page.wait_for_timeout(500)
            raise RuntimeError("Browser did not return a valid plain-text playlist")
        finally:
            browser.close()


def fetch(url):
    if urlsplit(url).scheme.lower() not in {"http", "https"}:
        raise ValueError("TXT_URL must be an HTTP or HTTPS URL")
    try:
        text = fetch_http(url)
    except Exception:
        print("HTTP fetch failed; trying normal browser loading")
    else:
        if not is_html(text):
            return text
        print("HTTP returned HTML; trying normal browser loading")
    try:
        return fetch_browser(url)
    except Exception:
        raise RuntimeError(
            "Browser loading failed or access was restricted; existing output is preserved. "
            "Check that Playwright/Chromium are installed, or use an accessible TXT mirror."
        ) from None


def main():
    source = os.environ.get("TXT_URL", "").strip()
    if not source:
        raise ValueError("Set repository Actions secret TXT_URL first")
    output, count, skipped = convert(fetch(source))
    destination = Path("live.m3u")
    temporary = destination.with_suffix(".m3u.tmp")
    temporary.write_text(output, encoding="utf-8")
    temporary.replace(destination)
    print(f"Generated {count} channels; skipped {skipped} unrecognized lines")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Conversion failed: {exc}", file=sys.stderr)
        sys.exit(1)
