(() => {
  const key = "youtube.ad-cleaner:mod.js";
  const selectors = [
    "ytd-ad-slot-renderer", "ytd-display-ad-renderer",
    "ytd-promoted-sparkles-web-renderer", "ytd-promoted-video-renderer",
    "ytd-in-feed-ad-layout-renderer", "ytd-banner-promo-renderer",
    "#player-ads", "#masthead-ad", ".video-ads", ".ytp-ad-module",
    ".ytp-ad-overlay-container", "ytd-action-companion-ad-renderer"
  ];
  const hideAds = (root = document) => {
    for (const selector of selectors) {
      try { root.querySelectorAll(selector).forEach(el => { el.style.setProperty("display", "none", "important"); }); }
      catch (_) {}
    }
  };
  const skipVisibleAd = () => {
    const buttons = [
      ".ytp-ad-skip-button",
      ".ytp-ad-skip-button-modern",
      "button.ytp-skip-ad-button",
      "button[aria-label*='Skip' i]"
    ];
    for (const selector of buttons) {
      const button = document.querySelector(selector);
      if (button && button.getClientRects().length && !button.disabled) {
        button.click();
        break;
      }
    }
  };
  hideAds();
  const observer = new MutationObserver(() => { hideAds(); skipVisibleAd(); });
  observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ["class", "aria-label"] });
  const onRoute = () => { hideAds(); skipVisibleAd(); };
  window.addEventListener("yt-navigate-finish", onRoute);
  window.__diamondaCleanup = window.__diamondaCleanup || {};
  window.__diamondaCleanup[key] = () => {
    observer.disconnect();
    window.removeEventListener("yt-navigate-finish", onRoute);
    delete window.__diamondaCleanup[key];
    for (const selector of selectors) {
      try { document.querySelectorAll(selector).forEach(el => el.style.removeProperty("display")); } catch (_) {}
    }
  };
})();
