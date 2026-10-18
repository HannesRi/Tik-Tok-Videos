import subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from lib_v4 import *

CAM = ("hue=s=0,eq=contrast=1.18:gamma=0.9:brightness=-0.02,"
       "curves=all='0/0 0.12/0.05 0.5/0.48 0.85/0.88 1/0.98',vignette=angle=PI/3.6")
WIDE = (1.06, 1.10)
DETAIL = (1.75, 1.85)
SCY = 0.4734

def site(clip, st, look=WIDE, beats=2, sp=1.25): return dict(type="site", clip=clip, st=st, z=look, beats=beats, sp=sp)
def cam(clip, st, beats, sp, z0, z1, cx, cy, ease_zoom=False):
    return dict(type="cam", clip=clip, st=st, beats=beats, sp=sp, z=(z0, z1), cx=cx, cy=cy, ease=ease_zoom)
def hook(clip, a, spa, b_end, c_sp=1.0, z=(1.10, 1.45)):
    return dict(type="hook", clip=clip, st=a, spa=spa, b_end=b_end, spc=c_sp, z=z, beats=8)

PARTS = {
 "teil1": [
    ("00_hook_falz",   hook("IMG_0026.MOV", 28.60, 2.0, 36.95)),
    ("01_selfie",      cam("IMG_0005.MOV", 0.00, 2, 1.0, 1.00, 1.04, 0.5, 0.45)),
    ("02_druse",       site("IMG_0025.MOV", 61.85)),
    ("03_strahl",      site("IMG_0025.MOV", 27.15, DETAIL)),
    ("04_walk_in",     cam("IMG_0013.MOV", 15.20, 2, 1.5, 1.30, 1.34, 0.50, 0.62)),
    ("05_ferro",       site("IMG_0027.MOV", 91.20)),
    ("06_gravitas",    site("IMG_0029.MOV", 23.20, DETAIL)),
    ("07_glance",      cam("IMG_0013.MOV", 26.95, 2, 1.0, 1.45, 1.50, 0.60, 0.55)),
    ("08_schwarm",     site("IMG_0027.MOV", 126.80)),
    ("09_nullzeit",    site("IMG_0029.MOV", 43.00, DETAIL)),
    ("10_fitcheck",    cam("IMG_0017.MOV", 4.00, 2, 1.6, 1.35, 1.40, 0.50, 0.65)),
    ("11_menger",      site("IMG_0027.MOV", 105.50)),
    ("12_to_camera",   cam("IMG_0013.MOV", 46.60, 3, 1.25, 1.20, 1.50, 0.50, 0.45, True)),
 ],
 "teil2": [
    ("00_hook_cubus",  hook("IMG_0026.MOV", 3.55, 1.0, 10.85)),
    ("01_selfie",      cam("IMG_0020.MOV", 0.00, 2, 1.0, 1.00, 1.04, 0.5, 0.45)),
    ("02_laptop_open", cam("IMG_0011.MOV", 1.00, 1, 2.5, 1.05, 1.08, 0.5, 0.55)),
    ("03_inspiration", cam("IMG_0016.mov", 8.80, 1, 2.0, 1.00, 1.03, 0.5, 0.50)),
    ("04_code_purple", cam("IMG_0009.MOV", 10.00, 1, 1.5, 1.00, 1.03, 0.5, 0.50)),
    ("05_code_front",  cam("IMG_0008.MOV", 16.00, 1, 1.5, 1.00, 1.03, 0.5, 0.45)),
    ("06_guss",        site("IMG_0026.MOV", 94.00)),
    ("07_velum",       site("IMG_0026.MOV", 120.75)),
    ("08_tunnel",      site("IMG_0027.MOV", 10.45, DETAIL, sp=1.1)),
    ("09_stare",       cam("IMG_0012.MOV", 6.60, 2, 1.0, 1.00, 1.04, 0.5, 0.40)),
    ("10_nachbild",    site("IMG_0030.MOV", 9.25)),
    ("11_argent",      site("IMG_0030.MOV", 46.00)),
    ("12_metropolis",  site("IMG_0027.MOV", 70.60, DETAIL)),
    ("13_hair",        cam("IMG_0013.MOV", 17.00, 2, 1.5, 1.35, 1.40, 0.48, 0.58)),
    ("14_to_camera",   cam("IMG_0017.MOV", 107.90, 3, 1.25, 1.15, 1.45, 0.50, 0.50, True)),
 ],
}

def grid(k): return round(k * BEAT * FPS)

def frame_counts(shots):
    out, pos = [], 0
    for _, s in shots:
        out.append(grid(pos + s["beats"]) - grid(pos)); pos += s["beats"]
    return out

def zoom_expr(z0, z1, n, eased):
    x = f"on/{max(n - 1, 1)}"
    return f"{z0}+({z1}-{z0})*{ease(x) if eased else x}"

def render(job):
    part, sid, s, n = job
    clip = s["clip"]; out = f"shots_v4/{part}_{sid}.mp4"
    enc = ["-frames:v", str(n), "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(FPS), out]
    if s["type"] == "cam":
        vf = (f"setpts=(PTS-STARTPTS)/{s['sp']},fps={FPS},{TM},"
              f"{zp(zoom_expr(*s['z'], n, s['ease']), s['cx'], s['cy'])},{CAM},setsar=1")
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(s["st"]), "-i", f"{RAW}/{clip}",
               "-t", f"{n / FPS * s['sp'] + 0.3:.3f}", "-an", "-vf", vf] + enc
    else:
        m, rot = screen_prep(clip, s["st"])
        post = (f"[1]format=rgba[m];[v][m]overlay=format=auto:shortest=1,{rot},format=yuv420p,"
                f"{zp(zoom_expr(*s['z'], n, s['type'] == 'hook'), 0.5, SCY)},{SCREEN_GRADE},setsar=1")
        if s["type"] == "site":
            pre = f"[0]setpts=(PTS-STARTPTS)/{s['sp']},fps={FPS},{TM}[v];"
            src_len = n / FPS * s["sp"] + 0.3
        else:
            na, nb = grid(3), grid(5) - grid(3); nc = n - na - nb
            la = na / FPS * s["spa"]; lb = s["b_end"] - s["st"] - la
            spb = lb / (nb / FPS); lc = nc / FPS * s["spc"]
            k = max(2, min(4, round(spb * 0.6)))
            pre = (f"[0]split=3[s1][s2][s3];"
                   f"[s1]trim=0:{la:.4f},setpts=(PTS-STARTPTS)/{s['spa']},fps={FPS},trim=end_frame={na}[a];"
                   f"[s2]trim={la:.4f}:{la + lb:.4f},tmix=frames={k},setpts=(PTS-STARTPTS)/{spb:.4f},fps={FPS},trim=end_frame={nb}[b];"
                   f"[s3]trim={la + lb:.4f}:{la + lb + lc + 0.1:.4f},setpts=(PTS-STARTPTS)/{s['spc']},fps={FPS},trim=end_frame={nc}[c];"
                   f"[a][b][c]concat=n=3:v=1:a=0,setparams=range=tv:color_primaries=bt2020:color_trc=arib-std-b67:colorspace=bt2020nc,{TM}[v];")
            src_len = la + lb + lc + 0.4
            print(sid, f"A {na}f x{s['spa']}  B {nb}f x{spb:.2f} tmix{k}  C {nc}f x{s['spc']}")
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(s["st"]), "-i", f"{RAW}/{clip}", "-loop", "1", "-i", m,
               "-t", f"{src_len:.3f}", "-an", "-filter_complex", pre + post] + enc
    r = subprocess.run(cmd, capture_output=True, text=True)
    return out, r.returncode, n, r.stderr[-400:]

if __name__ == "__main__":
    only = set(sys.argv[1:]); jobs = []
    for part, shots in PARTS.items():
        fc = frame_counts(shots)
        print(part, sum(fc), "frames", f"{sum(fc) / FPS:.2f}s")
        with open(f"concat4_{part}.txt", "w") as f:
            for (sid, s), n in zip(shots, fc):
                f.write(f"file 'shots_v4/{part}_{sid}.mp4'\n")
                if not only or sid in only or part in only: jobs.append((part, sid, s, n))
    with ThreadPoolExecutor(2) as ex:
        for out, rc, n, err in ex.map(render, jobs): print(out, rc, n, err)
