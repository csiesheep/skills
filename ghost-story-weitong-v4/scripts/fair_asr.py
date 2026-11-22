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


DIG = '零一二三四五六七八九'


def cn_number(m):
    """12 -> 十二, 210 -> 二百一十: his ASR writes numbers in characters (1.2% of his lines have a digit, ours had
    2 to 9%)."""
    s = m.group(0)
    if len(s) > 4 or s.startswith('0'):
        return ''.join(DIG[int(c)] for c in s)
    n, out = int(s), ''
    for unit, v in (('千', 1000), ('百', 100), ('十', 10)):
        q, n = divmod(n, v)
        if q:
            out += ('' if unit == '十' and q == 1 and not out else DIG[q]) + unit
        elif out and n:
            out += '' if out.endswith('零') else '零'
    return out + (DIG[n] if n else '') or '零'


def his_lines(text):
    """One ASR segment in his format: spaces inside it become line breaks (8 to 15% of our lines had a space, 2.8%
    of his), digits become characters. The 2026-11-22 judge took both as signs of a fake."""
    text = re.sub(r'(?<!\d)2(?=[點個隻次天年位張台包條分秒週周間樓種杯句])', '兩', text)  # 兩點, not 二點
    text = re.sub(r'\d+', cn_number, text)
    # a long segment with commas becomes one line per clause: his lines average 8.6 characters
    return [p for p in re.split(r'[\s，。！？,.!?、；;]+', text.strip()) if p]


def queue_empty():
    q = json.load(urllib.request.urlopen('http://127.0.0.1:8188/queue'))
    return not q['queue_running'] and not q['queue_pending']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('story'); ap.add_argument('out'); ap.add_argument('--chars', type=int, default=420)
    ap.add_argument('--tag', default=None, help='reuse clips already rendered under this tag (skip TTS)')
    ap.add_argument('--names', default='',
                    help='the characters\' names, comma separated (阿斌,灰灰): given to whisper as hotwords so each name '
                         'comes back in one spelling; a judge read 阿兵/阿斌/阿冰 as 「故意灑錯字」')
    ap.add_argument('--plain', action='store_true',
                    help='the input is plain text (one of his transcripts for the control test), not a story.md')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.plain:  # the control: his own transcript, his cast renamed the way blind_test renames his excerpts
        import random
        lines = blind_test.scrub(blind_test.his(a.story, a.chars), blind_test.HIS_NAMES, random.Random(1)).split('\n')
    else:
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
        # the GPU is shared: H3 voices go in only when the queue is empty, never between someone's Qwen jobs
        waited = 0
        while not queue_empty():
            if waited == 0:
                print('ComfyUI is busy; waiting for an empty queue', flush=True)
            time.sleep(30); waited += 30
            if waited > 3 * 3600:
                sys.exit('ComfyUI stayed busy for 3 hours; run again later')
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
    names = [n.strip() for n in a.names.replace('，', ',').split(',') if n.strip()]
    rows, t0 = [], 0.0
    for j in jobs:
        f = sorted(OUT.glob(j['name'] + '_*.flac'))[-1]
        # the prompt keeps whisper in traditional characters: the control run's first segment came back simplified
        # (而几个小时后…), and 5 of 428 lines in earlier runs did too; his transcripts are traditional
        segs, info = m.transcribe(str(f), language='zh', vad_filter=True, hotwords=' '.join(names) or None,
                                  initial_prompt='以下是台灣人用繁體中文講的鬼故事。')
        for s in segs:
            for line in his_lines(s.text):
                rows.append(f'{int(t0 + s.start)}\t{line}')
        t0 += info.duration
    variants = {n: sum(r.count(n) for r in rows) for n in names}
    print('names as spelled in the transcript:', variants, flush=True)
    with open(Path(a.out) / 'ours_asr.txt', 'w', encoding='utf-8') as fh:
        fh.write('# ours (TTS -> ASR)\n' + '\n'.join(rows) + '\n')
    print('wrote', Path(a.out) / 'ours_asr.txt', len(rows), 'lines')


if __name__ == '__main__':
    main()
