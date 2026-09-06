# -*- coding: utf-8 -*-
"""Генерация фоновой иллюстрации «Магическая помощь» через веб-Gemini (nano-banana).
Копия эталона _gem_images.py, изменён только блок данных (IMG_DIR / IMAGES)."""
import asyncio
import base64
import io
import os
import random
import re
import sys

SK = r"C:\Users\cenic\.config\opencode\skills\notebooklm\scripts"
sys.path.insert(0, SK)
from config import BROWSER_PROFILE_DIR  # noqa: E402
from browser_utils import USER_AGENT, BROWSER_ARGS  # noqa: E402
from patchright.async_api import async_playwright  # noqa: E402

IMG_DIR = r"D:\13\images"
os.makedirs(IMG_DIR, exist_ok=True)

IMAGES = [
    (
        "bg_magic.jpg",
        "An old sage in a hooded robe with a crooked staff stands by a lake in the middle "
        "of a forest; his right hand rests on a white wolf; the moon is reflected in the "
        "lake water; soft pale moonlight, light mist, calm mystical atmosphere, faded pale "
        "colors, suitable as a website background, no text, no watermark.",
    ),
]

TMP = r"C:\Users\cenic\AppData\Local\Temp\opencode"
LOG = os.path.join(TMP, "_gem_img_log.txt")
ONLY = set(sys.argv[1:]) if len(sys.argv) > 1 else None
DONE_MARK = os.path.join(TMP, "_gem_done.txt")

log_f = io.open(LOG, "a", encoding="utf-8")


def log(msg):
    print(msg)
    log_f.write(msg + "\n")
    log_f.flush()


async def dismiss_popups(page):
    for sel in ['button[aria-label*="Dismiss"]', 'button[aria-label*="Закрыть"]',
                'button[aria-label="Close"]', '.dismiss-button']:
        try:
            b = page.locator(sel).first
            if await b.count() and await b.is_visible():
                await b.click(timeout=2000)
        except Exception:
            pass


async def send_prompt(page, text):
    ta = page.locator('rich-textarea div[contenteditable="true"]').first
    await ta.wait_for(state="visible", timeout=30000)
    await ta.click()
    await page.keyboard.insert_text(text)
    await asyncio.sleep(1.0)
    # Enter может отправить; надёжнее кнопка
    btn = page.locator('button.send-button:not([disabled]), button[aria-label*="Send"]:not([disabled])').first
    try:
        if await btn.count() and await btn.is_enabled():
            await btn.click()
        else:
            await page.keyboard.press("Enter")
    except Exception:
        await page.keyboard.press("Enter")


async def wait_image(page, before_count, timeout_s=180):
    """Ждём новую сгенерированную картинку в чате."""
    deadline = asyncio.get_event_loop().time() + timeout_s
    while asyncio.get_event_loop().time() < deadline:
        imgs = page.locator("model-response img[srcset], model-response img.gserv-image, message-content img")
        n = await imgs.count()
        if n > before_count:
            # дождаться полной загрузки последней
            last = imgs.nth(n - 1)
            try:
                await last.wait_for(state="visible", timeout=15000)
                src = await last.get_attribute("src")
                if src and not src.startswith("data:image/svg"):
                    return last
            except Exception:
                pass
        await asyncio.sleep(2)
    return None


async def download_via_button(page, img_el, out_path):
    """Кнопка Download под картинкой -> expect_download."""
    box = await img_el.bounding_box()
    if box:
        await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    await asyncio.sleep(1.2)
    card = img_el.locator("xpath=ancestor::image-card|ancestor::div[contains(@class,'image-container')]").first
    scope = card if await card.count() else img_el.locator("xpath=..")
    dbtn = scope.locator('button:has([aria-label*="Download"]), button[aria-label*="Download"], button[aria-label*="Скачать"]').first
    if not await dbtn.count():
        dbtn = page.locator('button[aria-label*="Download"], button[aria-label*="Скачать"]').last
    async with page.expect_download(timeout=30000) as dl_info:
        await dbtn.click()
    dl = await dl_info.value
    await dl.save_as(out_path)


async def fetch_b64(page, url):
    js = """
    async (u) => {
        const r = await fetch(u);
        const b = await r.blob();
        return await new Promise((res) => {
            const fr = new FileReader();
            fr.onload = () => res(fr.result.split(',')[1]);
            fr.readAsDataURL(b);
        });
    }
    """
    return await page.evaluate(js, url)


async def main():
    pw = await async_playwright().start()
    ctx = await pw.chromium.launch_persistent_context(
        user_data_dir=str(BROWSER_PROFILE_DIR),
        headless=True,
        viewport={"width": 1680, "height": 950},
        user_agent=USER_AGENT,
        args=BROWSER_ARGS,
        timeout=90000,
    )
    page = ctx.pages[0] if ctx.pages else await ctx.new_page()
    page.set_default_timeout(45000)
    ok = fail = skip = 0
    try:
        await page.goto("https://gemini.google.com/app", wait_until="domcontentloaded")
        await asyncio.sleep(8)
        await dismiss_popups(page)
        # проверка логина
        body = await page.content()
        if re.search(r"Sign in|Войти", body[:60000]) and 'accounts.google.com' in page.url:
            log("FAIL: Google не залогинен")
            return
        log("Gemini открыт: " + page.url)

        for i, (fname, prompt) in enumerate(IMAGES, 1):
            out = os.path.join(IMG_DIR, fname)
            if ONLY and fname not in ONLY:
                continue
            if os.path.exists(DONE_MARK) and fname in io.open(DONE_MARK, encoding="utf-8").read().split():
                skip += 1
                log("[%d/%d] skip %s" % (i, len(IMAGES), fname))
                continue
            full = ("Generate an image: " + prompt +
                    " Soft-glow fantasy illustration, faded pale colors, no text or watermarks.")
            before = await page.locator("model-response img, message-content img").count()
            try:
                await send_prompt(page, full)
                img = await wait_image(page, before)
                if not img:
                    raise RuntimeError("картинка не появилась (возможно отказ)")
                tmp_png = out.replace(".jpg", ".png")
                got = False
                try:
                    await download_via_button(page, img, tmp_png)
                    got = os.path.exists(tmp_png)
                except Exception as e:
                    log("  кнопка Download fail (%s), пробую blob-fetch" % str(e)[:60])
                    src = await img.get_attribute("src")
                    if src and src.startswith("http"):
                        b64 = await fetch_b64(page, src)
                        if b64 and len(b64) > 50000:
                            io.open(tmp_png, "wb").write(base64.b64decode(b64))
                            got = True
                if not got:
                    raise RuntimeError("скачивание не удалось")
                from PIL import Image
                im = Image.open(tmp_png).convert("RGB")
                im.save(out, "JPEG", quality=90)
                os.remove(tmp_png)
                kb = os.path.getsize(out) // 1024
                ok += 1
                log("[%d/%d] OK %s (%d KB)" % (i, len(IMAGES), fname, kb))
                with io.open(DONE_MARK, "a", encoding="utf-8") as dm:
                    dm.write(fname + "\n")
            except Exception as e:
                fail += 1
                log("[%d/%d] FAIL %s: %s" % (i, len(IMAGES), fname, str(e)[:140]))
            await asyncio.sleep(random.uniform(6, 10))
    finally:
        await ctx.close()
        await pw.stop()
    log("ИТОГ: ok=%d fail=%d skip=%d" % (ok, fail, skip))


if __name__ == "__main__":
    asyncio.run(main())