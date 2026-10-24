// 用《生在中國》的引擎找人、看一生（不開瀏覽器，幾秒掃幾萬生）。
//   node life.mjs show <seed> <period_id> [sex F|M] [status 士|農|...]
//        印出這一生：出生、每年的抉擇（id=選項）、家人（marriage/birth/childDeath/spouseDeath/remarriage）、搬家、史事、死因。
//   node life.mjs scan --periods qing_mid,ming_late [--sex F] [--status 士] [--need footbind,flee_famine] [--min-moves 2]
//                      [--min-age 40] [--max-death-year 1945] [--n 20000] [--top 15]
//        依條件掃，分數 = 抉擇數 + 家人大事 + 搬家×3，印前 N 名（seed、時期、出生年、享年、抉擇、家人、搬家）。
//   node life.mjs periods     列出 period_id
// 注意：引擎的 city 欄位和遊戲畫面上顯示的地名不一定一樣（例：引擎南陽、畫面開封）。字幕一律用錄影裡畫面上的地名。
// 同一個 seed + period + sex + status、policy=auto 與錄影（點系統自動那一項）是同一生。
import { createLife, SPEC } from 'file:///C:/Users/sheep/code/china_life/engine/life.js';
import fs from 'node:fs';

const [cmd, ...rest] = process.argv.slice(2);
const opt = (name, def) => { const i = rest.indexOf('--' + name); return i < 0 ? def : rest[i + 1]; };

function run(seed, period_id, sex, status) {
  const args = { seed, period_id, policy: 'auto', consistency: 'v13', birthCap: SPEC.birthCap };
  if (sex) args.sex = sex;
  if (status) args.status = status;
  const g = createLife(args);
  const years = [];
  while (!g.done) {
    const y = g.step(); const h = y?.happened || {};
    const parts = [];
    for (const c of h.choices || []) parts.push({ k: 'C', v: `${c.id}=${c.choice}` });
    for (const f of h.family || []) parts.push({ k: 'F', v: f.kind || f.type });
    for (const m of h.moves || []) parts.push({ k: 'M', v: `${m.from}>${m.to}(${m.reason})${m.city || ''}` });
    for (const e of h.events || []) parts.push({ k: 'E', v: String(e.name || e.title || e.id || '') });
    if (parts.length) years.push({ age: y.year.age, year: y.year.year, parts });
  }
  return { r: g.result(), years };
}

if (cmd === 'periods') {
  const csv = fs.readFileSync('C:/Users/sheep/code/china_life/data/periods.csv', 'utf8').split('\n').slice(1);
  console.log(csv.map(l => l.split(',').slice(0, 2).join(' ')).filter(Boolean).join('\n'));
} else if (cmd === 'show') {
  const [seed, period, sex, status] = rest;
  const { r, years } = run(+seed, period, sex, status);
  console.log(`${seed} ${period} ${r.period} 生於 ${r.birth_year} ${r.sex} ${r.status} 享年 ${r.death_age}（${r.death_year}）${r.death_cause}`);
  for (const y of years) console.log(`${String(y.age).padStart(3)} ${y.year}  ${y.parts.map(p => p.k + ':' + p.v).join('  ')}`);
} else if (cmd === 'scan') {
  const periods = opt('periods', 'qing_mid').split(','), sex = opt('sex'), status = opt('status');
  const need = (opt('need', '') || '').split(',').filter(Boolean);
  const minMoves = +opt('min-moves', 0), minAge = +opt('min-age', 35), maxDeath = +opt('max-death-year', 9999);
  const n = +opt('n', 20000), top = +opt('top', 15);
  const out = [];
  for (let i = 0; i < n; i++) {
    const period = periods[i % periods.length], seed = 3100001 + i * 7919;
    let res; try { res = run(seed, period, sex, status); } catch (e) { continue; }
    const { r, years } = res;
    const parts = years.flatMap(y => y.parts.map(p => ({ ...p, age: y.age })));
    const ids = parts.filter(p => p.k === 'C').map(p => p.v.split('=')[0]);
    const moves = parts.filter(p => p.k === 'M').length;
    if (r.death_age < minAge || r.death_year > maxDeath || moves < minMoves || !need.every(x => ids.includes(x))) continue;
    const fam = parts.filter(p => p.k === 'F' && p.v !== 'birth').length;
    out.push([ids.length + fam + moves * 3, `${seed} ${period} ${r.birth_year} ${r.sex} ${r.status} 享年${r.death_age} ${r.death_cause} | ` +
      parts.filter(p => p.k !== 'E').map(p => `${p.age}:${p.v}`).join(' ')]);
  }
  out.sort((a, b) => b[0] - a[0]);
  console.log(`${out.length} 生符合`);
  console.log(out.slice(0, top).map(x => x[1]).join('\n'));
} else {
  console.log(fs.readFileSync(new URL(import.meta.url), 'utf8').split('\n').filter(l => l.startsWith('//')).join('\n'));
}
