// Scroll reveal — gentle, and skipped entirely for reduced-motion users.
    (function () {
      var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      var items = document.querySelectorAll(".reveal");
      if (reduce || !("IntersectionObserver" in window)) {
        items.forEach(function (el) { el.classList.add("in"); });
      } else {
        var io = new IntersectionObserver(function (entries) {
          entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
        }, { threshold: .15 });
        items.forEach(function (el) { io.observe(el); });
      }
    })();

    // Interactive guide — fully user-paced. No autoplay, no popups, nothing forced.
    (function () {
      var steps = Array.prototype.slice.call(document.querySelectorAll(".step"));
      var total = steps.length, i = 0;
      var prev = document.getElementById("gprev"), next = document.getElementById("gnext");
      var fill = document.getElementById("gfill"), dotsWrap = document.getElementById("gdots");
      steps.forEach(function (_, idx) {
        var d = document.createElement("button");
        d.className = "dot" + (idx === 0 ? " on" : "");
        d.setAttribute("aria-label", "Step " + (idx + 1));
        d.addEventListener("click", function () { go(idx); });
        dotsWrap.appendChild(d);
      });
      function go(n) {
        i = Math.max(0, Math.min(total - 1, n));
        steps.forEach(function (s, idx) { s.classList.toggle("active", idx === i); });
        Array.prototype.forEach.call(dotsWrap.children, function (d, idx) { d.classList.toggle("on", idx === i); });
        fill.style.width = ((i + 1) / total * 100) + "%";
        prev.disabled = i === 0; next.disabled = i === total - 1;
      }
      prev.addEventListener("click", function () { go(i - 1); });
      next.addEventListener("click", function () { go(i + 1); });
      go(0);
    })();
