import os
import sys
import re
import json
import time
import hashlib
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
ARTICLES_DIR = BASE_DIR / "articles"
IMAGES_DIR = BASE_DIR / "images"
RAW_JSON_DIR = BASE_DIR / "raw_json"
PROFILE_DIR = BASE_DIR / ".browser_profile"

CIRCLE_KEY = "28b13634316e"
MAGAZINE_KEY = "m125fc4524aca"
TEST_NOTE_KEY = "n19898395d501"  # Latest membership note to verify membership access


def sanitize_filename(name: str, max_len: int = 60) -> str:
    # Remove Windows invalid filename characters
    cleaned = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", name).strip(" ._")
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip(" ._")
    return cleaned or "untitled"


def get_ext_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lower()
    for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]:
        if path.endswith(ext):
            return ext
    # Check query param format=jpeg etc.
    qs = urllib.parse.parse_qs(parsed.query)
    fmt = qs.get("format", [""])[0].lower()
    if fmt in ["jpeg", "jpg"]:
        return ".jpg"
    if fmt in ["png", "gif", "webp"]:
        return f".{fmt}"
    return ".jpg"


def download_image(url: str, dest_path: Path, cookie_header: str) -> bool:
    if dest_path.exists() and dest_path.stat().st_size > 0:
        return True
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Referer": "https://note.com/",
    }
    if cookie_header and "note.com" in url:
        headers["Cookie"] = cookie_header
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
                if data:
                    dest_path.write_bytes(data)
                    return True
        except Exception as e:
            if attempt == 2:
                print(f"  [WARN] Failed to download image {url}: {e}")
            time.sleep(0.5 * (attempt + 1))
    return False


def fetch_json_with_cookies(url: str, cookie_header: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://note.com/kenhori2/membership",
        "X-Requested-With": "XMLHttpRequest",
    }
    if cookie_header:
        headers["Cookie"] = cookie_header
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(1.0 * (attempt + 1))
    return {}


def process_article_html(note_data: dict, cookie_header: str, prev_link: str = None, next_link: str = None) -> tuple[str, list[tuple[str, Path]]]:
    key = note_data.get("key", "")
    title = note_data.get("name", "無題")
    publish_at = (note_data.get("publish_at") or note_data.get("created_at") or "")[:10]
    publish_full = (note_data.get("publish_at") or note_data.get("created_at") or "")[:16].replace("T", " ")
    body_html = note_data.get("body") or ""
    eyecatch_url = note_data.get("eyecatch")
    note_url = note_data.get("note_url") or f"https://note.com/kenhori2/n/{key}"
    can_read = note_data.get("can_read", False)
    remained_char = note_data.get("remained_char_num", 0) or 0
    like_count = note_data.get("like_count", 0)

    image_tasks = []  # list of (url, dest_path)
    note_img_dir = IMAGES_DIR / key

    # 1. Eyecatch image
    eyecatch_html = ""
    if eyecatch_url:
        ext = get_ext_from_url(eyecatch_url)
        eyecatch_filename = f"eyecatch{ext}"
        eyecatch_dest = note_img_dir / eyecatch_filename
        image_tasks.append((eyecatch_url, eyecatch_dest))
        eyecatch_rel = f"../images/{key}/{eyecatch_filename}"
        eyecatch_html = f'<div class="eyecatch"><img src="{eyecatch_rel}" alt="アイキャッチ画像"></div>'

    # 2. Embedded contents replacement (YouTube, Twitter, external cards, etc.)
    embedded_list = note_data.get("embedded_contents") or []
    embed_map = {}
    for emb in embedded_list:
        emb_key = emb.get("key")
        if emb_key:
            embed_html = emb.get("html_for_embed") or emb.get("html_for_display") or ""
            emb_url = emb.get("url") or ""
            if not embed_html and emb_url:
                embed_html = f'<div class="embed-link"><a href="{emb_url}" target="_blank" rel="noopener">{emb_url}</a></div>'
            elif emb_url:
                embed_html = f'<div class="embed-container">{embed_html}<div class="embed-source"><a href="{emb_url}" target="_blank" rel="noopener">{emb_url}</a></div></div>'
            embed_map[emb_key] = embed_html

    def replace_embed_figure(match):
        full_tag = match.group(0)
        m_key = re.search(r'embedded-content-key=["\']([^"\']+)["\']', full_tag)
        m_src = re.search(r'data-src=["\']([^"\']+)["\']', full_tag)
        if m_key and m_key.group(1) in embed_map:
            return embed_map[m_key.group(1)]
        if m_src:
            src_url = m_src.group(1)
            return f'<div class="embed-link"><a href="{src_url}" target="_blank" rel="noopener">{src_url}</a></div>'
        return full_tag

    body_html = re.sub(
        r'<figure[^>]*embedded-content-key=[^>]*>.*?</figure>',
        replace_embed_figure,
        body_html,
        flags=re.DOTALL,
    )

    # 3. Download and rewrite <img> tags in body_html
    img_counter = [0]

    def replace_img_src(match):
        prefix = match.group(1)
        img_url = match.group(2)
        suffix = match.group(3)
        if not img_url.startswith("http"):
            return match.group(0)
        img_counter[0] += 1
        ext = get_ext_from_url(img_url)
        url_hash = hashlib.md5(img_url.encode("utf-8")).hexdigest()[:8]
        filename = f"img_{img_counter[0]:03d}_{url_hash}{ext}"
        dest = note_img_dir / filename
        image_tasks.append((img_url, dest))
        rel_path = f"../images/{key}/{filename}"
        return f'{prefix}{rel_path}{suffix}'

    body_html = re.sub(
        r'(<img[^>]+src=["\'])([^"\']+)(["\'])',
        replace_img_src,
        body_html,
    )

    # Hashtags
    hashtags = []
    for ht in note_data.get("hashtag_notes") or []:
        tag_name = (ht.get("hashtag") or {}).get("name")
        if tag_name:
            hashtags.append(tag_name)
    tags_html = ""
    if hashtags:
        tags_spans = "".join(f'<span class="tag">{t}</span>' for t in hashtags)
        tags_html = f'<div class="tags">{tags_spans}</div>'

    # Notice if paywalled / truncated
    paywall_notice = ""
    if remained_char > 0 and not can_read:
        paywall_notice = f"""
        <div class="paywall-warning">
            <strong>※この記事は残り {remained_char:,} 文字が有料またはプラン対象外のため未取得です。</strong><br>
            <a href="{note_url}" target="_blank" rel="noopener">noteで元記事を開く</a>
        </div>
        """

    nav_prev = f'<a class="nav-btn" href="{prev_link}">← 前の記事</a>' if prev_link else '<span></span>'
    nav_next = f'<a class="nav-btn" href="{next_link}">次の記事 →</a>' if next_link else '<span></span>'

    html_doc = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | 堀元 見 noteアーカイブ</title>
    <style>
        :root {{
            --bg: #f8f9fa;
            --card-bg: #ffffff;
            --text: #222222;
            --muted: #666666;
            --border: #e5e7eb;
            --accent: #2cb696;
            --link: #0066cc;
            --quote-bg: #f3f4f6;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg: #121212;
                --card-bg: #1e1e1e;
                --text: #e5e7eb;
                --muted: #9ca3af;
                --border: #374151;
                --accent: #2cb696;
                --link: #60a5fa;
                --quote-bg: #262626;
            }}
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 0;
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
            line-height: 1.85;
            font-size: 17px;
        }}
        .container {{
            max-width: 780px;
            margin: 0 auto;
            padding: 24px 16px 64px;
        }}
        .top-bar {{
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 14px;
        }}
        .top-bar a {{
            color: var(--accent);
            text-decoration: none;
            font-weight: 600;
        }}
        .top-bar a:hover {{ text-decoration: underline; }}
        article {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 32px 36px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}
        @media (max-width: 600px) {{
            article {{ padding: 20px 18px; }}
        }}
        .eyecatch {{
            margin: -32px -36px 24px -36px;
            border-radius: 12px 12px 0 0;
            overflow: hidden;
        }}
        @media (max-width: 600px) {{
            .eyecatch {{ margin: -20px -18px 20px -18px; }}
        }}
        .eyecatch img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        h1.article-title {{
            font-size: 26px;
            line-height: 1.4;
            margin: 0 0 12px 0;
        }}
        .meta {{
            color: var(--muted);
            font-size: 14px;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            align-items: center;
        }}
        .meta a {{ color: var(--muted); }}
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 20px;
        }}
        .tag {{
            background: var(--quote-bg);
            color: var(--muted);
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 13px;
        }}
        .article-body p {{
            margin: 0 0 1.5em 0;
            word-break: break-word;
        }}
        .article-body h2 {{
            font-size: 22px;
            margin: 2em 0 0.8em;
            padding-bottom: 6px;
            border-bottom: 2px solid var(--accent);
        }}
        .article-body h3 {{
            font-size: 19px;
            margin: 1.6em 0 0.6em;
        }}
        .article-body figure {{
            margin: 1.8em 0;
            text-align: center;
        }}
        .article-body img {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
        }}
        .article-body figcaption {{
            font-size: 13px;
            color: var(--muted);
            margin-top: 6px;
        }}
        .article-body blockquote {{
            margin: 1.5em 0;
            padding: 16px 20px;
            background: var(--quote-bg);
            border-left: 4px solid var(--accent);
            border-radius: 0 8px 8px 0;
        }}
        .article-body a {{
            color: var(--link);
            word-break: break-all;
        }}
        .embed-link, .embed-source {{
            margin: 12px 0;
            padding: 12px 16px;
            background: var(--quote-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 14px;
        }}
        .paywall-warning {{
            margin-top: 32px;
            padding: 20px;
            background: #fff3cd;
            color: #664d03;
            border: 1px solid #ffecb5;
            border-radius: 8px;
            text-align: center;
        }}
        .footer-nav {{
            margin-top: 32px;
            display: flex;
            justify-content: space-between;
            gap: 16px;
        }}
        .nav-btn {{
            display: inline-block;
            padding: 10px 16px;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text);
            text-decoration: none;
            font-size: 14px;
            max-width: 48%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .nav-btn:hover {{
            border-color: var(--accent);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="top-bar">
            <a href="../index.html">← 記事一覧に戻る</a>
            <a href="{note_url}" target="_blank" rel="noopener">noteで元記事を見る ↗</a>
        </div>
        <article>
            {eyecatch_html}
            <h1 class="article-title">{title}</h1>
            <div class="meta">
                <span>公開日: {publish_full}</span>
                <span>スキ: ♥ {like_count}</span>
                <span>ID: {key}</span>
            </div>
            {tags_html}
            <div class="article-body">
                {body_html}
            </div>
            {paywall_notice}
        </article>
        <div class="footer-nav">
            {nav_prev}
            {nav_next}
        </div>
    </div>
</body>
</html>
"""
    return html_doc, image_tasks


def build_index_html(articles_meta: list[dict]):
    rows_html = []
    full_count = sum(1 for a in articles_meta if a["is_full"])
    total_count = len(articles_meta)

    for a in articles_meta:
        badge = (
            '<span class="badge badge-full">全文保存済</span>'
            if a["is_full"]
            else '<span class="badge badge-preview">プレビューのみ</span>'
        )
        src_badge = (
            '<span class="badge badge-mem">メンバーシップ特典</span>'
            if a["in_membership_list"]
            else '<span class="badge badge-mag">マガジン収録</span>'
        )
        rows_html.append(f"""
        <div class="card" data-title="{a['title'].lower()}" data-date="{a['date']}" data-full="{'1' if a['is_full'] else '0'}" data-source="{'mem' if a['in_membership_list'] else 'mag'}">
            <div class="card-main">
                <div class="card-meta">
                    <span class="date">{a['date']}</span>
                    {src_badge}
                    {badge}
                    <span class="likes">♥ {a['likes']}</span>
                </div>
                <a class="card-title" href="articles/{a['filename']}">{a['title']}</a>
            </div>
            <div class="card-actions">
                <a class="open-btn" href="articles/{a['filename']}">読む</a>
                <a class="orig-link" href="{a['note_url']}" target="_blank" rel="noopener" title="note元記事">元記事↗</a>
            </div>
        </div>
        """)

    index_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>堀元 見 メンバーシップ・マガジン記事一覧 ({total_count}件)</title>
    <style>
        :root {{
            --bg: #f4f6f8;
            --card-bg: #ffffff;
            --text: #1f2937;
            --muted: #6b7280;
            --border: #e5e7eb;
            --accent: #2cb696;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg: #111827;
                --card-bg: #1f2937;
                --text: #f3f4f6;
                --muted: #9ca3af;
                --border: #374151;
                --accent: #2cb696;
            }}
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 0;
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Hiragino Kaku Gothic ProN", Meiryo, sans-serif;
        }}
        header {{
            background: var(--card-bg);
            border-bottom: 1px solid var(--border);
            padding: 28px 20px;
            text-align: center;
        }}
        header h1 {{
            margin: 0 0 8px 0;
            font-size: 24px;
        }}
        header p {{
            margin: 0;
            color: var(--muted);
            font-size: 14px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 24px 16px 64px;
        }}
        .controls {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 20px;
            background: var(--card-bg);
            padding: 16px;
            border-radius: 10px;
            border: 1px solid var(--border);
        }}
        .controls input[type="search"] {{
            flex: 1;
            min-width: 220px;
            padding: 10px 14px;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: var(--bg);
            color: var(--text);
            font-size: 15px;
        }}
        .controls select {{
            padding: 10px 12px;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: var(--bg);
            color: var(--text);
            font-size: 14px;
        }}
        .count-bar {{
            font-size: 14px;
            color: var(--muted);
            margin-bottom: 12px;
        }}
        .list {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            transition: border-color 0.15s;
        }}
        .card:hover {{
            border-color: var(--accent);
        }}
        .card-main {{
            flex: 1;
            min-width: 0;
        }}
        .card-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
            font-size: 13px;
            color: var(--muted);
            margin-bottom: 6px;
        }}
        .card-title {{
            font-size: 17px;
            font-weight: 600;
            color: var(--text);
            text-decoration: none;
            display: block;
            line-height: 1.4;
        }}
        .card-title:hover {{
            color: var(--accent);
        }}
        .badge {{
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        .badge-full {{ background: #d1fae5; color: #065f46; }}
        .badge-preview {{ background: #fef3c7; color: #92400e; }}
        .badge-mem {{ background: #dbeafe; color: #1e40af; }}
        .badge-mag {{ background: #f3e8ff; color: #6b21a8; }}
        .card-actions {{
            display: flex;
            gap: 8px;
            align-items: center;
            flex-shrink: 0;
        }}
        .open-btn {{
            background: var(--accent);
            color: #fff;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
        }}
        .orig-link {{
            color: var(--muted);
            text-decoration: none;
            font-size: 12px;
            padding: 6px 8px;
        }}
    </style>
</head>
<body>
    <header>
        <h1>「堀元見の炎上するから有料で書く話」ローカルアーカイブ</h1>
        <p>保存記事数: {total_count}件 （うち全文保存: {full_count}件）</p>
    </header>
    <div class="container">
        <div class="controls">
            <input type="search" id="searchInput" placeholder="タイトルで検索..." oninput="filterArticles()">
            <select id="filterSelect" onchange="filterArticles()">
                <option value="all">すべて表示 ({total_count}件)</option>
                <option value="full">全文保存済みのみ ({full_count}件)</option>
                <option value="mem">メンバーシップ特典一覧のみ</option>
            </select>
            <select id="sortSelect" onchange="sortArticles()">
                <option value="desc">新しい順</option>
                <option value="asc">古い順</option>
            </select>
        </div>
        <div class="count-bar" id="countBar">表示中: {total_count}件</div>
        <div class="list" id="articleList">
            {''.join(rows_html)}
        </div>
    </div>
    <script>
        function filterArticles() {{
            const q = document.getElementById('searchInput').value.toLowerCase();
            const f = document.getElementById('filterSelect').value;
            const cards = document.querySelectorAll('.card');
            let visible = 0;
            cards.forEach(c => {{
                const title = c.getAttribute('data-title');
                const isFull = c.getAttribute('data-full') === '1';
                const src = c.getAttribute('data-source');
                let show = title.includes(q);
                if (show && f === 'full' && !isFull) show = false;
                if (show && f === 'mem' && src !== 'mem') show = false;
                c.style.display = show ? 'flex' : 'none';
                if (show) visible++;
            }});
            document.getElementById('countBar').textContent = '表示中: ' + visible + '件';
        }}
        function sortArticles() {{
            const order = document.getElementById('sortSelect').value;
            const list = document.getElementById('articleList');
            const cards = Array.from(list.querySelectorAll('.card'));
            cards.sort((a, b) => {{
                const da = a.getAttribute('data-date');
                const db = b.getAttribute('data-date');
                return order === 'asc' ? da.localeCompare(db) : db.localeCompare(da);
            }});
            cards.forEach(c => list.appendChild(c));
        }}
    </script>
</body>
</html>
"""
    (BASE_DIR / "index.html").write_text(index_content, encoding="utf-8")


def main():
    for d in [BASE_DIR, ARTICLES_DIR, IMAGES_DIR, RAW_JSON_DIR, PROFILE_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    cookie_header = ""
    cookie_file = BASE_DIR / "cookie.txt"
    if len(sys.argv) > 1 and sys.argv[1].strip():
        raw_c = sys.argv[1].strip()
        cookie_header = raw_c if "=" in raw_c else f"_note_session_v5={raw_c}"
    elif cookie_file.exists() and cookie_file.read_text(encoding="utf-8").strip():
        raw_c = cookie_file.read_text(encoding="utf-8").strip()
        cookie_header = raw_c if "=" in raw_c else f"_note_session_v5={raw_c}"

    if not cookie_header:
        print("==========================================================", flush=True)
        print("1. 専用Chromeウィンドウを起動します。noteにログインしてください...", flush=True)
        print("==========================================================", flush=True)

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                channel="chrome",
                headless=False,
                viewport={"width": 1100, "height": 800},
                ignore_default_args=["--enable-automation"],
                args=["--disable-blink-features=AutomationControlled"],
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://note.com/login?redirectPath=%2Fkenhori2%2Fmembership")

            # Wait until user logs in and can access membership or is logged in on note.com
            logged_in = False
            for _ in range(300):  # Wait up to 10 minutes
                time.sleep(2)
                try:
                    cookies = context.cookies("https://note.com")
                    cookie_names = {c["name"] for c in cookies}
                    cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
                    current_url = page.url

                    # Check if logged in via API test on the latest membership note
                    if "_note_session_v5" in cookie_names and "/login" not in current_url and "/mfa" not in current_url:
                        test_res = fetch_json_with_cookies(f"https://note.com/api/v3/notes/{TEST_NOTE_KEY}", cookie_header)
                        nd = test_res.get("data", {})
                        if nd.get("can_read") or (nd.get("remained_char_num") == 0 and nd.get("body")):
                            print("[OK] ログインおよびメンバーシップ権限を確認しました！", flush=True)
                            logged_in = True
                            break
                        else:
                            # Check if user is logged in at least
                            plans = nd.get("circle_plans") or []
                            is_mem = any(pl.get("is_member") for pl in plans)
                            if is_mem:
                                print("[OK] メンバーシップ加入済みアカウントを確認しました！", flush=True)
                                logged_in = True
                                break
                            else:
                                print(f"[待機中] ログイン検知 (URL={current_url}) - メンバーシップ権限を確認中...", flush=True)
                except Exception as e:
                    pass

            if not logged_in:
                print("[WARN] タイムアウトまたは未ログイン状態です。現在のセッションで取得を試みます。", flush=True)

            # Close browser so user knows authentication step is complete
            context.close()

    # Step 2: Fetch membership notes list
    print("\n2. メンバーシップ特典記事の一覧を取得しています...", flush=True)
    membership_keys = []
    membership_key_set = set()
    page_num = 1
    while True:
        url = f"https://note.com/api/v3/memberships/{CIRCLE_KEY}/notes?page={page_num}"
        res = fetch_json_with_cookies(url, cookie_header)
        items = res.get("data") or []
        if not items:
            break
        for item in items:
            k = item.get("key")
            if k and k not in membership_key_set:
                membership_keys.append(k)
                membership_key_set.add(k)
        print(f"  メンバーシップ一覧 Page {page_num}: {len(items)}件 (累計 {len(membership_keys)}件)", flush=True)
        if not res.get("next_page"):
            break
        page_num += 1
        time.sleep(0.2)

    # Step 3: Also check magazine m125fc4524aca ('堀元見の、炎上するから有料で書く話')
    print("\n3. マガジン「堀元見の、炎上するから有料で書く話」の記事一覧を取得しています...", flush=True)
    magazine_keys = []
    mag_page = 1
    while True:
        url = f"https://note.com/api/v1/layout/magazine/{MAGAZINE_KEY}/section?page={mag_page}"
        res = fetch_json_with_cookies(url, cookie_header)
        sec = (res.get("data") or {}).get("section") or {}
        contents = sec.get("contents") or []
        if not contents:
            break
        for item in contents:
            k = item.get("key")
            if k:
                magazine_keys.append(k)
        if mag_page % 5 == 0 or sec.get("is_last_page"):
            print(f"  マガジン一覧 Page {mag_page}: 累計 {len(magazine_keys)}件", flush=True)
        if sec.get("is_last_page"):
            break
        mag_page += 1
        time.sleep(0.15)

    # Combine keys preserving order (membership notes + magazine notes)
    all_keys = list(membership_keys)
    for k in magazine_keys:
        if k not in membership_key_set:
            all_keys.append(k)

    print(f"\n合計対象記事数: {len(all_keys)}件 (メンバーシップ一覧: {len(membership_keys)}件, マガジン追加分: {len(all_keys) - len(membership_keys)}件)", flush=True)

    # Step 4: Fetch each article detail (JSON)
    print("\n4. 各記事の本文データを取得しています...", flush=True)
    notes_detail = []
    for idx, key in enumerate(all_keys, 1):
        raw_path = RAW_JSON_DIR / f"{key}.json"
        nd = None
        if raw_path.exists():
            try:
                cached = json.loads(raw_path.read_text(encoding="utf-8"))
                # Re-fetch if cached version was not full text
                if cached.get("can_read") or (cached.get("remained_char_num") in (0, None) and cached.get("body")):
                    nd = cached
            except Exception:
                pass

        if nd is None:
            try:
                res = fetch_json_with_cookies(f"https://note.com/api/v3/notes/{key}", cookie_header)
                nd = res.get("data") or {}
                raw_path.write_text(json.dumps(nd, ensure_ascii=False, indent=2), encoding="utf-8")
                time.sleep(0.15)
            except Exception as e:
                print(f"  [ERROR] Failed to fetch {key}: {e}", flush=True)
                continue

        is_full = bool(nd.get("can_read") or (nd.get("remained_char_num") in (0, None) and nd.get("body")))
        # Only include if it's in membership_key_set OR is_full (readable via membership/free)
        if key in membership_key_set or is_full:
            notes_detail.append(nd)

        if idx % 20 == 0 or idx == len(all_keys):
            print(f"  進捗: {idx}/{len(all_keys)}件取得完了 (保存対象: {len(notes_detail)}件)", flush=True)

    # Sort articles by publish_at descending
    notes_detail.sort(
        key=lambda x: (x.get("publish_at") or x.get("created_at") or ""),
        reverse=True,
    )

    # Precompute filenames for navigation links
    filenames = []
    for nd in notes_detail:
        key = nd.get("key", "")
        date_str = (nd.get("publish_at") or nd.get("created_at") or "0000-00-00")[:10]
        safe_title = sanitize_filename(nd.get("name", "無題"))
        filenames.append(f"{date_str}_{key}_{safe_title}.html")

    # Step 5: Generate HTML files and collect image download tasks
    print("\n5. HTMLファイルを生成しています...", flush=True)
    all_image_tasks = []
    articles_meta = []

    for i, nd in enumerate(notes_detail):
        key = nd.get("key", "")
        fname = filenames[i]
        prev_link = filenames[i + 1] if i + 1 < len(filenames) else None
        next_link = filenames[i - 1] if i - 1 >= 0 else None

        html_doc, img_tasks = process_article_html(nd, cookie_header, prev_link=prev_link, next_link=next_link)
        (ARTICLES_DIR / fname).write_text(html_doc, encoding="utf-8")
        all_image_tasks.extend(img_tasks)

        is_full = bool(nd.get("can_read") or (nd.get("remained_char_num") in (0, None) and nd.get("body")))
        articles_meta.append({
            "key": key,
            "title": nd.get("name", "無題"),
            "date": (nd.get("publish_at") or nd.get("created_at") or "")[:10],
            "likes": nd.get("like_count", 0),
            "filename": fname,
            "note_url": nd.get("note_url") or f"https://note.com/kenhori2/n/{key}",
            "is_full": is_full,
            "in_membership_list": key in membership_key_set,
        })

    build_index_html(articles_meta)
    try:
        import build_and_upgrade
        build_and_upgrade.main()
    except Exception as e:
        print(f"  [WARN] build_and_upgrade error: {e}", flush=True)
    print(f"  HTML生成完了: {len(articles_meta)}件 (index.html 作成済み)", flush=True)

    # Step 6: Download all images concurrently
    print(f"\n6. 画像ファイルをダウンロードしています (全 {len(all_image_tasks)} 枚)...", flush=True)
    completed_imgs = 0
    if all_image_tasks:
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(download_image, url, dest, cookie_header)
                for url, dest in all_image_tasks
            ]
            for idx, fut in enumerate(as_completed(futures), 1):
                if fut.result():
                    completed_imgs += 1
                if idx % 50 == 0 or idx == len(all_image_tasks):
                    print(f"  画像進捗: {idx}/{len(all_image_tasks)}枚完了", flush=True)

    print("\n==========================================================", flush=True)
    print("すべての処理が完了しました！", flush=True)
    print(f"保存先フォルダ: {BASE_DIR}", flush=True)
    print(f"一覧ページ:     {BASE_DIR / 'index.html'}", flush=True)
    print("==========================================================", flush=True)


if __name__ == "__main__":
    main()
