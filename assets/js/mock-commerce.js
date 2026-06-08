(function () {
  "use strict";

  const TOKEN_STORAGE_KEY = "ai-master-mock-tokens";
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
        }));
    }
    return configPromise;
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
    saveLocalToken(examSlug, examId, token);
    return true;
  }

  async function hasAccess(examSlug, examId) {
    const config = await loadConfig();
    if (!isCheckoutEnabled(config) || examId === "sample") return true;
    const token = consumeUrlToken() || getLocalToken(examSlug, examId);
    if (!token) return false;
    return verifyAccess(examSlug, examId, token);
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

  async function preparePlayPage(examSlug, examId) {
    if (examId === "sample") return true;

    const config = await loadConfig();
    if (!isCheckoutEnabled(config)) return true;

    const gate = document.getElementById("mock-access-gate");
    if (gate) gate.hidden = false;

    const ok = await hasAccess(examSlug, examId);
    if (!ok) {
      window.location.replace(
        `index.html?purchase=${encodeURIComponent(examId)}`
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
    verifyAccess,
    startCheckout,
    fulfillSession,
    saveLocalToken,
    getLocalToken,
    formatPrice,
    preparePlayPage,
  };
})();
