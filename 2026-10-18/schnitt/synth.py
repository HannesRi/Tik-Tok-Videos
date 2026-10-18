import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 48000
DUR = 24.5
BEAT = 0.5           # 120 BPM
N = int(DUR * SR)
rng = np.random.default_rng(7)
L = np.zeros(N); R = np.zeros(N)

def add(sig, t0, gain=1.0, pan=0.0):
    i0 = int(round(t0 * SR))
    if i0 >= N: return
    s = sig[: N - i0] * gain
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    if s.ndim == 2:
        L[i0:i0 + len(s)] += s[:, 0] * l * 1.414; R[i0:i0 + len(s)] += s[:, 1] * r * 1.414
    else:
        L[i0:i0 + len(s)] += s * l * 1.414; R[i0:i0 + len(s)] += s * r * 1.414

def filt(x, kind, f, order=4):
    sos = butter(order, f, btype=kind, fs=SR, output='sos'); return sosfilt(sos, x)

def tt(d): return np.arange(int(d * SR)) / SR

def kick(d=0.5):
    t = tt(d); f = 44 + 120 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 6.5)
    click = filt(rng.standard_normal(len(t)), 'highpass', 2500) * np.exp(-t * 400) * 0.25
    return np.tanh(1.6 * (body + click)) * 0.9

def hat(open_=False):
    d = 0.18 if open_ else 0.05; t = tt(d)
    n = filt(rng.standard_normal(len(t)), 'highpass', 7500)
    return n * np.exp(-t * (18 if open_ else 70)) * 0.35

def clap():
    t = tt(0.35); n = filt(rng.standard_normal(len(t)), 'bandpass', [900, 3200])
    env = np.zeros_like(t)
    for off in (0.0, 0.011, 0.022):
        m = t >= off; env[m] += np.exp(-(t[m] - off) * 160)
    env += np.exp(-np.maximum(t - 0.03, 0) * 16) * (t >= 0.03) * 0.6
    return n * env * 0.5

def reverb(x, secs=2.2, wet=0.35, seed=1):
    r = np.random.default_rng(seed); t = tt(secs)
    irL = r.standard_normal(len(t)) * np.exp(-t * 3.2 / secs * 2)
    irR = r.standard_normal(len(t)) * np.exp(-t * 3.2 / secs * 2)
    irL = filt(irL, 'lowpass', 5000); irR = filt(irR, 'lowpass', 5000)
    irL /= np.sqrt((irL ** 2).sum()); irR /= np.sqrt((irR ** 2).sum())
    n = len(x) + len(t)
    wl = np.zeros(n); wr = np.zeros(n)
    cl = fftconvolve(x, irL); cr = fftconvolve(x, irR)
    wl[:len(cl)] = cl; wr[:len(cr)] = cr
    dry = np.concatenate([x, np.zeros(len(t))])
    return np.stack([dry * (1 - wet) + wl * wet, dry * (1 - wet) + wr * wet], 1)

def saw(freq, d, harm_max=5000, tilt=1.25, detune_cents=(-8, 0, 8)):
    t = tt(d); out = np.zeros_like(t)
    for c in detune_cents:
        f = freq * 2 ** (c / 1200); ph0 = rng.uniform(0, 2 * np.pi)
        k = 1
        while k * f < harm_max:
            out += np.sin(2 * np.pi * k * f * t + ph0 * k) / k ** tilt; k += 1
    return out / len(detune_cents)

def env_adsr(d, a=0.25, r=0.6):
    t = tt(d); e = np.minimum(1, t / a) * np.minimum(1, np.maximum(0, (d - t) / r)); return e

def pad(notes, d, gain=0.10):
    s = sum(saw(f, d) for f in notes) / len(notes)
    s = filt(s, 'lowpass', 2200, 2) * env_adsr(d, 0.35, 0.9)
    return s * gain

def impact(d=2.5):
    t = tt(d); f = 52 * np.exp(-t * 0.35) + 4
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    noise = filt(rng.standard_normal(len(t)), 'lowpass', 1800) * np.exp(-t * 9) * 0.5
    return np.tanh(1.3 * (boom + noise)) * 0.8

def riser(d, f_lo=600, f_hi=9000):
    t = tt(d); n = rng.standard_normal(len(t)); out = np.zeros_like(n)
    seg = int(0.02 * SR)
    for i in range(0, len(n), seg):
        frac = i / len(n); fc = f_lo * (f_hi / f_lo) ** frac
        sos = butter(2, [fc * 0.6, min(fc * 1.6, 20000)], btype='bandpass', fs=SR, output='sos')
        out[i:i + seg] = sosfilt(sos, n[max(0, i - 2000):i + seg])[-len(n[i:i + seg]):]
    return out * (t / d) ** 2.2 * 0.45

def whoosh(d=0.45):
    t = tt(d); x = riser(d, 400, 7000); return x * np.minimum(1, (d - t) / 0.05)

def sub(freq, d):
    t = tt(d); s = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(4 * np.pi * freq * t)
    return s * np.minimum(1, t / 0.01) * np.minimum(1, (d - t) / 0.03) * 0.5

A2, C3, D3, E3, F2, G2 = 110.0, 130.81, 146.83, 164.81, 87.31, 98.0
CH = {  # pad voicings
    'Am': [220.0, 261.63, 329.63, 440.0],
    'F':  [174.61, 220.0, 261.63, 349.23],
    'C':  [196.0, 261.63, 329.63, 392.0],
    'G':  [196.0, 246.94, 293.66, 392.0],
}
ROOT = {'Am': 55.0, 'F': 43.65, 'C': 65.41, 'G': 49.0}

# ---------- arrangement ----------
pad_bus = np.zeros(N)
def padbus(sig, t0):
    i0 = int(t0 * SR); s = sig[: N - i0]; pad_bus[i0:i0 + len(s)] += s

# hook + intro pads
padbus(pad(CH['Am'], 4.6, 0.11), 0.0)
padbus(pad(CH['F'], 4.6, 0.11), 4.5)
# drop pads: Am F C G Am F  (one per 2 s bar)
for i, c in enumerate(['Am', 'F', 'C', 'G', 'Am', 'F']):
    padbus(pad(CH[c], 2.3, 0.10), 9.0 + 2 * i)
# outro pad
padbus(pad(CH['Am'], 3.8, 0.12), 21.0)
pw = reverb(pad_bus, 2.8, 0.45, seed=3)[:N]
L += pw[:, 0]; R += pw[:, 1]

# impacts on the big moments
for t0, g in ((0.0, 1.0), (1.5, 0.55), (4.5, 0.6), (9.0, 1.0), (21.0, 0.9)):
    add(reverb(impact(), 1.8, 0.3, seed=int(t0 * 10)), t0, g)

# hook ticking hats (tension)
for i in range(int(4.5 / (BEAT / 4))):
    t0 = i * BEAT / 4
    add(hat(), t0, 0.35 if i % 4 else 0.6, pan=0.25 if i % 2 else -0.25)

# whoosh into hand-cover cut (4.5)
add(whoosh(0.5), 4.0, 0.9)
# whoosh into each hook cut
add(whoosh(0.35), 1.15, 0.5)

# build 4.5 - 9.0 : kick on beats, hats, bass
for i in range(9):
    t0 = 4.5 + i * BEAT
    if t0 < 8.75: add(kick(), t0, 0.6)
for i in range(int(4.5 / (BEAT / 2))):
    t0 = 4.5 + i * BEAT / 2
    if t0 < 8.8: add(hat(open_=(i % 2 == 1)), t0, 0.3, pan=0.2)
# snare/clap roll into the drop
roll_t = 7.0; step = BEAT / 2
while roll_t < 8.9:
    add(reverb(clap(), 0.8, 0.2), roll_t, 0.25 + 0.5 * (roll_t - 7.0) / 1.9)
    roll_t += step
    if roll_t > 8.0: step = BEAT / 4
    if roll_t > 8.5: step = BEAT / 8
add(riser(2.0), 7.0, 0.9)
for t0, f in ((4.5, ROOT['F']), (6.5, ROOT['F'])):
    add(sub(f * 2, 2.0), t0, 0.35)

# drop 9.0 - 21.0
kicks = [9.0 + i * BEAT for i in range(24)]
for t0 in kicks: add(kick(), t0, 1.0)
for i in range(12):
    add(reverb(clap(), 1.2, 0.3, seed=i), 9.0 + BEAT + i * 2 * BEAT, 0.7)
for i in range(int(12 / (BEAT / 4))):
    t0 = 9.0 + i * BEAT / 4
    v = [0.25, 0.15, 0.45, 0.15][i % 4]
    add(hat(open_=(i % 4 == 2)), t0, v, pan=(0.3 if i % 2 else -0.3))
# sidechained sub bass, 8th-note pulse
for b, c in enumerate(['Am', 'F', 'C', 'G', 'Am', 'F']):
    for k in range(8):
        t0 = 9.0 + b * 2 + k * BEAT / 2
        if k % 2 == 1: add(sub(ROOT[c] * 2, BEAT / 2 - 0.02), t0, 0.55)
        else: add(sub(ROOT[c], BEAT / 2 - 0.02), t0, 0.35)
# little whoosh on every montage cut
for i in range(1, 12):
    add(whoosh(0.25), 9.0 + i - 0.25, 0.22, pan=(0.4 if i % 2 else -0.4))
# riser into the outro
add(riser(1.5, 1200, 12000), 19.5, 0.5)

# outro: slow kick heartbeat fading
for i, t0 in enumerate([21.0, 22.0, 23.0]):
    add(kick(), t0, 0.5 * (0.7 ** i))

# ---------- master ----------
mix = np.stack([L, R], 1)
mix = filt(mix.T, 'highpass', 28, 2).T
peak = np.max(np.abs(mix)); mix = mix / peak * 0.9
mix = np.tanh(mix * 1.4) / np.tanh(1.4)
fade = np.ones(N); fl = int(0.6 * SR); fade[-fl:] = np.linspace(1, 0, fl) ** 1.5
mix *= fade[:, None]
wavfile.write('music_raw.wav', SR, (mix * 0.89 * 32767).astype(np.int16))
print('ok', mix.shape, float(np.abs(mix).max()))
