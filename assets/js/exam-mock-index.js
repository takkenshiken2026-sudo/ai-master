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

  function examRowHtml(exam, minutes, options) {
    const { unlocked } = options;
    if (unlocked) {
      return `<a href="play.html?exam=${encodeURIComponent(exam.id)}" class="exam-mode-row exam-mode-row--mock">
          <div class="exam-mode-row__main">
            <div class="exam-mode-row__head">
              <h2 class="exam-mode-row__name">${escapeHtml(exam.title)}</h2>
            </div>
            <p class="exam-mode-row__desc">本番と同じ問題数・制限時間で一気に解く総仕上げです。時間配分の練習や実力チェックに向いています。</p>
            <p class="exam-mode-row__meta">${exam.questionCount}問 · ${minutes}分</p>
          </div>
          <span class="exam-mode-row__go">受験する<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M6 4l4 4-4 4" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
        </a>`;
    }
    return `<div class="exam-mode-row exam-mode-row--mock exam-mode-row--locked">
        <div class="exam-mode-row__main">
          <div class="exam-mode-row__head">
            <h2 class="exam-mode-row__name">${escapeHtml(exam.title)}</h2>
            <span class="exam-mode-badge exam-mode-badge--paid">セット購入後</span>
          </div>
          <p class="exam-mode-row__desc">3本セットを購入すると、すべての模擬試験を何度でも受験できます。</p>
          <p class="exam-mode-row__meta">${exam.questionCount}問 · ${minutes}分</p>
        </div>
      </div>`;
  }

  function bundlePurchaseHtml(options) {
    const { priceLabel, examSlug, bundleId, bundleTitle } = options;
    return `<div class="exam-mode-row exam-mode-row--mock exam-mode-row--purchase exam-mode-row--bundle" data-exam-id="${escapeAttr(bundleId)}">
        <div class="exam-mode-row__main">
          <div class="exam-mode-row__head">
            <h2 class="exam-mode-row__name">${escapeHtml(bundleTitle)}</h2>
            <span class="exam-mode-badge exam-mode-badge--paid">3本セット</span>
          </div>
          <p class="exam-mode-row__desc">模擬試験3回分をまとめて購入できます。購入後は3回すべて何度でも受験可能です（買い切り）。</p>
          <p class="exam-mode-row__meta">3回分 · ${escapeHtml(priceLabel)}（買い切り）</p>
        </div>
        <button
          type="button"
          class="exam-mode-row__buy"
          data-exam-slug="${escapeAttr(examSlug)}"
          data-exam-id="${escapeAttr(bundleId)}"
          data-exam-title="${escapeAttr(bundleTitle)}"
        >購入する</button>
      </div>`;
  }

  function showPurchaseNotice(list, bundleId) {
    const notice = document.createElement("p");
    notice.className = "mock-purchase-notice";
    notice.textContent =
      "模擬試験は3本セット購入後に受験できます。購入済みの方はメールのリンクから入るか、購入完了画面のリンクをご利用ください。";
    list.prepend(notice);
    if (!bundleId) return;
    const row = list.querySelector(`[data-exam-id="${CSS.escape(bundleId)}"]`);
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
    const bundleTitle = config.bundleTitle || "模擬試験3本セット";

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
      const bundleId = commerce
        ? commerce.bundleExamId(commerceConfig)
        : "bundle";

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

      let hasBundle = true;
      if (checkoutOn && commerce) {
        hasBundle = await commerce.hasBundleAccess(examSlug);
      }

      if (checkoutOn) {
        const intro = document.querySelector(".hub-intro");
        if (intro) {
          intro.textContent +=
            " 3本セットの買い切りです。購入後は3回すべて何度でも受験できます。";
        }
      }

      if (checkoutOn && !hasBundle) {
        const bundleWrap = document.createElement("div");
        bundleWrap.innerHTML = bundlePurchaseHtml({
          priceLabel,
          examSlug,
          bundleId,
          bundleTitle,
        });
        list.appendChild(bundleWrap.firstElementChild);
      }

      for (const id of examOrder) {
        const exam = exams[id];
        if (!exam) continue;

        const row = document.createElement("div");
        row.innerHTML = examRowHtml(
          { ...exam, id },
          minutes,
          { unlocked: hasBundle || !checkoutOn }
        );
        list.appendChild(row.firstElementChild);
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
