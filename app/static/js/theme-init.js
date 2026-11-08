// Loaded in <head> before the page renders, so dark mode never flashes white.
// The choice is kept in localStorage (no cookie); default follows the system setting.
(function () {
  var choice = null;
  try { choice = localStorage.getItem("al-theme"); } catch (e) {}
  var dark = choice ? choice === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
  document.documentElement.classList.toggle("dark", dark);
})();
