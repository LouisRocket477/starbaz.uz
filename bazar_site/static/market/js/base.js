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

  function setupNavSync() {
    var body = document.body;
    if (!body) return;
    var isAuthenticated = body.getAttribute("data-authenticated") === "true";
    var url = body.getAttribute("data-nav-status-url");
    if (!isAuthenticated || !url) return;

    var unreadDot = document.getElementById("navUnreadDot");
    var unreadDotMobileTop = document.getElementById("navUnreadDotMobileTop");
    var ticketDot = document.getElementById("navAdminTicketDot");
    var ticketDotMobileTop = document.getElementById("navAdminTicketDotMobileTop");
    var audioEl = document.getElementById("site-notify-sound");

    // хранение последнего уведомленного сообщения, чтобы не пищало бесконечно
    var storageKey = "sb_last_notified_unread_id";
    function getLastNotifiedId() {
      try {
        var v = localStorage.getItem(storageKey);
        var n = parseInt(v || "0", 10);
        return isNaN(n) ? 0 : n;
      } catch (e) {
        return 0;
      }
    }
    function setLastNotifiedId(id) {
      try {
        localStorage.setItem(storageKey, String(id || 0));
      } catch (e) {}
    }

    function playNotify() {
      if (!audioEl || !audioEl.play) return;
      audioEl.currentTime = 0;
      audioEl.play().catch(function () {
        // браузер мог заблокировать автоплей до жеста — ок, просто молча
      });
    }

    function apply(data) {
      if (!data) return;
      if (unreadDot) {
        unreadDot.style.display = data.unread_chat_count > 0 ? "inline-block" : "none";
      }
      if (unreadDotMobileTop) {
        unreadDotMobileTop.style.display = data.unread_chat_count > 0 ? "inline-block" : "none";
      }
      if (ticketDot) {
        ticketDot.style.display = data.open_support_tickets > 0 ? "inline-block" : "none";
        if (data.open_support_tickets > 0) {
          ticketDot.title = "Открытые тикеты: " + data.open_support_tickets;
        }
      }
      if (ticketDotMobileTop) {
        ticketDotMobileTop.style.display = data.open_support_tickets > 0 ? "inline-block" : "none";
        if (data.open_support_tickets > 0) {
          ticketDotMobileTop.title = "Открытые тикеты: " + data.open_support_tickets;
        }
      }

      // Звук: только когда пришло новое непрочитанное (по последнему id)
      var lastUnreadId = parseInt(String(data.unread_last_id || 0), 10) || 0;
      var prevNotified = getLastNotifiedId();
      if (lastUnreadId > 0 && lastUnreadId > prevNotified) {
        // не пищим, если пользователь уже в чате (там своя логика и он и так видит)
        if (!/\/chat\/\d+\/?$/.test(window.location.pathname)) {
          playNotify();
        }
        setLastNotifiedId(lastUnreadId);
      }
    }

    function tick() {
      fetch(url, { method: "GET", credentials: "same-origin", cache: "no-store" })
        .then(function (r) { return r.json(); })
        .then(apply)
        .catch(function () {});
    }

    tick();
    setInterval(tick, 2000);
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
  setupNavSync();
  setupScrollTop();
})();

