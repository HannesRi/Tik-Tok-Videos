import subprocess, os, math, numpy as np

RAW = '../raw'
FPS = 30
BEAT = 60 / 130
TM = ("zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=100,format=gbrpf32le,"
      "zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv:d=error_diffusion,format=yuv420p")
TMG = TM.replace(":d=error_diffusion,format=yuv420p", ",format=gray")
SCREEN_GRADE = "eq=contrast=1.04:saturation=1.05"
CAM_GRADES = {
    "muted": ("colorbalance=rs=-0.03:gs=0.0:bs=0.04:rm=-0.04:bm=0.02:rh=0.02:bh=-0.02,"
              "eq=contrast=1.05:saturation=0.72:gamma=0.97,curves=all='0/0.02 0.3/0.26 0.7/0.74 1/0.98',vignette=PI/6"),
    "bw": "hue=s=0,eq=contrast=1.12:gamma=0.95,curves=all='0/0.03 0.3/0.24 0.7/0.76 1/0.97',vignette=PI/6",
}
GRAIN = "noise=c0s=5:c0f=t+u"

def lid(clip, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", f"{RAW}/{clip}", "-frames:v", "1",
                          "-vf", TMG, "-f", "rawvideo", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(3840, 2160).astype(float)
    def top(x0, x1):
        band = a[:, x0:x1].mean(1); wall = np.median(band[700:950])
        return next(y for y in range(950, 1400) if band[y] < 0.45 * wall)
    return top(150, 350), top(1810, 2010)

def mask(tl, tr):
    path = f"masks/m_{tl}_{tr}.png"
    if os.path.exists(path): return path
    H, W = 3840, 2160
    y = np.arange(H)[:, None].astype(float); x = np.arange(W)[None, :].astype(float)
    ss = lambda e0, e1, v: (lambda t: t * t * (3 - 2 * t))(np.clip((v - e0) / (e1 - e0), 0, 1))
    top = tl + (tr - tl) * (x - 250) / (1910 - 250) + 84
    a = np.maximum(np.maximum(1 - ss(top - 2, top + 2, y), ss(2470, 2980, y)),
                   np.maximum(1 - ss(30, 44, x), ss(2110, 2124, x)) * (y < 2700))
    img = np.zeros((H, W, 4), np.uint8); img[..., 3] = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-i", "-", path],
                   input=img.tobytes(), check=True)
    return path

def screen_prep(clip, t):
    """filter chain (after TM) that blacks out wall/menu bar and levels the laptop; returns (mask_path, chain)"""
    tl, tr = lid(clip, t)
    ang = math.atan((tl - tr) / (1910 - 250))
    return mask(tl, tr), f"rotate=a={ang:.5f}:fillcolor=black"

def zp(z, cx, cy):
    return (f"zoompan=z='{z}':x='clip({cx}*iw-iw/zoom/2,0,iw-iw/zoom)':y='clip({cy}*ih-ih/zoom/2,0,ih-ih/zoom)'"
            f":d=1:s=1080x1920:fps={FPS}")

def ease(x): return f"(clip({x},0,1)*clip({x},0,1)*(3-2*clip({x},0,1)))"
