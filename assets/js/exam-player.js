(function () {
  "use strict";

  const COUNT_PRESETS = [5, 10, 30];
  const CHOICE_KEYS = ["A", "B", "C", "D"];

  function choiceKeyToNum(key) {
    const i = CHOICE_KEYS.indexOf(key);
    return i >= 0 ? String(i + 1) : key;
  }

  function formatChoiceAnswer(key, choices) {
    if (!key) return "—";
    const num = choiceKeyToNum(key);
    const text = choices?.[key];
    return text ? `${num}. ${text}` : String(num);
  }

  function $(sel, root) {
    return (root || document).querySelector(sel);
  }

  function parseConfig(root) {
    try {
      return JSON.parse(root.dataset.config || "{}");
    } catch {
      return {};
    }
  }

  function storagePrefix(config) {
    return config.storagePrefix || "gkentei";
  }

  function storageKey(config, suffix) {
    const base = config.storageKey || config.mode || "exam";
    const scope = config.setId || config.examId;
    const scoped = scope ? `-${scope}` : "";
    return `${storagePrefix(config)}-${base}${scoped}-${suffix}`;
  }

  function formatTime(sec) {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${String(s).padStart(2, "0")}`;
  }

  function formatRate(correct, answered) {
    if (!answered) return "—";
    return `${Math.round((correct / answered) * 100)}%`;
  }

  function shuffle(list) {
    const arr = list.slice();
    for (let i = arr.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }

  function domainSortKey(domain) {
    const m = String(domain).match(/第(\d+)章/);
    if (m) return parseInt(m[1], 10);
    return 1000;
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

  function showQuizConfirmDialog(options) {
    const {
      title,
      lead = "",
      message,
      unanswered,
      answered,
      total,
      confirmLabel = "結果を見る",
      cancelLabel = "戻って回答する",
    } = options;

    return new Promise((resolve) => {
      const root = document.createElement("div");
      root.className = "quiz-confirm-modal";
      root.innerHTML = `
        <div class="quiz-confirm-modal__backdrop" data-action="cancel"></div>
        <div class="quiz-confirm-modal__panel" role="alertdialog" aria-modal="true" aria-labelledby="quiz-confirm-title">
          <div class="quiz-confirm-modal__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
              <path d="M12 9v4M12 17h.01" stroke-linecap="round"/>
              <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke-linejoin="round"/>
            </svg>
          </div>
          <p class="quiz-confirm-modal__eyebrow">採点前の確認</p>
          <h2 class="quiz-confirm-modal__title" id="quiz-confirm-title">${escapeHtml(title)}</h2>
          ${lead ? `<p class="quiz-confirm-modal__lead">${escapeHtml(lead)}</p>` : ""}
          <div class="quiz-confirm-modal__stats">
            <div class="quiz-confirm-modal__stat quiz-confirm-modal__stat--warn">
              <span class="quiz-confirm-modal__stat-value">${escapeHtml(String(unanswered))}</span>
              <span class="quiz-confirm-modal__stat-label">未回答</span>
            </div>
            <div class="quiz-confirm-modal__stat">
              <span class="quiz-confirm-modal__stat-value">${escapeHtml(`${answered} / ${total}`)}</span>
              <span class="quiz-confirm-modal__stat-label">回答済み</span>
            </div>
          </div>
          <p class="quiz-confirm-modal__message">${escapeHtml(message)}</p>
          <div class="quiz-confirm-modal__actions">
            <button type="button" class="quiz-confirm-modal__cancel" data-action="cancel">${escapeHtml(cancelLabel)}</button>
            <button type="button" class="quiz-confirm-modal__confirm" data-action="confirm">${escapeHtml(confirmLabel)}</button>
          </div>
        </div>
      `;

      const close = (result) => {
        root.remove();
        document.body.classList.remove("quiz-confirm-modal-open");
        resolve(result);
      };

      root.addEventListener("click", (event) => {
        const action = event.target.closest("[data-action]")?.dataset.action;
        if (action === "cancel") close(false);
        if (action === "confirm") close(true);
      });

      document.addEventListener(
        "keydown",
        function onKey(event) {
          if (event.key === "Escape") {
            document.removeEventListener("keydown", onKey);
            close(false);
          }
        },
        { once: true }
      );

      document.body.classList.add("quiz-confirm-modal-open");
      document.body.appendChild(root);
      root.querySelector("[data-action='confirm']")?.focus();
    });
  }

  function mockExamsEnabled() {
    return !(window.AI_MASTER && window.AI_MASTER.mockExamsEnabled === false);
  }

  function questionSlug(id) {
    return String(id)
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  }

  class ExamPlayer {
    constructor(root) {
      this.root = root;
      this.config = parseConfig(root);
      this.data = null;
      this.allQuestions = [];
      this.questions = [];
      this.index = 0;
      this.answered = false;
      this.selected = null;
      this.timerId = null;
      this.deadline = null;
      this.keyHandler = null;
      this.sessionScore = { correct: 0, answered: 0 };
      this.sessionAnswers = {};
      this.mockAnswers = {};
      this.selectedSetupCount = 10;
      this.selectedSetupDomain = "";

      this.ensureSetupPanel();
      this.ensureCompleteUI();
      this.ensureMockClosedPanel();
      this.ensureMockBriefingPanel();
      this.ensureMockNavigator();

      this.el = {
        bar: $(".quiz-bar", root),
        progress: $(".quiz-progress", root),
        accuracy: $(".quiz-accuracy", root),
        timer: $(".quiz-timer", root),
        setup: $(".quiz-setup", root),
        setupCountOptions: $(".quiz-setup__count-options", root),
        setupDomainOptions: $(".quiz-setup__domain-options", root),
        setupSummary: $(".quiz-setup__summary", root),
        setupStart: $(".quiz-setup__start", root),
        stage: $(".quiz-stage", root),
        meta: $(".quiz-meta", root),
        bookmark: $(".quiz-bookmark", root),
        prompt: $(".quiz-prompt", root),
        hintTf: $(".quiz-hint--tf", root),
        hintChoice: $(".quiz-hint--choice", root),
        choices: $(".quiz-choices", root),
        feedback: $(".quiz-feedback", root),
        verdict: $(".quiz-feedback__verdict", root),
        feedbackBody: $(".quiz-feedback__body", root),
        actions: $(".quiz-actions", root),
        nextBtn: $(".quiz-next", root),
        hintNext: $(".quiz-hint--next", root),
        paywall: $(".quiz-paywall", root),
        complete: $(".quiz-complete", root),
        completeRateValue: $(".quiz-complete__rate-value", root),
        completeDetail: $(".quiz-complete__detail", root),
        completeMessage: $(".quiz-complete__message", root),
        completeShare: $(".quiz-complete__share-x", root),
        mockClosed: $(".quiz-mock-closed", root),
        mockBriefing: $(".quiz-mock-briefing", root),
        navigator: $(".quiz-navigator", root),
        abort: $(".quiz-abort", root),
      };

      this.ensureAbortButton();
      this.initUI();
    }

    setView(mode) {
      const setup = mode === "setup";
      const play = mode === "play";
      const done = mode === "complete";
      const paywall = mode === "paywall";
      const mockClosed = mode === "mock-closed";
      const mockBriefing = mode === "mock-briefing";
      const showNavigator = play && this.isMockDeferFeedback();

      if (this.el.setup) this.el.setup.hidden = !setup;
      if (this.el.bar) this.el.bar.hidden = !play;
      if (this.el.stage) this.el.stage.hidden = !play;
      if (this.el.complete) this.el.complete.hidden = !done;
      if (this.el.paywall) this.el.paywall.hidden = !paywall;
      if (this.el.mockClosed) this.el.mockClosed.hidden = !mockClosed;
      if (this.el.mockBriefing) this.el.mockBriefing.hidden = !mockBriefing;
      if (this.el.navigator) this.el.navigator.hidden = !showNavigator;
      if (this.el.abort) {
        this.el.abort.hidden = !(play && this.canInterrupt());
      }
      this.updateMockFocusMode(mode);
    }

    canInterrupt() {
      return this.useSetup() && !this.isMockDeferFeedback();
    }

    updateMockFocusMode(mode) {
      if (!this.isMockDeferFeedback()) return;
      const focus = mode === "play" || mode === "mock-briefing";
      document.body.classList.toggle("mock-exam-focus", focus);
      document.body.classList.toggle("mock-exam-briefing", mode === "mock-briefing");
    }

    initUI() {
      this.setView("loading");
    }

    ensureSetupPanel() {
      const legacy = $(".quiz-setup", this.root);
      if (legacy && !$(".quiz-setup__count-options", legacy)) {
        legacy.remove();
      }
      if ($(".quiz-setup__count-options", this.root)) return;

      const panel = document.createElement("div");
      panel.className = "quiz-setup";
      panel.hidden = true;
      panel.innerHTML = `
        <div class="quiz-setup__top">
          <div class="quiz-setup__count-block">
            <p class="quiz-setup__label">出題数</p>
            <div class="quiz-setup__options quiz-setup__count-options" role="group" aria-label="出題数"></div>
            <p class="quiz-setup__summary"></p>
          </div>
          <button type="button" class="quiz-setup__start">スタート</button>
        </div>
        <hr class="quiz-setup__divider" />
        <div class="quiz-setup__domain-block">
          <p class="quiz-setup__label quiz-setup__label--domain">分野を選ぶ</p>
          <div class="quiz-setup__options quiz-setup__domain-options" role="group" aria-label="分野"></div>
        </div>
      `;
      const bar = $(".quiz-bar", this.root);
      if (bar) {
        this.root.insertBefore(panel, bar);
      } else {
        this.root.prepend(panel);
      }
    }

    ensureCompleteUI() {
      const complete = $(".quiz-complete", this.root);
      if (!complete || $(".quiz-complete__hero", complete)) return;

      const retryText =
        $(".quiz-complete__retry", complete)?.textContent.trim() || "もう一度挑戦";
      const backText =
        $(".quiz-complete__back", complete)?.textContent.trim() || "トップへ戻る";

      complete.className = "quiz-complete";
      complete.innerHTML = `
        <p class="quiz-complete__label">完了</p>
        <div class="quiz-complete__hero">
          <span class="quiz-complete__rate-value">—</span>
          <span class="quiz-complete__rate-label">正答率</span>
        </div>
        <p class="quiz-complete__detail"></p>
        <p class="quiz-complete__message"></p>
        <a class="quiz-complete__share-x" href="#" target="_blank" rel="noopener noreferrer">
          <span class="quiz-complete__share-icon" aria-hidden="true">𝕏</span>
          結果を投稿
        </a>
        <div class="quiz-complete__actions">
          <button type="button" class="quiz-btn quiz-complete__retry">${escapeHtml(retryText)}</button>
          <button type="button" class="quiz-btn quiz-btn--primary quiz-complete__back">${escapeHtml(backText)}</button>
        </div>
      `;
    }

    ensureMockClosedPanel() {
      if ($(".quiz-mock-closed", this.root)) return;
      const panel = document.createElement("div");
      panel.className = "quiz-mock-closed";
      panel.hidden = true;
      panel.innerHTML = `
        <h2>準備中</h2>
        <p>模擬試験は現在準備中です。公開までしばらくお待ちください。</p>
        <button type="button" class="quiz-btn quiz-btn--primary quiz-mock-closed__back">戻る</button>
      `;
      this.root.appendChild(panel);
      panel.querySelector(".quiz-mock-closed__back")?.addEventListener("click", () => {
        window.location.href = this.config.backUrl || "../";
      });
    }

    ensureMockBriefingPanel() {
      if ($(".quiz-mock-briefing", this.root)) return;
      const panel = document.createElement("div");
      panel.className = "quiz-mock-briefing";
      panel.hidden = true;
      panel.innerHTML = `
        <div class="quiz-mock-briefing__card">
          <h2 class="quiz-mock-briefing__title">模擬試験</h2>
          <p class="quiz-mock-briefing__lead"></p>
          <p class="quiz-mock-briefing__meta"></p>
          <ul class="quiz-mock-briefing__rules">
            <li>四肢択一形式で、本番と同じ問題数に挑戦します</li>
            <li>正解・解説は結果画面でまとめて確認できます</li>
            <li>問題一覧から任意の問題に移動できます</li>
            <li>中断した場合、回答は保存されず最初からやり直しになります</li>
          </ul>
          <div class="quiz-mock-briefing__actions">
            <button type="button" class="quiz-btn quiz-mock-briefing__back">一覧に戻る</button>
            <button type="button" class="quiz-btn quiz-btn--primary quiz-mock-briefing__start">模擬試験を開始</button>
          </div>
        </div>
      `;
      const bar = $(".quiz-bar", this.root);
      if (bar) {
        this.root.insertBefore(panel, bar);
      } else {
        this.root.prepend(panel);
      }
      panel.querySelector(".quiz-mock-briefing__start")?.addEventListener("click", () => {
        this.beginMockSession();
      });
      panel.querySelector(".quiz-mock-briefing__back")?.addEventListener("click", () => {
        window.location.href = this.config.backUrl || "../";
      });
    }

    isMockSession() {
      return Boolean(this.config.examId);
    }

    isMockDeferFeedback() {
      if (!this.isMockSession() || this.config.mockDeferFeedback === false) return false;
      if (this.config.mockDeferFeedback === true) return true;
      return this.config.examId !== "sample";
    }

    isMockNoPersist() {
      return this.isMockDeferFeedback() && this.config.mockNoPersist !== false;
    }

    ensureMockNavigator() {
      if ($(".quiz-navigator", this.root)) return;
      const nav = document.createElement("div");
      nav.className = "quiz-navigator";
      nav.hidden = true;
      nav.innerHTML = `
        <p class="quiz-navigator__label">問題一覧</p>
        <div class="quiz-navigator__grid" role="navigation" aria-label="問題一覧"></div>
        <div class="quiz-navigator__footer">
          <p class="quiz-navigator__status"></p>
          <button type="button" class="quiz-btn quiz-btn--primary quiz-navigator__finish">結果を見る</button>
        </div>
      `;
      const stage = $(".quiz-stage", this.root);
      if (stage) {
        this.root.insertBefore(nav, stage);
      } else {
        this.root.appendChild(nav);
      }
    }

    computeMockScore() {
      let correct = 0;
      let answered = 0;
      this.questions.forEach((q, i) => {
        const sel = this.mockAnswers[i] ?? this.mockAnswers[String(i)];
        if (!sel) return;
        answered += 1;
        if (sel === q.answer) correct += 1;
      });
      return { correct, answered };
    }

    computeMockDomainStats() {
      const map = new Map();
      this.questions.forEach((q, i) => {
        const domain = q.domain || "その他";
        if (!map.has(domain)) {
          map.set(domain, { correct: 0, answered: 0, total: 0 });
        }
        const stat = map.get(domain);
        stat.total += 1;
        const sel = this.mockAnswers[i] ?? this.mockAnswers[String(i)];
        if (!sel) return;
        stat.answered += 1;
        if (sel === q.answer) stat.correct += 1;
      });
      return [...map.entries()].sort(
        (a, b) => domainSortKey(a[0]) - domainSortKey(b[0]) || a[0].localeCompare(b[0], "ja")
      );
    }

    loadMockAnswers() {
      if (!this.isMockDeferFeedback() || this.isMockNoPersist()) return;
      const raw = localStorage.getItem(storageKey(this.config, "answers"));
      if (!raw) {
        this.mockAnswers = {};
        return;
      }
      try {
        this.mockAnswers = JSON.parse(raw);
      } catch {
        this.mockAnswers = {};
      }
    }

    saveMockAnswers() {
      if (!this.isMockDeferFeedback() || this.isMockNoPersist()) return;
      localStorage.setItem(storageKey(this.config, "answers"), JSON.stringify(this.mockAnswers));
    }

    renderMockDomainStats() {
      const complete = this.el.complete;
      if (!complete) return;
      let block = $(".quiz-domain-stats", complete);
      if (!block) {
        block = document.createElement("div");
        block.className = "quiz-domain-stats";
        const review = $(".quiz-review", complete);
        if (review) complete.insertBefore(block, review);
        else complete.appendChild(block);
      }
      const rows = this.computeMockDomainStats();
      block.hidden = false;
      block.innerHTML = `
        <h3 class="quiz-domain-stats__title">分野別の正答率</h3>
        <table class="quiz-domain-stats__table">
          <thead>
            <tr><th>分野</th><th>正答率</th><th>正解</th></tr>
          </thead>
          <tbody>
            ${rows
              .map(([domain, stat]) => {
                const rate = stat.answered ? formatRate(stat.correct, stat.answered) : "—";
                return `<tr>
                  <td>${escapeHtml(domain)}</td>
                  <td>${rate}</td>
                  <td>${stat.correct} / ${stat.answered} 問</td>
                </tr>`;
              })
              .join("")}
          </tbody>
        </table>
      `;
    }

    updateNavigator() {
      if (!this.isMockDeferFeedback()) return;
      const nav = this.el.navigator || $(".quiz-navigator", this.root);
      if (!nav) return;
      const grid = $(".quiz-navigator__grid", nav);
      const status = $(".quiz-navigator__status", nav);
      const { answered } = this.computeMockScore();
      const total = this.questions.length;
      if (status) {
        status.textContent = `回答済み ${answered} / ${total} 問`;
      }
      if (!grid) return;
      grid.innerHTML = "";
      this.questions.forEach((_, i) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "quiz-navigator__cell";
        if (i === this.index) btn.classList.add("is-current");
        if (this.mockAnswers[i] ?? this.mockAnswers[String(i)]) {
          btn.classList.add("is-answered");
        }
        btn.textContent = String(i + 1);
        btn.setAttribute("aria-label", `問題 ${i + 1}`);
        btn.addEventListener("click", () => this.jumpToQuestion(i));
        grid.appendChild(btn);
      });
    }

    jumpToQuestion(i) {
      if (i < 0 || i >= this.questions.length) return;
      this.index = i;
      this.saveProgress();
      this.render();
    }

    updateMockActions() {
      if (!this.isMockDeferFeedback() || !this.el.actions) return;
      const isLast = this.index >= this.questions.length - 1;
      this.el.actions.hidden = false;
      if (this.el.nextBtn) {
        this.el.nextBtn.textContent = "次の問題へ";
        this.el.nextBtn.disabled = isLast;
      }
      if (this.el.hintNext) {
        this.el.hintNext.innerHTML = isLast
          ? "最後の問題です。結果は上部の「結果を見る」から確認できます。"
          : "キーボード <kbd>Enter</kbd> で次へ";
      }
    }

    async requestFinish() {
      const { answered } = this.computeMockScore();
      const total = this.questions.length;
      if (answered < total) {
        const ok = await showQuizConfirmDialog({
          title: "未回答の問題があります",
          lead: "もう少しだけ頑張りませんか？",
          unanswered: total - answered,
          answered,
          total,
          message:
            "未回答は採点対象外です。回答した問題のみで正答率を表示します。",
          confirmLabel: "このまま結果を見る",
          cancelLabel: "戻って回答する",
        });
        if (!ok) return;
      }
      this.finish(false);
    }

    markChoicesDeferred(selected) {
      this.el.choices.querySelectorAll(".quiz-choice").forEach((btn) => {
        btn.classList.remove("is-selected", "is-correct", "is-wrong");
        btn.disabled = false;
        if (btn.dataset.value === selected) btn.classList.add("is-selected");
      });
    }

    questionPrompt(q) {
      return this.isDrill() ? q.statement : q.question;
    }

    formatReviewAnswer(q, key) {
      if (!key) return "—";
      if (this.isDrill()) return escapeHtml(key);
      return escapeHtml(formatChoiceAnswer(key, q.choices));
    }

    renderAnswerReview(answers, options = {}) {
      const complete = this.el.complete;
      if (!complete) return;
      const onlyAnswered = options.onlyAnswered === true;
      let review = $(".quiz-review", complete);
      if (!review) {
        review = document.createElement("div");
        review.className = "quiz-review";
        complete.appendChild(review);
      }
      review.hidden = false;

      const items = this.questions
        .map((q, i) => {
          const selected = answers[i] ?? answers[String(i)];
          if (onlyAnswered && !selected) return "";
          const correct = q.answer;
          const isCorrect = !!selected && selected === correct;
          const verdict = !selected
            ? "未回答"
            : isCorrect
              ? "正解"
              : "不正解";
          const verdictClass = !selected
            ? "is-unanswered"
            : isCorrect
              ? "is-correct"
              : "is-wrong";
          const shouldOpen = !isCorrect;
          const itemModifier =
            verdictClass === "is-wrong"
              ? " quiz-review__item--wrong"
              : verdictClass === "is-unanswered"
                ? " quiz-review__item--unanswered"
                : "";
          return `
            <details class="quiz-review__item${itemModifier}"${shouldOpen ? " open" : ""}>
              <summary class="quiz-review__summary">
                <span class="quiz-review__no">問 ${i + 1}</span>
                <span class="quiz-review__verdict ${verdictClass}">${verdict}</span>
              </summary>
              <div class="quiz-review__body">
                <p class="quiz-review__question">${escapeHtml(this.questionPrompt(q) || "")}</p>
                <p class="quiz-review__line"><strong>あなたの回答</strong> ${this.formatReviewAnswer(q, selected)}</p>
                <p class="quiz-review__line"><strong>正解</strong> ${this.formatReviewAnswer(q, correct)}</p>
                <p class="quiz-review__explanation">${escapeHtml(q.explanation || "")}</p>
              </div>
            </details>
          `;
        })
        .filter(Boolean)
        .join("");

      const title = onlyAnswered ? "解いた問題の正解と解説" : "問題別の正解と解説";
      const hint = onlyAnswered
        ? "不正解は最初から開いています。"
        : "不正解・未回答は最初から開いています。";

      review.innerHTML = `
        <h3 class="quiz-review__title">${title}</h3>
        <p class="quiz-review__hint">${hint}</p>
        <div class="quiz-review__list" aria-label="問題別の解説一覧">
          ${items}
        </div>
      `;
      complete.classList.add("quiz-complete--with-review");
    }

    scrollCompleteSummary() {
      const target =
        $(".quiz-complete__hero", this.el.complete) ||
        this.el.completeRateValue ||
        this.el.complete;
      if (!target) return;
      requestAnimationFrame(() => {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }

    renderMockReview() {
      this.renderAnswerReview(this.mockAnswers);
    }

    shareLabel() {
      if (this.config.shareLabel) return this.config.shareLabel;
      const heading = document.querySelector(".hub-header h1");
      return heading?.textContent.trim() || "AIマスター";
    }

    sharePageUrl() {
      if (this.config.shareUrl) return this.config.shareUrl;
      const canonical = document.querySelector('link[rel="canonical"]');
      if (canonical?.href) return canonical.href;
      return window.location.href.split("#")[0].split("?")[0];
    }

    shareExamTag() {
      if (this.config.shareExamTag) return this.config.shareExamTag;
      const label = this.shareLabel();
      const match = label.match(/^(G検定|生成AIパスポート)/);
      if (match) return match[1];
      const prefix = storagePrefix(this.config);
      if (prefix === "genai-passport") return "生成AIパスポート";
      return "G検定";
    }

    shareHashtags() {
      const examTag = this.shareExamTag();
      return `#AIマスター #${examTag} #資格マスター`;
    }

    buildShareUrl(interrupted) {
      const { correct, answered } = this.sessionScore;
      const rate = formatRate(correct, answered);
      const label = this.shareLabel();
      const headline = interrupted
        ? `${label}を中断。正答率 ${rate}（${correct}/${answered}問）`
        : `${label}を完了！正答率 ${rate}（${correct}/${answered}問）`;
      const text = [headline, "", this.shareHashtags()].join("\n");
      const params = new URLSearchParams({
        text,
        url: this.sharePageUrl(),
      });
      return `https://twitter.com/intent/tweet?${params.toString()}`;
    }

    updateCompleteRateTone(rateText) {
      const value = this.el.completeRateValue;
      if (!value) return;
      value.classList.remove(
        "quiz-complete__rate-value--high",
        "quiz-complete__rate-value--mid",
        "quiz-complete__rate-value--low"
      );
      const pct = parseInt(rateText, 10);
      if (Number.isNaN(pct)) return;
      if (pct >= 80) value.classList.add("quiz-complete__rate-value--high");
      else if (pct >= 50) value.classList.add("quiz-complete__rate-value--mid");
      else value.classList.add("quiz-complete__rate-value--low");
    }

    ensureAbortButton() {
      if (this.el.abort) return;
      if (!this.el.bar) return;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "quiz-abort";
      btn.textContent = "中断";
      btn.hidden = true;
      const timer = $(".quiz-timer", this.root);
      if (timer) {
        this.el.bar.insertBefore(btn, timer);
      } else {
        this.el.bar.appendChild(btn);
      }
      this.el.abort = btn;
      btn.addEventListener("click", () => this.interruptSession());
    }

    ensureAccuracyInBar() {
      if (!this.el.bar) return;
      let acc = $(".quiz-accuracy", this.root);
      if (!acc) {
        acc = document.createElement("div");
        acc.className = "quiz-accuracy";
        acc.hidden = true;
        const timer = $(".quiz-timer", this.root);
        if (timer) {
          this.el.bar.insertBefore(acc, timer);
        } else {
          this.el.bar.appendChild(acc);
        }
      }
      this.el.accuracy = acc;
    }

    showMockBriefingLoading() {
      if (!this.isMockSession() || this.config.mockBriefing === false) return;
      const panel = this.el.mockBriefing || $(".quiz-mock-briefing", this.root);
      if (!panel) return;
      const lead = $(".quiz-mock-briefing__lead", panel);
      const meta = $(".quiz-mock-briefing__meta", panel);
      if (lead) lead.textContent = "問題データを読み込んでいます…";
      if (meta) meta.textContent = "しばらくお待ちください。";
      this.setView("mock-briefing");
    }

    async start() {
      this.showMockBriefingLoading();
      const res = await fetch(this.config.dataUrl);
      if (!res.ok) throw new Error("問題データを読み込めませんでした");
      this.data = await res.json();
      this.allQuestions = this.resolveQuestions();
      this.bindEvents();

      if (this.isMockSession() && !mockExamsEnabled()) {
        this.showMockClosed();
        return;
      }

      if (this.useSetup()) {
        this.showSetup();
        return;
      }

      this.questions = this.allQuestions.slice();
      if (this.isMockNoPersist()) {
        this.clearProgress();
        this.index = 0;
        this.deadline = null;
        this.mockAnswers = {};
        this.sessionScore = { correct: 0, answered: 0 };
      } else {
        this.loadProgress();
        this.loadMockAnswers();
        this.loadSessionScore();
      }
      this.applyDeepLinkQuestion();
      if (this.isPaywalled()) {
        this.showPaywall();
        return;
      }
      if (this.needsMockBriefing()) {
        this.showMockBriefing();
        return;
      }
      this.setView("play");
      this.startTimer();
      this.render();
    }

    needsMockBriefing() {
      if (!this.isMockSession() || this.config.mockBriefing === false) return false;
      if (this.isMockNoPersist()) return true;
      if (this.index > 0) return false;
      const saved = localStorage.getItem(storageKey(this.config, "index"));
      if (saved !== null && parseInt(saved, 10) > 0) return false;
      if (this.deadline) return false;
      return true;
    }

    showMockBriefing() {
      const panel = this.el.mockBriefing || $(".quiz-mock-briefing", this.root);
      if (!panel) {
        this.setView("play");
        this.startTimer();
        this.render();
        return;
      }
      const exam = this.data.exams?.[this.config.examId];
      const minutes = this.config.timeLimitMinutes ?? this.data.timeLimitMinutes;
      const title = $(".quiz-mock-briefing__title", panel);
      const lead = $(".quiz-mock-briefing__lead", panel);
      const meta = $(".quiz-mock-briefing__meta", panel);
      if (title) title.textContent = exam?.title || "模擬試験";
      if (lead) {
        lead.textContent = minutes
          ? `${this.questions.length}問・${minutes}分です。準備はよろしいですか？`
          : `${this.questions.length}問です。準備はよろしいですか？`;
      }
      if (meta) {
        meta.textContent = minutes
          ? "開始すると制限時間のカウントが始まります。"
          : "お試し用の短いセットです。";
      }
      this.setView("mock-briefing");
    }

    beginMockSession() {
      if (this.isPaywalled()) {
        this.showPaywall();
        return;
      }
      if (this.isMockNoPersist()) {
        this.clearProgress();
        this.index = 0;
        this.deadline = null;
        this.mockAnswers = {};
        this.sessionScore = { correct: 0, answered: 0 };
      }
      this.setView("play");
      this.startTimer();
      this.render();
    }

    useSetup() {
      if (new URLSearchParams(window.location.search).get("q")) return false;
      return !this.config.examId && this.config.setup !== false;
    }

    applyDeepLinkQuestion() {
      const param = new URLSearchParams(window.location.search).get("q");
      if (!param) return;
      const target = questionSlug(param);
      const idx = this.questions.findIndex((q) => questionSlug(q.id) === target);
      if (idx >= 0) this.index = idx;
    }

    isDrill() {
      return this.data.mode === "drill" || this.config.mode === "drill";
    }

    resolveQuestions() {
      if (this.config.setId && this.data.sets) {
        const set = this.data.sets.find((s) => s.id === this.config.setId);
        return set?.questions || [];
      }
      if (this.config.examId && this.data.exams) {
        return this.data.exams[this.config.examId]?.questions || [];
      }
      return this.data.questions || [];
    }

    getDomains() {
      const counts = new Map();
      this.allQuestions.forEach((q) => {
        const d = q.domain || "その他";
        counts.set(d, (counts.get(d) || 0) + 1);
      });
      return [...counts.entries()]
        .sort((a, b) => domainSortKey(a[0]) - domainSortKey(b[0]) || a[0].localeCompare(b[0], "ja"));
    }

    getFilteredPool(domain) {
      if (!domain) return this.allQuestions.slice();
      return this.allQuestions.filter((q) => (q.domain || "その他") === domain);
    }

    getSetupPoolMax() {
      return this.getFilteredPool(this.selectedSetupDomain).length;
    }

    normalizeSetupCount(maxCount) {
      if (maxCount <= 0) return 0;
      if (this.selectedSetupCount > maxCount) {
        this.selectedSetupCount = maxCount;
      }
      if (this.selectedSetupCount === maxCount) {
        return;
      }
      const presets = COUNT_PRESETS.filter((n) => n <= maxCount);
      if (!presets.includes(this.selectedSetupCount)) {
        this.selectedSetupCount = presets[presets.length - 1] || maxCount;
      }
    }

    renderSetupCounts() {
      if (!this.el.setupCountOptions) return;
      const maxCount = this.getSetupPoolMax();
      this.normalizeSetupCount(maxCount);

      const counts = COUNT_PRESETS.filter((n) => n <= maxCount);
      const showAll = maxCount > 0 && (maxCount > 30 || !counts.includes(maxCount));
      let html = counts
        .map(
          (n) =>
            `<button type="button" class="quiz-setup__pill${this.selectedSetupCount === n ? " is-active" : ""}" data-count="${n}">${n}問</button>`
        )
        .join("");
      if (showAll) {
        html += `<button type="button" class="quiz-setup__pill${this.selectedSetupCount === maxCount ? " is-active" : ""}" data-count="${maxCount}">全問</button>`;
      }
      this.el.setupCountOptions.innerHTML = html;
    }

    renderSetupDomains() {
      if (!this.el.setupDomainOptions) return;
      const domains = this.getDomains();
      let html = `<button type="button" class="quiz-setup__pill${!this.selectedSetupDomain ? " is-active" : ""}" data-domain="">すべて</button>`;
      html += domains
        .map(
          ([name]) =>
            `<button type="button" class="quiz-setup__pill${this.selectedSetupDomain === name ? " is-active" : ""}" data-domain="${escapeAttr(name)}">${escapeHtml(name)}</button>`
        )
        .join("");
      this.el.setupDomainOptions.innerHTML = html;
    }

    setupFieldLabel() {
      return this.config.setupFieldLabel || "分野";
    }

    updateSetupSummary() {
      if (!this.el.setupSummary) return;
      const pool = this.getFilteredPool(this.selectedSetupDomain);
      const fieldCount = this.selectedSetupDomain ? 1 : this.getDomains().length;
      this.el.setupSummary.textContent = `${this.setupFieldLabel()} ${fieldCount} ・ 該当 ${pool.length}問`;
    }

    refreshSetup() {
      this.renderSetupDomains();
      this.renderSetupCounts();
      this.updateSetupSummary();
    }

    showSetup() {
      this.ensureAccuracyInBar();
      this.setView("setup");
      this.unbindKeyboard();
      this.selectedSetupDomain = "";
      this.selectedSetupCount = 10;
      const domainLabel = $(".quiz-setup__label--domain", this.root);
      if (domainLabel) {
        domainLabel.textContent = this.config.setupDomainLabel || "分野を選ぶ";
      }
      this.refreshSetup();
    }

    beginSession() {
      const domain = this.selectedSetupDomain;
      const count = this.selectedSetupCount;
      const pool = shuffle(this.getFilteredPool(domain));
      const take = Math.min(count, pool.length);
      this.questions = pool.slice(0, take);
      this.index = 0;
      this.sessionScore = { correct: 0, answered: 0 };
      this.sessionAnswers = {};
      this.deadline = null;
      this.clearProgress();

      if (!this.questions.length) {
        this.updateSetupSummary();
        return;
      }

      this.setView("play");
      this.startTimer();
      this.render();
    }

    stopActiveSession() {
      if (this.timerId) {
        window.clearInterval(this.timerId);
        this.timerId = null;
      }
      this.clearProgress();
      this.deadline = null;
      this.answered = false;
      this.selected = null;
      this.unbindKeyboard();
    }

    setCompleteHeading(text) {
      const label = $(".quiz-complete__label", this.el.complete);
      const heading = this.el.complete?.querySelector("h2");
      if (label) label.textContent = text;
      if (heading) heading.textContent = text;
    }

    interruptSession() {
      if (!this.canInterrupt()) return;
      const { answered } = this.sessionScore;

      if (answered === 0) {
        if (!window.confirm("演習を中断して出題設定に戻りますか？")) return;
        this.stopActiveSession();
        this.index = 0;
        this.sessionScore = { correct: 0, answered: 0 };
        this.sessionAnswers = {};
        this.questions = [];
        this.showSetup();
        return;
      }

      if (!window.confirm("演習を中断して、ここまでの結果を表示しますか？")) return;
      this.stopActiveSession();
      this.finish(false, { interrupted: true });
    }

    loadProgress() {
      const saved = localStorage.getItem(storageKey(this.config, "index"));
      if (saved !== null) {
        const idx = parseInt(saved, 10);
        if (!Number.isNaN(idx) && idx >= 0 && idx < this.questions.length) {
          this.index = idx;
        }
      }
      const deadline = localStorage.getItem(storageKey(this.config, "deadline"));
      if (deadline) this.deadline = parseInt(deadline, 10);
    }

    loadSessionScore() {
      if (this.isMockDeferFeedback() || this.isMockNoPersist()) return;
      const raw = localStorage.getItem(storageKey(this.config, "score"));
      if (raw) {
        try {
          this.sessionScore = JSON.parse(raw);
        } catch {
          this.sessionScore = { correct: 0, answered: 0 };
        }
      }
    }

    saveProgress() {
      if (this.useSetup() || this.isMockNoPersist()) return;
      localStorage.setItem(storageKey(this.config, "index"), String(this.index));
      if (this.deadline) {
        localStorage.setItem(storageKey(this.config, "deadline"), String(this.deadline));
      }
    }

    clearProgress() {
      localStorage.removeItem(storageKey(this.config, "index"));
      localStorage.removeItem(storageKey(this.config, "deadline"));
      localStorage.removeItem(storageKey(this.config, "score"));
      localStorage.removeItem(storageKey(this.config, "answers"));
      this.mockAnswers = {};
    }

    bookmarkKey() {
      return `${storagePrefix(this.config)}-bookmarks-${this.config.storageKey || "exam"}`;
    }

    getBookmarks() {
      try {
        return JSON.parse(localStorage.getItem(this.bookmarkKey()) || "[]");
      } catch {
        return [];
      }
    }

    isBookmarked(questionId) {
      return this.getBookmarks().includes(questionId);
    }

    toggleBookmark(questionId) {
      const list = this.getBookmarks();
      const i = list.indexOf(questionId);
      if (i >= 0) list.splice(i, 1);
      else list.push(questionId);
      localStorage.setItem(this.bookmarkKey(), JSON.stringify(list));
      this.updateBookmarkButton(questionId);
    }

    updateBookmarkButton(questionId) {
      if (!this.el.bookmark) return;
      const on = this.isBookmarked(questionId);
      this.el.bookmark.classList.toggle("is-active", on);
      this.el.bookmark.setAttribute("aria-pressed", on ? "true" : "false");
    }

    isPaywalled() {
      const limit = this.config.freeLimit ?? this.data.freeLimit;
      return limit != null && this.index >= limit;
    }

    bindEvents() {
      this.el.setup?.addEventListener("click", (e) => {
        const pill = e.target.closest(".quiz-setup__pill");
        if (!pill) return;
        if (pill.closest(".quiz-setup__count-options")) {
          this.selectedSetupCount = parseInt(pill.dataset.count, 10);
          this.renderSetupCounts();
          return;
        }
        if (pill.closest(".quiz-setup__domain-options")) {
          this.selectedSetupDomain = pill.dataset.domain || "";
          this.refreshSetup();
        }
      });
      this.el.setupStart?.addEventListener("click", () => this.beginSession());
      this.el.nextBtn?.addEventListener("click", () => this.goNext());
      $(".quiz-reset", this.root)?.addEventListener("click", () => this.reset());
      $(".quiz-paywall__back", this.root)?.addEventListener("click", () => {
        window.location.href = this.config.backUrl || "../";
      });
      $(".quiz-complete__retry", this.root)?.addEventListener("click", () => this.reset());
      $(".quiz-complete__back", this.root)?.addEventListener("click", () => {
        window.location.href = this.config.backUrl || "../";
      });
      this.el.bookmark?.addEventListener("click", () => {
        const q = this.questions[this.index];
        if (q?.id) this.toggleBookmark(q.id);
      });
      $(".quiz-navigator__finish", this.root)?.addEventListener("click", () => {
        this.requestFinish();
      });
    }

    bindKeyboard() {
      this.unbindKeyboard();
      this.keyHandler = (e) => {
        if (!this.el.stage || this.el.stage.hidden) return;
        if (e.target.matches("input, textarea, select")) return;

        if (e.key === "Enter") {
          if (this.isMockDeferFeedback()) {
            e.preventDefault();
            this.goNext();
            return;
          }
          if (this.answered && this.el.actions && !this.el.actions.hidden) {
            e.preventDefault();
            this.goNext();
          }
          return;
        }

        if (this.answered && !this.isMockDeferFeedback()) return;

        if (this.isDrill()) {
          if (e.key === "1") this.submit("○");
          if (e.key === "2") this.submit("×");
          return;
        }

        const map = { 1: "A", 2: "B", 3: "C", 4: "D" };
        if (map[e.key]) this.submit(map[e.key]);
      };
      document.addEventListener("keydown", this.keyHandler);
    }

    unbindKeyboard() {
      if (this.keyHandler) {
        document.removeEventListener("keydown", this.keyHandler);
        this.keyHandler = null;
      }
    }

    startTimer() {
      if (this.timerId) {
        window.clearInterval(this.timerId);
        this.timerId = null;
      }
      const minutes = this.config.timeLimitMinutes ?? this.data.timeLimitMinutes;
      if (!minutes || !this.el.timer) return;
      this.el.timer.hidden = false;
      if (!this.deadline) {
        this.deadline = Date.now() + minutes * 60 * 1000;
        this.saveProgress();
      }
      this.tickTimer();
      this.timerId = window.setInterval(() => this.tickTimer(), 1000);
    }

    tickTimer() {
      if (!this.deadline || !this.el.timer) return;
      const remain = Math.max(0, Math.floor((this.deadline - Date.now()) / 1000));
      this.el.timer.textContent = `残り ${formatTime(remain)}`;
      this.el.timer.classList.toggle("is-warning", remain <= 600);
      if (remain === 0) {
        window.clearInterval(this.timerId);
        this.finish(true);
      }
    }

    updateProgressBar() {
      const total = this.questions.length;
      const { correct, answered } = this.sessionScore;
      if (this.el.progress) {
        this.el.progress.innerHTML = `問題 <strong>${this.index + 1}</strong> / ${total}`;
      }
      if (this.el.accuracy) {
        if (this.isMockDeferFeedback()) {
          this.el.accuracy.hidden = true;
        } else if (answered > 0) {
          this.el.accuracy.hidden = false;
          this.el.accuracy.innerHTML = `正答率 <strong>${formatRate(correct, answered)}</strong>`;
        } else {
          this.el.accuracy.hidden = true;
        }
      }
      if (this.isMockDeferFeedback()) {
        this.updateNavigator();
      }
    }

    render() {
      this.ensureAccuracyInBar();

      if (!this.questions.length) {
        this.el.prompt.textContent = "問題がありません。";
        return;
      }
      if (!this.isMockDeferFeedback() && this.index >= this.questions.length) {
        this.finish(false);
        return;
      }

      this.setView("play");
      this.bindKeyboard();

      const q = this.questions[this.index];
      this.updateProgressBar();

      this.el.meta.textContent = q.domain || q.topic || "";

      const saved = this.isMockDeferFeedback()
        ? this.mockAnswers[this.index] ?? this.mockAnswers[String(this.index)]
        : null;
      this.answered = false;
      this.selected = saved || null;
      this.el.feedback.hidden = true;
      if (this.isMockDeferFeedback()) {
        this.updateMockActions();
      } else if (this.el.actions) {
        this.el.actions.hidden = true;
      }
      this.updateBookmarkButton(q.id);

      if (this.isDrill()) {
        this.renderDrill(q);
      } else {
        this.renderChoice(q);
      }

      if (saved) {
        this.markChoicesDeferred(saved);
      }
    }

    renderDrill(q) {
      this.el.prompt.textContent = q.statement;
      if (this.el.hintTf) {
        this.el.hintTf.hidden = false;
        this.el.hintTf.innerHTML = "キーボード <kbd>1</kbd> ○ <kbd>2</kbd> × で回答";
      }
      if (this.el.hintChoice) this.el.hintChoice.hidden = true;

      this.el.choices.className = "quiz-choices quiz-choices--tf";
      this.el.choices.innerHTML = "";
      ["○", "×"].forEach((sym) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "quiz-choice";
        btn.dataset.value = sym;
        btn.setAttribute("aria-label", sym === "○" ? "正しい" : "誤り");
        btn.textContent = sym;
        btn.addEventListener("click", () => this.submit(sym));
        this.el.choices.appendChild(btn);
      });
    }

    renderChoice(q) {
      this.el.prompt.textContent = q.question;
      if (this.el.hintTf) this.el.hintTf.hidden = true;
      if (this.el.hintChoice) {
        this.el.hintChoice.hidden = false;
        this.el.hintChoice.innerHTML = "キーボード <kbd>1</kbd>〜<kbd>4</kbd> で回答";
      }

      this.el.choices.className = "quiz-choices";
      this.el.choices.innerHTML = "";
      CHOICE_KEYS.forEach((key, i) => {
        const text = q.choices[key];
        if (!text) return;
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "quiz-choice";
        btn.dataset.value = key;
        btn.innerHTML = `<span class="quiz-choice__label">${i + 1}</span><span class="quiz-choice__text">${escapeHtml(text)}</span>`;
        btn.addEventListener("click", () => this.submit(key));
        this.el.choices.appendChild(btn);
      });
    }

    submit(value) {
      if (this.isMockDeferFeedback()) {
        const q = this.questions[this.index];
        this.mockAnswers[this.index] = value;
        this.selected = value;
        this.saveMockAnswers();
        this.markChoicesDeferred(value);
        this.updateProgressBar();
        this.updateMockActions();
        return;
      }

      if (this.answered) return;
      const q = this.questions[this.index];
      const correctAnswer = q.answer;
      const isCorrect = value === correctAnswer;

      this.answered = true;
      this.selected = value;
      this.sessionAnswers[this.index] = value;
      this.markChoices(correctAnswer);
      this.showFeedback(isCorrect, q, correctAnswer);
      if (this.el.actions) this.el.actions.hidden = false;
      this.recordScore(isCorrect);
      this.updateProgressBar();
    }

    markChoices(correctAnswer) {
      this.el.choices.querySelectorAll(".quiz-choice").forEach((btn) => {
        btn.disabled = true;
        const val = btn.dataset.value;
        if (val === this.selected) btn.classList.add("is-selected");
        if (val === correctAnswer) btn.classList.add("is-correct");
        else if (val === this.selected) btn.classList.add("is-wrong");
      });
    }

    showFeedback(isCorrect, q, correctAnswer) {
      this.el.feedback.hidden = false;
      this.el.feedback.classList.toggle("is-correct", isCorrect);
      this.el.feedback.classList.toggle("is-wrong", !isCorrect);
      const correctLabel = this.isDrill() ? correctAnswer : choiceKeyToNum(correctAnswer);
      this.el.verdict.textContent = isCorrect ? "正解" : `不正解 — 正解は ${correctLabel}`;
      this.el.verdict.classList.toggle("is-correct", isCorrect);
      this.el.verdict.classList.toggle("is-wrong", !isCorrect);
      this.el.feedbackBody.textContent = q.explanation || "";
    }

    recordScore(isCorrect) {
      this.sessionScore.answered += 1;
      if (isCorrect) this.sessionScore.correct += 1;
      if (!this.useSetup()) {
        localStorage.setItem(storageKey(this.config, "score"), JSON.stringify(this.sessionScore));
      }
    }

    goNext() {
      if (this.isMockDeferFeedback()) {
        if (this.index >= this.questions.length - 1) return;
        this.index += 1;
        this.saveProgress();
        this.render();
        return;
      }

      if (!this.answered || (this.el.actions && this.el.actions.hidden)) return;
      this.index += 1;
      this.saveProgress();
      if (this.isPaywalled()) {
        this.showPaywall();
        return;
      }
      if (this.index >= this.questions.length) {
        this.finish(false);
        return;
      }
      this.render();
    }

    showPaywall() {
      this.setView("paywall");
      this.unbindKeyboard();
      if (this.timerId) window.clearInterval(this.timerId);
    }

    showMockClosed() {
      this.setView("mock-closed");
      this.unbindKeyboard();
      if (this.timerId) window.clearInterval(this.timerId);
    }

    finish(timedOut, options = {}) {
      const interrupted = options.interrupted === true;
      if (this.timerId) window.clearInterval(this.timerId);
      this.setView("complete");
      this.unbindKeyboard();

      let { correct, answered } = this.sessionScore;
      if (this.isMockDeferFeedback()) {
        ({ correct, answered } = this.computeMockScore());
        this.sessionScore = { correct, answered };
        if (!this.isMockNoPersist()) {
          localStorage.setItem(storageKey(this.config, "score"), JSON.stringify(this.sessionScore));
        }
      }

      const rate = formatRate(correct, answered);
      const total = this.questions.length;
      let msg;
      if (interrupted) {
        msg = `演習を中断しました。（全 ${total} 問中 ${answered} 問に回答）`;
      } else if (timedOut) {
        msg = "制限時間が終了しました。";
      } else if (this.isMockDeferFeedback() && answered < total) {
        msg = `回答済み ${answered} / ${total} 問で採点しました。`;
      } else {
        msg = "すべての問題に回答しました。";
      }

      this.setCompleteHeading(interrupted ? "中断" : "完了");

      if (this.el.completeRateValue) {
        this.el.completeRateValue.textContent = rate;
        this.updateCompleteRateTone(rate);
      }
      if (this.el.completeDetail) {
        this.el.completeDetail.textContent = this.isMockDeferFeedback()
          ? `${correct} / ${total} 問正解（回答 ${answered} 問）`
          : `${correct} / ${answered} 問正解`;
      }
      if (this.el.completeMessage) {
        this.el.completeMessage.textContent = msg;
      }
      if (this.el.completeShare) {
        this.el.completeShare.href = this.buildShareUrl(interrupted);
      }
      if (this.isMockDeferFeedback()) {
        this.renderMockDomainStats();
        this.renderMockReview();
      } else if (this.useSetup() && answered > 0) {
        this.renderAnswerReview(this.sessionAnswers, { onlyAnswered: interrupted });
      }
      this.scrollCompleteSummary();
    }

    reset() {
      this.clearProgress();
      this.index = 0;
      this.deadline = null;
      this.answered = false;
      this.sessionScore = { correct: 0, answered: 0 };
      this.sessionAnswers = {};
      this.mockAnswers = {};
      this.setCompleteHeading("完了");
      const review = $(".quiz-review", this.el.complete);
      if (review) review.hidden = true;
      const domainStats = $(".quiz-domain-stats", this.el.complete);
      if (domainStats) domainStats.hidden = true;
      this.el.complete?.classList.remove("quiz-complete--with-review");

      if (this.useSetup()) {
        this.showSetup();
        return;
      }

      if (this.isPaywalled()) {
        this.showPaywall();
        return;
      }

      if (this.isMockNoPersist() && this.config.mockBriefing !== false) {
        this.showMockBriefing();
        return;
      }

      this.setView("play");
      this.startTimer();
      this.render();
    }
  }

  function bootExamPlayer() {
    const root = document.getElementById("exam-player");
    if (!root || root.dataset.playerBooted === "1") return;
    if (root.dataset.awaitBoot === "1") return;
    root.dataset.playerBooted = "1";
    const player = new ExamPlayer(root);
    player.start().catch((err) => {
      const msg = err.message || "読み込みに失敗しました。";
      if (player.el.setupSummary) {
        player.setView("setup");
        if (player.el.setup) player.el.setup.hidden = false;
        player.el.setupSummary.textContent = msg;
      } else {
        player.setView("play");
        const prompt = $(".quiz-prompt", root);
        if (prompt) prompt.textContent = msg;
      }
    });
  }

  window.bootExamPlayer = bootExamPlayer;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootExamPlayer);
  } else {
    bootExamPlayer();
  }
})();
