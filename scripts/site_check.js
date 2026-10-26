// Monthly courtesy test of casalafonte.it. Run: node scripts/site_check.mjs [url]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
const URL_ = process.argv[2] || 'https://casalafonte.it/';
const LANGS = ['en', 'de', 'it', 'nl', 'da', 'fr'];
const problems = [], ok = [];
const check = (cond, msg) => (cond ? ok : problems).push(msg);

const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1365, height: 900 } });
const errs = [];
const LOCAL = process.env.LOCAL_ROOT;
async function local(pg) { if (!LOCAL) return; await pg.route('**/*', async r => { const u = new URL(r.request().url()); if (u.hostname !== 'casalafonte.it') return u.hostname.includes('googletagmanager') ? r.fulfill({ body: '' }) : r.continue(); let f = decodeURIComponent(u.pathname); if (f === '/') f = '/index.html'; try { const body = fs.readFileSync(path.join(LOCAL, f)); r.fulfill({ body, contentType: f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : f.endsWith('.json') ? 'application/json' : 'image/jpeg' }); } catch { r.fulfill({ status: 404, body: '' }); } }); }
await local(p);
p.on('pageerror', e => errs.push(e.message));
const res = await p.goto(URL_, { waitUntil: LOCAL ? 'load' : 'networkidle' });
check(res && res.status() === 200, `Page loads (HTTP ${res && res.status()})`);
try { await p.click('#ck-no', { timeout: 3000 }); } catch {}

for (const l of LANGS) {
  await p.click('#l-' + l);
  await p.waitForTimeout(250);
  const r = await p.evaluate(() => ({
    lang: document.documentElement.lang,
    empty: [...document.querySelectorAll('[data-i18n]')].filter(e => !e.innerHTML.trim()).map(e => e.getAttribute('data-i18n')),
  }));
  check(r.lang === l && r.empty.length === 0, `Language ${l.toUpperCase()}: ${r.empty.length ? 'missing texts ' + r.empty.join(', ') : 'all texts present'}`);
}
await p.click('#l-en');

const imgs = await p.evaluate(async () => {
  const all = [...document.images];
  for (const i of all) { i.loading = 'eager'; }
  await new Promise(r => setTimeout(r, 4000));
  return all.filter(i => !i.complete || i.naturalWidth === 0).map(i => i.getAttribute('src'));
});
check(imgs.length === 0, `Images: ${imgs.length ? 'broken ' + imgs.join(', ') : 'all load'}`);

const busy = await p.evaluate(async () => { try { const r = await fetch('busy.json?' + Date.now()); return await r.json(); } catch { return null; } });
const age = busy && busy.updated ? (Date.now() - Date.parse(busy.updated.replace(/\+00:00$/, 'Z'))) / 36e5 : 1e9;
check(age < 24, `Availability calendar: last updated ${busy ? busy.updated : 'never'} (${Math.round(age)} h ago)`);
check(await p.isVisible('#availability'), 'Availability calendar is shown');

await p.fill('#f-name', 'Site Check');
await p.fill('#f-email', 'check@example.com');
await p.fill('#f-in', '2027-06-12');
await p.fill('#f-out', '2027-06-19');
await p.fill('#f-ad', '4');
await p.fill('#f-dog', '1');
await p.click('#request button[type=submit]');
await p.waitForTimeout(500);
const q = await p.evaluate(() => ({
  shown: !document.getElementById('out').hidden,
  est: document.getElementById('est').innerText,
  quote: document.getElementById('quote').innerText,
  mail: document.getElementById('mailbtn').getAttribute('href') || '',
}));
check(q.shown && /€/.test(q.est + q.quote), `Price quote: ${q.shown ? (q.est || '').replace(/\s+/g, ' ').slice(0, 80) : 'not shown'}`);
check(/^mailto:dglaessl@gmail\.com\?/.test(q.mail) && /subject=/.test(q.mail), 'Request email link is built');
check(/75/.test(q.quote), 'Dog fee appears in the quote');

const wa = await p.evaluate(() => [...document.querySelectorAll('a.wa')].map(a => a.href));
check(wa.length >= 2 && wa.every(h => /^https:\/\/wa\.me\/1\d{10}\?text=/.test(h)), `WhatsApp links: ${wa.length}`);

await p.click('#faq-open');
await p.waitForTimeout(300);
check(await p.isVisible('#faq'), 'Questions panel opens');

const m = await b.newPage({ viewport: { width: 375, height: 700 } });
await local(m);
await m.goto(URL_, { waitUntil: LOCAL ? 'load' : 'networkidle' });
const ov = await m.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
check(!ov, 'Phone layout: no sideways scrolling');
await b.close();

check(errs.length === 0, `JavaScript errors: ${errs.length ? errs.join(' | ') : 'none'}`);

const lines = [...problems.map(s => '❌ ' + s), ...ok.map(s => '✅ ' + s)];
console.log(lines.join('\n'));
fs.writeFileSync('site-check.md', `## Site check ${new Date().toISOString().slice(0, 10)}\n\n${lines.join('\n\n')}\n`);
process.exit(problems.length ? 1 : 0);
})();
