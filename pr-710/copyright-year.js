// Keeps the end of the copyright range in the footer current, so the year
// never goes stale. The markup ships with a fallback year, which stays
// visible when a reader has JavaScript turned off.
document.querySelectorAll('.copyright-year').forEach(function (el) {
  el.textContent = String(new Date().getFullYear());
});
