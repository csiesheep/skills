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
       "whisper": lambda d=None: whisper()}
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
