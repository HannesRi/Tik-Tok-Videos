import json, subprocess, sys, os
from concurrent.futures import ThreadPoolExecutor

RAW = '../raw'
FPS = 30
TM = ("zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=100,format=gbrpf32le,"
      "zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv:d=error_diffusion,format=yuv420p")

# id, clip, src_start, speed, out_dur, z0, z1, cx, cy, kind
SHOTS = [
    ("01_hook_gravitas", "IMG_0029.MOV", 23.00, 1.0, 1.5, 1.25, 1.35, 0.5, 0.46, "screen"),
    ("02_hook_falz",     "IMG_0026.MOV", 42.25, 1.0, 1.5, 1.25, 1.35, 0.5, 0.46, "screen"),
    ("03_selfie_point",  "IMG_0022.MOV", 0.20, 1.15, 1.5, 1.00, 1.05, 0.5, 0.42, "cam"),
    ("04_laptop_open",   "IMG_0011.MOV", 0.75, 2.0, 1.0, 1.05, 1.10, 0.5, 0.55, "cam"),
    ("05_inspiration",   "IMG_0016.mov", 8.60, 1.6, 1.0, 1.00, 1.06, 0.5, 0.50, "cam"),
    ("06_code_purple",   "IMG_0009.MOV", 9.50, 1.6, 1.0, 1.00, 1.06, 0.5, 0.50, "cam"),
    ("07_code_hands",    "IMG_0018.MOV", 15.00, 1.6, 0.5, 1.00, 1.04, 0.5, 0.55, "cam"),
    ("08_code_front",    "IMG_0008.MOV", 16.00, 1.6, 1.0, 1.00, 1.06, 0.5, 0.45, "cam"),
    ("09_m01_druse",     "IMG_0025.MOV", 61.60, 1.3, 1.0, 1.12, 1.20, 0.5, 0.46, "screen"),
    ("10_m02_cubus",     "IMG_0026.MOV", 9.75, 1.6, 1.0, 1.12, 1.20, 0.5, 0.46, "screen"),
    ("11_m03_strahl",    "IMG_0025.MOV", 26.75, 1.6, 1.0, 1.12, 1.20, 0.5, 0.46, "screen"),
    ("12_m04_ferro",     "IMG_0027.MOV", 90.90, 1.6, 1.0, 1.12, 1.20, 0.5, 0.46, "screen"),
    ("13_m05_metropolis","IMG_0027.MOV", 70.40, 1.6, 1.0, 1.12, 1.20, 0.5, 0.46, "screen"),
    ("14_m06_domino",    "IMG_0028.MOV", 22.60, 1.6, 1.0, 1.12, 1.20, 0.5, 0.46, "screen"),
    ("15_m07_nullzeit",  "IMG_0029.MOV", 42.30, 1.6, 1.0, 1.12, 1.20, 0.5, 0.46, "screen"),
    ("16_m08_vitrum",    "IMG_0028.MOV", 59.60, 1.6, 1.0, 1.12, 1.20, 0.5, 0.46, "screen"),
    ("17_m09_schwarm",   "IMG_0027.MOV", 126.40, 1.6, 1.0, 1.12, 1.20, 0.5, 0.46, "screen"),
    ("18_m10_sumi",      "IMG_0030.MOV", 80.30, 1.6, 1.0, 1.12, 1.20, 0.5, 0.46, "screen"),
    ("19_m11_fragment",  "IMG_0028.MOV", 7.25, 1.6, 1.0, 1.12, 1.20, 0.5, 0.46, "screen"),
    ("20_m12_menger",    "IMG_0027.MOV", 105.40, 1.6, 1.0, 1.12, 1.20, 0.5, 0.46, "screen"),
    ("21_end_selfie",    "IMG_0012.MOV", 1.00, 1.0, 3.5, 1.00, 1.05, 0.5, 0.40, "cam"),
]

GRADE = {"screen": "eq=contrast=1.05:saturation=1.10",
         "cam": "eq=contrast=1.04:saturation=1.06"}

def render(s):
    sid, clip, st, sp, dur, z0, z1, cx, cy, kind = s
    n = round(dur * FPS)
    src_dur = dur * sp + 0.2
    vf = (f"setpts=(PTS-STARTPTS)/{sp},fps={FPS},{TM},"
          f"zoompan=z='{z0}+({z1}-{z0})*on/{max(n-1,1)}':x='{cx}*iw-iw/zoom/2':y='{cy}*ih-ih/zoom/2':d=1:s=1080x1920:fps={FPS},"
          f"{GRADE[kind]},setsar=1")
    out = f"shots/{sid}.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(st), "-i", f"{RAW}/{clip}", "-t", f"{src_dur:.3f}", "-an",
           "-vf", vf, "-frames:v", str(n), "-c:v", "libx264", "-crf", "12", "-preset", "medium",
           "-pix_fmt", "yuv420p", "-r", str(FPS), out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    got = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                          "stream=nb_read_frames", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
    return sid, r.returncode, r.stderr[-300:], n, got

only = set(sys.argv[1:])
todo = [s for s in SHOTS if not only or s[0] in only]
with ThreadPoolExecutor(2) as ex:
    for sid, rc, err, n, got in ex.map(render, todo):
        print(sid, "rc", rc, "frames", got, "/", n, err)
json.dump(SHOTS, open("shots.json", "w"), indent=1)
