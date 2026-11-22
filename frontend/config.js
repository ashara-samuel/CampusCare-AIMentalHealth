// Where the frontend finds the API.
//
// - Served by the backend on the web (same origin as the API) -> use relative
//   paths ("" base).
// - Packaged as a mobile app (Capacitor serves from capacitor://localhost or
//   http://localhost) -> calls must go to the deployed API over the network.
//
// Set API_BASE to your deployed backend URL. The check below keeps the web build
// same-origin automatically; only the mobile app uses the absolute URL.
(function () {
  var API_BASE = "https://campuscare-n76g.onrender.com";
  // If the page is actually served from the API origin (the web build), use
  // relative paths; otherwise (mobile shell, file://, etc.) use the absolute API.
  window.CAMPUSCARE_API_BASE = (location.origin === API_BASE) ? "" : API_BASE;
})();
