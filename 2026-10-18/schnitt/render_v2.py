import subprocess
from concurrent.futures import ThreadPoolExecutor

RAW = '../raw'
FPS = 30
BPM = 130
BEAT = 60 / BPM
TM = ("zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=100,format=gbrpf32le,"
      "zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv:d=error_diffusion,format=yuv420p")

# id, clip, src_start, speed, beats, z0, z1, cx, cy, punch, kind
SHOTS = [
    ("00_hook_gravitas", "IMG_0029.MOV", 23.00, 1.0, 4, 1.25, 1.40, 0.5, 0.46, 0.00, "screen"),
    ("01_druse",         "IMG_0025.MOV", 61.85, 2.0, 1, 1.15, 1.20, 0.5, 0.46, 0.12, "screen"),
    ("02_cubus",         "IMG_0026.MOV", 10.55, 2.0, 1, 1.15, 1.20, 0.5, 0.46, 0.12, "screen"),
    ("03_strahl",        "IMG_0025.MOV", 27.15, 2.0, 1, 1.15, 1.20, 0.5, 0.46, 0.12, "screen"),
    ("04_ferro",         "IMG_0027.MOV", 91.20, 2.0, 1, 1.15, 1.20, 0.5, 0.46, 0.12, "screen"),
    ("05_metropolis",    "IMG_0027.MOV", 70.60, 2.0, 1, 1.15, 1.20, 0.5, 0.46, 0.12, "screen"),
    ("06_falz",          "IMG_0026.MOV", 42.30, 2.0, 1, 1.15, 1.20, 0.5, 0.46, 0.12, "screen"),
    ("07_nullzeit",      "IMG_0029.MOV", 43.00, 2.0, 1, 1.15, 1.20, 0.5, 0.46, 0.12, "screen"),
    ("08_sumi",          "IMG_0030.MOV", 80.40, 2.0, 1, 1.15, 1.20, 0.5, 0.46, 0.12, "screen"),
    ("09_schwarm",       "IMG_0027.MOV", 126.80, 2.0, 1, 1.15, 1.20, 0.5, 0.46, 0.12, "screen"),
    ("10_menger",        "IMG_0027.MOV", 105.50, 2.0, 1, 1.15, 1.20, 0.5, 0.46, 0.12, "screen"),
    ("11_fragment",      "IMG_0028.MOV", 7.45, 2.0, 1, 1.15, 1.20, 0.5, 0.46, 0.12, "screen"),
    ("12_guss",          "IMG_0026.MOV", 84.00, 2.0, 1, 1.15, 1.20, 0.5, 0.46, 0.12, "screen"),
    ("13_end_selfie",    "IMG_0022.MOV", 0.08, 1.0, 4, 1.00, 1.06, 0.5, 0.42, 0.06, "cam"),
]
GRADE = {"screen": "eq=contrast=1.06:saturation=1.12", "cam": "eq=contrast=1.04:saturation=1.06"}

def frames_for(shots):
    out, beat_pos = [], 0
    for s in shots:
        a = round(beat_pos * BEAT * FPS); beat_pos += s[4]; b = round(beat_pos * BEAT * FPS)
        out.append(b - a)
    return out

def render(args):
    s, n = args
    sid, clip, st, sp, beats, z0, z1, cx, cy, punch, kind = s
    src_dur = n / FPS * sp + 0.2
    z = f"({z0}+({z1}-{z0})*on/{max(n-1,1)})*(1+{punch}*exp(-on/2.5))"
    vf = (f"setpts=(PTS-STARTPTS)/{sp},fps={FPS},{TM},"
          f"zoompan=z='{z}':x='{cx}*iw-iw/zoom/2':y='{cy}*ih-ih/zoom/2':d=1:s=1080x1920:fps={FPS},"
          f"{GRADE[kind]},setsar=1")
    out = f"shots_v2/{sid}.mp4"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(st), "-i", f"{RAW}/{clip}", "-t", f"{src_dur:.3f}",
                        "-an", "-vf", vf, "-frames:v", str(n), "-c:v", "libx264", "-crf", "12", "-preset", "medium",
                        "-pix_fmt", "yuv420p", "-r", str(FPS), out], capture_output=True, text=True)
    return sid, r.returncode, n, r.stderr[-300:]

if __name__ == "__main__":
    fr = frames_for(SHOTS)
    print("total frames", sum(fr), "=", sum(fr) / FPS, "s")
    with ThreadPoolExecutor(2) as ex:
        for sid, rc, n, err in ex.map(render, zip(SHOTS, fr)):
            print(sid, rc, n, err)
    with open("concat_v2.txt", "w") as f:
        for s in SHOTS: f.write(f"file 'shots_v2/{s[0]}.mp4'\n")
