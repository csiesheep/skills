"""Check a v3 screenplay's header (length, narration, lines, speaking parts, biggest picture, joke table)
against the 說書吐槽 rules in references/voice.md.

Usage: python style_check.py <screenplay.md> [--length 2:50]
Prints one row per rule: value, reference, and 必改 / 注意 / ok. Exit code 1 if any 必改.
It reads only the header the writer filled in; the reviewer's independent joke count is the cross-check.
"""
import re, sys, argparse

TYPES = {'吐槽角色', '旁白吐槽', '自嘲', '日常荒謬', '鬼的人性反應', '其他'}


def secs(t):
    t = t.strip()
    m = re.match(r'^(\d+):(\d{1,2})(?:\.\d+)?$', t)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m = re.match(r'^(\d+(?:\.\d+)?)\s*秒?$', t)
    return float(m.group(1)) if m else None


def field(text, key):
    m = re.search(r'\*\*' + key + r'\*\*[：:]\s*([^\n]+)', text)
    return m.group(1).strip() if m else None


def parse(text):
    h = {}
    h['length'] = secs(field(text, '長度') or '') if field(text, '長度') else None
    v = field(text, '旁白')
    h['narr'] = int(re.search(r'\d+', v).group()) if v and re.search(r'\d+', v) else None
    v = field(text, '台詞')
    h['lines'] = float(re.search(r'\d+(?:\.\d+)?', v).group()) if v and re.search(r'\d', v) else None
    v = field(text, '開口角色')
    if v:
        n = re.findall(r'\d+', v)
        h['roles'] = int(n[0]) if n else None
        h['voice_only'] = int(n[1]) if len(n) > 1 else 0
    else:
        h['roles'] = None; h['voice_only'] = 0
    v = field(text, '最大畫面')
    h['peak'] = secs(v) if v else None
    jokes = []
    m = re.search(r'\*\*笑點\*\*[：:]\s*\n((?:\s*\|[^\n]*\n?)+)', text)
    if m:
        for row in m.group(1).strip().split('\n'):
            cells = [c.strip() for c in row.strip().strip('|').split('|')]
            if len(cells) < 5 or cells[0] in ('秒',) or set(cells[0]) <= set('-: '):
                continue
            s = secs(cells[0])
            if s is None:
                continue
            pay = cells[4]
            ps = None
            pm = re.match(r'^(\d+:\d{1,2})', pay)
            if pm:
                ps = secs(pm.group(1))
            jokes.append(dict(s=s, type=cells[1], who=cells[2], line=cells[3], payoff=pay, payoff_s=ps))
    h['jokes'] = sorted(jokes, key=lambda j: j['s'])
    return h


def mmss(s):
    return '—' if s is None else f'{int(s)//60}:{int(s)%60:02d}'


def check(h, L):
    rows = []
    def add(rule, value, ref, level):
        rows.append((rule, value, ref, level))
    J = h['jokes']; pk = h['peak']
    scale = L / 172.0
    # header presence
    for k, name in (('narr', '旁白'), ('lines', '台詞'), ('peak', '最大畫面'), ('roles', '開口角色')):
        if h[k] is None:
            add(f'表頭有「{name}」', '缺', '必填', '必改')
    # length
    if h['length'] is not None:
        add('長度', mmss(h['length']), '2:45–2:52，不超過 2:59',
            '必改' if h['length'] > 179 else ('注意' if not 165 <= h['length'] <= 172 and L == 172 else 'ok'))
    # speech budgets
    if h['narr'] is not None:
        lo, hi = round(200 * scale), round(240 * scale)
        add('旁白字數', h['narr'], f'{lo}–{hi}', 'ok' if lo <= h['narr'] <= hi else ('必改' if h['narr'] > hi * 1.15 else '注意'))
    if h['lines'] is not None:
        lo, hi = round(40 * scale), round(50 * scale)
        add('台詞秒數', h['lines'], f'{lo}–{hi}', 'ok' if lo <= h['lines'] <= hi else '注意')
    if h['roles'] is not None:
        add('開口角色', f"{h['roles']}（只出聲 {h['voice_only']}）", '最多 4，第 4 個只出聲',
            '必改' if h['roles'] > 4 or (h['roles'] == 4 and h['voice_only'] < 1) else 'ok')
    if pk is not None:
        add('最大畫面', mmss(pk), f'{mmss(105*scale)}–{mmss(135*scale)}', 'ok' if 105 * scale - 3 <= pk <= 135 * scale + 3 else '注意')
    # jokes
    n = len(J)
    lo, hi = max(1, round(3 * scale)), max(2, round(4 * scale))
    add('笑點數', n, f'{lo}–{hi}（那個頻道 4 分鐘以下每分鐘約 1.3 個）',
        'ok' if lo <= n <= hi else ('必改' if n < max(1, lo - 1) or n > hi + 2 else '注意'))
    bad = [j['type'] for j in J if j['type'] not in TYPES]
    if bad:
        add('笑點類型', '、'.join(bad), '、'.join(sorted(TYPES)), '注意')
    if not J:
        return rows
    first = J[0]['s']
    add('第一個笑點', mmss(first), f'{mmss(10*scale)}–{mmss(25*scale)}（那個頻道在片長約 9% 處）',
        'ok' if 10 * scale - 3 <= first <= 25 * scale + 5 else '注意')
    front = sum(j['s'] <= 0.4 * L for j in J) / n
    add('前 40% 的笑點比例', f'{front:.0%}', '一半以上（那個頻道約 62%）', 'ok' if front >= 0.5 else '注意')
    if pk is not None:
        near = [mmss(j['s']) for j in J if abs(j['s'] - pk) <= 5]
        add('最大畫面 ±5 秒內的笑點', '、'.join(near) or '沒有', '沒有（那個頻道只有 3%）', '必改' if near else 'ok')
        before = [j['s'] for j in J if j['s'] < pk - 5]
        if before:
            gap = pk - max(before)
            need = 25 * scale
            add('最後一個驚嚇前笑點離最大畫面', f'{gap:.0f} 秒', f'至少 {need:.0f} 秒（那個頻道約 15% 片長）',
                'ok' if gap >= need else ('必改' if gap < 10 else '注意'))
        after = [j for j in J if j['s'] > pk + 5]
        add('最大畫面後的笑點', len(after), '最多 1 個，只能是一句抱怨',
            'ok' if len(after) <= 1 and all(j['type'] != '鬼的人性反應' for j in after) else '必改')
        if L - pk > 0:
            tail = [j for j in J if j['s'] >= L - 5]
            if tail:
                add('結尾 5 秒內的笑點', mmss(tail[-1]['s']), '不准用笑點收尾', '必改')
    gr = [j for j in J if j['type'] == '鬼的人性反應']
    if gr:
        ok = len(gr) <= 1 and (pk is None or all(j['s'] > pk for j in gr))
        add('鬼的人性反應', len(gr), '最多 1 個，只在驚嚇後', 'ok' if ok else '必改')
    two = [j for j in J if j['type'] == '吐槽角色']
    add('兩個活人之間的吐槽', len(two), '至少 1 個', 'ok' if two else '注意')
    cb = [j for j in J if j['payoff'] and j['payoff'] not in ('—', '-', '－', '無', '')]
    cb_ok = [j for j in cb if j['payoff_s'] is not None and j['payoff_s'] > j['s']]
    add('有回收的笑點', f'{len(cb_ok)}／{n}', '至少 1 個，回收要寫秒數和是什麼（那個頻道 78% 的故事有）',
        'ok' if cb_ok else '必改')
    for j in cb:
        if j['payoff_s'] is None or j['payoff_s'] <= j['s']:
            add(f"{mmss(j['s'])} 的回收", j['payoff'][:20], '回收欄以「m:ss」開頭，且晚於笑點', '注意')
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('screenplay')
    ap.add_argument('--length', help='target length m:ss (default: the header, else 2:52)')
    a = ap.parse_args()
    text = open(a.screenplay, encoding='utf-8').read()
    h = parse(text)
    # budgets scale with the target length; a header over 2:59 is an error, not a new target
    L = secs(a.length) if a.length else (h['length'] if h['length'] and h['length'] <= 179 else 172)
    rows = check(h, L)
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    print(f'style_check  {a.screenplay}  長度 {mmss(L)}  笑點 {len(h["jokes"])} 個\n')
    print('| 規則 | 稿子 | 參考 | 判定 |')
    print('|---|---|---|---|')
    for r in rows:
        print('| ' + ' | '.join(str(x) for x in r) + ' |')
    nb = sum(r[3] == '必改' for r in rows); nw = sum(r[3] == '注意' for r in rows)
    print(f'\n必改 {nb}、注意 {nw}')
    sys.exit(1 if nb else 0)


if __name__ == '__main__':
    main()
