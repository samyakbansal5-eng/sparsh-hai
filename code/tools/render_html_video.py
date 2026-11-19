"""Render a deterministic HTML animation (window.render(t), window.START, window.D) to MP4, one file per scene.
python tools/render_html_video.py media/teaser.html media/SPARSH_teaser.mp4"""
import asyncio, os, subprocess, sys
from playwright.async_api import async_playwright
FPS = 30


async def main(html, out):
    tmp = out + "_parts"; os.makedirs(tmp, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome")
        pg = await b.new_page(viewport={"width": 1920, "height": 1080})
        await pg.goto("file://" + os.path.abspath(html)); await pg.wait_for_timeout(1000)
        start = await pg.evaluate("window.START"); dur = await pg.evaluate("window.D")
        parts = []
        for k, (s0, d) in enumerate(zip(start, dur)):
            part = os.path.join(tmp, f"scene{k:02d}.mp4"); parts.append(part)
            if os.path.exists(part):
                continue
            tmpf = part + ".tmp.mp4"
            ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), tmpf], stdin=subprocess.PIPE)
            for i in range(int(round(d * FPS))):
                await pg.evaluate(f"render({s0 + i / FPS})")
                ff.stdin.write(await pg.screenshot(type="jpeg", quality=92))
            ff.stdin.close(); ff.wait()
            if ff.returncode == 0:
                os.rename(tmpf, part)
            print("scene", k, "done", flush=True)
        await b.close()
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    print("wrote", out)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
