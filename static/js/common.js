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
