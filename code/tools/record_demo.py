"""
End-to-end UI test that also records the screen-capture part of the demo video.
Requires the app running:  PORT=5055 python app/server.py
Usage: python tools/record_demo.py --out media/raw_demo   (writes a .webm + screenshots)
Every click here is a real interaction with the real app - nothing is mocked.
"""
import argparse
import asyncio
import json
import os
import time

from playwright.async_api import async_playwright

CURSOR_JS = """
(() => { if (window.__cur) return; const c = document.createElement('div'); window.__cur = c;
 c.style.cssText='position:fixed;z-index:99999;width:26px;height:26px;border-radius:50%;background:rgba(244,185,66,.55);border:3px solid #1f2a44;pointer-events:none;transform:translate(-50%,-50%);transition:left .45s ease,top .45s ease,width .15s,height .15s;left:-50px;top:-50px';
 document.body.appendChild(c);
 window.__move=(x,y)=>{c.style.left=x+'px';c.style.top=y+'px'};
 window.__press=()=>{c.style.width='16px';c.style.height='16px';setTimeout(()=>{c.style.width='26px';c.style.height='26px'},180)};
})();
"""


SLOW = 1.7  # slower pacing so viewers can follow


async def run(base, out, headless=True):
    os.makedirs(out, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", headless=headless)
        ctx = await b.new_context(viewport={"width": 1440, "height": 900}, record_video_dir=out,
                                  record_video_size={"width": 1440, "height": 900}, device_scale_factor=1)
        pg = await ctx.new_page()
        t0 = time.time(); marks = []
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        shots = 0

        async def shot(name):
            nonlocal shots
            shots += 1
            marks.append({"shot": name, "t": round(time.time() - t0, 2)})
            await pg.screenshot(path=os.path.join(out, f"{shots:02d}_{name}.png"))

        async def cursor():
            await pg.evaluate(CURSOR_JS)

        async def click(sel, pause=700):
            await cursor()
            box = await pg.locator(sel).first.bounding_box()
            x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            await pg.evaluate(f"window.__move({x},{y})")
            await pg.wait_for_timeout(550)
            await pg.evaluate("window.__press()")
            await pg.locator(sel).first.click()
            await pg.wait_for_timeout(int(pause * SLOW))

        async def canvas_xy(px, py):
            r = await pg.locator("#cv").bounding_box()
            w = await pg.evaluate("S.w"); h = await pg.evaluate("S.h")
            return r["x"] + px * r["width"] / w, r["y"] + py * r["height"] / h

        async def canvas_click(px, py, pause=700):
            await cursor()
            x, y = await canvas_xy(px, py)
            await pg.evaluate(f"window.__move({x},{y})"); await pg.wait_for_timeout(550)
            await pg.evaluate("window.__press()"); await pg.mouse.click(x, y); await pg.wait_for_timeout(int(pause * SLOW))

        async def canvas_drag(b):
            x0, y0 = await canvas_xy(b[0], b[1]); x1, y1 = await canvas_xy(b[2], b[3])
            await pg.evaluate(f"window.__move({x0},{y0})"); await pg.wait_for_timeout(600)
            await pg.mouse.move(x0, y0); await pg.mouse.down()
            for k in range(1, 16):
                xx, yy = x0 + (x1 - x0) * k / 15, y0 + (y1 - y0) * k / 15
                await pg.mouse.move(xx, yy); await pg.evaluate(f"window.__move({xx},{yy})"); await pg.wait_for_timeout(35)
            await pg.mouse.up(); await pg.wait_for_timeout(1500)

        await pg.goto(base)
        await cursor()
        await pg.wait_for_timeout(3000); await shot("start")
        await click("summary:has-text('Try a sample')", 900)
        await click("img[data-f='demo_glare_board.jpg']", 400)
        await pg.wait_for_selector("#work:not(.hidden)"); await cursor()
        await pg.wait_for_timeout(5000); await shot("ai_result")
        # 1) inspect the uncertain (red dashed) box: it is badly placed -> redraw it
        await canvas_click(1146, 228, 1600); await shot("low_conf_card")
        await click("#kRedraw", 500)
        await canvas_drag([1086, 106, 1194, 292]); await shot("redrawn")
        # 2) keep the green boxes
        await click("#acceptHighBtn", 1200)
        # 3) add the two switches the AI missed (washed out by flash glare)
        await click("#addBtn", 300); await canvas_drag([658, 108, 766, 292])
        await click("#addBtn", 300); await canvas_drag([800, 107, 906, 292]); await shot("added_missed")
        await pg.wait_for_timeout(800)
        await click("#toAssignBtn", 1200); await shot("assign_start")
        plan = [("light", "Tube light"), ("fan", "Ceiling fan"), ("light", "Bed lamp"), ("socket", "Charger point"),
                ("other", "Geyser"), ("light", "Bathroom light"), ("unused", "")]
        for k, (fn, name) in enumerate(plan):
            await pg.wait_for_selector("#card:not(.hidden)")
            if name:
                await pg.locator("#kName").fill(name)
            await click(f".funcs button[data-f='{fn}']", 500)
            if fn != "unused":
                await click("#kVer", 700)
            else:
                # move to next manually
                await pg.evaluate("next()")
            if k == 1:
                await shot("assign_mid")
        await pg.wait_for_timeout(900); await shot("ready_confirm")
        await click("#confirmBtn", 1800); await shot("confirmed")
        # guide (English) in the same tab so it is captured in the video
        href = await pg.get_attribute("#guideEn", "href")
        await pg.goto(base.rstrip("/") + href); await pg.wait_for_timeout(3500); await shot("guide_en")
        for y in (500, 1000, 1500, 2200):
            await pg.evaluate(f"window.scrollTo({{top:{y},behavior:'smooth'}})"); await pg.wait_for_timeout(2300)
        await shot("guide_legend")
        await pg.goto(base.rstrip("/") + href.replace("lang=en", "lang=hi")); await pg.wait_for_timeout(4000); await shot("guide_hi")
        marks.append({"shot": "end", "t": round(time.time() - t0, 2)})
        json.dump(marks, open(os.path.join(out, "marks.json"), "w"), indent=1)
        await ctx.close(); await b.close()
        print("errors:", errors)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:5055/")
    ap.add_argument("--out", default="media/raw_demo")
    a = ap.parse_args()
    asyncio.run(run(a.base, a.out))
