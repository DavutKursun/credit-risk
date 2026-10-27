"""Record docs/img/demo.gif against the live Space (or a local server): the clear-decline sample → Score → reasons → move the income
slider → Policy tab → Monitoring tab. Screenshots are assembled with Pillow; ≤ 30 s, ≤ 3 MB.

Usage: python scripts/demo_gif.py [--base https://davutkursun-credit-risk.hf.space] [--out docs/img/demo.gif] [--width 1100] [--height 760]
Needs: pip install playwright pillow && python -m playwright install chromium
"""

from __future__ import annotations

import argparse
import io
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 3 * 1024 * 1024
SET_RANGE = "(e, v) => { e.value = v; e.dispatchEvent(new Event('input', {bubbles: true})); e.dispatchEvent(new Event('change', {bubbles: true})); }"


def record(base: str, width: int, height: int) -> list[tuple[Image.Image, int]]:
    from playwright.sync_api import sync_playwright

    frames: list[tuple[Image.Image, int]] = []

    def shot(page, hold_ms: int) -> None:
        frames.append((Image.open(io.BytesIO(page.screenshot(full_page=False))).convert("RGB"), hold_ms))

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(base.rstrip("/") + "/ui/", wait_until="networkidle", timeout=120_000)
        page.wait_for_selector("text=Score with both models", timeout=60_000)
        time.sleep(1.0)
        shot(page, 1800)
        page.get_by_label("Prefill from a sample application").click()
        page.get_by_role("option", name="clear_decline").click()
        time.sleep(1.5)
        shot(page, 1500)
        page.get_by_role("button", name="Score with both models").click()
        page.wait_for_selector("text=DECLINE", timeout=60_000)
        time.sleep(1.0)
        shot(page, 2600)
        page.mouse.wheel(0, 900)
        time.sleep(0.8)
        shot(page, 2600)  # the reasons and the notice
        page.mouse.wheel(0, -900)
        time.sleep(0.5)
        slider = page.locator("input[type=range]").first  # annual income
        for v in (60_000, 90_000, 140_000):
            slider.evaluate(SET_RANGE, v)
            time.sleep(1.6)
            shot(page, 1500)
        page.mouse.wheel(0, 900)
        time.sleep(0.8)
        shot(page, 2200)
        page.get_by_role("tab", name="Policy").click()
        time.sleep(2.0)
        shot(page, 2600)
        page.mouse.wheel(0, 700)
        time.sleep(0.8)
        shot(page, 2200)
        page.get_by_role("tab", name="Monitoring").click()
        time.sleep(2.0)
        shot(page, 2600)
        page.mouse.wheel(0, 700)
        time.sleep(0.8)
        shot(page, 2400)
        browser.close()
    return frames


def write_gif(frames: list[tuple[Image.Image, int]], out: Path) -> int:
    scale = 1.0
    while True:
        imgs = [f.resize((int(f.width * scale), int(f.height * scale)), Image.LANCZOS).quantize(colors=128, method=Image.MEDIANCUT) for f, _ in frames]
        buf = io.BytesIO()
        imgs[0].save(buf, format="GIF", save_all=True, append_images=imgs[1:], duration=[h for _, h in frames], loop=0, optimize=True)
        if buf.tell() <= MAX_BYTES or scale < 0.5:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(buf.getvalue())
            return buf.tell()
        scale *= 0.85


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://davutkursun-credit-risk.hf.space")
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "img" / "demo.gif")
    ap.add_argument("--width", type=int, default=1100)
    ap.add_argument("--height", type=int, default=760)
    a = ap.parse_args(argv)
    frames = record(a.base, a.width, a.height)
    total_ms = sum(h for _, h in frames)
    size = write_gif(frames, a.out)
    print(f"{a.out}: {len(frames)} frames, {total_ms / 1000:.1f} s, {size / 1024:.0f} KB")
    return 0 if total_ms <= 30_000 and size <= MAX_BYTES else 1


if __name__ == "__main__":
    raise SystemExit(main())
