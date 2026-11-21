#!/usr/bin/env python3
"""Build a blind voice test: three of his excerpts and one of ours, shuffled, made to look alike.

    python blind_test.py story.md <his transcripts dir> <out dir> [--seed N] [--chars 420]

Writes <out dir>/blind.md (four excerpts A-D, no names of sources) and <out dir>/key.json (which is ours).
Give blind.md to a fresh subagent with the prompt in SKILL.md step 3; never give it key.json.
Our excerpt is taken from the first half of the story (the banter part, where voice matters most), his from the
same relative place of a random story of similar length. Punctuation is removed from ours and both are cut into
breath-group lines, because his transcripts have no punctuation; his recurring cast names are replaced with ordinary names; ours are left as written.
The transcripts stay local; blind.md goes only to a local subagent and is not published.
"""
import argparse, glob, json, os, random, re

HAN = re.compile(r'[一-鿿]')


def ours(path, n):
    t = re.sub(r'<!--.*?-->', '', open(path, encoding='utf-8').read(), flags=re.S)
    body = '\n'.join(t.splitlines()[1:])
    parts = [x.strip() for x in re.split(r'[，。？！：；、「」…—\n]+', body) if HAN.search(x)]
    start = len(parts) // 6
    out, c = [], 0
    for p in parts[start:]:
        out.append(p); c += len(HAN.findall(p))
        if c >= n:
            break
    return out


def his(path, n, frac=0.17):
    L = [l.split('\t', 1)[1].strip() for l in open(path, encoding='utf-8').read().splitlines()[1:] if '\t' in l]
    L = [l for l in L if HAN.search(l)]
    start = int(len(L) * frac)
    out, c = [], 0
    for p in L[start:]:
        out.append(p); c += len(HAN.findall(p))
        if c >= n:
            break
    return out


def scrub(lines, names, rnd):
    # His recurring cast becomes ordinary names; ○○ masks gave the 2026-11-21 test away.
    pool = ['阿凱', '小胖', '阿翔', '大熊', '阿哲', '小安', '阿豪', '小柏']
    rnd.shuffle(pool)
    s = '\n'.join(lines)
    for i, nm in enumerate(names):
        s = s.replace(nm, pool[i % len(pool)])
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('story'); ap.add_argument('his_dir'); ap.add_argument('out')
    ap.add_argument('--seed', type=int, default=None); ap.add_argument('--chars', type=int, default=420)
    ap.add_argument('--ours-file', default=None,
                    help="our excerpt already passed through TTS and ASR (fair_asr.py's ours_asr.txt)")
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    his_names = ['阿騰', '維騰', '韋騰', '土豆', '小剛', '小康', '馬鏡', '馬騎', '馬竟', '馬桿', '洋蔥']
    files = [f for f in glob.glob(os.path.join(a.his_dir, '*.txt')) if os.path.getsize(f) > 6000]
    picks = rnd.sample(files, 3)
    items = [('his', os.path.basename(f), scrub(his(f, a.chars), his_names, rnd)) for f in picks]
    if a.ours_file:
        ol = [l.split('\t', 1)[1].strip() for l in open(a.ours_file, encoding='utf-8').read().splitlines()[1:] if '\t' in l]
    else:
        ol = ours(a.story, a.chars)
    items.append(('ours', os.path.basename(a.story), '\n'.join(ol)))
    rnd.shuffle(items)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, 'blind.md'), 'w', encoding='utf-8') as f:
        f.write('# 四段口述鬼故事的逐字稿（沒有標點，一行是一口氣；有的有語音辨識的錯字）\n\n')
        for i, (_, _, txt) in enumerate(items):
            f.write(f'## {"ABCD"[i]}\n\n{txt}\n\n')
    key = {"ABCD"[i]: {'who': w, 'src': s} for i, (w, s, _) in enumerate(items)}
    json.dump(key, open(os.path.join(a.out, 'key.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote', os.path.join(a.out, 'blind.md'), '; ours is', [k for k, v in key.items() if v['who'] == 'ours'][0])


if __name__ == '__main__':
    main()
