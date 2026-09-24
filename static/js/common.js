async function nsFetch(url, options = {}) {
  options.headers = Object.assign({}, options.headers, {
    "X-CSRFToken": window.NETSCOPE_CSRF,
    "Content-Type": "application/json",
  });
  const res = await fetch(url, options);
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  return res.json();
}

(function initPageLoading() {
  const showLoader = () => {
    const loader = document.getElementById("ns-page-loader");
    if (!loader) return;
    loader.classList.add("is-visible");
    loader.setAttribute("aria-hidden", "false");
  };

  const hideLoader = () => {
    const loader = document.getElementById("ns-page-loader");
    if (!loader) return;
    loader.classList.remove("is-visible");
    loader.setAttribute("aria-hidden", "true");
  };

  document.addEventListener("DOMContentLoaded", () => {
    hideLoader();

    document.querySelectorAll("a[href]").forEach(link => {
      link.addEventListener("click", event => {
        if (
          event.defaultPrevented ||
          event.metaKey ||
          event.ctrlKey ||
          event.shiftKey ||
          event.altKey ||
          link.target === "_blank" ||
          link.hasAttribute("download")
        ) return;

        const url = new URL(link.href, window.location.href);
        const samePage = url.origin === window.location.origin &&
          url.pathname === window.location.pathname &&
          url.search === window.location.search;

        if (url.origin !== window.location.origin || samePage) return;
        showLoader();
      });
    });
  });

  window.addEventListener("pageshow", hideLoader);
})();
