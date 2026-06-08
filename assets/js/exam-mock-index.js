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
      ? '<p class="mock-landing__notice">受験には購入が必要です。購入済みの方はメールのリンクから入るか、購入完了画面のリンクをご利用ください。</p>'
      : "";
    const whyPoints = (pitch?.whyPoints || [])
      .map(
        (point, index) => `<li class="mock-landing-point">
          <span class="mock-landing-point__no">${String(index + 1).padStart(2, "0")}</span>
          <div class="mock-landing-point__body">
            <h3 class="mock-landing-point__title">${escapeHtml(point.title)}</h3>
            <p class="mock-landing-point__text">${escapeHtml(point.body)}</p>
          </div>
        </li>`
      )
      .join("");
    const forPoints = (pitch?.forPoints || [])
      .map((point) => `<li>${escapeHtml(point)}</li>`)
      .join("");
    const pitchWhy = pitch
      ? `<section class="mock-landing-section">
          <h2 class="mock-landing-section__title">${escapeHtml(pitch.whyTitle || "")}</h2>
          <p class="mock-landing-section__lead">${escapeHtml(pitch.whyLead || "")}</p>
          <ol class="mock-landing-points">${whyPoints}</ol>
        </section>
        <section class="mock-landing-section">
          <h2 class="mock-landing-section__title">${escapeHtml(pitch.forTitle || "")}</h2>
          <ul class="mock-landing-checks">${forPoints}</ul>
        </section>
        <section class="mock-landing-section mock-landing-section--band">
          <h2 class="mock-landing-section__title">${escapeHtml(pitch.compareTitle || "")}</h2>
          <p class="mock-landing-section__text">${escapeHtml(pitch.compareBody || "")}</p>
        </section>`
      : "";

    return `<div class="mock-landing" data-exam-id="${escapeAttr(bundleId)}">
        ${notice}
        <div class="mock-landing-hero">
          <div class="mock-landing-hero__copy">
            <p class="mock-landing-hero__eyebrow">模擬試験 · 3本セット · 買い切り</p>
            <p class="mock-landing-hero__price">${escapeHtml(priceLabel)}</p>
            <p class="mock-landing-hero__spec">第1回・第2回・第3回 · 各 ${escapeHtml(String(questionCount))}問 · ${minutes}分</p>
            <p class="mock-landing-hero__desc">購入後は3回すべて何度でも受験できます。第1回から順に、またはお好きな回から始められます。</p>
            ${buyButtonHtml(examSlug, bundleId, bundleTitle, "mock-landing-hero__buy")}
          </div>
          <ul class="mock-landing-hero__facts" aria-label="セット内容">
            <li><strong>3回</strong><span>模擬試験</span></li>
            <li><strong>${escapeHtml(String(questionCount))}問</strong><span>各回の出題数</span></li>
            <li><strong>${minutes}分</strong><span>制限時間</span></li>
            <li><strong>再受験</strong><span>何度でも可</span></li>
          </ul>
        </div>
        <div class="mock-landing-body">
          ${pitchWhy}
          <div class="mock-landing-cta">
            <div class="mock-landing-cta__copy">
              <p class="mock-landing-cta__title">${escapeHtml(bundleTitle)}</p>
              <p class="mock-landing-cta__meta">${escapeHtml(priceLabel)} · 3本セット · 買い切り</p>
            </div>
            ${buyButtonHtml(examSlug, bundleId, bundleTitle, "mock-landing-cta__buy")}
          </div>
        </div>
      </div>`;
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

      const pageWrap = document.querySelector(".page-wrap");

      if (checkoutOn && !hasBundle) {
        pageWrap?.classList.add("page-wrap--mock-sales");
        setIntro(
          introEl,
          config.purchaseIntro ||
            "本番・過去問を想定した模擬試験です。3回分をセットでご購入いただけます。"
        );
        list.classList.remove("exam-mode-list");
        list.classList.add("mock-landing-root");
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
        pageWrap?.classList.remove("page-wrap--mock-sales");
        list.classList.add("exam-mode-list");
        list.classList.remove("mock-landing-root");
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
        const btn = event.target.closest(
          ".mock-landing-hero__buy, .mock-landing-cta__buy, .exam-mode-row__buy"
        );
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
