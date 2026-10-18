import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 48000
BEAT = 60 / 130
S16 = BEAT / 4
END = round(33 * BEAT * 30) / 30
N = int(END * SR) + SR // 2
rng = np.random.default_rng(11)
bus = {k: np.zeros((N, 2)) for k in ("drums", "bass", "bell", "fx")}

def tt(d): return np.arange(int(d * SR)) / SR
def filt(x, kind, f, order=2): return sosfilt(butter(order, f, btype=kind, fs=SR, output='sos'), x, axis=0)
def place(name, sig, t0, gain=1.0, pan=0.0):
    i0 = int(round(t0 * SR))
    if i0 >= N or i0 < 0: return
    s = sig[: N - i0] * gain
    if s.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4) * 1.414, np.sin((pan + 1) * np.pi / 4) * 1.414
        s = np.stack([s * l, s * r], 1)
    bus[name][i0:i0 + len(s)] += s

# ---------------- instruments ----------------
def kick():
    t = tt(0.42); f = 46 + 180 * np.exp(-t * 38)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    click = filt(rng.standard_normal(len(t)), 'highpass', 3000) * np.exp(-t * 500) * 0.35
    return np.tanh(2.4 * (body + click)) * 0.95

def b808(freq, d, slide_to=None):
    t = tt(d)
    f = freq * (1 + 0.6 * np.exp(-t * 45))
    if slide_to: f = f * (slide_to / freq) ** np.clip((t - d * 0.45) / (d * 0.35), 0, 1)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    env = np.minimum(1, t / 0.004) * np.exp(-t * 1.2) * np.minimum(1, (d - t) / 0.02)
    s = np.tanh(3.2 * s * env) * 0.75
    return filt(s, 'lowpass', 2400)

def cowbell(freq, d=0.22):
    t = tt(d)
    sq = lambda f: np.sign(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)))
    s = 0.6 * sq(freq) + 0.4 * sq(freq * 1.4836)
    s = filt(s, 'bandpass', [freq * 0.8, min(freq * 3.2, 9000)])
    env = np.exp(-t * 16) * 0.75 + np.exp(-t * 70) * 0.25
    return np.tanh(1.6 * s * env) * 0.55

def clap():
    t = tt(0.32); n = filt(rng.standard_normal(len(t)), 'bandpass', [1000, 4200])
    env = sum(np.exp(-np.maximum(t - o, 0) * 180) * (t >= o) for o in (0, 0.009, 0.019))
    env = env + np.exp(-np.maximum(t - 0.026, 0) * 22) * (t >= 0.026) * 0.7
    body = np.sin(2 * np.pi * 210 * t) * np.exp(-t * 40) * 0.4
    return np.tanh(1.5 * (n * env + body)) * 0.55

def hat(open_=False):
    d = 0.22 if open_ else 0.045; t = tt(d)
    n = filt(rng.standard_normal(len(t)), 'highpass', 8000, 4)
    return n * np.exp(-t * (14 if open_ else 85)) * 0.32

def tom(freq):
    t = tt(0.22); f = freq * (1 + 0.5 * np.exp(-t * 30))
    return np.tanh(1.8 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14)) * 0.45

def snare():
    t = tt(0.16); n = filt(rng.standard_normal(len(t)), 'bandpass', [1500, 7000])
    return (n * np.exp(-t * 30) + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 45) * 0.5) * 0.45

def impact():
    t = tt(2.6); f = 58 * np.exp(-t * 0.6) + 22
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.0)
    crash = filt(rng.standard_normal(len(t)), 'highpass', 2500) * np.exp(-t * 3.5) * 0.35
    return np.tanh(1.6 * boom) * 0.9 + crash

def riser(d, f0=500, f1=11000):
    n = rng.standard_normal(int(d * SR)); out = np.zeros_like(n); seg = 960
    for i in range(0, len(n), seg):
        fr = i / len(n); fc = f0 * (f1 / f0) ** fr
        out[i:i + seg] = sosfilt(butter(2, [fc * 0.7, min(fc * 1.5, 20000)], 'bandpass', fs=SR, output='sos'),
                                 n[max(0, i - 2000):i + seg])[-len(n[i:i + seg]):]
    return out * (np.arange(len(n)) / len(n)) ** 2.5 * 0.6

def reverb(x, secs=1.6, seed=1):
    r = np.random.default_rng(seed); t = tt(secs)
    out = []
    for ch in range(2):
        ir = filt(r.standard_normal(len(t)) * np.exp(-t * 5.5 / secs), 'lowpass', 6000)
        ir /= np.sqrt((ir ** 2).sum())
        out.append(fftconvolve(x[:, ch], ir)[: len(x)])
    return np.stack(out, 1)

# ---------------- score ----------------
A4, C5, D5, E5, F4, G4, E4 = 440.0, 523.25, 587.33, 659.26, 349.23, 392.0, 329.63
RIFF_A = {0: A4, 2: A4, 4: C5, 6: A4, 8: G4, 11: E4, 12: G4, 14: A4,
          16: A4, 18: A4, 20: C5, 22: A4, 24: D5, 27: C5, 28: G4, 30: E4}
RIFF_B = {0: E5, 2: D5, 4: C5, 6: A4, 8: G4, 11: A4, 12: C5, 14: D5,
          16: E5, 18: D5, 20: C5, 22: A4, 24: F4, 27: G4, 28: A4, 30: A4}
ROOTS = [55.0, 43.65, 65.41, 49.0]           # A1 F1 C2 G1 per bar
BASS_STEPS = [(0, 3), (3, 3), (6, 4), (10, 2), (12, 4)]
KICKS = [0, 3, 6, 10]
DROP = 5 * BEAT
OUTRO = 30 * BEAT

def bell_riff(t0, riff, steps, gain, pan=0.15):
    for s, f in riff.items():
        if s < steps: place("bell", cowbell(f), t0 + s * S16, gain * (1.0 if s % 4 == 0 else 0.85), pan)

# intro: muffled riff (3 beats), then build
bell_riff(0.0, RIFF_A, 12, 0.9)
place("bass", b808(55.0, 3 * BEAT), 0.0, 0.35)
for i in range(12): place("drums", hat(), i * S16, 0.35 if i % 2 else 0.55, 0.2)
# build (beats 3-5): snare roll accelerating, riser, kick 8ths
t = 3 * BEAT; step = S16
while t < DROP - S16 * 1.0:
    prog = (t - 3 * BEAT) / (2 * BEAT)
    place("drums", snare(), t, 0.35 + 0.6 * prog, -0.1)
    t += step if prog < 0.5 else step / 2
for k in range(4): place("drums", kick(), 3 * BEAT + k * BEAT / 2, 0.55)
place("fx", riser(2 * BEAT - S16), 3 * BEAT, 1.0)

# drop: bars from beat 5
bar = 0
while DROP + bar * 4 * BEAT < OUTRO - 1e-6:
    b0 = DROP + bar * 4 * BEAT
    steps_in_bar = min(16, round((OUTRO - b0) / S16))
    riff = RIFF_A if (bar // 2) % 2 == 0 else RIFF_B
    bell_riff(b0, {k - 16 * (bar % 2): v for k, v in riff.items() if 16 * (bar % 2) <= k < 16 * (bar % 2) + steps_in_bar}, 16, 1.0)
    root = ROOTS[bar % 4]
    for s, ln in BASS_STEPS:
        if s < steps_in_bar:
            slide = root * 2 if (s == 12 and bar % 2 == 1) else None
            place("bass", b808(root, ln * S16, slide), b0 + s * S16, 0.9)
    for s in KICKS + ([12] if bar % 2 else []):
        if s < steps_in_bar: place("drums", kick(), b0 + s * S16, 1.0)
    for s in (4, 12):
        if s < steps_in_bar: place("drums", clap(), b0 + s * S16, 0.9)
    for s in range(0, steps_in_bar, 2):
        place("drums", hat(open_=(s == 10)), b0 + s * S16, 0.55 if s % 4 == 0 else 0.4, 0.25)
    if steps_in_bar == 16:
        for s in (13, 15): place("drums", hat(), b0 + s * S16, 0.3, 0.25)
    for s, f in ((7, 180), (9, 150), (14, 120)):
        if s < steps_in_bar: place("drums", tom(f), b0 + s * S16, 0.6, -0.3)
    bar += 1
# fill into outro (beat 29 -> 30): snare 16ths
for k in range(4): place("drums", snare(), 29 * BEAT + k * S16, 0.45 + 0.12 * k)
place("fx", impact(), DROP, 1.0)

# outro: hit + echoing bell + long 808
place("fx", impact(), OUTRO, 0.6)
place("drums", kick(), OUTRO, 1.0)
place("bass", b808(55.0, 3 * BEAT + 0.4), OUTRO, 0.85)
for i, (s, f) in enumerate(sorted(RIFF_A.items())[:6]):
    place("bell", cowbell(f), OUTRO + s * S16, 0.75 * 0.8 ** i)
for s in range(0, 12, 2): place("drums", hat(), OUTRO + s * S16, 0.3, 0.25)

# ---------------- mix ----------------
intro_end = int(3 * BEAT * SR)
lp = filt(bus["bell"][:intro_end], 'lowpass', 900)
fade = np.linspace(0, 1, intro_end)[:, None]
bus["bell"][:intro_end] = lp * (1 - fade) + bus["bell"][:intro_end] * fade * 0.6
bus["bell"] = bus["bell"] * 0.8 + reverb(bus["bell"], 1.4, 3) * 0.35
# silence gap right before the drop
g0, g1 = int((DROP - S16) * SR), int(DROP * SR)
for k in bus: bus[k][g0:g1] *= np.linspace(1, 0, g1 - g0)[:, None] ** 3 if k != "fx" else 1
# sidechain duck for bass & bell on kicks
duck = np.ones(N)
for b in range(int(END / BEAT) + 1):
    for s in KICKS:
        i0 = int((DROP + b * 4 * BEAT + s * S16) * SR)
        if DROP <= i0 / SR < OUTRO and i0 < N:
            seg = min(int(0.12 * SR), N - i0)
            duck[i0:i0 + seg] = np.minimum(duck[i0:i0 + seg], 0.45 + 0.55 * np.linspace(0, 1, seg) ** 1.5)
mix = bus["drums"] * 0.9 + (bus["bass"] * 0.85 + bus["bell"] * 0.7) * duck[:, None] + bus["fx"] * 0.55
mix = filt(mix, 'highpass', 25)
mix = mix[: int(END * SR)]
mix /= np.max(np.abs(mix))
mix = np.tanh(mix * 1.8) / np.tanh(1.8)
tail = int(0.35 * SR); mix[-tail:] *= np.linspace(1, 0, tail)[:, None]
wavfile.write("phonk_raw.wav", SR, (mix * 0.95 * 32767).astype(np.int16))
print("ok", END, mix.shape)
