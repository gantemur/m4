export function encodeScenario(state) {
  return btoa(unescape(encodeURIComponent(JSON.stringify(state)))).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}

export function decodeScenario(value) {
  try {
    const normalized = value.replaceAll("-", "+").replaceAll("_", "/");
    const padding = "=".repeat((4 - normalized.length % 4) % 4);
    return JSON.parse(decodeURIComponent(escape(atob(normalized + padding))));
  } catch {
    return null;
  }
}
