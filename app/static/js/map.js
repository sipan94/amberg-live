// OpenStreetMap with "two-click" privacy: nothing is requested from OSM servers
// until the visitor clicks "Karte laden" (or chose to always load maps on this device).
(function () {
  "use strict";

  var CONSENT_KEY = "al-map-consent";
  var AMBERG = [49.4448, 11.8581];
  var boxes = document.querySelectorAll("[data-map]");
  if (!boxes.length) return;

  var leafletPromise = null;

  function loadLeaflet(box) {
    if (window.L) return Promise.resolve();
    if (leafletPromise) return leafletPromise;
    leafletPromise = new Promise(function (resolve, reject) {
      var css = document.createElement("link");
      css.rel = "stylesheet";
      css.href = box.dataset.leafletCss;
      document.head.appendChild(css);
      var script = document.createElement("script");
      script.src = box.dataset.leafletJs;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
    return leafletPromise;
  }

  function popupContent(marker) {
    var wrap = document.createElement("div");
    var title = document.createElement(marker.url ? "a" : "strong");
    title.textContent = marker.title;
    if (marker.url) {
      title.href = marker.url;
      title.style.fontWeight = "700";
    }
    wrap.appendChild(title);
    [marker.when, marker.place].forEach(function (line) {
      if (!line) return;
      var p = document.createElement("div");
      p.textContent = line;
      wrap.appendChild(p);
    });
    return wrap;
  }

  function initMap(box) {
    var markers = JSON.parse(box.dataset.map || "[]");
    var consent = box.querySelector("[data-map-consent]");
    if (consent) consent.remove();

    var map = L.map(box, { scrollWheelZoom: false });
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '<a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">' +
        box.dataset.attribution + "</a>",
    }).addTo(map);

    var points = [];
    markers.forEach(function (m) {
      L.circleMarker([m.lat, m.lng], {
        radius: 9, color: "#ffffff", weight: 2, fillColor: m.color || "#b38600", fillOpacity: 0.95,
      }).addTo(map).bindPopup(popupContent(m));
      points.push([m.lat, m.lng]);
    });

    if (points.length > 1) map.fitBounds(points, { padding: [30, 30], maxZoom: 16 });
    else if (points.length === 1) map.setView(points[0], 16);
    else map.setView(AMBERG, 14);
  }

  function show(box) {
    loadLeaflet(box).then(function () { initMap(box); });
  }

  var remembered = false;
  try { remembered = localStorage.getItem(CONSENT_KEY) === "1"; } catch (e) {}

  boxes.forEach(function (box) {
    if (remembered) {
      show(box);
      return;
    }
    box.querySelector("[data-map-load]").addEventListener("click", function () {
      var remember = box.querySelector("[data-map-remember]");
      if (remember && remember.checked) {
        try { localStorage.setItem(CONSENT_KEY, "1"); } catch (e) {}
      }
      show(box);
    });
  });
})();
