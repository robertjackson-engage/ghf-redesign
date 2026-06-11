/* GHF Coach configuration.
   The API key lives server-side in `.anthropic-key` at the project root —
   serve.py proxies chat calls so the key never ships to the browser.
   (proxyUrl: "" + apiKey in localStorage is the static-hosting fallback.) */
window.GHF_CHAT = {
  /* the proxy only exists when running serve.py locally; on GitHub Pages the
     widget falls back to its in-browser key gate (key stays in localStorage) */
  proxyUrl: (location.hostname === "localhost" || location.hostname === "127.0.0.1") ? "/api/chat" : "",
  apiKey: "",
  model: "claude-sonnet-4-6"
};
