const ICON_BASE = '../assets/images/tools/';
const FEATURED_LIMIT = 3;

function toolUrl(tool) {
  return `${tool.id}/`;
}

function logoSrc(tool) {
  return `${ICON_BASE}${tool.logo}`;
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function parseState() {
  const params = new URLSearchParams(window.location.search);
  return {
    cat: params.get('cat') || 'all',
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

function matchesSearch(tool, q) {
  if (!q) return true;
  const haystack = [
    tool.name,
    tool.maker,
    tool.tagline,
    tool.catLabel,
    ...(tool.caps || []),
  ].join(' ').toLowerCase();
  return haystack.includes(q.toLowerCase());
}

function getFiltered(cat, q) {
  return TOOLS.filter((tool) => {
    const catMatch = cat === 'all' || tool.cat === cat;
    return catMatch && matchesSearch(tool, q);
  });
}

function countByCategory() {
  const counts = { all: TOOLS.length };
  CATEGORIES.forEach((c) => {
    if (c.id !== 'all') counts[c.id] = 0;
  });
  TOOLS.forEach((t) => {
    if (counts[t.cat] !== undefined) counts[t.cat] += 1;
  });
  return counts;
}

function toolIcon(tool, size) {
  const cls = size === 'sm' ? 'tool-icon tool-icon--sm' : 'tool-icon';
  return `<div class="${cls}"><img src="${logoSrc(tool)}" alt="" width="32" height="32" loading="lazy"></div>`;
}

function renderCategoryFilters(cat, q) {
  const row = document.getElementById('toolsCategoryFilters');
  if (!row) return;
  const counts = countByCategory();
  row.innerHTML = CATEGORIES.map((c) => {
    const isActive = c.id === cat;
    const href = buildListUrl(c.id, 1, q);
    return (
      `<a href="${href}" class="filter-chip${isActive ? ' active' : ''}" data-cat="${c.id}"` +
      `${isActive ? ' aria-current="true"' : ''}>` +
      `<span class="filter-chip-label">${escapeHtml(c.label)}</span>` +
      `<span class="filter-chip-count">${counts[c.id] ?? 0}</span>` +
      `</a>`
    );
  }).join('');
}

function renderFeatured() {
  const section = document.getElementById('featuredSection');
  const grid = document.getElementById('featuredGrid');
  const { cat, page, q } = parseState();

  if (!section || !grid) return;

  const show = cat === 'all' && page === 1 && !q;
  section.hidden = !show;
  if (!show) return;

  grid.innerHTML = TOOLS.filter((t) => t.featured)
    .slice(0, FEATURED_LIMIT)
    .map((t) => `
    <a href="${toolUrl(t)}" class="featured-card">
      <div class="featured-head">
        ${toolIcon(t)}
        <h3 class="featured-name">${escapeHtml(t.name)}</h3>
      </div>
      <p class="featured-tagline">${escapeHtml(t.tagline)}</p>
    </a>
  `).join('');
}

const TOOL_CHEVRON =
  '<svg class="tool-row-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">' +
  '<path d="M6 4l4 4-4 4" stroke-linecap="round" stroke-linejoin="round"/></svg>';

function renderListRows(tools) {
  return tools.map((t) => `
    <li class="tool-row">
      <a href="${toolUrl(t)}" class="tool-row-link">
        ${toolIcon(t, 'sm')}
        <div class="tool-row-body">
          <div class="tool-row-top">
            <h2 class="tool-row-name">${escapeHtml(t.name)}</h2>
          </div>
          <p class="tool-row-maker">${escapeHtml(t.maker)}</p>
          <p class="tool-row-desc">${escapeHtml(t.tagline)}</p>
        </div>
        <div class="tool-row-aside">
          <span class="tool-category">${escapeHtml(t.catLabel)}</span>
          ${TOOL_CHEVRON}
        </div>
      </a>
    </li>
  `).join('');
}

function renderPagination(cat, page, q, totalPages) {
  const nav = document.getElementById('pagination');
  if (!nav) return;
  if (totalPages <= 1) {
    nav.innerHTML = '';
    updateHeadLinks(cat, page, q, totalPages);
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
  updateHeadLinks(cat, page, q, totalPages);
}

function updateHeadLinks(cat, page, q, totalPages) {
  const remove = (rel) => {
    const el = document.querySelector(`link[rel="${rel}"]`);
    if (el) el.remove();
  };
  remove('prev');
  remove('next');

  if (page > 1) {
    const link = document.createElement('link');
    link.rel = 'prev';
    link.href = buildListUrl(cat, page - 1, q);
    document.head.appendChild(link);
  }
  if (page < totalPages) {
    const link = document.createElement('link');
    link.rel = 'next';
    link.href = buildListUrl(cat, page + 1, q);
    document.head.appendChild(link);
  }
}

function render() {
  const { cat, page, q } = parseState();
  const filtered = getFiltered(cat, q);
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const start = (safePage - 1) * PAGE_SIZE;
  const pageTools = filtered.slice(start, start + PAGE_SIZE);

  renderCategoryFilters(cat, q);
  renderFeatured();

  const list = document.getElementById('toolList');
  const meta = document.getElementById('resultMeta');
  const range = document.getElementById('resultRange');

  if (filtered.length === 0) {
    if (list) list.innerHTML = '<li class="tool-empty">条件に合うツールが見つかりませんでした。</li>';
    if (meta) meta.textContent = '0件';
    if (range) range.textContent = '';
    renderPagination(cat, 1, q, 1);
    return;
  }

  const end = Math.min(start + PAGE_SIZE, filtered.length);
  const catLabel = CATEGORIES.find((c) => c.id === cat)?.label || '';
  if (meta) {
    if (q || cat !== 'all') {
      meta.textContent = `${catLabel ? `${catLabel}: ` : ''}${filtered.length}件（全${TOOLS.length}件中）`;
    } else {
      meta.textContent = `${TOOLS.length}件のAIツール`;
    }
  }
  if (range) {
    range.textContent = `${start + 1}〜${end}件を表示`;
  }
  if (list) list.innerHTML = renderListRows(pageTools);
  renderPagination(cat, safePage, q, totalPages);

  const searchInput = document.getElementById('searchInput');
  if (searchInput && searchInput.value !== q) {
    searchInput.value = q;
  }

  window.SEO?.updateToolsBreadcrumb?.(cat);
}

let searchTimer;
document.getElementById('searchInput')?.addEventListener('input', (e) => {
  clearTimeout(searchTimer);
  const q = e.target.value.trim();
  searchTimer = setTimeout(() => {
    const { cat } = parseState();
    window.location.href = buildListUrl(cat, 1, q);
  }, 300);
});

function renderSitemap() {
  const list = document.getElementById('toolSitemapList');
  if (!list) return;
  list.innerHTML = TOOLS.map((t) =>
    `<li><a href="${toolUrl(t)}">${escapeHtml(t.name)}</a><span>${escapeHtml(t.catLabel)}</span></li>`
  ).join('');
}

window.addEventListener('popstate', render);
render();
renderSitemap();
