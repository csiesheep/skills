#!/usr/bin/env python3
"""Check a ghost-story-weitong-v4 story against the style rules (references/style.md).

The story is plain text with HTML-comment markers where the beats and jokes are:

    <!-- 異狀 -->            first anomaly (put it just before the sentence)
    <!-- 鬼 -->              ghost first clearly seen or identified
    <!-- 反轉 -->            each twist
    <!-- 驚嚇 -->            the biggest scare (exactly one)
    <!-- 收尾 -->            start of the ending
    <!-- 笑 吐槽角色 a -->   a joke: type, then an id (any short word)
    <!-- 回收 a -->          where joke a comes back as a clue / comes true / the ghost answers it

Positions are measured in spoken characters (punctuation, spaces and markers removed) and converted to
seconds at 4.5 characters a second, the channel's median speech rate.

Usage: python weitong_check.py story.md [--rate 4.5]
Prints a table of rule / value / reference / verdict (必改, 注意, ok). Exit code 1 if any 必改.
"""
import argparse, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TYPES = {'吐槽角色', '旁白吐槽', '自嘲', '日常荒謬', '鬼的人性反應', '諧音梗', '其他'}
MARK = re.compile(r'<!--\s*(.*?)\s*-->', re.S)
SPOKEN = re.compile(r'[一-鿿A-Za-z0-9]')


# Kept in step with references/avoid.md by hand. MUST: the channel's names, fixed lines and series.
# WARN: ordinary words that are also his names or tics (小康家庭, 洋蔥圈, 好死不死) - a person decides.
AVOID_MUST = [
    '阿騰', '維騰', '韋騰', '微騰', '阿燈', '阿藤', '土豆', '小剛', '馬鏡', '馬騎', '馬竟', '馬桿', '馬鹽',
    '故事開始囉', '故事開始了', '這故事是發生在', '故事說完了', '故事，說完了', '故事一，結束',
    '就讓他來扛', '來扛吧', '如此如此', '這般這般', '嗯，沒錯，這就是', '嗯沒錯這就是',
    '你們都以為故事到這邊就結束了',
    '吃了大便', '擦不完的大便', '跟肉粽一樣', '被貓監視的老鼠',
    '微鬼畫', '睡前故事', '草莓牛奶', '怪奇微微疼', '日本人真實故事',
]
# 2026-11-21 owner: common Taiwanese slang is allowed (哭喔, 北七, 你倒咧, 好死不死 ...).
AVOID_WARN = ['小康', '洋蔥', '以下就是', '的故事：']
# written-only words a storyteller does not say aloud (2026-11-22: 「只見」 named by both blind judges)
WRITTEN = ['只見', '映入眼簾', '不禁', '彷彿', '宛如', '霎時', '頓時間', '油然而生', '不由得', '竟是', '此時此刻']


def load_avoid():
    return AVOID_MUST


def avoid_hits(clean):
    must = [w for w in AVOID_MUST if w in clean]
    warn = [w for w in AVOID_WARN if w in clean]
    if re.search(r'^\s*故事[一二三1-3]', clean, re.M):
        must.append('故事N 報幕')
    return must, warn


def parse(text):
    events = []  # (pos_chars, kind, args)
    pos = 0
    i = 0
    for m in MARK.finditer(text):
        pos += len(SPOKEN.findall(text[i:m.start()]))
        i = m.end()
        parts = m.group(1).split()
        if parts:
            events.append((pos, parts[0], parts[1:]))
    pos += len(SPOKEN.findall(text[i:]))
    return events, pos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('story')
    ap.add_argument('--rate', type=float, default=4.5)
    ap.add_argument('--chars', default='2200-2700',
                    help='target spoken characters, e.g. 850-1000 when the owner asks for a short one')
    a = ap.parse_args()
    raw = open(a.story, encoding='utf-8').read()
    events, total = parse(raw)
    clean = MARK.sub('', raw)
    sec = lambda c: c / a.rate
    frac = lambda c: c / max(total, 1)
    rows = []

    def add(rule, val, ref, verdict):
        rows.append((rule, val, ref, verdict))

    # length
    mins = sec(total) / 60
    lo_c, hi_c = (int(x) for x in a.chars.split('-'))
    v = 'ok' if lo_c <= total <= hi_c else ('注意' if lo_c * .85 <= total <= hi_c * 1.15 else '必改')
    add('長度（唸出來的字）', f'{total} 字 ≈ {mins:.1f} 分', f'{lo_c:,}–{hi_c:,} 字', v)

    def one(kind):
        return [p for p, k, _ in events if k == kind]

    # beats
    an = one('異狀')
    if not an:
        add('第一個異狀', '沒標', '.15–.40（中位 .27）', '必改')
    else:
        f = frac(an[0]); add('第一個異狀', f'{f:.2f}', '.15–.40（中位 .27）', 'ok' if .15 <= f <= .40 else '注意')
    gh = one('鬼')
    if gh:
        f = frac(gh[0]); add('鬼第一次被看清', f'{f:.2f}', '.51–.87（中位 .69）', 'ok' if .51 <= f <= .87 else '注意')
    else:
        add('鬼第一次被看清', '沒標', '.51–.87', '注意')
    pk = one('驚嚇')
    peak = None
    if len(pk) != 1:
        add('最大驚嚇', f'標了 {len(pk)} 個', '剛好 1 個', '必改')
    else:
        peak = pk[0]; f = frac(peak)
        v = 'ok' if .74 <= f <= .94 else ('注意' if .65 <= f <= .97 else '必改')
        add('最大驚嚇', f'{f:.2f}', '.74–.94（中位 .85）', v)
    tw = one('反轉')
    add('反轉', f'{len(tw)} 個', '2–3 個', 'ok' if 2 <= len(tw) <= 3 else ('注意' if len(tw) == 4 else '必改'))
    en = one('收尾')
    end = en[0] if en else None
    if end is None:
        add('收尾段', '沒標', '最後約 5%', '注意')
    else:
        f = frac(end); add('收尾段開始', f'{f:.2f}', '.92–.97', 'ok' if f >= .90 else '注意')

    # jokes
    jokes = [(p, args[0] if args else '?', args[1] if len(args) > 1 else None) for p, k, args in events if k == '笑']
    bad_types = [t for _, t, _ in jokes if t not in TYPES]
    if bad_types:
        add('笑點類型', '、'.join(sorted(set(bad_types))), '、'.join(sorted(TYPES)), '必改')
    n = len(jokes)
    lo, hi = round(0.6 * mins), round(1.1 * mins)
    v = 'ok' if lo <= n <= hi else ('注意' if 4 <= n <= 12 else '必改')
    add('笑點數', f'{n}（{n / max(mins, .1):.2f}／分）', f'{lo}–{hi}（他 0.81／分）', v)
    if jokes:
        s0 = sec(jokes[0][0])
        add('第一個笑點', f'{s0:.0f} 秒', '30–80 秒（中位 49）', 'ok' if 20 <= s0 <= 90 else ('注意' if s0 <= 150 else '必改'))
        q = [0] * 5
        for p, _, _ in jokes:
            q[min(int(frac(p) * 5), 4)] += 1
        front = (q[0] + q[1]) / n
        add('笑點五等份', '／'.join(map(str, q)), '28／27／20／15／10%', 'ok' if front >= .45 else '注意')
        tc = {}
        for _, t, _ in jokes:
            tc[t] = tc.get(t, 0) + 1
        ghostj = tc.get('鬼的人性反應', 0)
        add('鬼的人性反應', f'{ghostj}', '最多 1，且在驚嚇後', 'ok' if ghostj <= 1 else '必改')
    if peak is not None and jokes:
        before = [p for p, _, _ in jokes if p < peak]
        after = [p for p, _, _ in jokes if p > peak]
        near = [p for p, _, _ in jokes if abs(sec(p - peak)) <= 5]
        add('驚嚇 ±5 秒內的笑點', f'{len(near)}', '0（他只有 3% 的故事有）', 'ok' if not near else '必改')
        if before:
            gap = sec(peak - before[-1])
            add('最後一個笑點到驚嚇', f'{gap:.0f} 秒', '≥ 60 秒（中位 80）', 'ok' if gap >= 60 else ('注意' if gap >= 25 else '必改'))
        add('驚嚇後的笑點', f'{len(after)}', '最多 1（只能是主角抱怨）', 'ok' if len(after) <= 1 else '必改')
        if end is not None:
            inend = [p for p, _, _ in jokes if p >= end]
            add('收尾段裡的笑點', f'{len(inend)}', '0（不以笑點收）', 'ok' if not inend else '必改')

    # callbacks
    ids = {jid: p for p, _, jid in jokes if jid}
    backs = {}
    for p, k, args in events:
        if k == '回收' and args:
            backs.setdefault(args[0], []).append(p)
    paid = [j for j, p in ids.items() if any(b > p for b in backs.get(j, []))]
    orphan = [b for b in backs if b not in ids]
    v = 'ok' if len(paid) >= 2 else ('注意' if len(paid) == 1 else '必改')
    add('回收（寫的人標的）', f'{len(paid)}：{"、".join(paid) or "—"}', '≥ 2（審稿另外分 A/B/C）', v)
    if orphan:
        add('回收對不到笑點', '、'.join(orphan), '每個回收要有同 id 的笑點', '必改')
    if paid:
        gaps = sorted(sec(min(b for b in backs[j] if b > ids[j]) - ids[j]) for j in paid)
        add('回收的間距', '、'.join(f'{g:.0f}' for g in gaps) + ' 秒', '他中位 271 秒（12 則）', 'ok')

    # voice
    hits, warn = avoid_hits(clean)
    add('avoid.md 的字串', '、'.join(hits) or '0', '0', '必改' if hits else 'ok')
    if warn:
        add('像他的字（人判斷）', '、'.join(warn), '是一般用法就留', '注意')
    nx = clean.count('沒想到')
    add('「沒想到」', f'{nx}', '最多 2', 'ok' if nx <= 2 else '注意')
    # 2026-11-22 vet_night_xray: both blind judges named 「只見」 as written Chinese he never says
    bookish = [w for w in WRITTEN if w in clean]
    add('書面語（只見、彷彿…）', '、'.join(bookish) or '0', '0', '必改' if bookish else 'ok')
    # he talks to the listeners at most 3 times, only to ask for them, to guess their curiosity or to reassure
    # (02-voice §4); a comment turned toward them (「你們身邊應該也有個這樣的朋友吧」) gave two stories away
    narr = re.sub(r'「[^」]*」', '', clean)
    # replaces a count of 各位/你一定想… that found 0 in both stories the judges caught on exactly this
    to_them = [s for s in re.split(r'[。！？\n]', narr) if re.search(r'你們|大家|各位|你一定|你可能|說到這裡', s)]
    remarks = [m.group(0) for s in to_them for m in [re.search(r'(你們|大家).{0,12}應該(也)?.{0,10}吧', s)] if m]
    add('旁白對聽眾說話', f'{len(to_them)} 次', '最多 3', 'ok' if len(to_them) <= 3 else '必改')
    if remarks:
        add('對聽眾的評論（「你們…應該也…吧」）', '、'.join(remarks), '0：只替聽眾問、預告好奇、安撫', '必改')
    # voice fingerprint against his 205 stories (references/fingerprint.json, built by voice.py)
    try:
        sys.path.insert(0, HERE)
        import voice
        for label, val, ref, verdict in voice.compare(voice.fingerprint(voice.lines_of_story(a.story))):
            add('口氣：' + label.split('（')[0].split('每')[0], val, ref, verdict)
    except FileNotFoundError:
        add('口氣指紋', '沒有 fingerprint.json', '先跑 voice.py build', '注意')
    q = re.findall(r'「([^」]*)」', clean)
    dshare = sum(len(SPOKEN.findall(x)) for x in q) / max(total, 1)
    add('台詞佔比', f'{dshare:.2f}', '0.35–0.55（他中位 0.45，p10 0.20；213 則抽取估計）', 'ok' if .3 <= dshare <= .65 else ('注意' if dshare >= .2 else '必改'))

    lines = [l.strip() for l in clean.splitlines() if l.strip() and not l.startswith('#') and not l.startswith('[')]
    if lines:
        last = len(SPOKEN.findall(lines[-1]))
        add('最後一行', f'{last} 字', '8–25 字', 'ok' if 8 <= last <= 25 else '注意')

    w = max(len(r[0]) for r in rows)
    print(f'{"規則":<{w}}  值  ／  參考  ／  判定')
    for r in rows:
        print(f'{r[0]:<{w}}  {r[1]}  ／  {r[2]}  ／  {r[3]}')
    must = sum(r[3] == '必改' for r in rows)
    note = sum(r[3] == '注意' for r in rows)
    print(f'\n必改 {must}，注意 {note}')
    sys.exit(1 if must else 0)


if __name__ == '__main__':
    main()
