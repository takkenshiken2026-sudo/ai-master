(function () {
  "use strict";

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderStatLabel(stat) {
    const note = stat.note ? `（${stat.note}）` : "";
    return `${stat.label}${note}`;
  }

  function renderStats(stats) {
    return stats
      .map(
        (stat) => `
        <div class="exam-hero__stat">
          <p class="exam-hero__stat-value">${escapeHtml(stat.value)}</p>
          <p class="exam-hero__stat-label">${escapeHtml(renderStatLabel(stat))}</p>
        </div>`
      )
      .join("");
  }

  function renderHero(profile, modeKey) {
    const hub = profile.hub;
    const mode = profile.modes?.[modeKey] || {};
    const isHub = modeKey === "hub";
    const modeLabel = mode.label || "";
    const title = isHub
      ? hub?.title || `${profile.examName} 試験対策`
      : modeLabel
        ? `${profile.examName} ${modeLabel}`
        : profile.examName;
    const ledeParts = [...(profile.lede || [])];
    if (isHub && hub?.hint) {
      ledeParts.push(hub.hint);
    }
    const lede = ledeParts
      .map((p) => `<p class="exam-hero__lede">${escapeHtml(p)}</p>`)
      .join("");
    const hint =
      !isHub && mode.hint
        ? `<p class="exam-hero__hint">${escapeHtml(mode.hint)} <a href="questions/">問題一覧</a>（解説付き）も閲覧できます。</p>`
        : "";

    return `
      <div class="exam-hero__inner">
        <p class="exam-hero__org">${escapeHtml(profile.org || "")}</p>
        <h1 class="exam-hero__title">${escapeHtml(title)}</h1>
        <div class="exam-hero__copy">${lede}</div>
        ${hint}
        <div class="exam-hero__stats" aria-label="試験概要">
          ${renderStats(profile.stats || [])}
        </div>
        <p class="exam-hero__disclaimer">当サイトの問題は本番・過去問を想定した模擬問題です（公式の過去問ではありません）。</p>
      </div>
    `;
  }

  document.addEventListener("DOMContentLoaded", async () => {
    const root = document.querySelector("[data-exam-hero]");
    if (!root) return;

    const examId = root.dataset.examHero;
    const modeKey = root.dataset.examMode || "";
    if (!examId) return;

    const profilesUrl =
      root.dataset.profilesUrl || "../../../assets/data/exam-profiles.json";

    try {
      const res = await fetch(profilesUrl);
      if (!res.ok) throw new Error("profile load failed");
      const data = await res.json();
      const profile = data[examId];
      if (!profile) throw new Error("unknown exam");
      root.innerHTML = renderHero(profile, modeKey);
      root.hidden = false;
    } catch {
      root.innerHTML = `<p class="exam-hero__fallback">試験情報を読み込めませんでした。</p>`;
      root.hidden = false;
    }
  });
})();
