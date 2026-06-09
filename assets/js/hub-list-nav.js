(function () {
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

  /** 入力中は一覧を更新せず、Enter またはクリア時のみ検索する */
  function bindSearchInput({ inputId, render, buildUrl, getCurrentQ }) {
    const input = document.getElementById(inputId);
    if (!input) return;

    let composing = false;

    function urlQuery() {
      if (getCurrentQ) return getCurrentQ();
      return (new URLSearchParams(window.location.search).get('q') || '').trim();
    }

    function applySearch(usePush) {
      if (composing) return;
      const q = input.value.trim();
      if (q === urlQuery()) return;
      const url = buildUrl(q);
      if (usePush) navigate(url, render);
      else replace(url, render);
    }

    input.addEventListener('compositionstart', () => {
      composing = true;
    });

    input.addEventListener('compositionend', () => {
      composing = false;
    });

    input.addEventListener('keydown', (e) => {
      if (e.key !== 'Enter') return;
      e.preventDefault();
      applySearch(true);
    });

    input.addEventListener('search', () => {
      applySearch(false);
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
  };
})();
