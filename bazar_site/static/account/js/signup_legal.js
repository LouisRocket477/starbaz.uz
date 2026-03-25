document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("signup-form");
  const openBtn = document.getElementById("signup-legal-open");
  const modalEl = document.getElementById("signupLegalModal");
  const scrollBox = document.getElementById("signup-legal-scroll");
  const acceptBtn = document.getElementById("signup-legal-accept");
  const hint = document.getElementById("signup-legal-hint");
  const acceptRulesCheckbox = document.getElementById("signup-accept-rules");

  if (!form || !openBtn || !modalEl || !scrollBox || !acceptBtn) {
    return;
  }

  let modalInstance = null;

  const ensureModalInstance = () => {
    if (!modalInstance) {
      modalInstance = new bootstrap.Modal(modalEl);
    }
    return modalInstance;
  };

  const resetState = () => {
    acceptBtn.disabled = true;
    if (hint) {
      hint.textContent = "Пролистайте текст до конца, чтобы активировать кнопку согласия.";
    }
    scrollBox.scrollTop = 0;
  };

  openBtn.addEventListener("click", (event) => {
    event.preventDefault();
    resetState();
    ensureModalInstance().show();
    // Если текста мало и прокрутка не нужна — сразу активируем кнопку
    const threshold = 10;
    if (scrollBox.scrollHeight - scrollBox.clientHeight <= threshold) {
      acceptBtn.disabled = false;
      if (hint) {
        hint.textContent = "Вы можете подтвердить согласие и завершить регистрацию.";
      }
    }
  });

  const checkScrolledToBottom = () => {
    const threshold = 10;
    const distance =
      scrollBox.scrollHeight - scrollBox.clientHeight - scrollBox.scrollTop;
    if (distance <= threshold) {
      acceptBtn.disabled = false;
      if (hint) {
        hint.textContent = "Вы можете подтвердить согласие и завершить регистрацию.";
      }
    }
  };

  scrollBox.addEventListener("scroll", checkScrolledToBottom);

  acceptBtn.addEventListener("click", () => {
    if (acceptBtn.disabled) return;
    if (acceptRulesCheckbox) {
      acceptRulesCheckbox.checked = true;
    }
    ensureModalInstance().hide();
    form.submit();
  });
});

