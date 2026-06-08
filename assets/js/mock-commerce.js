(function () {
  "use strict";

  const TOKEN_STORAGE_KEY = "ai-master-mock-tokens";
  const DEFAULT_MOCK_IDS = ["mock_01", "mock_02", "mock_03"];
  const DEFAULT_BUNDLE_ID = "bundle";
  let configPromise = null;

  function loadConfig() {
    if (!configPromise) {
      configPromise = fetch("/assets/data/mock-commerce.json")
        .then((res) => {
          if (!res.ok) throw new Error("config load failed");
          return res.json();
        })
        .catch(() => ({
          checkoutEnabled: false,
          supabaseUrl: "",
          supabaseAnonKey: "",
          priceYen: 980,
          bundleExamId: DEFAULT_BUNDLE_ID,
          mockExamIds: DEFAULT_MOCK_IDS,
        }));
    }
    return configPromise;
  }

  function bundleExamId(config) {
    return config?.bundleExamId || DEFAULT_BUNDLE_ID;
  }

  function mockExamIds(config) {
    return config?.mockExamIds || DEFAULT_MOCK_IDS;
  }

  function isCheckoutEnabled(config) {
    return Boolean(
      config?.checkoutEnabled &&
        config?.supabaseUrl &&
        config?.supabaseAnonKey
    );
  }

  function tokenKey(examSlug, examId) {
    return `${examSlug}:${examId}`;
  }

  function readTokenStore() {
    try {
      return JSON.parse(localStorage.getItem(TOKEN_STORAGE_KEY) || "{}");
    } catch {
      return {};
    }
  }

  function writeTokenStore(store) {
    localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(store));
  }

  function getLocalToken(examSlug, examId) {
    return readTokenStore()[tokenKey(examSlug, examId)] || "";
  }

  function saveLocalToken(examSlug, examId, token) {
    const store = readTokenStore();
    store[tokenKey(examSlug, examId)] = token;
    writeTokenStore(store);
  }

  function consumeUrlToken() {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("access");
    if (!token) return "";
    params.delete("access");
    const next = `${window.location.pathname}${
      params.toString() ? `?${params.toString()}` : ""
    }`;
    window.history.replaceState({}, "", next);
    return token;
  }

  async function callFunction(config, name, body) {
    const res = await fetch(`${config.supabaseUrl}/functions/v1/${name}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${config.supabaseAnonKey}`,
        apikey: config.supabaseAnonKey,
      },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg =
        data.error ||
        data.message ||
        (data.code ? `${data.code}` : "") ||
        "Request failed";
      throw new Error(msg);
    }
    return data;
  }

  async function verifyAccess(examSlug, examId, token) {
    const config = await loadConfig();
    if (!isCheckoutEnabled(config) || !token) return false;
    const data = await callFunction(config, "verify-mock-access", {
      examSlug,
      examId,
      token,
    });
    if (!data.ok) return false;
    saveLocalToken(examSlug, bundleExamId(config), token);
    return true;
  }

  async function hasBundleAccess(examSlug) {
    const config = await loadConfig();
    if (!isCheckoutEnabled(config)) return true;
    const ids = mockExamIds(config);
    const bundleId = bundleExamId(config);
    const token = consumeUrlToken() || getLocalToken(examSlug, bundleId);
    if (!token) return false;
    return verifyAccess(examSlug, ids[0], token);
  }

  async function hasAccess(examSlug, examId) {
    const config = await loadConfig();
    if (examId === "sample") return false;
    if (!isCheckoutEnabled(config)) return true;
    const ids = mockExamIds(config);
    if (!ids.includes(examId)) return false;
    return hasBundleAccess(examSlug);
  }

  async function startCheckout(examSlug, examId, examTitle, email) {
    const config = await loadConfig();
    if (!isCheckoutEnabled(config)) {
      throw new Error("Checkout is not enabled");
    }
    const data = await callFunction(config, "create-mock-checkout", {
      examSlug,
      examId,
      examTitle,
      email: email || undefined,
    });
    if (!data.url) throw new Error("Checkout URL missing");
    window.location.href = data.url;
  }

  async function fulfillSession(sessionId) {
    const config = await loadConfig();
    if (!isCheckoutEnabled(config)) {
      throw new Error("Checkout is not enabled");
    }
    return callFunction(config, "fulfill-mock-session", { sessionId });
  }

  function formatPrice(config) {
    const yen = config?.priceYen ?? 980;
    return `¥${yen.toLocaleString("ja-JP")}`;
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function showMessageDialog(options) {
    const { title, message, confirmLabel = "OK" } = options;
    return new Promise((resolve) => {
      const root = document.createElement("div");
      root.className = "mock-checkout-modal";
      root.innerHTML = `
        <div class="mock-checkout-modal__backdrop" data-action="close"></div>
        <div class="mock-checkout-modal__panel" role="alertdialog" aria-modal="true" aria-labelledby="mock-checkout-msg-title">
          <h2 class="mock-checkout-modal__title" id="mock-checkout-msg-title">${escapeHtml(title)}</h2>
          <p class="mock-checkout-modal__message">${escapeHtml(message)}</p>
          <div class="mock-checkout-modal__actions mock-checkout-modal__actions--single">
            <button type="button" class="mock-checkout-modal__confirm" data-action="confirm">${escapeHtml(confirmLabel)}</button>
          </div>
        </div>
      `;
      const close = () => {
        root.remove();
        document.body.classList.remove("mock-checkout-modal-open");
        resolve();
      };
      root.addEventListener("click", (event) => {
        const action = event.target.closest("[data-action]")?.dataset.action;
        if (action === "close" || action === "confirm") close();
      });
      document.addEventListener(
        "keydown",
        function onKey(event) {
          if (event.key === "Escape") {
            document.removeEventListener("keydown", onKey);
            close();
          }
        },
        { once: true }
      );
      document.body.classList.add("mock-checkout-modal-open");
      document.body.appendChild(root);
      root.querySelector("[data-action='confirm']")?.focus();
    });
  }

  function showPurchaseDialog(options) {
    const { examTitle, priceLabel } = options;
    return new Promise((resolve) => {
      const root = document.createElement("div");
      root.className = "mock-checkout-modal";
      root.innerHTML = `
        <div class="mock-checkout-modal__backdrop" data-action="cancel"></div>
        <div class="mock-checkout-modal__panel" role="dialog" aria-modal="true" aria-labelledby="mock-checkout-title">
          <button type="button" class="mock-checkout-modal__close" data-action="cancel" aria-label="閉じる">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8" stroke-linecap="round"/></svg>
          </button>
          <p class="mock-checkout-modal__eyebrow">お支払い</p>
          <h2 class="mock-checkout-modal__title" id="mock-checkout-title">${escapeHtml(examTitle)}</h2>
          <p class="mock-checkout-modal__price">${escapeHtml(priceLabel)}<span class="mock-checkout-modal__price-note">（買い切り · 3回分）</span></p>
          <ul class="mock-checkout-modal__summary">
            <li>第1回・第2回・第3回をすべて受験可能</li>
            <li>購入後は何度でも再受験できます</li>
            <li>決済完了後すぐに受験を開始できます</li>
          </ul>
          <label class="mock-checkout-modal__field">
            <span class="mock-checkout-modal__label">確認メール（任意）</span>
            <input type="email" class="mock-checkout-modal__input" name="email" placeholder="example@email.com" autocomplete="email">
            <span class="mock-checkout-modal__hint">受験リンクを送る場合のみ入力してください。空欄でも購入できます。</span>
          </label>
          <p class="mock-checkout-modal__secure">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M8 1.5L3 4v3.5c0 3 2.2 5.8 5 6.5 2.8-.7 5-3.5 5-6.5V4L8 1.5z" stroke-linejoin="round"/></svg>
            お支払いは Stripe の安全なページで行われます
          </p>
          <div class="mock-checkout-modal__actions">
            <button type="button" class="mock-checkout-modal__cancel" data-action="cancel">キャンセル</button>
            <button type="button" class="mock-checkout-modal__confirm" data-action="confirm">Stripeで支払う</button>
          </div>
        </div>
      `;

      const panel = root.querySelector(".mock-checkout-modal__panel");
      const input = root.querySelector(".mock-checkout-modal__input");
      const confirmBtn = root.querySelector("[data-action='confirm']");

      const finish = (email) => {
        root.remove();
        document.body.classList.remove("mock-checkout-modal-open");
        resolve(email);
      };

      root.addEventListener("click", (event) => {
        const action = event.target.closest("[data-action]")?.dataset.action;
        if (action === "cancel") finish(null);
        if (action === "confirm") finish(input.value.trim());
      });

      panel?.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && event.target !== input) {
          event.preventDefault();
          finish(input.value.trim());
        }
      });

      document.addEventListener(
        "keydown",
        function onKey(event) {
          if (event.key === "Escape") {
            document.removeEventListener("keydown", onKey);
            finish(null);
          }
        },
        { once: true }
      );

      document.body.classList.add("mock-checkout-modal-open");
      document.body.appendChild(root);
      input?.focus();
    });
  }

  async function preparePlayPage(examSlug, examId) {
    if (examId === "sample") {
      window.location.replace("index.html");
      return false;
    }

    const config = await loadConfig();
    if (!isCheckoutEnabled(config)) return true;

    const gate = document.getElementById("mock-access-gate");
    if (gate) gate.hidden = false;

    const ok = await hasAccess(examSlug, examId);
    if (!ok) {
      window.location.replace(
        `index.html?purchase=${encodeURIComponent(bundleExamId(config))}`
      );
      return false;
    }

    if (gate) gate.hidden = true;
    return true;
  }

  window.MockCommerce = {
    loadConfig,
    isCheckoutEnabled,
    hasAccess,
    hasBundleAccess,
    verifyAccess,
    startCheckout,
    fulfillSession,
    saveLocalToken,
    getLocalToken,
    formatPrice,
    preparePlayPage,
    showPurchaseDialog,
    showMessageDialog,
    bundleExamId,
    mockExamIds,
  };
})();
