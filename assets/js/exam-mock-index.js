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

  function examRowHtml(exam, minutes) {
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

  function buyButtonHtml(examSlug, bundleId, bundleTitle, className) {
    return `<button
        type="button"
        class="${className}"
        data-exam-slug="${escapeAttr(examSlug)}"
        data-exam-id="${escapeAttr(bundleId)}"
        data-exam-title="${escapeAttr(bundleTitle)}"
      >購入する</button>`;
  }

  function pitchHtml(pitch, buyOptions) {
    if (!pitch) return "";
    const whyPoints = (pitch.whyPoints || [])
      .map(
        (point) => `<li class="mock-purchase-pitch__item">
          <h3 class="mock-purchase-pitch__item-title">${escapeHtml(point.title)}</h3>
          <p class="mock-purchase-pitch__item-body">${escapeHtml(point.body)}</p>
        </li>`
      )
      .join("");
    const forPoints = (pitch.forPoints || [])
      .map((point) => `<li>${escapeHtml(point)}</li>`)
      .join("");
    const bottomBuy = buyOptions
      ? `<div class="mock-purchase-pitch__cta">
          ${buyButtonHtml(
            buyOptions.examSlug,
            buyOptions.bundleId,
            buyOptions.bundleTitle,
            "mock-purchase__buy mock-purchase__buy--secondary"
          )}
        </div>`
      : "";

    return `<div class="mock-purchase-pitch">
        <section class="mock-purchase-pitch__section">
          <h2 class="mock-purchase-pitch__heading">${escapeHtml(pitch.whyTitle || "")}</h2>
          <p class="mock-purchase-pitch__lead">${escapeHtml(pitch.whyLead || "")}</p>
          <ul class="mock-purchase-pitch__reasons">${whyPoints}</ul>
        </section>
        <section class="mock-purchase-pitch__section">
          <h2 class="mock-purchase-pitch__heading">${escapeHtml(pitch.forTitle || "")}</h2>
          <ul class="mock-purchase-pitch__checks">${forPoints}</ul>
        </section>
        <section class="mock-purchase-pitch__section mock-purchase-pitch__section--muted">
          <h2 class="mock-purchase-pitch__heading">${escapeHtml(pitch.compareTitle || "")}</h2>
          <p class="mock-purchase-pitch__compare">${escapeHtml(pitch.compareBody || "")}</p>
        </section>
        ${bottomBuy}
      </div>`;
  }

  function purchasePageHtml(options) {
    const {
      priceLabel,
      examSlug,
      bundleId,
      bundleTitle,
      minutes,
      questionCount,
      showNotice,
      pitch,
    } = options;
    const notice = showNotice
      ? '<p class="mock-purchase__notice">受験には購入が必要です。購入済みの方はメールのリンクから入るか、購入完了画面のリンクをご利用ください。</p>'
      : "";
    const buyOptions = { examSlug, bundleId, bundleTitle };
    return `<section class="mock-purchase" data-exam-id="${escapeAttr(bundleId)}">
        ${notice}
        <div class="mock-purchase__card">
          <p class="mock-purchase__eyebrow">3本セット · 買い切り</p>
          <h2 class="mock-purchase__title">${escapeHtml(bundleTitle)}</h2>
          <p class="mock-purchase__price">${escapeHtml(priceLabel)}</p>
          <ul class="mock-purchase__features">
            <li>模擬試験 <strong>3回分</strong>（第1回・第2回・第3回）</li>
            <li>各回 <strong>${questionCount}問 · ${minutes}分</strong>（本番形式）</li>
            <li>購入後は <strong>何度でも再受験</strong>できます</li>
          </ul>
          ${buyButtonHtml(examSlug, bundleId, bundleTitle, "mock-purchase__buy")}
          <p class="mock-purchase__foot">購入後、このページに第1回・第2回・第3回が表示されます。</p>
        </div>
        ${pitchHtml(pitch, buyOptions)}
      </section>`;
  }

  function setIntro(introEl, text) {
    if (introEl && text) introEl.textContent = text;
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
    const introEl = document.querySelector(".hub-intro");

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

      const copyUrl =
        config.purchaseCopyUrl || "/assets/data/mock-purchase-copy.json";
      const [examRes, copyRes] = await Promise.all([
        fetch(dataUrl),
        fetch(copyUrl).catch(() => null),
      ]);
      const data = await examRes.json();
      let pitch = null;
      if (copyRes?.ok) {
        try {
          const allCopy = await copyRes.json();
          pitch = allCopy[examSlug] || null;
        } catch {
          pitch = null;
        }
      }
      const exams = data.exams || {};
      const minutes = data.timeLimitMinutes || 60;
      const enabled = mockExamsEnabled();
      const firstExam = exams[examOrder[0]];
      const questionCount = firstExam?.questionCount || "";

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

      if (checkoutOn && !hasBundle) {
        setIntro(
          introEl,
          config.purchaseIntro ||
            "本番・過去問を想定した模擬試験です。3回分をセットでご購入いただけます。"
        );
        list.innerHTML = purchasePageHtml({
          priceLabel,
          examSlug,
          bundleId,
          bundleTitle,
          minutes,
          questionCount,
          showNotice: Boolean(purchaseParam),
          pitch,
        });
      } else {
        setIntro(
          introEl,
          checkoutOn
            ? config.purchasedIntro ||
                "受験する回を選んでください。購入済みのため、何度でも再受験できます。"
            : config.freeIntro ||
                "本番・過去問を想定した模擬試験です。受験する回を選んでください。"
        );
        for (const id of examOrder) {
          const exam = exams[id];
          if (!exam) continue;
          const row = document.createElement("div");
          row.innerHTML = examRowHtml({ ...exam, id }, minutes);
          list.appendChild(row.firstElementChild);
        }
      }

      list.addEventListener("click", async (event) => {
        const btn = event.target.closest(".mock-purchase__buy, .exam-mode-row__buy");
        if (!btn || !commerce) return;
        const examId = btn.dataset.examId;
        const slug = btn.dataset.examSlug;
        const title = btn.dataset.examTitle;
        if (!examId || !slug) return;

        const email = await commerce.showPurchaseDialog({
          examTitle: title,
          priceLabel,
        });
        if (email === null) return;

        btn.disabled = true;
        const original = btn.textContent;
        btn.textContent = "Stripeへ移動中…";
        try {
          await commerce.startCheckout(slug, examId, title, email);
        } catch (error) {
          btn.disabled = false;
          btn.textContent = original;
          await commerce.showMessageDialog({
            title: "購入を開始できませんでした",
            message:
              error instanceof Error
                ? error.message
                : "しばらくしてから再度お試しください。",
          });
        }
      });
    } catch {
      list.innerHTML = "<p>模擬試験データを読み込めませんでした。</p>";
    }
  });
})();
