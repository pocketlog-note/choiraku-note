/* ちょいラク帳：なくても読めるが、あると便利になる小さな機能だけ。 */
(function () {
  var d = document;

  // コードのコピー
  d.querySelectorAll("figure.code").forEach(function (fig) {
    var btn = fig.querySelector(".copy");
    var code = fig.querySelector("code");
    if (!btn || !code) return;
    btn.hidden = false;
    btn.addEventListener("click", function () {
      var text = code.textContent;
      var ok = function () {
        btn.textContent = "コピーしました";
        btn.classList.add("done");
        setTimeout(function () { btn.textContent = "コピー"; btn.classList.remove("done"); }, 1800);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(ok, fallback);
      } else { fallback(); }
      function fallback() {
        var r = d.createRange(); r.selectNodeContents(code);
        var s = getSelection(); s.removeAllRanges(); s.addRange(r);
        try { if (d.execCommand("copy")) ok(); } catch (e) {}
        s.removeAllRanges();
      }
    });
  });

  // 明るさの切り替え
  var tb = d.querySelector(".theme");
  if (tb) {
    tb.hidden = false;
    tb.addEventListener("click", function () {
      var root = d.documentElement;
      var cur = root.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      var next = cur === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      try { localStorage.setItem("theme", next); } catch (e) {}
    });
  }

  // 一覧の絞り込み
  var filters = d.querySelector(".filters");
  if (filters) {
    filters.hidden = false;
    var rows = d.querySelectorAll(".row");
    var none = d.querySelector(".none");
    filters.addEventListener("click", function (e) {
      var b = e.target.closest(".filter");
      if (!b) return;
      filters.querySelectorAll(".filter").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      var k = b.dataset.kind, n = 0;
      rows.forEach(function (r) { var show = !k || r.dataset.kind === k; r.hidden = !show; if (show) n++; });
      if (none) none.hidden = n > 0;
    });
  }

  // 読了バーと、いま読んでいる節の強調
  var bar = d.querySelector(".progress");
  var content = d.querySelector(".content");
  var links = d.querySelectorAll(".toc li a");
  if (bar && d.querySelector(".post")) {
    var tick = false;
    var update = function () {
      var el = d.querySelector(".post");
      var r = el.getBoundingClientRect();
      var total = r.height - innerHeight;
      var p = total > 0 ? Math.min(1, Math.max(0, -r.top / total)) : 0;
      bar.style.transform = "scaleX(" + p + ")";
      tick = false;
    };
    addEventListener("scroll", function () { if (!tick) { tick = true; requestAnimationFrame(update); } }, { passive: true });
    update();
  }
  if (content && links.length && "IntersectionObserver" in window) {
    var map = {};
    links.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting && map[e.target.id]) {
          links.forEach(function (a) { a.classList.remove("on"); });
          map[e.target.id].classList.add("on");
        }
      });
    }, { rootMargin: "-80px 0px -65% 0px" });
    content.querySelectorAll("h2[id]").forEach(function (h) { io.observe(h); });
  }
})();
