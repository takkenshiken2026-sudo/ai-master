(function () {
  "use strict";

  function mockExamsEnabled() {
    return !(window.AI_MASTER && window.AI_MASTER.mockExamsEnabled === false);
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  document.addEventListener("DOMContentLoaded", async () => {
    const list = document.getElementById("mock-pick-list");
    if (!list) return;

    let config = {};
    try {
      config = JSON.parse(list.dataset.mockConfig || "{}");
    } catch {
      config = {};
    }

    const dataUrl = config.dataUrl;
    const examOrder = config.examOrder || ["mock_01", "mock_02", "mock_03"];
    const sampleDesc =
      config.sampleDesc ||
      "3問だけ試せるサンプルです。操作感を確認してから本番形式に挑戦できます。";

    if (!dataUrl) {
      list.innerHTML = "<p>模擬試験の設定がありません。</p>";
      return;
    }

    try {
      const res = await fetch(dataUrl);
      const data = await res.json();
      const exams = data.exams || {};
      const minutes = data.timeLimitMinutes || 60;
      const enabled = mockExamsEnabled();

      list.innerHTML = "";

      if (!enabled) {
        list.innerHTML =
          '<p class="mock-unavailable">模擬試験は現在準備中です。受験は公開までお待ちください。</p>';
        return;
      }

      examOrder.forEach((id) => {
        const exam = exams[id];
        if (!exam) return;

        const a = document.createElement("a");
        a.href = `play.html?exam=${encodeURIComponent(id)}`;
        a.className = "exam-mode-row";
        a.innerHTML = `
          <div class="exam-mode-row__main">
            <div class="exam-mode-row__head">
              <h2 class="exam-mode-row__name">${escapeHtml(exam.title)}</h2>
            </div>
            <p class="exam-mode-row__desc">本番と同じ問題数・制限時間で一気に解く総仕上げです。時間配分の練習や実力チェックに向いています。</p>
            <p class="exam-mode-row__meta">${exam.questionCount}問 · ${minutes}分</p>
          </div>
          <span class="exam-mode-row__go">受験する<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M6 4l4 4-4 4" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
        `;
        list.appendChild(a);
      });

      const sample = exams.sample;
      if (sample) {
        const sampleRow = document.createElement("a");
        sampleRow.href = "play.html?exam=sample";
        sampleRow.className = "exam-mode-row exam-mode-row--sample";
        sampleRow.innerHTML = `
          <div class="exam-mode-row__main">
            <div class="exam-mode-row__head">
              <h2 class="exam-mode-row__name">${escapeHtml(sample.title)}</h2>
              <span class="exam-mode-badge exam-mode-badge--free">お試し</span>
            </div>
            <p class="exam-mode-row__desc">${escapeHtml(sampleDesc)}</p>
            <p class="exam-mode-row__meta">${sample.questionCount}問 · 制限時間なし</p>
          </div>
          <span class="exam-mode-row__go">試す<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M6 4l4 4-4 4" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
        `;
        list.appendChild(sampleRow);
      }
    } catch {
      list.innerHTML = "<p>模擬試験データを読み込めませんでした。</p>";
    }
  });
})();
