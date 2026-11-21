#!/usr/bin/env python3
"""Voice fingerprint: the same counts for his ASR transcripts and for our stories.

    python voice.py build <dir of transcripts>   # writes ../references/fingerprint.json (numbers only)
    python voice.py story.md                     # prints our story's fingerprint against his range

A transcript file is one story: a header line, then `seconds TAB text`. Our story is plain text (markers in
<!-- --> are ignored). Counts are per 100 or per 1,000 Chinese characters, so long and short texts compare.
"""
import glob, json, os, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FP = os.path.join(HERE, '..', 'references', 'fingerprint.json')
HAN = re.compile(r'[一-鿿]')

PARTICLES = '啦喔欸蛤齁耶吧啊呢嘛咧捏哦哇唉'
GROUPS = {
    # label: (per, words, explanation)
    'particles': (100, None, '語氣詞（啦喔欸蛤齁耶吧啊呢嘛咧捏哦哇唉）每百字'),
    'exclaim': (1000, ['我靠', '哇靠', '靠北', '天啊', '唉唷', '哎呦', '喔呦', '欸欸', '蛤', '哭喔', '北七', '傻眼',
                       '傻住', '笑死', '真的假的', '不會吧', '屁啦', '鬼咧', '三小'], '驚嘆和吐槽詞每千字'),
    'intens': (1000, ['直接', '根本', '整個', '超', '有夠', '莫名', '到底', '完全', '一堆'], '口語強調詞每千字'),
    'ask': (1000, ['什麼', '幹嘛', '怎樣', '誰啊', '嗎', '是喔', '對啊', '好啦', '好啊', '有啊'], '問句和應答詞每千字'),
    'trans': (1000, ['這時', '當下', '就這樣', '只不過', '結果', '突然', '沒想到', '想當然', '反正', '然後'],
              '轉場詞每千字'),
    'wo': (100, ['我'], '「我」每百字'),
    'aside': (1000, ['說老實話', '老實說', '說真的', '說也奇怪', '簡單的說', '簡單來說', '基本上', '總而言之', '重點是',
                     '你知道嗎', '認真來講'], '旁白插話（說老實話、說也奇怪、基本上…）每千字'),
    'conn': (1000, ['之後', '此時', '並且', '接著', '隨即', '於是', '雖然說', '原來', '一看', '不知道為什麼', '當然的'],
             '敘事連接詞（之後、此時、並且、便…）每千字'),
    'comment': (1000, ['居然', '甚至', '反而', '竟然', '嗯', '呃'], '旁白評論和遲疑（居然、甚至、反而、嗯、呃）每千字'),
    'er': (1000, None, '以「而」起頭的一口氣（而就在、而我也、而直到…）每千字'),
}


def lines_of_transcript(path):
    out = []
    for l in open(path, encoding='utf-8').read().splitlines()[1:]:
        if '\t' in l:
            out.append(l.split('\t', 1)[1])
    return out


def lines_of_story(path):
    t = re.sub(r'<!--.*?-->', '', open(path, encoding='utf-8').read(), flags=re.S)
    body = [l for l in t.splitlines()[1:] if l.strip()]
    # ASR segments are breath groups; split our lines at punctuation to compare the same unit
    return [x for l in body for x in re.split(r'[，。？！：；、「」…—]', l) if HAN.search(x)]


def fingerprint(lines):
    txt = ''.join(lines)
    n = len(HAN.findall(txt)) or 1
    f = {}
    for k, (per, words, _) in GROUPS.items():
        if k == 'er':
            c = sum(1 for l in lines if l.strip().startswith('而'))
        elif words is None:
            c = sum(txt.count(ch) for ch in PARTICLES)
        else:
            c = sum(txt.count(w) for w in words)
            if k == 'conn':
                c += len(re.findall(r'便[一-鿿]', txt)) - txt.count('方便') - txt.count('隨便') - txt.count('便利') - txt.count('便當')
            if k == 'exclaim':
                c -= txt.count('靠近') + txt.count('依靠')  # 靠 as a verb is not 我靠
        f[k] = per * c / n
    lens = [len(HAN.findall(l)) for l in lines if HAN.search(l)]
    f['line_len'] = statistics.median(lens) if lens else 0
    f['chars'] = n
    return f


def build(d):
    rows = [fingerprint(lines_of_transcript(p)) for p in sorted(glob.glob(os.path.join(d, '*.txt')))]
    rows = [r for r in rows if r['chars'] > 600]
    out = {'n_stories': len(rows), 'built_from': 'research/weiteng/nuwa_src (209 crawled stories, ASR)', 'metrics': {}}
    for k in list(GROUPS) + ['line_len']:
        v = sorted(r[k] for r in rows)
        q = lambda p: round(v[int(p * (len(v) - 1))], 2)
        out['metrics'][k] = {'p10': q(.1), 'p25': q(.25), 'p50': q(.5), 'p75': q(.75), 'p90': q(.9),
                             'label': GROUPS[k][2] if k in GROUPS else '一行（呼吸群）字數中位'}
    json.dump(out, open(FP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'wrote {FP} from {len(rows)} stories')


def compare(f):
    ref = json.load(open(FP, encoding='utf-8'))['metrics']
    rows = []
    for k, m in ref.items():
        v = f[k]
        if k in ('particles', 'exclaim', 'intens', 'line_len'):
            verdict = '必改' if v < m['p10'] else ('注意' if v < m['p25'] else 'ok')
        else:
            verdict = 'ok' if m['p10'] <= v <= m['p90'] else '注意'
        rows.append((m['label'], f'{v:.2f}', f"{m['p25']}–{m['p75']}（中位 {m['p50']}，p10 {m['p10']}）", verdict))
    return rows


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == 'build':
        build(sys.argv[2])
    elif len(sys.argv) == 2:
        for r in compare(fingerprint(lines_of_story(sys.argv[1]))):
            print('  ／  '.join(r))
    else:
        print(__doc__)
