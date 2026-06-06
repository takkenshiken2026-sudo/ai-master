(function () {
  "use strict";

  function mockExamsEnabled() {
    return !(window.AI_MASTER && window.AI_MASTER.mockExamsEnabled === false);
  }

  document.addEventListener("DOMContentLoaded", async () => {
    const grid = document.getElementById("mock-pick-grid");
    if (!grid) return;

    let config = {};
    try {
      config = JSON.parse(grid.dataset.mockConfig || "{}");
    } catch {
      config = {};
    }

    const dataUrl = config.dataUrl;
    const examOrder = config.examOrder || ["mock_01", "mock_02", "mock_03"];

    if (!dataUrl) {
      grid.innerHTML = "<p>模擬試験の設定がありません。</p>";
      return;
    }

    try {
      const res = await fetch(dataUrl);
      const data = await res.json();
      const exams = data.exams || {};
      const minutes = data.timeLimitMinutes || 60;

      const enabled = mockExamsEnabled();
      grid.innerHTML = enabled
        ? ""
        : '<p class="mock-unavailable">模擬試験は現在準備中です。受験は公開までお待ちください。</p>';

      examOrder.forEach((id) => {
        const exam = exams[id];
        if (!exam) return;
        if (enabled) {
          const a = document.createElement("a");
          a.href = `play.html?exam=${encodeURIComponent(id)}`;
          a.className = "mock-pick-card";
          a.innerHTML = `
            <h2 class="mock-pick-name">${exam.title}</h2>
            <p class="mock-pick-meta">${exam.questionCount}問 · ${minutes}分</p>
            <span class="mock-pick-cta">受験する →</span>
          `;
          grid.appendChild(a);
          return;
        }
        const card = document.createElement("div");
        card.className = "mock-pick-card mock-pick-card--disabled";
        card.innerHTML = `
          <h2 class="mock-pick-name">${exam.title}</h2>
          <p class="mock-pick-meta">${exam.questionCount}問 · ${minutes}分</p>
          <span class="mock-pick-cta">準備中</span>
        `;
        grid.appendChild(card);
      });

      const sample = exams.sample;
      const sampleLink = document.getElementById("mock-sample-link");
      if (sample && sampleLink && enabled) {
        sampleLink.href = "play.html?exam=sample";
        sampleLink.hidden = false;
      }
    } catch {
      grid.innerHTML = "<p>模擬試験データを読み込めませんでした。</p>";
    }
  });
})();
