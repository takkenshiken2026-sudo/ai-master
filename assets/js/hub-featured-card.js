/** ハブ人気カード — 用語辞典・学習ガイド・キャリア共通 */
const HUB_ICON_BASE = '../assets/images/';

const HUB_CATEGORY_SHORT = {
  glossary: {
    basics: '基礎',
    'models-tech': 'モデル',
    'genai-use': '生成AI',
    'data-ops': 'データ',
    governance: '倫理',
  },
  career: {
    role: '職種',
    learn: '学ぶ',
    move: '転職',
    market: '市場',
  },
};

function hubCategoryShortLabel(hub, category, fullLabel) {
  const mapped = HUB_CATEGORY_SHORT[hub]?.[category];
  if (mapped) return mapped;
  if (hub === 'guide') {
    if (category.startsWith('g-kentei')) return 'G検定';
    if (category.startsWith('genai')) return 'パスポート';
    const guideLabels = {
      compare: '比較',
      terms: '用語',
      audience: '対象者',
      enterprise: '企業',
      trends: 'トレンド',
      'exam-tips': '受験',
      'after-cert': '取得後',
    };
    if (guideLabels[category]) return guideLabels[category];
  }
  if (fullLabel && fullLabel.includes('・')) return fullLabel.split('・')[0];
  return fullLabel || category;
}

function hubFeaturedIcon(iconPath) {
  if (!iconPath) return '';
  return (
    `<div class="hub-featured-icon">` +
    `<img src="${HUB_ICON_BASE}${iconPath}" alt="" width="56" height="56" loading="lazy">` +
    `</div>`
  );
}

function hubListIconTile(iconPath, label) {
  const icon = iconPath
    ? `<img class="hub-list-icon-tile__img" src="${HUB_ICON_BASE}${iconPath}" alt="" width="32" height="32" loading="lazy">`
    : '<span class="hub-list-icon-tile__img hub-list-icon-tile__img--empty" aria-hidden="true"></span>';
  const text = label
    ? `<span class="hub-list-icon-tile__label">${label}</span>`
    : '';
  return `<div class="hub-list-icon-tile">${icon}${text}</div>`;
}

function hubListIcon(iconPath, label) {
  return hubListIconTile(iconPath, label || '');
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
