(function () {
  function setupHeartbeat() {
    var body = document.body;
    if (!body) return;

    var heartbeatUrl = body.getAttribute("data-heartbeat-url");
    var isAuthenticated = body.getAttribute("data-authenticated") === "true";

    if (!heartbeatUrl || !isAuthenticated) {
      return;
    }

    function sendHeartbeat() {
      fetch(heartbeatUrl, {
        method: "GET",
        credentials: "same-origin",
        cache: "no-store",
      }).catch(function () {
        // тихо игнорируем ошибки сети
      });
    }

    sendHeartbeat();
    setInterval(sendHeartbeat, 60000);
  }

  function setupScrollTop() {
    document.addEventListener("DOMContentLoaded", function () {
      var btn = document.getElementById("scrollTopBtn");
      if (!btn) return;

      function toggleBtn() {
        if (window.scrollY > 300) {
          btn.style.display = "block";
        } else {
          btn.style.display = "none";
        }
      }

      window.addEventListener("scroll", toggleBtn);
      toggleBtn();

      btn.addEventListener("click", function () {
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    });
  }

  setupHeartbeat();
  setupScrollTop();
})();

