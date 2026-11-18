"""Synthesised horror sound effects and a mixer. Standard library plus numpy; 44.1 kHz stereo float."""
import math
import subprocess
import wave
from pathlib import Path

import numpy as np

SR = 44100
rng = np.random.default_rng(11)


def secs(n):
    return int(round(n * SR))


def band(sig, lo, hi):
    """Band-pass by FFT mask with soft edges."""
    n = len(sig)
    spec = np.fft.rfft(sig)
    f = np.fft.rfftfreq(n, 1 / SR)
    m = np.clip((f - lo * 0.8) / (lo * 0.2 + 1e-9), 0, 1) * np.clip((hi * 1.2 - f) / (hi * 0.2 + 1e-9), 0, 1)
    return np.fft.irfft(spec * m, n)


def env(n, a, r, shape=2.0):
    t = np.arange(n)
    e = np.ones(n)
    ai, ri = max(1, int(a * SR)), max(1, int(r * SR))
    e[:ai] = np.linspace(0, 1, min(ai, n))[:n] if ai <= n else np.linspace(0, 1, n)
    if ri < n:
        e[-ri:] *= np.linspace(1, 0, ri) ** shape
    return e


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * peak


def drone(d, f0=55.0):
    n = secs(d); t = np.arange(n) / SR
    lfo = 0.5 + 0.5 * np.sin(2 * math.pi * 0.07 * t)
    x = (np.sin(2 * math.pi * f0 * t) * 0.5 + np.sin(2 * math.pi * f0 * 1.5 * t + 1) * 0.25
         + np.sin(2 * math.pi * (f0 * 2.01) * t) * 0.12) * (0.6 + 0.4 * lfo)
    x += band(rng.normal(0, 1, n), 40, 220) * 0.6
    return norm(x, 0.5) * env(n, 1.5, 1.5)


def wind(d):
    n = secs(d); t = np.arange(n) / SR
    x = band(rng.normal(0, 1, n), 250, 1400)
    am = 0.55 + 0.45 * np.sin(2 * math.pi * 0.13 * t + rng.uniform(0, 6)) * np.sin(2 * math.pi * 0.051 * t)
    return norm(x * am, 0.5) * env(n, 1.0, 1.0)


def insects(d):
    n = secs(d); t = np.arange(n) / SR
    x = np.zeros(n)
    for f in (4200, 5100, 6100):
        chirp = np.sin(2 * math.pi * f * t) * (0.5 + 0.5 * np.sign(np.sin(2 * math.pi * rng.uniform(14, 22) * t)))
        gate = (np.sin(2 * math.pi * rng.uniform(0.3, 0.6) * t + rng.uniform(0, 6)) > 0.2).astype(float)
        x += chirp * gate * rng.uniform(0.2, 0.4)
    x = band(x, 3000, 8000)
    return norm(x, 0.18) * env(n, 0.8, 0.8)


def rustle(d, density=6.0):
    n = secs(d); x = np.zeros(n)
    for _ in range(int(d * density)):
        s = rng.integers(0, max(1, n - secs(0.4))); ln = secs(rng.uniform(0.08, 0.35))
        b = band(rng.normal(0, 1, ln), 900, 5500) * env(ln, 0.01, ln / SR * 0.8, 1.5)
        x[s:s + ln] += b * rng.uniform(0.3, 1.0)
    return norm(x, 0.45)


def heartbeat(d, bpm=72):
    n = secs(d); x = np.zeros(n); step = 60 / bpm
    beat = lambda: (lambda ln: np.sin(2 * math.pi * 52 * np.arange(ln) / SR) * np.exp(-np.arange(ln) / (0.07 * SR)))(secs(0.25))
    t = 0.05
    while t < d - 0.3:
        for off, amp in ((0, 1.0), (0.28, 0.7)):
            s = secs(t + off); b = beat() * amp
            x[s:s + len(b)] += b[: max(0, n - s)]
        t += step
    return norm(x, 0.8)


def stinger():
    ln = secs(2.4); t = np.arange(ln) / SR
    f = 90 * np.exp(-t * 1.2) + 28
    boom = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    hit = band(rng.normal(0, 1, ln), 200, 6000) * np.exp(-t * 9)
    return norm(boom + hit * 0.5, 1.0)


def riser(d=1.0):
    n = secs(d); t = np.linspace(0, 1, n)
    x = rng.normal(0, 1, n)
    out = np.zeros(n); seg = secs(0.05)
    for i in range(0, n, seg):
        lo = 300 + 4000 * t[i]
        out[i:i + seg] = band(x[i:i + seg] if len(x[i:i + seg]) > 16 else np.zeros(16)[: len(x[i:i + seg])], lo, lo * 2.5)[: len(x[i:i + seg])]
    return norm(out * t ** 2, 0.6)


def whoosh(d=0.45):
    n = secs(d); t = np.linspace(0, 1, n)
    x = band(rng.normal(0, 1, n), 300, 3000) * np.sin(math.pi * t) ** 2
    return norm(x, 0.5)


def pop():
    ln = secs(0.06); t = np.arange(ln) / SR
    return np.sin(2 * math.pi * 520 * t) * np.exp(-t / 0.012) * 0.25


def ping():
    ln = secs(0.5); t = np.arange(ln) / SR
    x = np.sin(2 * math.pi * 1320 * t) * (t < 0.12) + np.sin(2 * math.pi * 1760 * t) * (t >= 0.14)
    return x * np.exp(-((t % 0.14) / 0.08)) * 0.35


def ring(d=None):
    """An old desk phone's bell: a hammer striking two bells about 20 times a second for 1.6 s, then a short tail."""
    ln = secs(2.0); t = np.arange(ln) / SR
    tone = sum(a * np.sin(2 * math.pi * f * t) for f, a in ((980, 1.0), (1240, 0.8), (2650, 0.35), (3410, 0.2)))
    strike = (np.sin(2 * math.pi * 20 * t) > 0).astype(float)
    env = np.convolve(strike, np.exp(-np.arange(secs(0.03)) / secs(0.012)), mode="same")
    gate = (t < 1.6) + (t >= 1.6) * np.exp(-(t - 1.6) / 0.12)
    return norm(tone * env * gate, 0.55)


def zipper(d=0.7):
    n = secs(d); x = np.zeros(n)
    for i in range(int(d * 60)):
        s = int(i / 60 * SR); ln = secs(0.008)
        x[s:s + ln] += rng.normal(0, 1, ln)[: max(0, n - s)] * rng.uniform(0.4, 1)
    return norm(band(x, 1500, 8000), 0.5)


def whisper(syllables=3, d=1.4):
    """Breathy formant noise in syllables: a voice calling a name, no words."""
    n = secs(d); x = np.zeros(n)
    for k in range(syllables):
        s = secs(0.05 + k * d / syllables); ln = secs(d / syllables * 0.75)
        e = np.sin(np.linspace(0, math.pi, ln)) ** 1.5
        v = band(rng.normal(0, 1, ln), 700, 1300) + 0.7 * band(rng.normal(0, 1, ln), 2200, 3200)
        x[s:s + ln] += (v * e)[: max(0, n - s)]
    # a little echo
    y = x.copy(); dl = secs(0.18)
    y[dl:] += x[:-dl] * 0.35
    return norm(y, 0.7)


def silence(d):
    return np.zeros(secs(d))


LIB = {"drone": drone, "wind": wind, "insects": insects, "rustle": rustle, "heartbeat": heartbeat,
       "stinger": lambda d=None: stinger(), "riser": riser, "whoosh": lambda d=None: whoosh(),
       "pop": lambda d=None: pop(), "ping": lambda d=None: ping(), "zipper": lambda d=None: zipper(),
       "whisper": lambda d=None: whisper(), "ring": lambda d=None: ring()}
BEDS = {"drone", "wind", "insects", "rustle", "heartbeat"}


def read_audio(path: Path, ffmpeg: str) -> np.ndarray:
    tmp = path.with_suffix(".tmp.wav")
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(path), "-ac", "2", "-ar", str(SR), str(tmp)], check=True)
    with wave.open(str(tmp)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    tmp.unlink()
    a = a.reshape(-1, 2)
    rms = float(np.sqrt((a ** 2).mean())) + 1e-9
    return a * (0.1 / rms)          # every track at the same loudness before the version's gain


def mix(total_s, events, music=None, music_gain=0.32, duck=()):
    """events: (start_s, name, dur_s, gain, pan). duck: (start, end) ranges where music drops."""
    n = secs(total_s) + SR
    out = np.zeros((n, 2), dtype=np.float64)
    for start, name, dur, gain, pan in events:
        x = _make(name, dur)
        x = np.asarray(x, dtype=np.float64) * gain
        s = secs(start); e = min(n, s + len(x)); x = x[: e - s]
        l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        out[s:e, 0] += x * l * 1.41; out[s:e, 1] += x * r * 1.41
    if music is not None:
        m = music
        reps = int(math.ceil(n / len(m)))
        m = np.tile(m, (reps, 1))[:n].astype(np.float64)
        g = np.full(n, music_gain)
        for a, b in duck:
            sa, sb = secs(a), secs(b)
            g[sa:sb] = music_gain * 0.12
            ramp = secs(0.3)
            g[max(0, sa - ramp):sa] = np.linspace(music_gain, music_gain * 0.12, len(g[max(0, sa - ramp):sa]))
            g[sb:sb + ramp] = np.linspace(music_gain * 0.12, music_gain, len(g[sb:sb + ramp]))
        fade = env(n, 1.0, 2.5, 1.0)
        out += m * (g * fade)[:, None]
    out = out[: secs(total_s)]
    peak = np.max(np.abs(out)) + 1e-9
    out = out / peak * 0.89
    return out


def write_wav(path: Path, a: np.ndarray):
    with wave.open(str(path), "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- recorded (generated) samples override the synths
SAMPLE_DIR = Path(".")  # the brand's generated sound effects (brand/sfx), set by use_samples()


def use_samples(folder):
    global SAMPLE_DIR
    SAMPLE_DIR = Path(folder)
    _samples.clear()


SAMPLE_MAP = {"insects": "night_mountain", "rustle": "bamboo_rustle", "drone": "dark_drone", "heartbeat": "heartbeat",
              "stinger": "jumpscare", "riser": "riser", "whoosh": "whoosh", "ping": "phone_ping",
              "whisper": "whisper_name", "zipper": "tent_zipper", "footsteps": "footsteps_leaves", "page": "page_flip"}
_samples = {}


def _sample(name):
    if name not in _samples:
        f = SAMPLE_DIR / f"{SAMPLE_MAP[name]}.flac"
        if not f.exists():
            _samples[name] = None
        else:
            import imageio_ffmpeg
            a = read_raw(f, imageio_ffmpeg.get_ffmpeg_exe())
            _samples[name] = norm(a.mean(axis=1), 0.9)
    return _samples[name]


def read_raw(path, ffmpeg):
    tmp = Path(str(path) + ".tmp.wav")
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(path), "-ac", "2", "-ar", str(SR), str(tmp)], check=True)
    with wave.open(str(tmp)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    tmp.unlink()
    return a.reshape(-1, 2)


def _fit(x, d):
    """Loop a bed to d seconds with short crossfades, fade in and out."""
    n = secs(d); xf = secs(0.6)
    if len(x) >= n:
        y = x[:n].copy()
    else:
        y = np.zeros(n); pos = 0; first = True
        while pos < n:
            seg = x[: min(len(x), n - pos)].copy()
            if not first and len(seg) > xf:
                seg[:xf] *= np.linspace(0, 1, xf); y[pos - xf:pos] *= np.linspace(1, 0, xf)
                pos -= xf
            y[pos:pos + len(seg)] += seg; pos += len(seg); first = False
    return y * env(n, min(1.0, d / 4), min(1.5, d / 4), 1.0)


def _make(name, d):
    if name in SAMPLE_MAP and _sample(name) is not None:
        x = _sample(name)
        return _fit(x, d) if name in BEDS else x
    return LIB[name](d) if name in BEDS or name == "riser" else LIB[name]()


LIB["footsteps"] = lambda d=None: rustle(d or 4, 3)
LIB["page"] = lambda d=None: whoosh(0.3)
BEDS.add("footsteps")


def bell(d=None):
    """A bus's stop-request chime 「叮」: one bright struck bell, a fast attack and a 1.2-s ring-out
    (〈末班車的下車鈴〉, 2026-10-30)."""
    ln = secs(1.3); t = np.arange(ln) / SR
    tone = sum(a * np.sin(2 * math.pi * f * t) * np.exp(-t / dk)
               for f, a, dk in ((1568, 1.0, 0.45), (3136, 0.35, 0.22), (4704, 0.18, 0.12), (2093, 0.25, 0.3)))
    click = np.exp(-t / 0.004) * rng.normal(0, 0.3, ln)
    return norm(tone + click, 0.5) * env(ln, 0.002, 0.2)


def rain(d):
    """Heavy rain on a bus roof: broadband hiss with a slow swell and a scatter of drops."""
    n = secs(d); t = np.arange(n) / SR
    x = band(rng.normal(0, 1, n), 900, 9000) * (0.75 + 0.25 * np.sin(2 * math.pi * 0.09 * t))
    drops = (rng.random(n) < 0.0009).astype(float) * rng.uniform(0.3, 1.0, n)
    x += np.convolve(drops, np.exp(-np.arange(secs(0.01)) / secs(0.002)), mode="same") * 0.8
    return norm(x, 0.5) * env(n, 0.8, 0.8)


LIB["bell"] = bell
LIB["rain"] = rain
BEDS.add("rain")


def knock(d=None):
    """A dull knock on a metal grate heard through water 「叩」: a low thud with a muffled metallic edge, 0.4 s
    (〈社區泳池的排水口〉, 2026-10-31). Name it three times about 0.45 s apart for 「叩、叩、叩」."""
    ln = secs(0.4); t = np.arange(ln) / SR
    thud = np.sin(2 * math.pi * 85 * t) * np.exp(-t / 0.07)
    metal = sum(a * np.sin(2 * math.pi * f * t) * np.exp(-t / dk) for f, a, dk in ((410, 0.35, 0.05), (690, 0.2, 0.035)))
    click = band(rng.normal(0, 1, ln), 200, 1200) * np.exp(-t / 0.008) * 0.4
    return norm(thud + metal + click, 0.8) * env(ln, 0.001, 0.15)


LIB["knock"] = knock


def slap(d=None):
    """A wet flip-flop sole slapping a bare heel on tile 「啪」: a short smack with a watery splat tail, 0.3 s
    (〈東河海邊的民宿〉, 2026-11-03). Name it three times about 0.7 s apart for 「啪，啪，啪」, slow."""
    ln = secs(0.3); t = np.arange(ln) / SR
    smack = band(rng.normal(0, 1, ln), 500, 4500) * np.exp(-t / 0.012)
    body = np.sin(2 * math.pi * 140 * t) * np.exp(-t / 0.03) * 0.6
    splat = band(rng.normal(0, 1, ln), 1500, 7000) * np.exp(-((t - 0.04) ** 2) / 0.0012) * 0.35
    return norm(smack + body + splat, 0.8) * env(ln, 0.001, 0.12)


def waves(d):
    """Slow surf on a stony beach: a low wash that swells and drains about every 7 s, with pebble hiss."""
    n = secs(d); t = np.arange(n) / SR
    swell = (0.5 + 0.5 * np.sin(2 * math.pi * t / 7.0 - 1.5)) ** 2
    x = band(rng.normal(0, 1, n), 120, 1800) * (0.25 + 0.75 * swell)
    x += band(rng.normal(0, 1, n), 2500, 9000) * np.clip(np.sin(2 * math.pi * t / 7.0 - 2.6), 0, 1) ** 3 * 0.35
    return norm(x, 0.5) * env(n, 1.5, 1.5)


def gasp(d=None):
    """A long, wet, rasping in-breath, like someone surfacing from water 「嘶——」, 1.4 s."""
    ln = secs(1.4); t = np.arange(ln) / SR
    rise = np.clip(t / 1.2, 0, 1)
    noise = rng.normal(0, 1, ln)
    air = band(noise, 500, 2200) * (1 - rise) * 0.6 + band(noise, 1800, 6000) * rise
    air *= (0.3 + 0.7 * rise)
    gurgle = np.sin(2 * math.pi * (90 + 40 * np.sin(2 * math.pi * 11 * t)) * t) * (rng.random(ln) < 0.5) * 0.15
    return norm(air + gurgle, 0.85) * env(ln, 0.05, 0.25)


LIB["slap"] = slap
LIB["waves"] = waves
LIB["gasp"] = gasp
BEDS.add("waves")
