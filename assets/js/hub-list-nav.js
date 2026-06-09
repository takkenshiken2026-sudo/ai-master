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

  window.HubNav = { navigate, replace, bindLinkClicks, bindPopstate };
})();
