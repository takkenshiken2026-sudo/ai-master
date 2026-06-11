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
    if (category.startsWith('genai')) return 'AIパスポート';
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

function hubTileLabelClass(label) {
  if (!label) return 'hub-list-icon-tile__label';
  if (label === 'AIパスポート') {
    return 'hub-list-icon-tile__label hub-list-icon-tile__label--micro';
  }
  // 64pxタイルで切れる長さ（5文字以上）のみ 10px に縮小
  return label.length >= 5
    ? 'hub-list-icon-tile__label hub-list-icon-tile__label--compact'
    : 'hub-list-icon-tile__label';
}

function hubListIconTile(iconPath, label) {
  const icon = iconPath
    ? `<img class="hub-list-icon-tile__img" src="${HUB_ICON_BASE}${iconPath}" alt="" width="34" height="34" loading="lazy">`
    : '<span class="hub-list-icon-tile__img hub-list-icon-tile__img--empty" aria-hidden="true"></span>';
  const text = label ? `<span class="${hubTileLabelClass(label)}">${label}</span>` : '';
  return `<div class="hub-list-icon-tile">${icon}${text}</div>`;
}

function hubListIcon(iconPath, label) {
  return hubListIconTile(iconPath, label || '');
}

function hubFeaturedCardIcon(iconPath, tileLabel) {
  if (!iconPath) return '';
  if (iconPath.includes('hub-icons/')) {
    return hubListIconTile(iconPath, tileLabel || '');
  }
  return hubFeaturedIcon(iconPath);
}

function hubFeaturedCardInner(name, summary, icon, badgeHtml, tileLabel) {
  const badge = badgeHtml || '';
  const title = `<h3 class="hub-featured-name">${name}</h3>`;
  const iconHtml = hubFeaturedCardIcon(icon, tileLabel);
  const head = iconHtml || badge
    ? `<div class="hub-featured-head">${iconHtml}${badge}${title}</div>`
    : title;
  const sum = summary ? `<p class="hub-featured-summary">${summary}</p>` : '';
  return head + sum;
}
