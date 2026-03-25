document.addEventListener('DOMContentLoaded', function () {
    var lastKnownCapsState = false;
    var lastKnownLayout = '—';

    function extractCapsState(event) {
        if (event && typeof event.getModifierState === 'function') {
            return event.getModifierState('CapsLock');
        }
        return null;
    }

    function detectLayoutByText(text) {
        if (!text) return '—';
        for (var i = text.length - 1; i >= 0; i--) {
            var ch = text[i];
            if (/[A-Za-z]/.test(ch)) return 'EN';
            if (/[А-Яа-яЁё]/.test(ch)) return 'RU';
        }
        return '—';
    }

    function detectLayoutByEvent(event) {
        if (!event || typeof event.key !== 'string') return null;
        var k = event.key;
        if (k.length !== 1) return null;
        if (/[A-Za-z]/.test(k)) return 'EN';
        if (/[А-Яа-яЁё]/.test(k)) return 'RU';
        return null;
    }

    function setupPasswordHints(inputId, hintId) {
        var input = document.getElementById(inputId);
        var hint = document.getElementById(hintId);
        if (!input || !hint) return;
        var layoutEl = hint.querySelector('[data-role="layout"]');
        var capsEl = hint.querySelector('[data-role="caps"]');
        var capsChip = hint.querySelector('[data-role="caps-chip"]');

        function updateHint(layout, capsOn) {
            if (layoutEl) layoutEl.textContent = layout;
            if (capsEl) capsEl.textContent = capsOn ? 'ВКЛ' : 'ВЫКЛ';
            if (capsChip) {
                capsChip.classList.toggle('is-warning', capsOn);
            }
        }

        function updateFromEvent(e) {
            var eventLayout = detectLayoutByEvent(e);
            if (eventLayout) {
                lastKnownLayout = eventLayout;
            }
            var capsState = extractCapsState(e);
            if (capsState !== null) {
                lastKnownCapsState = capsState;
            }
            var fallbackLayout = detectLayoutByText(input.value);
            updateHint(lastKnownLayout !== '—' ? lastKnownLayout : fallbackLayout, lastKnownCapsState);
        }

        input.addEventListener('keydown', updateFromEvent);
        input.addEventListener('keyup', updateFromEvent);
        input.addEventListener('input', function () {
            // На input не переопределяем состояние с клавиатуры,
            // чтобы убрать "мигание" во время ввода.
            var fallbackLayout = detectLayoutByText(input.value);
            updateHint(lastKnownLayout !== '—' ? lastKnownLayout : fallbackLayout, lastKnownCapsState);
        });
        input.addEventListener('focus', function (e) {
            updateFromEvent(e);
        });
        input.addEventListener('blur', function () {
            var fallbackLayout = detectLayoutByText(input.value);
            updateHint(lastKnownLayout !== '—' ? lastKnownLayout : fallbackLayout, lastKnownCapsState);
        });
    }

    function setupToggle(inputId, buttonId, eyeId) {
        var input = document.getElementById(inputId);
        var btn = document.getElementById(buttonId);
        var eye = document.getElementById(eyeId);
        if (!input || !btn || !eye) return;

        btn.addEventListener('click', function () {
            if (input.type === 'password') {
                input.type = 'text';
                eye.classList.remove('bi-eye');
                eye.classList.add('bi-eye-slash');
            } else {
                input.type = 'password';
                eye.classList.remove('bi-eye-slash');
                eye.classList.add('bi-eye');
            }
        });
    }

    // Логин
    setupToggle('password-input', 'toggle-password-visibility', 'password-eye');
    setupPasswordHints('password-input', 'password-hint');
    // Регистрация
    setupToggle('password1-input', 'toggle-password1-visibility', 'password1-eye');
    setupToggle('password2-input', 'toggle-password2-visibility', 'password2-eye');
    setupPasswordHints('password1-input', 'password1-hint');
    setupPasswordHints('password2-input', 'password2-hint');

    // Обновляем глобальное состояние CapsLock даже без ввода в поле.
    document.addEventListener('keydown', function (e) {
        var capsState = extractCapsState(e);
        if (capsState !== null) {
            lastKnownCapsState = capsState;
        }
        var layout = detectLayoutByEvent(e);
        if (layout) {
            lastKnownLayout = layout;
        }
    });
    document.addEventListener('keyup', function (e) {
        var capsState = extractCapsState(e);
        if (capsState !== null) {
            lastKnownCapsState = capsState;
        }
        var layout = detectLayoutByEvent(e);
        if (layout) {
            lastKnownLayout = layout;
        }
    });
});

