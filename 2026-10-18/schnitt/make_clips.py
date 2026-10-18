import subprocess, os, sys
from concurrent.futures import ThreadPoolExecutor
from lib_v4 import *

CAM = "eq=contrast=1.05:saturation=1.07"
OUT = "../clips/TikTok_Clips_18-10"

def S(name, clip, a, b): return dict(kind="site", name=name, clip=clip, a=a, b=b)
def C(name, clip, a, b, z=1.0, cx=0.5, cy=0.5): return dict(kind="cam", name=name, clip=clip, a=a, b=b, z=z, cx=cx, cy=cy)

PACK = {
 "Teil1": [
    S("01_FALZ_Hook_Speedramp", "IMG_0026.MOV", 28.0, 38.8),
    C("02_Selfie", "IMG_0005.MOV", 0.0, 2.15, 1.0, 0.5, 0.45),
    S("03_DRUSE", "IMG_0025.MOV", 61.3, 64.8),
    S("04_STRAHL", "IMG_0025.MOV", 26.6, 30.1),
    C("05_Reinlaufen", "IMG_0013.MOV", 14.5, 18.5, 1.30, 0.5, 0.62),
    S("06_FERRO", "IMG_0027.MOV", 90.4, 93.9),
    S("07_GRAVITAS", "IMG_0029.MOV", 22.8, 26.3),
    C("08_Blick", "IMG_0013.MOV", 26.0, 29.0, 1.45, 0.60, 0.55),
    S("09_SCHWARM", "IMG_0027.MOV", 125.0, 128.5),
    S("10_NULLZEIT", "IMG_0029.MOV", 42.0, 45.5),
    C("11_FitCheck", "IMG_0017.MOV", 3.0, 7.0, 1.35, 0.5, 0.65),
    S("12_Wuerfeltunnel", "IMG_0027.MOV", 105.0, 108.5),
    C("13_Ende_ZurKamera", "IMG_0013.MOV", 45.5, 50.0, 1.20, 0.5, 0.45),
 ],
 "Teil2": [
    S("01_CUBUS_Hook_Speedramp", "IMG_0026.MOV", 3.2, 12.6),
    C("02_Selfie", "IMG_0020.MOV", 0.0, 2.83, 1.0, 0.5, 0.45),
    C("03_LaptopAuf", "IMG_0011.MOV", 0.5, 4.0, 1.05, 0.5, 0.55),
    C("04_Inspiration", "IMG_0016.mov", 8.0, 11.5),
    C("05_Tippen", "IMG_0009.MOV", 9.0, 12.5),
    C("06_Tippen_vorne", "IMG_0008.MOV", 15.0, 18.5, 1.0, 0.5, 0.45),
    S("07_GUSS", "IMG_0026.MOV", 93.0, 96.5),
    S("08_VELUM", "IMG_0026.MOV", 119.5, 123.0),
    S("09_NeonTunnel", "IMG_0027.MOV", 9.0, 12.5),
    C("10_Blick", "IMG_0012.MOV", 6.0, 9.0, 1.0, 0.5, 0.40),
    S("11_NACHBILD", "IMG_0030.MOV", 8.5, 12.0),
    S("12_ARGENT", "IMG_0030.MOV", 45.5, 49.0),
    S("13_METROPOLIS", "IMG_0027.MOV", 70.0, 73.5),
    C("14_Haare", "IMG_0013.MOV", 16.5, 20.0, 1.35, 0.48, 0.58),
    C("15_Ende_ZurKamera", "IMG_0017.MOV", 107.0, 111.0, 1.15, 0.5, 0.5),
 ],
 "Extra_Websites": [
    S("KAUSTIK", "IMG_0026.MOV", 58.0, 61.5),
    S("RELIEF", "IMG_0029.MOV", 58.5, 62.0),
    S("SUMI", "IMG_0030.MOV", 79.5, 83.0),
    S("FRAGMENT", "IMG_0028.MOV", 6.5, 10.0),
    S("VITRUM", "IMG_0028.MOV", 55.5, 59.0),
    S("DOMINO", "IMG_0028.MOV", 21.5, 25.0),
    S("APERTUR", "IMG_0029.MOV", 4.0, 8.0),
    S("BRANDUNG", "IMG_0028.MOV", 38.0, 42.0),
 ],
}

def render(job):
    folder, c = job
    os.makedirs(f"{OUT}/{folder}", exist_ok=True)
    out = f"{OUT}/{folder}/{c['name']}.mp4"
    dur = c["b"] - c["a"]
    enc = ["-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-r", "30", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-an", "-movflags", "+faststart", out]
    if c["kind"] == "cam":
        vf = f"fps=30,{TM},{zp(c['z'], c['cx'], c['cy'])},{CAM},setsar=1"
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(c["a"]), "-i", f"{RAW}/{c['clip']}", "-vf", vf] + enc
    else:
        m, rot = screen_prep(c["clip"], c["a"] + 0.5)
        fc = (f"[0]fps=30,{TM}[v];[1]format=rgba[m];[v][m]overlay=format=auto:shortest=1,{rot},format=yuv420p,"
              f"{zp(1.06, 0.5, 0.4734)},{SCREEN_GRADE},setsar=1")
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(c["a"]), "-i", f"{RAW}/{c['clip']}", "-loop", "1", "-i", m,
               "-filter_complex", fc] + enc
    r = subprocess.run(cmd, capture_output=True, text=True)
    return out, r.returncode, r.stderr[-300:]

if __name__ == "__main__":
    jobs = [(f, c) for f, cs in PACK.items() for c in cs]
    with ThreadPoolExecutor(2) as ex:
        for out, rc, err in ex.map(render, jobs): print(rc, out, err)
