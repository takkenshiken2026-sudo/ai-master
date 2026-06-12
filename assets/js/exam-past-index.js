(function () {
  "use strict";

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function examRowHtml(exam, minutes) {
    return `<a href="play.html?exam=${encodeURIComponent(exam.id)}" class="exam-mode-row">
        <div class="exam-mode-row__main">
          <div class="exam-mode-row__head">
            <h2 class="exam-mode-row__name">${escapeHtml(exam.title)}</h2>
          </div>
          <p class="exam-mode-row__desc">本番と同じ問題数・制限時間で一気に解く演習です。時間配分の練習や実力チェックに向いています。</p>
          <p class="exam-mode-row__meta">${exam.questionCount}問 · ${minutes}分</p>
        </div>
        <span class="exam-mode-row__go">受験する<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M6 4l4 4-4 4" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
      </a>`;
  }

  document.addEventListener("DOMContentLoaded", async () => {
    const list = document.getElementById("past-pick-list");
    if (!list) return;

    let config = {};
    try {
      config = JSON.parse(list.dataset.pastConfig || "{}");
    } catch {
      config = {};
    }

    const dataUrl = config.dataUrl;
    const examOrder = config.examOrder || [];
    const introEl = document.querySelector(".hub-intro");

    if (!dataUrl) {
      list.innerHTML = "<p>過去問の設定がありません。</p>";
      return;
    }

    try {
      const res = await fetch(dataUrl);
      const data = await res.json();
      const exams = data.exams || {};
      const minutes = data.timeLimitMinutes || 120;
      const orderedIds =
        examOrder.length > 0 ? examOrder : Object.keys(exams);

      list.innerHTML = "";
      let count = 0;
      for (const id of orderedIds) {
        const exam = exams[id];
        if (!exam) continue;
        const row = document.createElement("div");
        row.innerHTML = examRowHtml({ ...exam, id }, minutes);
        list.appendChild(row.firstElementChild);
        count += 1;
      }

      if (!count) {
        list.innerHTML =
          '<p class="mock-unavailable">過去問は現在準備中です。公開までお待ちください。</p>';
        if (introEl && config.preparingIntro) {
          introEl.textContent = config.preparingIntro;
        }
      } else if (introEl && config.intro) {
        introEl.textContent = config.intro;
      }
    } catch {
      list.innerHTML = "<p>過去問データを読み込めませんでした。</p>";
    }
  });
})();
