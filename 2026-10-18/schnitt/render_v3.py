import subprocess, sys
from concurrent.futures import ThreadPoolExecutor

RAW = '../raw'
FPS = 30
BEAT = 60 / 130
TM = ("zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=100,format=gbrpf32le,"
      "zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv:d=error_diffusion,format=yuv420p")
GRADE = {"screen": "eq=contrast=1.06:saturation=1.12", "cam": "eq=contrast=1.05:saturation=1.07"}

LAP = dict(z0=1.15, z1=1.20, cx=0.5, cy=0.46, punch=0.12, kind="screen")   # laptop view
FS = dict(z0=2.90, z1=3.00, cx=0.5, cy=0.487, punch=0.08, kind="screen")   # website full screen
def site(clip, st, beats=1, sp=2.0, **kw): return dict(LAP, clip=clip, st=st, beats=beats, sp=sp, **kw)
def full(clip, st, beats=2, sp=1.5, **kw): return dict(FS, clip=clip, st=st, beats=beats, sp=sp, **kw)
def cam(clip, st, beats, sp, z0, z1, cx, cy, punch=0.05, **kw):
    return dict(clip=clip, st=st, beats=beats, sp=sp, z0=z0, z1=z1, cx=cx, cy=cy, punch=punch, kind="cam", **kw)
def hook(clip, st): return dict(FS, clip=clip, st=st, beats=7, sp=1.0, hook=True, punch=0)

PARTS = {
 "teil1": [
    ("00_hook_gravitas", hook("IMG_0029.MOV", 22.90)),
    ("01_selfie_me",     cam("IMG_0005.MOV", 0.00, 2, 1.0, 1.00, 1.05, 0.5, 0.45)),
    ("02_druse",         site("IMG_0025.MOV", 61.85)),
    ("03_cubus",         site("IMG_0026.MOV", 10.55)),
    ("04_walk_in",       cam("IMG_0013.MOV", 15.20, 2, 1.5, 1.30, 1.36, 0.50, 0.62)),
    ("05_strahl",        site("IMG_0025.MOV", 27.15)),
    ("06_ferro",         site("IMG_0027.MOV", 91.20, dive=True)),
    ("07_falz_fs",       full("IMG_0026.MOV", 42.30)),
    ("08_glance",        cam("IMG_0013.MOV", 26.95, 2, 1.0, 1.45, 1.52, 0.60, 0.55)),
    ("09_schwarm",       site("IMG_0027.MOV", 126.80)),
    ("10_nullzeit",      site("IMG_0029.MOV", 43.00, dive=True)),
    ("11_menger_fs",     full("IMG_0027.MOV", 105.50)),
    ("12_fitcheck",      cam("IMG_0017.MOV", 4.00, 2, 1.6, 1.35, 1.42, 0.50, 0.65)),
    ("13_fragment",      site("IMG_0028.MOV", 7.45)),
    ("14_to_camera",     cam("IMG_0013.MOV", 46.60, 3, 1.25, 1.20, 1.55, 0.50, 0.45)),
 ],
 "teil2": [
    ("00_hook_metropolis", hook("IMG_0027.MOV", 70.20)),
    ("01_selfie_point",  cam("IMG_0020.MOV", 0.00, 2, 1.0, 1.00, 1.05, 0.5, 0.45)),
    ("02_laptop_open",   cam("IMG_0011.MOV", 1.00, 1, 2.5, 1.05, 1.10, 0.5, 0.55)),
    ("03_inspiration",   cam("IMG_0016.mov", 8.80, 1, 2.0, 1.00, 1.05, 0.5, 0.5)),
    ("04_code_purple",   cam("IMG_0009.MOV", 10.00, 1, 1.5, 1.00, 1.05, 0.5, 0.5)),
    ("05_code_front",    cam("IMG_0008.MOV", 16.00, 1, 1.5, 1.00, 1.05, 0.5, 0.45)),
    ("06_guss",          site("IMG_0026.MOV", 94.00)),
    ("07_velum",         site("IMG_0026.MOV", 120.75, dive=True)),
    ("08_tunnel_fs",     full("IMG_0027.MOV", 10.45, sp=1.3)),
    ("09_stare",         cam("IMG_0012.MOV", 6.60, 2, 1.0, 1.00, 1.05, 0.5, 0.40)),
    ("10_nachbild",      site("IMG_0030.MOV", 9.25)),
    ("11_argent",        site("IMG_0030.MOV", 46.00, dive=True)),
    ("12_kaustik_fs",    full("IMG_0026.MOV", 59.60, sp=1.0, grade="eq=contrast=1.12:saturation=1.1:gamma=1.25")),
    ("13_hair",          cam("IMG_0013.MOV", 17.00, 2, 1.5, 1.35, 1.42, 0.48, 0.58)),
    ("14_relief",        site("IMG_0029.MOV", 62.00)),
    ("15_to_camera",     cam("IMG_0017.MOV", 107.90, 3, 1.25, 1.15, 1.45, 0.50, 0.50)),
 ],
}

def frame_counts(shots):
    out, pos = [], 0
    for _, s in shots:
        a = round(pos * BEAT * FPS); pos += s["beats"]; out.append(round(pos * BEAT * FPS) - a)
    return out

def smooth(x): return f"(clip({x},0,1)*clip({x},0,1)*(3-2*clip({x},0,1)))"

def exprs(s, n):
    if s.get("hook"):
        a = round(4 * BEAT * FPS); b = round(5 * BEAT * FPS)
        S = smooth(f"(on-{a})/{b - a}")
        z = (f"if(lt(on,{a}),2.90+0.08*on/{a},"
             f"if(lt(on,{b}),2.98+(1.15-2.98)*{S},1.15+0.04*(on-{b})/{max(n - b, 1)}))")
        cy = f"if(lt(on,{a}),0.487,if(lt(on,{b}),0.487+(0.46-0.487)*{S},0.46))"
        return z, "0.5", cy
    z = f"({s['z0']}+({s['z1']}-{s['z0']})*on/{max(n - 1, 1)})*(1+{s['punch']}*exp(-on/2.5))"
    if s.get("dive"):
        z += f"*(1+1.2*pow(clip((on-{n - 5})/4,0,1),2))"
    return z, str(s["cx"]), str(s["cy"])

def render(job):
    part, sid, s, n = job
    z, cx, cy = exprs(s, n)
    vf = (f"setpts=(PTS-STARTPTS)/{s['sp']},fps={FPS},{TM},"
          f"zoompan=z='{z}':x='clip({cx}*iw-iw/zoom/2,0,iw-iw/zoom)':y='clip({cy}*ih-ih/zoom/2,0,ih-ih/zoom)'"
          f":d=1:s=1080x1920:fps={FPS},{s.get('grade', GRADE[s['kind']])},setsar=1")
    out = f"shots_v3/{part}_{sid}.mp4"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(s["st"]), "-i", f"{RAW}/{s['clip']}",
                        "-t", f"{n / FPS * s['sp'] + 0.2:.3f}", "-an", "-vf", vf, "-frames:v", str(n),
                        "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(FPS), out],
                       capture_output=True, text=True)
    return out, r.returncode, n, r.stderr[-400:]

if __name__ == "__main__":
    only = set(sys.argv[1:])
    jobs = []
    for part, shots in PARTS.items():
        fc = frame_counts(shots)
        print(part, "frames", sum(fc), f"= {sum(fc) / FPS:.2f}s")
        with open(f"concat_{part}.txt", "w") as f:
            for (sid, s), n in zip(shots, fc):
                f.write(f"file 'shots_v3/{part}_{sid}.mp4'\n")
                if not only or sid in only or part in only: jobs.append((part, sid, s, n))
    with ThreadPoolExecutor(2) as ex:
        for out, rc, n, err in ex.map(render, jobs):
            print(out, rc, n, err)
