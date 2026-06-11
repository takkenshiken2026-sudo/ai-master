const PER_PAGE = 100;
const INDEX_URL = '../data/glossary-index.json';

const CATEGORY_ORDER = [
  'basics',
  'models-tech',
  'genai-use',
  'data-ops',
  'governance',
];

const HUB_CHEVRON =
  '<svg class="hub-list-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">' +
  '<path d="M6 4l4 4-4 4" stroke-linecap="round" stroke-linejoin="round"/></svg>';

let categories = {};
let allTerms = [];
let featuredItems = [];

function parseState() {
  const params = new URLSearchParams(window.location.search);
  const sort = params.get('sort') === 'az' ? 'az' : 'alpha';
  const cat = params.get('cat') || 'all';
  return {
    page: Math.max(1, parseInt(params.get('page') || '1', 10) || 1),
    q: (params.get('q') || '').trim(),
    sort,
    cat: CATEGORY_ORDER.includes(cat) ? cat : 'all',
  };
}

function buildListUrl(page, q, sort, cat) {
  const params = new URLSearchParams();
  if (cat && cat !== 'all') params.set('cat', cat);
  if (page > 1) params.set('page', String(page));
  if (q) params.set('q', q);
  if (sort === 'az') params.set('sort', 'az');
  const qs = params.toString();
  return qs ? `index.html?${qs}` : 'index.html';
}

function countByCategory() {
  const counts = { all: allTerms.length };
  CATEGORY_ORDER.forEach((id) => {
    counts[id] = 0;
  });
  allTerms.forEach((t) => {
    if (counts[t.category] !== undefined) counts[t.category] += 1;
  });
  return counts;
}

function matchesCategory(term, cat) {
  return cat === 'all' || term.category === cat;
}

function sortTerms(list, mode) {
  return [...list].sort((a, b) => {
    if (mode === 'az') {
      return (a.yomi || a.name).localeCompare(b.yomi || b.name, 'en');
    }
    const skA = a.sortKey || a.name.slice(0, 1);
    const skB = b.sortKey || b.name.slice(0, 1);
    const aJp = /^[ぁ-ん]/.test(skA);
    const bJp = /^[ぁ-ん]/.test(skB);
    if (aJp && !bJp) return -1;
    if (!aJp && bJp) return 1;
    return a.name.localeCompare(b.name, 'ja');
  });
}

function matchesSearch(term, q) {
  if (!q) return true;
  const needle = q.toLowerCase();
  const haystack = [term.name, term.yomi, term.summary, categories[term.category] || '']
    .join(' ')
    .toLowerCase();
  return haystack.includes(needle);
}

function renderFeaturedCard(term, icon) {
  const inner = hubFeaturedCardInner(
    escapeHtml(term.name),
    escapeHtml(term.summary || ''),
    icon,
  );
  return `<a href="${encodeURI(term.id)}/" class="hub-featured-card">${inner}</a>`;
}

function renderFeatured(cat, page, q, sort) {
  const section = document.getElementById('glossaryFeatured');
  const grid = document.getElementById('glossaryFeaturedGrid');
  if (!section || !grid) return;
  const show = cat === 'all' && page === 1 && !q;
  const featured = featuredItems
    .map(({ id, icon }) => {
      const term = allTerms.find((t) => t.id === id && t.published);
      return term ? { term, icon } : null;
    })
    .filter(Boolean);
  section.hidden = !show || featured.length === 0;
  if (!show || featured.length === 0) return;
  grid.innerHTML = featured.map(({ term, icon }) => renderFeaturedCard(term, icon)).join('');
}

function renderTermRow(term) {
  const catLabel = categories[term.category] || term.category;
  const status = term.published
    ? ''
    : '<span class="hub-list-pill">準備中</span>';
  const inner =
    `<div class="hub-list-body">` +
    `<div class="hub-list-top">` +
    `<h2 class="hub-list-name">${escapeHtml(term.name)}</h2>` +
    status +
    `</div>` +
    (term.summary ? `<p class="hub-list-desc">${escapeHtml(term.summary)}</p>` : '') +
    `</div>` +
    `<div class="hub-list-aside">` +
    `<span class="hub-list-cat">${escapeHtml(catLabel)}</span>` +
    HUB_CHEVRON +
    `</div>`;

  if (term.published) {
    return `<li class="hub-list-row"><a href="${encodeURI(term.id)}/" class="hub-list-link">${inner}</a></li>`;
  }
  return `<li class="hub-list-row hub-list-row--planned"><div class="hub-list-link" aria-disabled="true">${inner}</div></li>`;
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderCategoryFilters(cat, q, sort) {
  const row = document.getElementById('glossaryCategoryFilters');
  if (!row) return;

  const counts = countByCategory();
  const chips = [
  { id: 'all', label: 'すべて' },
  ...CATEGORY_ORDER.map((id) => ({ id, label: categories[id] || id })),
];

  row.innerHTML = chips
    .map(({ id, label }) => {
      const isActive = id === cat;
      const count = counts[id] ?? 0;
      const href = buildListUrl(1, q, sort, id);
      const cls = `filter-chip${isActive ? ' active' : ''}`;
      const aria = isActive ? ' aria-current="true"' : '';
      return (
        `<a href="${href}" class="${cls}" data-cat="${id}"${aria}>` +
        `<span class="filter-chip-label">${escapeHtml(label)}</span>` +
        `<span class="filter-chip-count">${count}</span>` +
        `</a>`
      );
    })
    .join('');
}

function renderPagination(page, q, sort, cat, totalPages) {
  const nav = document.getElementById('glossaryPagination');
  if (!nav) return;
  if (totalPages <= 1) {
    nav.innerHTML = '';
    updateHeadLinks(page, q, sort, cat, totalPages);
    return;
  }

  const pages = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i += 1) pages.push(i);
  } else {
    pages.push(1);
    if (page > 3) pages.push('…');
    for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i += 1) {
      pages.push(i);
    }
    if (page < totalPages - 2) pages.push('…');
    pages.push(totalPages);
  }

  let html = '';
  if (page > 1) {
    html += `<a href="${buildListUrl(page - 1, q, sort, cat)}" class="page-btn page-arrow" rel="prev" aria-label="前のページ">‹</a>`;
  } else {
    html += `<span class="page-btn page-arrow" aria-hidden="true" style="opacity:0.35">‹</span>`;
  }

  pages.forEach((p) => {
    if (p === '…') {
      html += '<span class="page-btn dots">…</span>';
    } else if (p === page) {
      html += `<span class="page-btn is-active" aria-current="page">${p}</span>`;
    } else {
      html += `<a href="${buildListUrl(p, q, sort, cat)}" class="page-btn">${p}</a>`;
    }
  });

  if (page < totalPages) {
    html += `<a href="${buildListUrl(page + 1, q, sort, cat)}" class="page-btn page-arrow" rel="next" aria-label="次のページ">›</a>`;
  } else {
    html += `<span class="page-btn page-arrow" aria-hidden="true" style="opacity:0.35">›</span>`;
  }

  nav.innerHTML = html;
  updateHeadLinks(page, q, sort, cat, totalPages);
}

function updateHeadLinks(page, q, sort, cat, totalPages) {
  ['prev', 'next'].forEach((rel) => {
    const el = document.querySelector(`link[rel="${rel}"]`);
    if (el) el.remove();
  });
  if (page > 1) {
    const link = document.createElement('link');
    link.rel = 'prev';
    link.href = buildListUrl(page - 1, q, sort, cat);
    document.head.appendChild(link);
  }
  if (page < totalPages) {
    const link = document.createElement('link');
    link.rel = 'next';
    link.href = buildListUrl(page + 1, q, sort, cat);
    document.head.appendChild(link);
  }
}

let lastFilterKey = '';

function render() {
  const { page, q, sort, cat } = parseState();
  const filtered = sortTerms(
    allTerms.filter((t) => matchesCategory(t, cat) && matchesSearch(t, q)),
    sort,
  );
  const totalPages = Math.max(1, Math.ceil(filtered.length / PER_PAGE));
  const filterKey = `${cat}:${sort}`;
  if (filterKey !== lastFilterKey) {
    renderCategoryFilters(cat, q, sort);
    lastFilterKey = filterKey;
  } else {
    HubNav.updateFilterHrefs('glossaryCategoryFilters', (id) => buildListUrl(1, q, sort, id));
  }
  renderFeatured(cat, page, q, sort);
  if (page > totalPages) {
    HubNav.replace(buildListUrl(totalPages, q, sort, cat), render);
    return;
  }
  const safePage = page;
  const start = (safePage - 1) * PER_PAGE;
  const pageTerms = filtered.slice(start, start + PER_PAGE);

  const meta = document.getElementById('glossaryResultMeta');
  const range = document.getElementById('glossaryResultRange');
  const list = document.getElementById('termList');
  const sortSelect = document.getElementById('glossarySortSelect');
  const searchInput = document.getElementById('glossarySearchInput');

  const publishedCount = allTerms.filter((t) => t.published).length;

  if (sortSelect && sortSelect.value !== sort) {
    sortSelect.value = sort;
  }
  HubNav.syncSearchInput(searchInput, q);

  if (filtered.length === 0) {
    if (meta) meta.textContent = '0件';
    if (range) range.textContent = '';
    if (list) {
      list.innerHTML = '<li class="hub-empty">該当する用語が見つかりませんでした。</li>';
    }
    renderPagination(1, q, sort, cat, 1);
    return;
  }

  const end = Math.min(start + PER_PAGE, filtered.length);
  const catLabel = cat === 'all' ? '' : categories[cat] || cat;
  if (meta) {
    if (q || cat !== 'all') {
      const scope = catLabel ? `${catLabel}: ` : '';
      meta.textContent = `${scope}${filtered.length.toLocaleString()}件（全${allTerms.length.toLocaleString()}件中）`;
    } else {
      meta.textContent = `${allTerms.length.toLocaleString()}件（解説公開 ${publishedCount.toLocaleString()}件 · 準備中 ${(allTerms.length - publishedCount).toLocaleString()}件）`;
    }
  }
  if (range) {
    range.textContent = `${start + 1}〜${end}件を表示`;
  }
  if (list) {
    list.innerHTML = pageTerms.map(renderTermRow).join('');
  }
  renderPagination(safePage, q, sort, cat, totalPages);
}

function bindEvents() {
  HubNav.bindLinkClicks(render);
  HubNav.bindPopstate(render);

  HubNav.bindSearchInput({
    inputId: 'glossarySearchInput',
    render,
    buildUrl(q) {
      const { sort, cat } = parseState();
      return buildListUrl(1, q, sort, cat);
    },
  });

  document.getElementById('glossarySortSelect')?.addEventListener('change', (e) => {
    const { q, cat } = parseState();
    const sort = e.target.value === 'az' ? 'az' : 'alpha';
    HubNav.navigate(buildListUrl(1, q, sort, cat), render);
  });
}

async function init() {
  try {
    const res = await fetch(INDEX_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    categories = data.categories || {};
    allTerms = data.terms || [];
    featuredItems = data.featured || (data.featuredIds || []).map((id) => ({ id }));
  } catch (err) {
    const list = document.getElementById('termList');
    if (list) {
      list.innerHTML =
        '<li class="hub-empty">用語データの読み込みに失敗しました。ページを再読み込みしてください。</li>';
    }
    console.error(err);
    return;
  }

  bindEvents();
  render();
}

init();
