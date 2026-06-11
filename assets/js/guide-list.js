const PER_PAGE = 15;
const INDEX_URL = '../data/guide-index.json';

const HUB_CHEVRON =
  '<svg class="hub-list-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">' +
  '<path d="M6 4l4 4-4 4" stroke-linecap="round" stroke-linejoin="round"/></svg>';

let categories = {};
let categoryOrder = [];
let allArticles = [];
let featuredItems = [];

function parseState() {
  const params = new URLSearchParams(window.location.search);
  const cat = params.get('cat') || 'all';
  return {
    cat: cat === 'all' || categoryOrder.includes(cat) ? cat : 'all',
    page: Math.max(1, parseInt(params.get('page') || '1', 10) || 1),
    q: (params.get('q') || '').trim(),
  };
}

function buildListUrl(cat, page, q) {
  const params = new URLSearchParams();
  if (cat && cat !== 'all') params.set('cat', cat);
  if (page > 1) params.set('page', String(page));
  if (q) params.set('q', q);
  const qs = params.toString();
  return qs ? `index.html?${qs}` : 'index.html';
}

function countByCategory() {
  const counts = { all: allArticles.length };
  categoryOrder.forEach((id) => {
    counts[id] = 0;
  });
  allArticles.forEach((a) => {
    if (counts[a.category] !== undefined) counts[a.category] += 1;
  });
  return counts;
}

function matchesCategory(article, cat) {
  return cat === 'all' || article.category === cat;
}

function matchesSearch(article, q) {
  if (!q) return true;
  const needle = q.toLowerCase();
  const haystack = [
    article.name,
    article.summary,
    article.keyword,
    categories[article.category] || '',
  ]
    .join(' ')
    .toLowerCase();
  return haystack.includes(needle);
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderArticleRow(article) {
  const catLabel = categories[article.category] || article.category;
  const tileLabel = hubCategoryShortLabel('guide', article.category, catLabel);
  const status = article.published
    ? ''
    : '<span class="hub-list-pill">準備中</span>';
  const inner =
    hubListIconTile(article.icon, escapeHtml(tileLabel)) +
    `<div class="hub-list-body">` +
    `<div class="hub-list-top">` +
    `<h2 class="hub-list-name">${escapeHtml(article.name)}</h2>` +
    status +
    `</div>` +
    (article.keyword ? `<p class="hub-list-sub">${escapeHtml(article.keyword)}</p>` : '') +
    (article.summary ? `<p class="hub-list-desc">${escapeHtml(article.summary)}</p>` : '') +
    `</div>` +
    `<div class="hub-list-aside">` +
    HUB_CHEVRON +
    `</div>`;

  if (article.published) {
    return `<li class="hub-list-row"><a href="${encodeURI(article.id)}/" class="hub-list-link">${inner}</a></li>`;
  }
  return `<li class="hub-list-row hub-list-row--planned"><div class="hub-list-link" aria-disabled="true">${inner}</div></li>`;
}

function renderFeaturedCard(item) {
  const article = allArticles.find((a) => a.id === item.id);
  if (!article) return '';
  const cls = article.published
    ? 'hub-featured-card'
    : 'hub-featured-card hub-featured-card--planned';
  const badge = article.published ? '' : '<span class="hub-list-pill">準備中</span>';
  const inner = hubFeaturedCardInner(
    escapeHtml(article.name),
    article.summary ? escapeHtml(article.summary) : '',
    item.icon,
    badge,
  );

  if (article.published) {
    return `<a href="${encodeURI(article.id)}/" class="${cls}">${inner}</a>`;
  }
  return `<div class="${cls}">${inner}</div>`;
}

function renderCategoryFilters(cat, q) {
  const row = document.getElementById('guideCategoryFilters');
  if (!row) return;
  const counts = countByCategory();
  const chips = [{ id: 'all', label: 'すべて' }, ...categoryOrder.map((id) => ({ id, label: categories[id] || id }))];
  row.innerHTML = chips
    .map(({ id, label }) => {
      const isActive = id === cat;
      const href = buildListUrl(id, 1, q);
      return (
        `<a href="${href}" class="filter-chip${isActive ? ' active' : ''}" data-cat="${id}"` +
        `${isActive ? ' aria-current="true"' : ''}>` +
        `<span class="filter-chip-label">${escapeHtml(label)}</span>` +
        `<span class="filter-chip-count">${counts[id] ?? 0}</span>` +
        `</a>`
      );
    })
    .join('');
}

function renderFeatured(cat, page, q) {
  const section = document.getElementById('guideFeatured');
  const grid = document.getElementById('guideFeaturedGrid');
  if (!section || !grid) return;
  const show = cat === 'all' && page === 1 && !q;
  const featured = featuredItems
    .map((item) => {
      const article = allArticles.find((a) => a.id === item.id && a.published);
      return article ? item : null;
    })
    .filter(Boolean);
  section.hidden = !show || featured.length === 0;
  if (!show || featured.length === 0) return;
  grid.innerHTML = featured.map(renderFeaturedCard).join('');
}

function renderPagination(cat, page, q, totalPages) {
  const nav = document.getElementById('guidePagination');
  if (!nav) return;
  if (totalPages <= 1) {
    nav.innerHTML = '';
    return;
  }
  const pages = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i += 1) pages.push(i);
  } else {
    pages.push(1);
    if (page > 3) pages.push('…');
    for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i += 1) pages.push(i);
    if (page < totalPages - 2) pages.push('…');
    pages.push(totalPages);
  }
  let html = '';
  if (page > 1) {
    html += `<a href="${buildListUrl(cat, page - 1, q)}" class="page-btn page-arrow" rel="prev" aria-label="前のページ">‹</a>`;
  }
  pages.forEach((p) => {
    if (p === '…') html += '<span class="page-btn dots">…</span>';
    else if (p === page) html += `<span class="page-btn is-active" aria-current="page">${p}</span>`;
    else html += `<a href="${buildListUrl(cat, p, q)}" class="page-btn">${p}</a>`;
  });
  if (page < totalPages) {
    html += `<a href="${buildListUrl(cat, page + 1, q)}" class="page-btn page-arrow" rel="next" aria-label="次のページ">›</a>`;
  }
  nav.innerHTML = html;
}

let lastFilterKey = '';

function render() {
  const { cat, page, q } = parseState();
  const filtered = allArticles.filter((a) => matchesCategory(a, cat) && matchesSearch(a, q));
  const totalPages = Math.max(1, Math.ceil(filtered.length / PER_PAGE));
  const publishedCount = allArticles.filter((a) => a.published).length;

  const filterKey = cat;
  if (filterKey !== lastFilterKey) {
    renderCategoryFilters(cat, q);
    lastFilterKey = filterKey;
  } else {
    HubNav.updateFilterHrefs('guideCategoryFilters', (id) => buildListUrl(id, 1, q));
  }
  renderFeatured(cat, page, q);

  if (page > totalPages) {
    HubNav.replace(buildListUrl(cat, totalPages, q), render);
    return;
  }

  const start = (page - 1) * PER_PAGE;
  const pageArticles = filtered.slice(start, start + PER_PAGE);

  const meta = document.getElementById('guideResultMeta');
  const range = document.getElementById('guideResultRange');
  const list = document.getElementById('guideList');
  const searchInput = document.getElementById('guideSearchInput');

  if (searchInput) HubNav.syncSearchInput(searchInput, q);

  const catLabel = cat === 'all' ? '' : categories[cat] || cat;

  if (filtered.length === 0) {
    if (meta) meta.textContent = '0件';
    if (range) range.textContent = '';
    if (list) list.innerHTML = '<li class="hub-empty">該当する記事が見つかりませんでした。</li>';
    renderPagination(cat, 1, q, 1);
    return;
  }

  const end = Math.min(start + PER_PAGE, filtered.length);
  if (meta) {
    if (q || cat !== 'all') {
      meta.textContent = `${catLabel ? `${catLabel}: ` : ''}${filtered.length}件（全${allArticles.length}件中）`;
    } else {
      meta.textContent = `${allArticles.length}件（公開 ${publishedCount}件 · 準備中 ${allArticles.length - publishedCount}件）`;
    }
  }
  if (range) range.textContent = `${start + 1}〜${end}件を表示`;
  if (list) list.innerHTML = pageArticles.map(renderArticleRow).join('');
  renderPagination(cat, page, q, totalPages);
}

function bindEvents() {
  HubNav.bindLinkClicks(render);
  HubNav.bindPopstate(render);

  HubNav.bindSearchInput({
    inputId: 'guideSearchInput',
    render,
    buildUrl(q) {
      const { cat } = parseState();
      return buildListUrl(cat, 1, q);
    },
  });
}

async function init() {
  try {
    const res = await fetch(INDEX_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    categories = data.categories || {};
    categoryOrder = data.categoryOrder || Object.keys(categories);
    allArticles = data.articles || [];
    featuredItems = data.featured || [];
  } catch (err) {
    const list = document.getElementById('guideList');
    if (list) {
      list.innerHTML = '<li class="hub-empty">データの読み込みに失敗しました。ページを再読み込みしてください。</li>';
    }
    console.error(err);
    return;
  }
  bindEvents();
  render();
}

init();
