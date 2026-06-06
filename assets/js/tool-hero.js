/**
 * tool-hero--split: 右カラムの画像高さを左コンテンツに合わせる（比率維持）
 */
(function () {
  var MQ = '(max-width: 900px)';

  function syncHero(hero) {
    var body = hero.querySelector('.tool-hero-body');
    var visual = hero.querySelector('.tool-hero-visual');
    if (!body || !visual) return;

    if (window.matchMedia(MQ).matches) {
      visual.style.maxHeight = '';
      return;
    }

    visual.style.maxHeight = body.offsetHeight + 'px';
  }

  function initHeroSync() {
    document.querySelectorAll('.tool-hero--split').forEach(function (hero) {
      syncHero(hero);

      if (typeof ResizeObserver === 'undefined') return;

      var body = hero.querySelector('.tool-hero-body');
      if (!body) return;

      var ro = new ResizeObserver(function () {
        syncHero(hero);
      });
      ro.observe(body);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHeroSync);
  } else {
    initHeroSync();
  }

  window.addEventListener('resize', initHeroSync);

  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(initHeroSync);
  }
})();
