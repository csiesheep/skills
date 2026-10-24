// 錄《生在中國》的畫面：用一個獨立的無頭 Chrome（暫存設定檔，不碰使用者的 Chrome），CDP screencast 存每一格。網址一律帶 internal=1（不進 GA、不上傳眾生簿）。
//   node record.mjs life  <out> --seed N [--extra "&period=qing_mid&sex=F"] [--mapshots]
//        照種子玩一生：按「開始這一生」、遇到抉擇停 2 秒再點自動那一項（與引擎 policy=auto 同一生），錄到結局，存分享卡 end_card.png。
//        --mapshots：另外每 0.2 秒把地圖 SVG 用 2.5 倍截一張（mapshots/），做大地圖用。副作用：screencast 會混進裁過的格子，render.py 會濾掉。
//   node record.mjs home  <out>   首頁 8 秒
//   node record.mjs cards <out> seed1,seed2,...   每個種子直接跑到結局，存分享卡（限時動態 9:16）
// 每段輸出：frames/000001.jpg…、frames.json（每格的時間）、events.json（點擊、抉擇、年齡、紀錄列的時間）。
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const PORT = 9333;
const BASE = 'https://games.csiesheep.com/china_life/';
const W = 405, H = 720, DPR = 1080 / 405;          // 1080×1920

const argv = process.argv.slice(2);
const [mode, outArg, extra] = argv;
const opt = name => { const i = argv.indexOf('--' + name); return i < 0 ? null : (argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[i + 1] : true); };
const LIFE_SEED = opt('seed'), LIFE_EXTRA = opt('extra') || '', MAPSHOTS = !!opt('mapshots');
if (mode === 'life' && !LIFE_SEED) throw new Error('life 要 --seed');
const OUT = path.resolve(outArg);
fs.mkdirSync(path.join(OUT, 'frames'), { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---------------------------------------------------------------- Chrome 與 CDP
const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'cl-rec-'));
const chrome = spawn(CHROME, [`--remote-debugging-port=${PORT}`, `--user-data-dir=${prof}`, '--headless=new',
  '--mute-audio', '--no-first-run', '--no-default-browser-check', '--hide-scrollbars', `--window-size=${W},${H}`, `--force-device-scale-factor=${DPR}`], { stdio: 'ignore' });
let ver;
for (let i = 0; i < 50 && !ver; i++) { await sleep(200); try { ver = await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json(); } catch { } }
if (!ver) throw new Error('Chrome 沒起來');
const tgt = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: 'PUT' })).json();
const ws = new WebSocket(tgt.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r, { once: true }));
let nextId = 1; const waiting = new Map(), handlers = {};
ws.addEventListener('message', ev => {
  const m = JSON.parse(ev.data);
  if (m.id && waiting.has(m.id)) { const { res, rej } = waiting.get(m.id); waiting.delete(m.id); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); }
  else if (m.method && handlers[m.method]) handlers[m.method](m.params);
});
const send = (method, params = {}) => new Promise((res, rej) => { const id = nextId++; waiting.set(id, { res, rej }); ws.send(JSON.stringify({ id, method, params })); });
// 換頁的那一瞬間 evaluate 會丟「Not attached to an active page」：等一下再試
const js = async expr => {
  for (let i = 0; ; i++) {
    try { const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true }); return r.result.value; }
    catch (e) { if (i > 40) throw e; await sleep(250); }
  }
};
let loaded = null;
handlers['Page.loadEventFired'] = () => { if (loaded) { loaded(); loaded = null; } };
const navigate = async url => { const p = new Promise(r => { loaded = r; }); await send('Page.navigate', { url }); await Promise.race([p, sleep(15000)]); await sleep(300); };

await send('Page.enable'); await send('Runtime.enable');
await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: DPR, mobile: true });
await send('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 5 });
await send('Page.addScriptToEvaluateOnNewDocument', { source: "try{localStorage.setItem('china_life.share_fmt','story')}catch(e){}" });

// ---------------------------------------------------------------- 錄影
const frames = [], events = [];
let recording = false, n = 0;
handlers['Page.screencastFrame'] = async p => {
  send('Page.screencastFrameAck', { sessionId: p.sessionId }).catch(() => { });
  if (!recording) return;
  const f = `${String(++n).padStart(6, '0')}.jpg`;
  fs.writeFileSync(path.join(OUT, 'frames', f), Buffer.from(p.data, 'base64'));
  frames.push({ f, t: p.metadata.timestamp });
};
const t0 = () => Date.now() / 1000;
const log = (type, data = {}) => { events.push({ t: t0(), type, ...data }); console.log(type, JSON.stringify(data)); };
async function startRec() { recording = true; await send('Page.startScreencast', { format: 'jpeg', quality: 88, maxWidth: 1080, maxHeight: 1920, everyNthFrame: 1 }); log('rec_start'); }
async function stopRec() { await send('Page.stopScreencast'); recording = false; log('rec_stop'); }
async function tapRole(sel, label) {
  const r = await js(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)return null;e.scrollIntoView({block:'nearest'});const b=e.getBoundingClientRect();return {x:b.x+b.width/2,y:b.y+b.height/2}})()`);
  if (!r) throw new Error(`找不到 ${sel}`);
  log('tap', { label, x: r.x, y: r.y });
  for (const type of ['mousePressed', 'mouseReleased']) await send('Input.dispatchMouseEvent', { type, x: r.x, y: r.y, button: 'left', clickCount: 1 });
}
const visible = sel => js(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e||e.hidden)return false;const b=e.getBoundingClientRect();return b.width>0&&b.height>0})()`);
async function saveEndCard(file) {
  for (let i = 0; i < 60; i++) { if (await js(`!!(document.querySelector('[data-role=end-card]')||{}).src`)) break; await sleep(250); }
  await sleep(800);   // 排名句晚到會再畫一次
  const b64 = await js(`(async()=>{const s=document.querySelector('[data-role=end-card]').src;const b=await (await fetch(s)).blob();const a=new Uint8Array(await b.arrayBuffer());let t='';for(let i=0;i<a.length;i+=8192)t+=String.fromCharCode(...a.subarray(i,i+8192));return btoa(t)})()`);
  fs.writeFileSync(file, Buffer.from(b64, 'base64'));
  return js(`window.__endCard`);
}

// 地圖特寫：錄 life 時另開一條迴圈，每 0.2 秒把 #screen-life 裡的地圖 SVG 用 2.5 倍截一張（mapshots/、mapshots.json）
let mapLoop = false; const mapShots = [];
async function startMapShots() {
  fs.mkdirSync(path.join(OUT, 'mapshots'), { recursive: true });
  mapLoop = true; let k = 0;
  (async () => {
    while (mapLoop) {
      try {
        const r = await js(`(()=>{const s=document.querySelector('#screen-life [data-role=map]')||document.querySelector('[data-role=map]');if(!s)return null;const b=s.getBoundingClientRect();return b.width>0?{x:b.x,y:b.y,w:b.width,h:b.height}:null})()`);
        if (r) {
          const t = t0();
          const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 90, clip: { x: r.x, y: r.y, width: r.w, height: r.h, scale: 2.5 } });
          const f = `${String(++k).padStart(5, '0')}.jpg`;
          fs.writeFileSync(path.join(OUT, 'mapshots', f), Buffer.from(shot.data, 'base64'));
          mapShots.push({ f, t, rect: r });
        }
      } catch (e) { }
      await sleep(200);
    }
  })();
}
const STATE = `(()=>{const q=r=>document.querySelector('[data-role='+r+']');const d=q('decision'),e=q('ending');
  const li=document.querySelector('[data-role=log] li');
  return {age:(q('age')||{}).textContent,dec:!!d&&!d.hidden,title:d&&!d.hidden?q('decision-title').textContent:'',end:!!e&&!e.hidden,
    row:li?li.textContent.trim().slice(0,60):'',rowCls:li?(li.dataset.kind||'')+' '+li.className:''}})()`;

try {
  if (mode === 'life') {
    await navigate(`${BASE}?internal=1&seed=${LIFE_SEED}${LIFE_EXTRA}&cv=v13&policy=manual&speed=normal`);
    await startRec();
    if (MAPSHOTS) await startMapShots();
    await sleep(1500);
    await tapRole('[data-role=start-button]', 'start');   // 網址有種子、沒有 autostart：先到首頁
    for (let i = 0; i < 80 && !(await visible('[data-role=begin-button]')); i++) await sleep(250);
    if (!(await visible('[data-role=begin-button]'))) throw new Error('戶帖沒出現');
    log('card_ready'); await sleep(3500);           // 戶帖填完、停一下
    // 戶帖還在動畫時第一下可能被吃掉（略過動畫）：點完確認戶帖收起來了，沒有就再點
    for (let k = 0; k < 6; k++) {
      await tapRole('[data-role=begin-button]', 'begin');
      await sleep(1500);
      if (!(await visible('[data-role=begin-button]'))) break;
      events.pop(); console.log('begin tap ignored, retry');
    }
    let last = {}, decSince = 0, lastTap = 0;
    for (let i = 0; i < 20000; i++) {
      const s = await js(STATE);
      if (s.age !== last.age) log('age', { age: s.age });
      if (s.row && s.row !== last.row) log('row', { text: s.row, cls: s.rowCls });
      // 抉擇卡：出現就計時；點完 1.5 秒後卡還在（接著又來一個抉擇），也重新計時
      if (s.dec && !decSince && (!last.dec || Date.now() - lastTap > 1500)) { log('decision', { title: s.title }); decSince = Date.now(); }
      if (s.dec && decSince && Date.now() - decSince > 2200) { await tapRole('[data-role=option][data-auto="1"]', 'option'); decSince = 0; lastTap = Date.now(); }
      if (s.end) { log('ending'); break; }
      last = s; await sleep(100);
    }
    await sleep(6000);
    log('card', await saveEndCard(path.join(OUT, 'end_card.png')));
    await stopRec();
  } else if (mode === 'home') {
    await navigate(`${BASE}?internal=1`);
    await sleep(1500); await startRec(); await sleep(8000); await stopRec();
  } else if (mode === 'cards') {
    for (const seed of extra.split(',')) {
      await navigate(`${BASE}?internal=1&seed=${seed}&cv=v13&policy=auto&speed=instant&autostart=1`);
      await sleep(1500);
      log('card', { seed, ...(await saveEndCard(path.join(OUT, `card_${seed}.png`))) });
    }
  }
} finally {
  mapLoop = false; await sleep(400);
  if (mapShots.length) fs.writeFileSync(path.join(OUT, 'mapshots.json'), JSON.stringify(mapShots));
  fs.writeFileSync(path.join(OUT, 'frames.json'), JSON.stringify(frames));
  fs.writeFileSync(path.join(OUT, 'events.json'), JSON.stringify(events, null, 1));
  ws.close(); chrome.kill();
  await sleep(500); try { fs.rmSync(prof, { recursive: true, force: true }); } catch { }
}
