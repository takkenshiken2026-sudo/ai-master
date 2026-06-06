/**
 * SEO ユーティリティ — パンくずリスト・構造化データ
 * 静的 HTML と併用し、フィルター付き一覧など動的ページを補完します。
 */
(function () {
  if (typeof SITE_CONFIG === 'undefined') return;

  function absoluteUrl(path) {
    const origin = SITE_CONFIG.origin.replace(/\/$/, '');
    const normalized = path.startsWith('/') ? path : `/${path}`;
    return `${origin}${normalized}`;
  }

  function injectJsonLd(data) {
    const script = document.createElement('script');
    script.type = 'application/ld+json';
    script.textContent = JSON.stringify(data);
    document.head.appendChild(script);
  }

  function buildBreadcrumbJsonLd(items) {
    return {
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      itemListElement: items.map((item, i) => ({
        '@type': 'ListItem',
        position: i + 1,
        name: item.name,
        item: item.url ? absoluteUrl(item.url) : undefined,
      })),
    };
  }

  function setBreadcrumbJsonLd(items) {
    let ld = document.getElementById('breadcrumb-ld');
    if (!ld) {
      ld = document.createElement('script');
      ld.id = 'breadcrumb-ld';
      ld.type = 'application/ld+json';
      document.head.appendChild(ld);
    }
    ld.textContent = JSON.stringify(buildBreadcrumbJsonLd(items));
  }

  /** ツール一覧 — カテゴリフィルター時にパンくずを更新 */
  function updateToolsBreadcrumb(cat) {
    const nav = document.getElementById('breadcrumb');
    if (!nav || typeof CATEGORIES === 'undefined') return;

    const items = [
      { name: 'ホーム', href: '../index.html', path: '/' },
      { name: 'AIツール', href: cat === 'all' ? null : 'index.html', path: '/tools/' },
    ];

    if (cat !== 'all') {
      const label = CATEGORIES.find((c) => c.id === cat)?.label || cat;
      items.push({ name: label, href: null, path: `/tools/?cat=${cat}` });
    }

    const ol = nav.querySelector('ol');
    if (!ol) return;

    ol.innerHTML = items.map((item, i) => {
      const isLast = i === items.length - 1;
      if (isLast || !item.href) {
        return `<li${isLast ? ' aria-current="page"' : ''}>${item.name}</li>`;
      }
      return `<li><a href="${item.href}">${item.name}</a></li>`;
    }).join('');

    setBreadcrumbJsonLd(items.map((item) => ({ name: item.name, url: item.path || null })));
  }

  window.SEO = { absoluteUrl, injectJsonLd, buildBreadcrumbJsonLd, updateToolsBreadcrumb };
})();
