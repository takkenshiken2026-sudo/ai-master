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

  function escapeAttr(str) {
    return escapeHtml(str).replace(/'/g, "&#39;");
  }

  function paidRowHtml(exam, minutes, options) {
    const { hasAccess, priceLabel, examSlug, examId } = options;
    const action = hasAccess
      ? `<a href="play.html?exam=${encodeURIComponent(examId)}" class="exam-mode-row exam-mode-row--mock">
          <div class="exam-mode-row__main">
            <div class="exam-mode-row__head">
              <h2 class="exam-mode-row__name">${escapeHtml(exam.title)}</h2>
              <span class="exam-mode-badge exam-mode-badge--paid">購入済み</span>
            </div>
            <p class="exam-mode-row__desc">本番と同じ問題数・制限時間で一気に解く総仕上げです。時間配分の練習や実力チェックに向いています。</p>
            <p class="exam-mode-row__meta">${exam.questionCount}問 · ${minutes}分</p>
          </div>
          <span class="exam-mode-row__go">受験する<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M6 4l4 4-4 4" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
        </a>`
      : `<div class="exam-mode-row exam-mode-row--mock exam-mode-row--purchase">
          <div class="exam-mode-row__main">
            <div class="exam-mode-row__head">
              <h2 class="exam-mode-row__name">${escapeHtml(exam.title)}</h2>
              <span class="exam-mode-badge exam-mode-badge--paid">有料</span>
            </div>
            <p class="exam-mode-row__desc">本番と同じ問題数・制限時間で一気に解く総仕上げです。購入後はメールのリンクから何度でも受験できます（買い切り）。</p>
            <p class="exam-mode-row__meta">${exam.questionCount}問 · ${minutes}分 · ${escapeHtml(priceLabel)}（買い切り）</p>
          </div>
          <button
            type="button"
            class="exam-mode-row__buy"
            data-exam-slug="${escapeAttr(examSlug)}"
            data-exam-id="${escapeAttr(examId)}"
            data-exam-title="${escapeAttr(exam.title)}"
          >購入する</button>
        </div>`;
    return action;
  }

  function showPurchaseNotice(list, examId) {
    const notice = document.createElement("p");
    notice.className = "mock-purchase-notice";
    notice.textContent =
      "この模擬試験は購入後に受験できます。購入済みの方はメールの受験リンクから入るか、購入完了画面のリンクをご利用ください。";
    list.prepend(notice);
    if (!examId) return;
    const row = list.querySelector(`[data-exam-id="${CSS.escape(examId)}"]`)?.closest(".exam-mode-row");
    row?.scrollIntoView({ behavior: "smooth", block: "center" });
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
    const examSlug = config.examSlug || "";
    const examOrder = config.examOrder || ["mock_01", "mock_02", "mock_03"];
    const sampleDesc =
      config.sampleDesc ||
      "3問だけ試せるサンプルです。操作感を確認してから本番形式に挑戦できます。";

    if (!dataUrl || !examSlug) {
      list.innerHTML = "<p>模擬試験の設定がありません。</p>";
      return;
    }

    const purchaseParam = new URLSearchParams(window.location.search).get("purchase");

    try {
      const commerce = window.MockCommerce;
      const commerceConfig = commerce ? await commerce.loadConfig() : null;
      const checkoutOn = commerce && commerce.isCheckoutEnabled(commerceConfig);
      const priceLabel = commerce ? commerce.formatPrice(commerceConfig) : "¥980";

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

      if (checkoutOn) {
        const intro = document.querySelector(".hub-intro");
        if (intro) {
          intro.textContent +=
            " 有料回は1回あたり買い切りです。購入後はメールの受験リンクから再入場できます。";
        }
      }

      for (const id of examOrder) {
        const exam = exams[id];
        if (!exam) continue;

        let hasAccess = true;
        if (checkoutOn && commerce) {
          hasAccess = await commerce.hasAccess(examSlug, id);
        }

        const row = document.createElement("div");
        row.innerHTML = paidRowHtml(exam, minutes, {
          hasAccess,
          priceLabel,
          examSlug,
          examId: id,
        });
        list.appendChild(row.firstElementChild);
      }

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

      if (checkoutOn && purchaseParam) {
        showPurchaseNotice(list, purchaseParam);
      }

      list.addEventListener("click", async (event) => {
        const btn = event.target.closest(".exam-mode-row__buy");
        if (!btn || !commerce) return;
        const examId = btn.dataset.examId;
        const slug = btn.dataset.examSlug;
        const title = btn.dataset.examTitle;
        if (!examId || !slug) return;

        const email = window.prompt(
          "購入確認メールを送るメールアドレス（任意・空欄可）",
          ""
        );
        if (email === null) return;

        btn.disabled = true;
        const original = btn.textContent;
        btn.textContent = "Stripeへ移動中…";
        try {
          await commerce.startCheckout(slug, examId, title, email.trim());
        } catch (error) {
          btn.disabled = false;
          btn.textContent = original;
          window.alert(
            error instanceof Error ? error.message : "購入を開始できませんでした。"
          );
        }
      });
    } catch {
      list.innerHTML = "<p>模擬試験データを読み込めませんでした。</p>";
    }
  });
})();
