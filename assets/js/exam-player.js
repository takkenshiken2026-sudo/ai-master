(function () {
  "use strict";

  const COUNT_PRESETS = [5, 10, 30];

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

  function mockExamsEnabled() {
    return !(window.AI_MASTER && window.AI_MASTER.mockExamsEnabled === false);
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
      this.selectedSetupCount = 10;
      this.selectedSetupDomain = "";

      this.ensureSetupPanel();
      this.ensureCompleteUI();
      this.ensureMockClosedPanel();

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
      };

      this.initUI();
    }

    setView(mode) {
      const setup = mode === "setup";
      const play = mode === "play";
      const done = mode === "complete";
      const paywall = mode === "paywall";
      const mockClosed = mode === "mock-closed";

      if (this.el.setup) this.el.setup.hidden = !setup;
      if (this.el.bar) this.el.bar.hidden = !play;
      if (this.el.stage) this.el.stage.hidden = !play;
      if (this.el.complete) this.el.complete.hidden = !done;
      if (this.el.paywall) this.el.paywall.hidden = !paywall;
      if (this.el.mockClosed) this.el.mockClosed.hidden = !mockClosed;
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

    isMockSession() {
      return Boolean(this.config.examId);
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

    buildShareUrl() {
      const { correct, answered } = this.sessionScore;
      const rate = formatRate(correct, answered);
      const label = this.shareLabel();
      const text = [
        `${label}を完了！正答率 ${rate}（${correct}/${answered}問）`,
        "",
        this.shareHashtags(),
      ].join("\n");
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

    async start() {
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
      this.loadProgress();
      this.loadSessionScore();
      if (this.isPaywalled()) {
        this.showPaywall();
        return;
      }
      this.setView("play");
      this.startTimer();
      this.render();
    }

    useSetup() {
      return !this.config.examId && this.config.setup !== false;
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
      if (this.useSetup()) return;
      localStorage.setItem(storageKey(this.config, "index"), String(this.index));
      if (this.deadline) {
        localStorage.setItem(storageKey(this.config, "deadline"), String(this.deadline));
      }
    }

    clearProgress() {
      localStorage.removeItem(storageKey(this.config, "index"));
      localStorage.removeItem(storageKey(this.config, "deadline"));
      localStorage.removeItem(storageKey(this.config, "score"));
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
    }

    bindKeyboard() {
      this.unbindKeyboard();
      this.keyHandler = (e) => {
        if (!this.el.stage || this.el.stage.hidden) return;
        if (e.target.matches("input, textarea, select")) return;

        if (e.key === "Enter") {
          if (this.answered && this.el.actions && !this.el.actions.hidden) {
            e.preventDefault();
            this.goNext();
          }
          return;
        }

        if (this.answered) return;

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
        if (answered > 0) {
          this.el.accuracy.hidden = false;
          this.el.accuracy.innerHTML = `正答率 <strong>${formatRate(correct, answered)}</strong>`;
        } else {
          this.el.accuracy.hidden = true;
        }
      }
    }

    render() {
      this.ensureAccuracyInBar();

      if (!this.questions.length) {
        this.el.prompt.textContent = "問題がありません。";
        return;
      }
      if (this.index >= this.questions.length) {
        this.finish(false);
        return;
      }

      this.setView("play");
      this.bindKeyboard();

      const q = this.questions[this.index];
      this.updateProgressBar();

      this.el.meta.textContent = q.domain || q.topic || "";

      this.answered = false;
      this.selected = null;
      this.el.feedback.hidden = true;
      if (this.el.actions) this.el.actions.hidden = true;
      this.updateBookmarkButton(q.id);

      if (this.isDrill()) {
        this.renderDrill(q);
      } else {
        this.renderChoice(q);
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
      ["A", "B", "C", "D"].forEach((key) => {
        const text = q.choices[key];
        if (!text) return;
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "quiz-choice";
        btn.dataset.value = key;
        btn.innerHTML = `<span class="quiz-choice__label">${key}</span><span class="quiz-choice__text">${escapeHtml(text)}</span>`;
        btn.addEventListener("click", () => this.submit(key));
        this.el.choices.appendChild(btn);
      });
    }

    submit(value) {
      if (this.answered) return;
      const q = this.questions[this.index];
      const correctAnswer = q.answer;
      const isCorrect = value === correctAnswer;

      this.answered = true;
      this.selected = value;
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
      this.el.verdict.textContent = isCorrect ? "正解" : `不正解 — 正解は ${correctAnswer}`;
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

    finish(timedOut) {
      if (this.timerId) window.clearInterval(this.timerId);
      this.setView("complete");
      this.unbindKeyboard();

      const { correct, answered } = this.sessionScore;
      const rate = formatRate(correct, answered);
      const msg = timedOut ? "制限時間が終了しました。" : "すべての問題に回答しました。";

      if (this.el.completeRateValue) {
        this.el.completeRateValue.textContent = rate;
        this.updateCompleteRateTone(rate);
      }
      if (this.el.completeDetail) {
        this.el.completeDetail.textContent = `${correct} / ${answered} 問正解`;
      }
      if (this.el.completeMessage) {
        this.el.completeMessage.textContent = msg;
      }
      if (this.el.completeShare) {
        this.el.completeShare.href = this.buildShareUrl();
      }
    }

    reset() {
      this.clearProgress();
      this.index = 0;
      this.deadline = null;
      this.answered = false;
      this.sessionScore = { correct: 0, answered: 0 };

      if (this.useSetup()) {
        this.showSetup();
        return;
      }

      if (this.isPaywalled()) {
        this.showPaywall();
        return;
      }
      this.setView("play");
      this.startTimer();
      this.render();
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    const root = document.getElementById("exam-player");
    if (!root) return;
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
  });
})();
