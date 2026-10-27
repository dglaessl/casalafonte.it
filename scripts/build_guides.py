#!/usr/bin/env python3
"""Builds the guide pages (EN/DE/NL/IT/DA/FR) from scripts/guides_content.py and writes scripts/guides.json
(used by build_langs.js for the sitemap and by the homepage links). Run: python3 scripts/build_guides.py"""
import json, os, re, html, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from guides_content import GUIDES, UI
LANGS = ['en', 'de', 'nl', 'it', 'da', 'fr']
HREFLANG = {l: l for l in LANGS}
BASE = 'https://casalafonte.it/'
esc = lambda s: html.escape(s, quote=True)
CSS = """:root{--paper:#f5eee3;--paper-2:#ece2d2;--ink:#2e2721;--muted:#6f6357;--soft:#a08f7c;--rule:#e2d6c4;--sage:#5e6a55;--sage-ink:#fff;--sun:#b5703f;
--f-display:"Cormorant Garamond",Garamond,"Times New Roman",serif;--f-body:"EB Garamond",Garamond,Georgia,serif;--f-ui:"Figtree","Helvetica Neue",Arial,sans-serif;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--paper:#1b1a18;--paper-2:#23221f;--ink:#ece6dc;--muted:#aaa093;--soft:#857b70;--rule:#35322d;--sage:#9fae92;--sage-ink:#141612;--sun:#d89c6c;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--f-body);font-size:19px;line-height:1.6}
img{max-width:100%;display:block}a{color:inherit;text-decoration-color:var(--soft);text-underline-offset:3px}
h1,h2,h3{font-family:var(--f-display);font-weight:400;line-height:1.1;margin:0;text-wrap:balance}
.wrap{max-width:1120px;margin:0 auto;padding-left:max(24px,env(safe-area-inset-left,0px));padding-right:max(24px,env(safe-area-inset-right,0px))}
.nav{border-bottom:1px solid var(--rule)}.nav .wrap{display:flex;align-items:center;justify-content:space-between;gap:1rem;min-height:68px;flex-wrap:wrap}
.brand{font-family:var(--f-display);font-size:1.45rem;text-decoration:none}
.links{display:flex;gap:1.3rem;align-items:center;flex-wrap:wrap}.links a{text-decoration:none;font-size:.9rem}
.langs a{font-family:var(--f-ui);font-size:.68rem;letter-spacing:.1em;padding:.2rem .3rem;opacity:.7}.langs a[aria-current]{opacity:1;border-bottom:1px solid currentColor}
.book{font-family:var(--f-ui);font-size:.82rem;border:1px solid currentColor;padding:.42rem 1rem;border-radius:999px;white-space:nowrap}
@media (max-width:700px){.links .hide-s{display:none}}
.hero img{width:100%;aspect-ratio:21/8;object-fit:cover}@media (max-width:640px){.hero img{aspect-ratio:4/3}}
article{padding-block:clamp(36px,5vw,64px) clamp(48px,6vw,80px)}
.crumbs{font-family:var(--f-ui);font-size:.78rem;color:var(--muted);margin-bottom:1rem}.crumbs a{color:var(--muted)}
.label{font-family:var(--f-display);font-style:italic;font-size:1.25rem;color:var(--sun)}
h1{font-size:clamp(2.4rem,5.4vw,3.8rem);font-weight:300;margin:.3rem 0 1rem}
.lede{font-size:1.2rem;color:var(--muted);max-width:40rem}.by{font-family:var(--f-display);font-style:italic;color:var(--muted);margin-top:.8rem}
.body{max-width:42rem;margin-top:clamp(28px,4vw,44px)}
.body section{padding-block:1.3rem;border-top:1px solid var(--rule)}.body h2{font-size:1.7rem;margin-bottom:.5rem}
.body p{margin:0;color:var(--ink)}
.tips{margin-top:1.6rem;padding:1.4rem 1.6rem;background:var(--paper-2)}.tips h2{font-size:1.5rem;margin-bottom:.6rem}
.tips ul{margin:0;padding-left:1.1rem;color:var(--muted)}.tips li{margin:.3rem 0}
.small{font-size:.9rem;color:var(--muted);margin-top:1rem}
.cta{margin-top:clamp(36px,5vw,56px);display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:clamp(20px,4vw,48px);align-items:center;border-top:1px solid var(--rule);padding-top:clamp(28px,4vw,44px)}
.cta img{width:100%;aspect-ratio:3/2;object-fit:cover}.cta h2{font-size:2rem;margin-bottom:.6rem}.cta p{color:var(--muted)}
.btns{display:flex;flex-wrap:wrap;gap:.7rem;margin-top:1.1rem}
.btn{font-family:var(--f-ui);font-size:.9rem;background:var(--sage);color:var(--sage-ink);padding:.8rem 1.4rem;border-radius:999px;text-decoration:none}
.ghost{font-family:var(--f-ui);font-size:.85rem;border:1px solid var(--rule);padding:.75rem 1.2rem;border-radius:999px;text-decoration:none}
@media (max-width:760px){.cta{grid-template-columns:1fr}}
.more{margin-top:clamp(36px,5vw,56px)}.more h2{font-size:1.5rem;margin-bottom:.8rem}.more ul{list-style:none;margin:0;padding:0;display:grid;gap:.4rem}
footer{border-top:1px solid var(--rule);padding-block:2.4rem 3rem;font-size:.85rem;color:var(--muted)}footer .wrap{display:flex;flex-wrap:wrap;justify-content:space-between;gap:.6rem 2rem}"""
LINKWORDS = {'en': 'thermal springs guide', 'de': 'Ratgeber zu den Thermalquellen', 'nl': 'gids over de thermale bronnen', 'it': 'guida alle terme', 'da': 'guide til de termiske kilder', 'fr': 'guide des sources thermales'}

def url(g, l): return BASE + GUIDES[g]['slug'][l] + '/'
def page(g, l):
    G, C, U = GUIDES[g], GUIDES[g][l], UI[l]
    home = U['home']
    alts = ''.join(f'<link rel="alternate" hreflang="{HREFLANG[k]}" href="{url(g,k)}">\n' for k in LANGS) + f'<link rel="alternate" hreflang="x-default" href="{url(g,"en")}">\n'
    secs = ''
    for h, p in C['sections']:
        p = esc(p)
        lw = LINKWORDS[l]
        if g != 'thermal' and lw in p:
            p = p.replace(lw, f'<a href="/{GUIDES["thermal"]["slug"][l]}/">{lw}</a>', 1)
        secs += f'<section><h2>{esc(h)}</h2><p>{p}</p></section>\n'
    tips = ''.join(f'<li>{esc(t)}</li>' for t in C['tips'])
    langs = ''.join(f'<a href="/{GUIDES[g]["slug"][k]}/" hreflang="{k}"{" aria-current=\"page\"" if k==l else ""}>{k.upper()}</a>' for k in LANGS)
    others = ''.join(f'<li><a href="/{GUIDES[o]["slug"][l]}/">{esc(GUIDES[o][l]["h1"])}</a></li>' for o in GUIDES if o != g)
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Article", "headline": C['h1'], "description": C['desc'], "inLanguage": l, "image": BASE + G['img'].lstrip('/'),
         "author": [{"@type": "Person", "name": "Daniel Glaessl"}, {"@type": "Person", "name": "Eva Friedrich"}],
         "publisher": {"@type": "Organization", "name": "Casa La Fonte", "url": BASE}, "mainEntityOfPage": url(g, l), "dateModified": "2026-10-27"},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Casa La Fonte", "item": BASE + home.lstrip('/')},
            {"@type": "ListItem", "position": 2, "name": C['h1'], "item": url(g, l)}]}]}
    return f'''<!doctype html>
<!-- Generated by scripts/build_guides.py from scripts/guides_content.py. Do not edit. -->
<html lang="{l}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(C['title'])}</title>
<meta name="description" content="{esc(C['desc'])}">
<link rel="canonical" href="{url(g,l)}">
{alts}<meta property="og:type" content="article"><meta property="og:title" content="{esc(C['h1'])}"><meta property="og:description" content="{esc(C['desc'])}"><meta property="og:image" content="{BASE}img/house-pool.jpg"><meta property="og:url" content="{url(g,l)}">
<link rel="icon" href="/img/house-pool.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,400&family=EB+Garamond:ital,wght@0,400;0,500;1,400&family=Figtree:wght@400;500&display=swap">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>{CSS}</style>
</head>
<body>
<nav class="nav"><div class="wrap"><a class="brand" href="{home}">Casa La Fonte</a><div class="links"><a class="hide-s" href="{home}#house">{U['house']}</a><a class="hide-s" href="{home}#photos">{U['photos']}</a><a class="hide-s" href="{home}#area">{U['area']}</a><a class="hide-s" href="{home}#prices">{U['prices']}</a><span class="langs">{langs}</span><a class="book" href="{home}#request">{U['book']}</a></div></div></nav>
<div class="hero"><img src="{G['img']}" alt="{esc(G['img_alt'][l])}" width="1600" height="900"></div>
<article class="wrap">
<p class="crumbs"><a href="{home}">Casa La Fonte</a> › {esc(C['label'])}</p>
<p class="label">{esc(C['label'])}</p>
<h1>{esc(C['h1'])}</h1>
<p class="lede">{esc(C['lede'])}</p>
<p class="by">{U['by']}</p>
<div class="body">
{secs}<div class="tips"><h2>{esc(C['tips_h'])}</h2><ul>{tips}</ul></div>
<p class="small">{U['times']}</p>
</div>
<div class="cta"><img src="/img/g/37-sm.webp" alt="Casa La Fonte" loading="lazy" width="640" height="427"><div><h2>{U['cta_h']}</h2><p>{U['cta_p']}</p><div class="btns"><a class="btn" href="{home}#prices">{U['cta_a']}</a><a class="ghost" href="{home}#photos">{U['cta_b']}</a></div></div></div>
<div class="more"><h2>{U['more']}</h2><ul>{others}</ul></div>
</article>
<footer><div class="wrap"><span>{U['ft']}</span><span>WhatsApp <a href="https://wa.me/14084420689">Daniel</a> · <a href="https://wa.me/16505268148">Eva</a> · CIN IT050027C25RW27RMD</span></div></footer>
</body>
</html>
'''
index = {}
for g in GUIDES:
    for l in LANGS:
        p = os.path.join(ROOT, GUIDES[g]['slug'][l], 'index.html')
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w').write(page(g, l))
    index[g] = {l: {'path': '/' + GUIDES[g]['slug'][l] + '/', 'h1': GUIDES[g][l]['h1']} for l in LANGS}
json.dump(index, open(os.path.join(ROOT, 'scripts', 'guides.json'), 'w'), ensure_ascii=False, indent=1)
print('guides written:', len(index) * len(LANGS))
