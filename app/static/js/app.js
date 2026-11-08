// Amberg Live – small progressive enhancements. The site works without JavaScript;
// this adds dark-mode toggle, favorites (localStorage), copy/share buttons, tidy filter URLs.
(function () {
  "use strict";

  var FAV_KEY = "al-favs";

  function readFavs() {
    try {
      var value = JSON.parse(localStorage.getItem(FAV_KEY) || "[]");
      return Array.isArray(value) ? value : [];
    } catch (e) {
      return [];
    }
  }

  function writeFavs(list) {
    try { localStorage.setItem(FAV_KEY, JSON.stringify(list)); } catch (e) { /* private mode */ }
  }

  // ---- Dark mode ------------------------------------------------------------
  document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var dark = !document.documentElement.classList.contains("dark");
      document.documentElement.classList.toggle("dark", dark);
      try { localStorage.setItem("al-theme", dark ? "dark" : "light"); } catch (e) {}
    });
  });

  // ---- Favorites ------------------------------------------------------------
  function syncHearts() {
    var favs = readFavs();
    document.querySelectorAll("[data-fav]").forEach(function (btn) {
      var on = favs.indexOf(btn.dataset.fav) !== -1;
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      btn.setAttribute("aria-label", on ? btn.dataset.labelRemove : btn.dataset.labelAdd);
    });
  }

  document.addEventListener("click", function (event) {
    var btn = event.target.closest("[data-fav]");
    if (!btn) return;
    event.preventDefault();
    var favs = readFavs();
    var index = favs.indexOf(btn.dataset.fav);
    if (index === -1) favs.push(btn.dataset.fav); else favs.splice(index, 1);
    writeFavs(favs);
    syncHearts();
    if (btn.closest("#favorites")) renderFavorites();
  });

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text; // textContent: titles can never inject HTML
    return node;
  }

  function renderFavorites() {
    var box = document.getElementById("favorites");
    if (!box) return;
    var empty = document.getElementById("favorites-empty");
    var favs = readFavs();
    if (!favs.length) {
      box.replaceChildren();
      empty.hidden = false;
      return;
    }
    fetch(box.dataset.api + "?slugs=" + encodeURIComponent(favs.join(",")))
      .then(function (r) { return r.json(); })
      .then(function (items) {
        box.replaceChildren();
        empty.hidden = items.length > 0;
        items.forEach(function (item) {
          var card = el("article", "relative flex items-center gap-3 rounded-2xl border border-stone-200 bg-white p-3 shadow-sm dark:border-stone-800 dark:bg-stone-900" + (item.past ? " opacity-60" : ""));
          var dot = el("span", "size-3 shrink-0 rounded-full");
          dot.style.background = item.color;
          var body = el("div", "min-w-0 flex-1");
          var title = el("h2", "font-bold leading-snug");
          var link = el("a", "after:absolute after:inset-0 hover:underline", item.title);
          link.href = item.url;
          title.appendChild(link);
          var meta = el("p", "text-sm text-stone-600 dark:text-stone-400",
            (item.past ? box.dataset.labelPast + " · " : "") + item.when + (item.location ? " · " + item.location : ""));
          body.append(title, meta);
          var remove = el("button", "relative z-10 inline-flex size-11 items-center justify-center rounded-full text-rose-600 hover:bg-stone-100 dark:hover:bg-stone-800", "✕");
          remove.type = "button";
          remove.dataset.fav = item.slug;
          remove.setAttribute("aria-label", box.dataset.labelRemove);
          card.append(dot, body, remove);
          box.appendChild(card);
        });
      })
      .catch(function () { box.replaceChildren(); empty.hidden = false; });
  }

  // ---- Copy link & native share --------------------------------------------
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var label = btn.querySelector("span");
      var original = label ? label.textContent : "";
      navigator.clipboard.writeText(btn.dataset.copy).then(function () {
        if (label) {
          label.textContent = btn.dataset.copiedLabel;
          setTimeout(function () { label.textContent = original; }, 2000);
        }
      });
    });
  });

  if (navigator.share) {
    document.querySelectorAll("[data-share]").forEach(function (btn) {
      btn.hidden = false;
      btn.classList.remove("hidden");
      btn.addEventListener("click", function () {
        navigator.share({ title: btn.dataset.shareTitle, url: btn.dataset.shareUrl }).catch(function () {});
      });
    });
  }

  // ---- Filter forms ---------------------------------------------------------
  document.querySelectorAll("form[role=search]").forEach(function (form) {
    // Leave empty fields out of the URL: /veranstaltungen?kategorie=sport instead of ?q=&kategorie=sport&preis=
    form.addEventListener("submit", function () {
      form.querySelectorAll("input, select").forEach(function (field) {
        if (!field.value || (field.type === "radio" && field.value === "alle")) field.disabled = true;
      });
    });
    form.querySelectorAll("[data-autosubmit]").forEach(function (field) {
      field.addEventListener("change", function () {
        // A quick period overrides a custom date range.
        form.querySelectorAll("input[type=date]").forEach(function (d) { d.value = ""; });
        form.requestSubmit ? form.requestSubmit() : form.submit();
      });
    });
  });

  // ---- Dashboard forms -------------------------------------------------------
  // "Really delete?" before destructive POST forms.
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });

  // Show "Wiederholen bis" only for recurring events, "Preis" only when not free.
  function bindToggle(control, target, isVisible) {
    if (!control || !target) return;
    var update = function () { target.hidden = !isVisible(control); };
    control.addEventListener("change", update);
    update();
  }
  bindToggle(document.getElementById("recurrence"), document.getElementById("until-wrap"),
    function (c) { return c.value !== "none"; });
  bindToggle(document.getElementById("is_free"), document.getElementById("price-wrap"),
    function (c) { return !c.checked; });

  // Admin: quick reasons fill the rejection text field.
  document.querySelectorAll("[data-reason]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var field = document.getElementById(btn.dataset.reasonTarget);
      if (!field) return;
      field.value = field.value ? field.value + " " + btn.dataset.reason : btn.dataset.reason;
      field.focus();
    });
  });

  // Back/forward cache restores disabled fields; re-enable them.
  window.addEventListener("pageshow", function () {
    document.querySelectorAll("form[role=search] [disabled]").forEach(function (f) { f.disabled = false; });
    syncHearts();
  });

  // ---- Progressive Web App ---------------------------------------------------
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js").catch(function () { /* site works without it */ });
    });
  }

  // Show our own "install app" button only when the browser offers installation.
  var installPrompt = null;
  var installButton = document.querySelector("[data-install]");
  window.addEventListener("beforeinstallprompt", function (event) {
    event.preventDefault();
    installPrompt = event;
    if (installButton) installButton.classList.remove("hidden");
  });
  if (installButton) {
    installButton.addEventListener("click", function () {
      if (!installPrompt) return;
      installPrompt.prompt();
      installPrompt.userChoice.finally(function () {
        installPrompt = null;
        installButton.classList.add("hidden");
      });
    });
  }

  syncHearts();
  renderFavorites();
})();
