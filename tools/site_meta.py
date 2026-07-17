"""サイト共通の OGP・ファビコン用 HTML スニペット。"""

from __future__ import annotations

import html

SITE_ORIGIN = "https://ai-master.jp"
SITE_OG_IMAGE = f"{SITE_ORIGIN}/assets/images/og-default.jpg"
SITE_OG_WIDTH = 1200
SITE_OG_HEIGHT = 630
GA4_MEASUREMENT_ID = "G-FWXFGSH6TD"
ADSENSE_CLIENT_ID = "ca-pub-7927260139193410"
ROBOTS_NOINDEX_FOLLOW = "noindex, follow"

SITE_ICONS_HTML = """  <link rel="icon" href="/assets/images/favicon.svg" type="image/svg+xml">
  <link rel="icon" href="/assets/images/favicon-32x32.png" type="image/png" sizes="32x32">
  <link rel="icon" href="/assets/images/favicon-16x16.png" type="image/png" sizes="16x16">
  <link rel="apple-touch-icon" href="/assets/images/apple-touch-icon.png">
  <link rel="manifest" href="/site.webmanifest">
  <meta name="theme-color" content="#1A5CDB">
"""

SITE_GA4_HTML = f"""  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_MEASUREMENT_ID}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', '{GA4_MEASUREMENT_ID}');
  </script>
"""

SITE_ADSENSE_HTML = f"""  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT_ID}"
     crossorigin="anonymous"></script>
"""


def render_og_meta(
    title: str,
    description: str,
    canonical: str,
    *,
    og_type: str = "website",
    og_image: str = SITE_OG_IMAGE,
    og_image_width: int | None = SITE_OG_WIDTH,
    og_image_height: int | None = SITE_OG_HEIGHT,
) -> str:
    esc_title = html.escape(title, quote=True)
    esc_desc = html.escape(description, quote=True)
    dims = ""
    if og_image_width and og_image_height:
        dims = f"""  <meta property="og:image:width" content="{og_image_width}">
  <meta property="og:image:height" content="{og_image_height}">
"""
    return f"""  <meta property="og:type" content="{og_type}">
  <meta property="og:site_name" content="AI Master">
  <meta property="og:title" content="{esc_title}">
  <meta property="og:description" content="{esc_desc}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:locale" content="ja_JP">
  <meta property="og:image" content="{og_image}">
{dims}  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="{og_image}">
"""


def render_robots_meta(content: str = ROBOTS_NOINDEX_FOLLOW) -> str:
    return f'  <meta name="robots" content="{content}">\n'


# /path/index.html を canonical の /path/ へ寄せる（GitHub Pages の二重 URL 対策）
SITE_CANONICAL_NORMALIZE_HTML = """  <script>
(function () {
  var path = location.pathname;
  if (!path.endsWith("/index.html")) return;
  location.replace(path.slice(0, -10) + location.search + location.hash);
})();
  </script>
"""

# 演習プレイヤーの ?q= 深いリンクは静的問題ページを canonical にする
PLAYER_DEEPLINK_CANONICAL_HTML = """  <script>
(function () {
  var q = new URLSearchParams(location.search).get("q");
  if (!q) return;
  var match = location.pathname.match(/(\\/exams\\/[^/]+\\/(?:practice|drill))\\/?$/);
  if (!match) return;
  var slug = q.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  var href = location.origin + match[1] + "/q/" + slug + "/";
  var link = document.querySelector('link[rel="canonical"]');
  if (link) link.href = href;
})();
  </script>
"""
