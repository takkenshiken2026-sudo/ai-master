(function () {
  const SEARCH_DEBOUNCE_MS = 800;

  function isListUrl(href) {
    if (!href || href.startsWith('#') || /^[a-z][a-z0-9+.-]*:/i.test(href)) return false;
    const path = href.split('?')[0];
    return path === '' || path === 'index.html';
  }

  function navigate(url, render) {
    if (isListUrl(url)) {
      window.history.pushState(null, '', url);
      render();
      return;
    }
    window.location.href = url;
  }

  function replace(url, render) {
    if (isListUrl(url)) {
      window.history.replaceState(null, '', url);
      render();
      return;
    }
    window.location.replace(url);
  }

  function bindLinkClicks(render) {
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href]');
      if (!link || link.target === '_blank') return;
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const href = link.getAttribute('href');
      if (!isListUrl(href)) return;
      e.preventDefault();
      navigate(href, render);
    });
  }

  function bindPopstate(render) {
    window.addEventListener('popstate', render);
  }

  function updateFilterHrefs(containerId, hrefForCat) {
    const row = document.getElementById(containerId);
    if (!row) return;
    row.querySelectorAll('a[data-cat]').forEach((link) => {
      const cat = link.dataset.cat;
      if (cat) link.href = hrefForCat(cat);
    });
  }

  function syncSearchInput(input, q) {
    if (!input || document.activeElement === input) return;
    if (input.value !== q) input.value = q;
  }

  function bindSearchInput({ inputId, render, buildUrl, debounceMs = SEARCH_DEBOUNCE_MS }) {
    const input = document.getElementById(inputId);
    if (!input) return;

    let timer;
    let composing = false;

    function applySearch() {
      if (composing) return;
      clearTimeout(timer);
      replace(buildUrl(input.value.trim()), render);
    }

    function scheduleSearch() {
      if (composing) return;
      clearTimeout(timer);
      timer = setTimeout(applySearch, debounceMs);
    }

    input.addEventListener('compositionstart', () => {
      composing = true;
      clearTimeout(timer);
    });

    input.addEventListener('compositionend', () => {
      composing = false;
      scheduleSearch();
    });

    input.addEventListener('input', () => {
      if (composing) return;
      scheduleSearch();
    });

    input.addEventListener('keydown', (e) => {
      if (e.key !== 'Enter') return;
      e.preventDefault();
      clearTimeout(timer);
      if (composing) return;
      navigate(buildUrl(input.value.trim()), render);
    });

    input.addEventListener('search', () => {
      if (input.value !== '') return;
      clearTimeout(timer);
      applySearch();
    });
  }

  window.HubNav = {
    navigate,
    replace,
    bindLinkClicks,
    bindPopstate,
    bindSearchInput,
    syncSearchInput,
    updateFilterHrefs,
    SEARCH_DEBOUNCE_MS,
  };
})();
