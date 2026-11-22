#!/usr/bin/env python3
"""Make our blind-test excerpt look like his: speak it with local H3 TTS (ComfyUI) and transcribe it back with
faster-whisper, so it carries the same kind of ASR errors and line breaks as his transcripts. All local.

    python fair_asr.py story.md <out_dir> [--chars 420]

Writes <out_dir>/ours_asr.txt in his transcript format (header, then `seconds TAB text`), which blind_test.py
takes with --ours-file. Needs ComfyUI on 127.0.0.1:8188 with the minimax-h3-audio-T8 nodes (ghost-film's speak.py)
and faster-whisper with the large-v3-turbo model (the same model that made his transcripts).
"""
import argparse, json, os, re, subprocess, sys, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import blind_test  # noqa: E402

SPEAK = Path.home() / '.claude/skills/ghost-film/scripts/speak.py'
OUT = Path('C:/Users/sheep/code/ComfyUI/output/ghost_film_vo')
VOICE = ('A young Taiwanese man in his early twenties, casual Taiwan Mandarin, telling friends a story at a late-night '
         'snack stall, relaxed and a little playful, natural pace')


def chunks(lines, size=55):
    out, cur = [], ''
    for l in lines:
        if cur and len(cur) + len(l) > size:
            out.append(cur); cur = ''
        cur += (('，' if cur else '') + l)
    if cur:
        out.append(cur)
    return out


def queue_empty():
    q = json.load(urllib.request.urlopen('http://127.0.0.1:8188/queue'))
    return not q['queue_running'] and not q['queue_pending']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('story'); ap.add_argument('out'); ap.add_argument('--chars', type=int, default=420)
    ap.add_argument('--tag', default=None, help='reuse clips already rendered under this tag (skip TTS)')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    lines = blind_test.ours(a.story, a.chars)
    parts = chunks(lines)
    tag = a.tag or ('weitong_fair_' + time.strftime('%H%M%S'))
    jobs = [{'name': f'{tag}_{i:02d}', 'text': t, 'voice': VOICE, 'acting': 'casual, conversational, a bit playful',
             'emotion': 'amused', 'intensity': 0.4, 'seconds': max(5.6, min(15.0, round(len(t) / 4.3 + 1.5, 1))), 'seed': 7 + i}
            for i, t in enumerate(parts)]
    jp = Path(a.out) / 'tts_jobs.json'
    json.dump(jobs, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    todo = [j for j in jobs if not sorted(OUT.glob(j['name'] + '_*.flac'))]
    if todo:  # with --tag, only the clips that are missing are rendered
        json.dump(todo, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        subprocess.run([sys.executable, '-X', 'utf8', str(SPEAK), str(jp)], check=True)
    deadline = time.time() + 3600
    while time.time() < deadline:
        time.sleep(15)
        files = [sorted(OUT.glob(j['name'] + '_*.flac')) for j in jobs]
        if all(files):
            time.sleep(5)  # let the last file finish writing
            break
    else:
        sys.exit('TTS timed out')
    from faster_whisper import WhisperModel
    m = WhisperModel('large-v3-turbo', device='cpu', compute_type='int8', cpu_threads=12)
    rows, t0 = [], 0.0
    for j in jobs:
        f = sorted(OUT.glob(j['name'] + '_*.flac'))[-1]
        segs, info = m.transcribe(str(f), language='zh', vad_filter=True)
        for s in segs:
            rows.append(f'{int(t0 + s.start)}\t{s.text.strip()}')
        t0 += info.duration
    with open(Path(a.out) / 'ours_asr.txt', 'w', encoding='utf-8') as fh:
        fh.write('# ours (TTS -> ASR)\n' + '\n'.join(rows) + '\n')
    print('wrote', Path(a.out) / 'ours_asr.txt', len(rows), 'lines')


if __name__ == '__main__':
    main()
