/** ハブ人気カード — 用語辞典・学習ガイド・キャリア共通 */
const HUB_ICON_BASE = '../assets/images/';

function hubFeaturedIcon(iconPath) {
  if (!iconPath) return '';
  return (
    `<div class="hub-featured-icon">` +
    `<img src="${HUB_ICON_BASE}${iconPath}" alt="" width="32" height="32" loading="lazy">` +
    `</div>`
  );
}

function hubFeaturedCardInner(name, summary, icon, badgeHtml) {
  const badge = badgeHtml || '';
  const title = `<h3 class="hub-featured-name">${name}</h3>`;
  const head = icon
    ? `<div class="hub-featured-head">${hubFeaturedIcon(icon)}${title}</div>`
    : badge + title;
  const sum = summary ? `<p class="hub-featured-summary">${summary}</p>` : '';
  return head + sum;
}
