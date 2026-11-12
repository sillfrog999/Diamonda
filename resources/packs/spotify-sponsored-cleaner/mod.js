(() => {
  const key = "spotify.sponsored-cleaner:mod.js";
  const selectors = [
    ".adSlot", "[data-testid='ad-banner']", "[data-testid='ad-slot']",
    "[data-testid='sponsored-content']", "[aria-label^='Sponsored' i]",
    "[aria-label*='Advertisement' i]"
  ];
  const original = new Map();
  const hideSponsored = (root = document) => {
    for (const selector of selectors) {
      try {
        root.querySelectorAll(selector).forEach(el => {
          if (!original.has(el)) original.set(el, el.getAttribute("style"));
          el.style.setProperty("display", "none", "important");
        });
      } catch (_) {}
    }
  };
  hideSponsored();
  const observer = new MutationObserver(() => hideSponsored());
  observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ["aria-label", "data-testid", "class"] });
  window.__diamondaCleanup = window.__diamondaCleanup || {};
  window.__diamondaCleanup[key] = () => {
    observer.disconnect();
    for (const [el, style] of original.entries()) {
      if (!el.isConnected) continue;
      if (style === null) el.removeAttribute("style");
      else el.setAttribute("style", style);
    }
    original.clear();
    delete window.__diamondaCleanup[key];
  };
})();
