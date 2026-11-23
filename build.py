"""content/*.md（記事）と pages/*.md（固定ページ）から静的サイト docs/ を作る。標準ライブラリだけで動く。

使い方:
  python build.py                      本番ビルド（下書き・未来日付・未記入の記事は除外）
  $env:INCLUDE_DRAFTS=1; python build.py   下書きも含めて確認用にビルド

記事の先頭のメタ情報:
---
title: タイトル
date: 2026-11-21          （未来の日付は、その日まで公開されない＝予約公開）
description: 一行説明（検索結果やSNSに出る）
emoji: 🍰                 （一覧カードのアイコン。任意）
pr: true                  （アフィリエイトリンクを含むとき。冒頭にPR表記が出る）
draft: true               （true の間は公開されない）
---
"""
import html
import os
import re
import shutil
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent
POSTS_SRC = ROOT / "content"
PAGES_SRC = ROOT / "pages"
OUT = ROOT / "docs"

SITE_URL = os.environ.get("SITE_URL", "https://example.invalid/choiraku-note").rstrip("/")  # 公開時は Actions が自動で設定。独自ドメインにしたら環境変数かここを変える
BASE_PATH = urlparse(SITE_URL).path  # 例: /choiraku-note（独自ドメインなら空）
SITE_NAME = "ちょいラク帳"
SITE_TAGLINE = "パソコンとAIで、毎日の面倒をちょっとラクにする。"
SITE_DESC = "ファイル整理、文章づくり、AIへの頼み方。手順を確かめながら、今日からできる小さな時短を書いています。"
AUTHOR = "ラク田"
AUTHOR_BIO = "頑張らずに続く時短が好きな会社員。手順を実際に動かして確かめてから書いています。"
PLACEHOLDER = re.compile(r"【(体験メモ|要確認)")
JST = timezone(timedelta(hours=9))
INCLUDE_DRAFTS = bool(os.environ.get("INCLUDE_DRAFTS"))


# ---------- 読み込み ----------
def parse(path):
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    meta, body = {}, text
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = m.group(2)
    return meta, body


def is_true(v):
    return str(v).lower() == "true"


def publish_status(meta, body):
    """公開してよければ None、ダメなら理由を返す。"""
    if INCLUDE_DRAFTS:
        return None
    if is_true(meta.get("draft")):
        return "下書き"
    try:
        d = datetime.strptime(meta.get("date", ""), "%Y-%m-%d").date()
    except ValueError:
        return "date の形式が不正"
    if d > datetime.now(JST).date():
        return f"予約（{d} 公開）"
    if PLACEHOLDER.search(body):
        return "未記入の【体験メモ】【要確認】が残っている"
    return None


# ---------- Markdown（必要な分だけ） ----------
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)

    def link(m):
        text, url = m.group(1), html.unescape(m.group(2))
        ext = url.startswith("http")
        attrs = ' target="_blank" rel="noopener sponsored"' if ext and is_affiliate(url) else (
            ' target="_blank" rel="noopener"' if ext else "")
        return f'<a href="{html.escape(url)}"{attrs}>{text}</a>'

    s = re.sub(r"\[(.+?)\]\((https?://[^)\s]+|[\w./#-]+\.html(?:#[\w-]+)?)\)", link, s)
    s = re.sub(r"(【(?:体験メモ|要確認).*?】)", r'<mark class="todo">\1</mark>', s)
    return s


AFFILIATE_HOSTS = ("amzn.to", "amazon.co.jp", "rakuten", "moshimo", "a8.net", "valuecommerce", "afl.")


def is_affiliate(url):
    return any(h in url for h in AFFILIATE_HOSTS)


LANG_LABEL = {"powershell": "PowerShell", "ps1": "PowerShell", "python": "Python", "bash": "シェル", "text": "そのまま貼る"}


def md_to_html(body):
    out, para, items, kind, quote = [], [], [], None, []
    headings = []

    def flush():
        nonlocal para, items, kind, quote
        if para:
            out.append("<p>" + "".join(inline(p) for p in para) + "</p>")
            para = []
        if items:
            lis = []
            for i in items:
                box = re.match(r"\[( |x)\] (.*)", i)
                if box:
                    mark = "☑" if box.group(1) == "x" else "☐"
                    lis.append(f'<li class="check">{mark} {inline(box.group(2))}</li>')
                else:
                    lis.append(f"<li>{inline(i)}</li>")
            out.append(f"<{kind}>" + "".join(lis) + f"</{kind}>")
            items, kind = [], None
        if quote:
            out.append('<div class="note">' + "<br>".join(inline(q) for q in quote) + "</div>")
            quote = []

    code, lang = None, ""  # コードブロック（```）の行を貯める。空行も保つ
    for line in body.splitlines():
        s = line.rstrip()
        if code is not None:
            if s.startswith("```"):
                label = LANG_LABEL.get(lang.lower(), "そのまま貼る" if not lang else lang)
                out.append(f'<figure class="code"><figcaption><span class="lang">{esc(label)}</span>'
                           f'<button type="button" class="copy" hidden>コピー</button></figcaption>'
                           f'<pre><code>{html.escape(chr(10).join(code), quote=False)}</code></pre></figure>')
                code = None
            else:
                code.append(line)
            continue
        if s.startswith("```"):
            flush()
            code, lang = [], s[3:].strip()
            continue
        if not s.strip():
            flush()
            continue
        m_ol = re.match(r"\d+\. (.*)", s)
        if s.startswith("## ") or s.startswith("### "):
            flush()
            level = 2 if s.startswith("## ") else 3
            text = s[level + 1:]
            hid = f"h{len(headings) + 1}"
            if level == 2:
                headings.append((hid, text))
            out.append(f'<h{level} id="{hid}">{inline(text)}</h{level}>')
        elif s.startswith("- "):
            if kind != "ul":
                flush()
                kind = "ul"
            items.append(s[2:])
        elif m_ol:
            if kind != "ol":
                flush()
                kind = "ol"
            items.append(m_ol.group(1))
        elif s.startswith("> ") or s == ">":
            if para or items:
                flush()
            quote.append(s[2:])
        else:
            if items or quote:
                flush()
            para.append(s.strip())
    flush()
    return "\n".join(out), headings


# ---------- HTML ----------
def esc(s):
    return html.escape(s, quote=True)


def layout(*, title, desc, inner, prefix, url, og_type="website", full_title=None, nav_here=""):
    full = full_title or f"{title}｜{SITE_NAME}"
    mark = ('<svg class="mark" viewBox="0 0 28 28" aria-hidden="true"><rect width="28" height="28" rx="8" fill="var(--signal)"/>'
            '<path d="M7.5 14.5l4.2 4.2L20.5 9.6" fill="none" stroke="#111827" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    def nav_a(href, label, key):
        cur = ' aria-current="page"' if nav_here == key else ""
        return f'<a href="{prefix}{href}"{cur}>{label}</a>'
    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(url)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{esc(url)}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta name="twitter:card" content="summary">
<meta name="color-scheme" content="light dark">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{prefix}feed.xml">
<script>try{{var t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
<link rel="stylesheet" href="{prefix}style.css">
<script src="{prefix}site.js" defer></script></head>
<body>
<a class="skip" href="#main">本文へ移動</a>
<div class="progress" aria-hidden="true"></div>
<header class="site"><div class="bar">
<a class="brand" href="{prefix}index.html">{mark}<span>{SITE_NAME}</span></a>
<nav aria-label="サイト内">{nav_a("index.html", "記事", "home")}{nav_a("about.html", "運営者", "about")}
<button type="button" class="theme" aria-label="表示の明るさを切り替える" hidden><span aria-hidden="true">◐</span></button></nav>
</div></header>
<main id="main">{inner}</main>
<footer class="site"><div class="bar foot">
<div><p class="brand-s">{SITE_NAME}</p><p class="muted">{SITE_TAGLINE}</p></div>
<nav aria-label="フッター"><a href="{prefix}about.html">運営者情報</a><a href="{prefix}privacy.html">プライバシーポリシー・免責事項</a><a href="{prefix}contact.html">お問い合わせ</a><a href="{prefix}feed.xml">RSS</a></nav>
<p class="small muted">© {datetime.now(JST).year} {SITE_NAME}</p>
</div></footer>
</body></html>"""


def verified_chip(p):
    if p["verified"]:
        return '<span class="chip ok"><i aria-hidden="true">✓</i>動かして確認済み</span>'
    return '<span class="chip warn"><i aria-hidden="true">!</i>画面では未確認</span>'


def row(p, prefix):
    no = re.match(r"(\d+)", p["slug"])
    num = no.group(1)[-2:].zfill(2) if no else "--"
    chips = (f'<span class="chip kind">{esc(p["kind"])}</span>'
             f'<span class="chip">所要 {esc(p["time"])}</span>{verified_chip(p)}')
    return (f'<a class="row" data-kind="{esc(p["kind"])}" href="{prefix}posts/{p["slug"]}.html">'
            f'<span class="no" aria-hidden="true">{num}</span>'
            f'<span class="main"><span class="rt">{esc(p["title"])}</span>'
            f'<span class="rd">{esc(p["desc"])}</span><span class="chips">{chips}</span></span>'
            f'<span class="go" aria-hidden="true">→</span></a>')


def build_post(p, all_posts):
    toc_items = "".join(f'<li><a href="#{hid}">{inline(t)}</a></li>' for hid, t in p["headings"])
    toc_side = f'<aside class="toc-side"><nav class="toc" aria-label="目次"><p>この記事の流れ</p><ol>{toc_items}</ol></nav></aside>' if len(p["headings"]) >= 3 else ""
    toc_m = f'<details class="toc-m"><summary>目次を開く</summary><ol>{toc_items}</ol></details>' if len(p["headings"]) >= 3 else ""
    pr = '<p class="pr">この記事にはPR（広告）を含みます。</p>' if p["pr"] else ""
    draft = '<p class="draft">下書きプレビュー（公開されていません）</p>' if p["status_note"] else ""
    others = [o for o in all_posts if o["slug"] != p["slug"]][:3]
    related = ""
    if others:
        related = '<section class="related"><h2>次に読むなら</h2><div class="rows">' + "".join(row(o, "../") for o in others) + "</div></section>"
    note = f'<p class="vnote">{esc(p["verified_note"])}</p>' if p["verified_note"] else ""
    facts = (f'<dl class="facts"><div><dt>所要時間</dt><dd>{esc(p["time"])}</dd></div>'
             f'<div><dt>むずかしさ</dt><dd>{esc(p["level"])}</dd></div>'
             f'<div><dt>環境</dt><dd>{esc(p["env"])}</dd></div>'
             f'<div><dt>確認状況</dt><dd>{verified_chip(p)}</dd></div></dl>')
    inner = f"""{draft}<div class="post-grid">
<article class="post">
<header class="post-head">
<p class="eyebrow"><span class="chip kind">{esc(p["kind"])}</span><time datetime="{p["date"]}">{p["date"]}</time><span>読むのに約{p["minutes"]}分</span></p>
<h1>{esc(p["title"])}</h1>
<p class="lede">{esc(p["desc"])}</p>{pr}
{facts}{note}{toc_m}
</header>
<div class="content">{p["html"]}</div>
<aside class="author"><span class="avatar" aria-hidden="true">ラ</span><div><p class="name">{AUTHOR}</p><p>{AUTHOR_BIO}</p></div></aside>
</article>
{toc_side}
</div>
{related}"""
    return layout(title=p["title"], desc=p["desc"], inner=inner, prefix="../",
                  url=f"{SITE_URL}/posts/{p['slug']}.html", og_type="article")


def build_home(posts):
    kinds = []
    for p in posts:
        if p["kind"] not in kinds:
            kinds.append(p["kind"])
    chips = '<button type="button" class="filter" aria-pressed="true" data-kind="">すべて</button>' + "".join(
        f'<button type="button" class="filter" aria-pressed="false" data-kind="{esc(k)}">{esc(k)}</button>' for k in kinds)
    rows = "".join(row(p, "") for p in posts) or '<p class="empty">最初の記事を準備中です。もう少しお待ちください。</p>'
    return f"""<section class="hero"><div class="bar">
<p class="eyebrow"><span class="chip kind">手順ノート</span><span>パソコンとAIの小さな時短</span></p>
<h1>面倒な作業を、<br class="sp">5分で終わらせる。</h1>
<p class="lede">{SITE_DESC}</p>
<ul class="promise">
<li><b>先に予定を見る</b><span>いきなり実行せず、結果をプレビューしてから動かします。</span></li>
<li><b>あとで戻せる</b><span>間違えても元に戻す手順を、必ずセットで書きます。</span></li>
<li><b>確かめた範囲を書く</b><span>動かして確認した所と、未確認の所を分けて示します。</span></li>
</ul></div></section>
<section class="list"><div class="bar">
<div class="list-head"><h2>記事</h2><div class="filters" role="group" aria-label="種類で絞り込む" hidden>{chips}</div></div>
<div class="rows" id="rows">{rows}</div>
<p class="none" hidden>この種類の記事は、まだありません。</p>
</div></section>"""


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "posts").mkdir(parents=True)
    shutil.copy(ROOT / "style.css", OUT / "style.css")
    shutil.copy(ROOT / "site.js", OUT / "site.js")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    posts = []
    for path in sorted(POSTS_SRC.glob("*.md")):
        meta, body = parse(path)
        reason = publish_status(meta, body)
        if reason:
            print(f"  非公開: {path.name}（{reason}）")
            continue
        content_html, headings = md_to_html(body)
        plain = re.sub(r"<[^>]+>", "", content_html)
        posts.append({
            "slug": path.stem,
            "title": meta.get("title", path.stem),
            "date": meta.get("date", ""),
            "desc": meta.get("description", ""),
            "kind": meta.get("kind", "手順"),
            "time": meta.get("time", "10分"),
            "level": meta.get("level", "やさしい"),
            "env": meta.get("env", "Windows 11"),
            "verified": is_true(meta.get("verified")),
            "verified_note": meta.get("verified_note", ""),
            "pr": is_true(meta.get("pr")),
            "status_note": is_true(meta.get("draft")),
            "html": content_html,
            "headings": headings,
            "minutes": max(1, round(len(plain) / 500)),
        })
    posts.sort(key=lambda p: p["date"], reverse=True)

    for p in posts:
        (OUT / "posts" / f"{p['slug']}.html").write_text(build_post(p, posts), encoding="utf-8")

    hero = build_home(posts)
    (OUT / "index.html").write_text(
        layout(title=SITE_NAME, desc=SITE_DESC, inner=hero, prefix="", url=f"{SITE_URL}/",
               full_title=f"{SITE_NAME}｜{SITE_TAGLINE}", nav_here="home"), encoding="utf-8")

    pages = []
    for path in sorted(PAGES_SRC.glob("*.md")):
        meta, body = parse(path)
        content_html, _ = md_to_html(body)
        title = meta.get("title", path.stem)
        inner = f'<article class="page"><h1>{esc(title)}</h1><div class="content">{content_html}</div></article>'
        (OUT / f"{path.stem}.html").write_text(
            layout(title=title, desc=meta.get("description", SITE_DESC), inner=inner, prefix="",
                   url=f"{SITE_URL}/{path.stem}.html", nav_here=path.stem), encoding="utf-8")
        pages.append(path.stem)

    nf = f'<article class="page"><h1>ページが見つかりません</h1><p>URLが変わったか、削除された可能性があります。</p><p><a href="{BASE_PATH}/index.html">トップへ戻る</a></p></article>'
    (OUT / "404.html").write_text(layout(title="ページが見つかりません", desc=SITE_DESC, inner=nf,
                                         prefix=f"{BASE_PATH}/", url=f"{SITE_URL}/404.html"), encoding="utf-8")

    # sitemap / RSS / robots
    urls = [f"{SITE_URL}/"] + [f"{SITE_URL}/posts/{p['slug']}.html" for p in posts] + [f"{SITE_URL}/{s}.html" for s in pages]
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"<url><loc>{esc(u)}</loc></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    items = ""
    for p in posts[:20]:
        d = datetime.strptime(p["date"], "%Y-%m-%d").replace(hour=6, tzinfo=JST)
        u = f"{SITE_URL}/posts/{p['slug']}.html"
        items += (f"<item><title>{esc(p['title'])}</title><link>{u}</link><guid>{u}</guid>"
                  f"<pubDate>{format_datetime(d)}</pubDate><description>{esc(p['desc'])}</description></item>\n")
    (OUT / "feed.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{SITE_NAME}</title>'
        f"<link>{SITE_URL}/</link><description>{esc(SITE_DESC)}</description><language>ja</language>\n{items}</channel></rss>\n",
        encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")

    print(f"記事 {len(posts)} 本・固定ページ {len(pages)} 枚を docs/ に出力しました"
          + ("（下書き込みプレビュー）" if INCLUDE_DRAFTS else ""))


if __name__ == "__main__":
    main()
