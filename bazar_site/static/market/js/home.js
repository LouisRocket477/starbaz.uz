document.addEventListener('DOMContentLoaded', function () {
    const messagesBox = document.getElementById('global-chat-messages');
    const form = document.getElementById('global-chat-form');
    const input = document.getElementById('global-chat-input');
    const submitBtn = document.getElementById('global-chat-submit');
    const replyPreview = document.getElementById('global-chat-reply-preview');
    const replyUserEl = document.getElementById('global-chat-reply-user');
    const replySnippetEl = document.getElementById('global-chat-reply-snippet');
    const replyCancelBtn = document.getElementById('global-chat-reply-cancel');
    const replyHiddenInput = document.getElementById('global-chat-reply-to');
    const cooldownEl = document.getElementById('global-chat-cooldown');
    const apiUrl = messagesBox && messagesBox.getAttribute('data-api-url');
    let currentReplyId = null;

    if (!messagesBox || !apiUrl) return;

    const COOLDOWN_SECONDS = 7;
    let cooldownUntil = 0;
    let cooldownTimerId = null;

    function escapeHtml(text) {
        if (!text) return '';
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function attachReplyHandlers() {
        const buttons = messagesBox.querySelectorAll('.global-chat-reply-btn');
        buttons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                const messageId = parseInt(btn.dataset.messageId, 10);
                const user = btn.dataset.user || '';
                const snippet = btn.dataset.content || '';
                currentReplyId = messageId;

                if (replyUserEl && replySnippetEl && replyPreview) {
                    replyUserEl.textContent = user;
                    replySnippetEl.textContent = snippet;
                    replyPreview.classList.remove('d-none');
                }
                if (replyHiddenInput) {
                    replyHiddenInput.value = messageId;
                }

                messagesBox.querySelectorAll('.global-chat-message-highlight').forEach(function (row) {
                    row.classList.remove('global-chat-message-highlight');
                });
                const row = messagesBox.querySelector('.global-chat-message[data-message-id="' + messageId + '"]');
                if (row) {
                    row.classList.add('global-chat-message-highlight');
                    row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }

                if (input) {
                    input.focus();
                }
            });
        });
    }

    if (replyCancelBtn && replyPreview) {
        replyCancelBtn.addEventListener('click', function () {
            currentReplyId = null;
            replyPreview.classList.add('d-none');
            if (replyHiddenInput) {
                replyHiddenInput.value = '';
            }
            messagesBox.querySelectorAll('.global-chat-message-highlight').forEach(function (row) {
                row.classList.remove('global-chat-message-highlight');
            });
        });
    }

    function renderMessages(items) {
        messagesBox.innerHTML = '';
        if (!items.length) {
            messagesBox.innerHTML = '<div class="small text-muted py-2 text-center">В чате пока нет сообщений.</div>';
            return;
        }
        items.forEach(function (m) {
            const row = document.createElement('div');
            row.className = 'global-chat-message';
            row.dataset.messageId = m.id;

            let inner = '';
            if (m.reply_to_user && m.reply_to_content) {
                inner += '<div class="global-chat-message-quote">↪ ' +
                    escapeHtml(m.reply_to_user) + ': ' +
                    escapeHtml(m.reply_to_content) +
                    '</div>';
            }
            inner += '<div class="d-flex justify-content-between align-items-center">' +
                '<div>' +
                '<a href="/seller/' + m.user_id + '/" class="global-chat-message-user text-decoration-none">' +
                escapeHtml(m.user) + ':</a> ' +
                '<span class="global-chat-message-text">' + escapeHtml(m.content) + '</span>' +
                '</div>' +
                '<div class="d-flex align-items-center gap-2">' +
                '<span class="global-chat-message-time">' + escapeHtml(m.created_at) + '</span>' +
                '<button type="button" class="btn btn-link btn-sm p-0 text-muted global-chat-reply-btn" ' +
                'data-message-id="' + m.id + '" ' +
                'data-user="' + escapeHtml(m.user) + '" ' +
                'data-content="' + escapeHtml(m.content.slice(0, 80)) + '">Ответить</button>' +
                '</div>' +
                '</div>';

            row.innerHTML = inner;
            messagesBox.appendChild(row);
        });
        attachReplyHandlers();
        messagesBox.scrollTop = messagesBox.scrollHeight;
    }

    function fetchMessages() {
        fetch(apiUrl)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data && data.messages) {
                    renderMessages(data.messages);
                }
            })
            .catch(function () {});
    }

    fetchMessages();
    setInterval(fetchMessages, 5000);

    if (form && input) {
        function getCsrfToken() {
            const csrfInput = document.querySelector('#global-chat-form input[name="csrfmiddlewaretoken"]');
            if (csrfInput && csrfInput.value) return csrfInput.value;
            const value = '; ' + document.cookie;
            const name = 'csrftoken';
            const parts = value.split('; ' + name + '=');
            if (parts.length === 2) return parts.pop().split(';').shift();
            return '';
        }

        function startCooldown() {
            cooldownUntil = Date.now() + COOLDOWN_SECONDS * 1000;
            if (cooldownTimerId) {
                clearInterval(cooldownTimerId);
            }
            updateCooldown();
            cooldownTimerId = setInterval(updateCooldown, 1000);
        }

        function updateCooldown() {
            const now = Date.now();
            const diff = Math.max(0, Math.round((cooldownUntil - now) / 1000));
            if (diff <= 0) {
                if (cooldownEl) {
                    cooldownEl.textContent = '';
                }
                if (submitBtn) {
                    submitBtn.disabled = false;
                }
                if (cooldownTimerId) {
                    clearInterval(cooldownTimerId);
                    cooldownTimerId = null;
                }
                return;
            }
            if (cooldownEl) {
                cooldownEl.textContent = `Следующее сообщение можно отправить через ${diff} с.`;
            }
            if (submitBtn) {
                submitBtn.disabled = true;
            }
        }

        function isInCooldown() {
            return Date.now() < cooldownUntil;
        }

        function shake() {
            const wrapper = form.querySelector('.input-group');
            if (!wrapper) return;
            wrapper.classList.add('global-chat-input-wrapper', 'shake');
            setTimeout(function () {
                wrapper.classList.remove('shake');
            }, 250);
        }

        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const text = input.value.trim();
            if (!text) return;

            if (isInCooldown()) {
                shake();
                updateCooldown();
                return;
            }

            const formData = new FormData(form);
            const csrftoken = getCsrfToken();
            if (csrftoken) {
                formData.set('csrfmiddlewaretoken', csrftoken);
            }

            fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken || '',
                    'Accept': 'application/json'
                },
                body: formData
            })
                .then(function (r) {
                    const contentType = r.headers.get('Content-Type') || '';
                    if (!r.ok) {
                        if (contentType.indexOf('application/json') !== -1) {
                            return r.json().then(function (d) { throw { status: r.status, data: d }; });
                        }
                        return r.text().then(function (t) { throw { status: r.status, raw: t }; });
                    }
                    return r.json();
                })
                .then(function (data) {
                    if (data && data.message) {
                        input.value = '';
                        if (replyHiddenInput) {
                            replyHiddenInput.value = '';
                        }
                        if (replyPreview) {
                            replyPreview.classList.add('d-none');
                        }
                        startCooldown();
                        fetchMessages();
                    }
                })
                .catch(function (err) {
                    if (err && err.data && err.data.error === 'cooldown') {
                        startCooldown();
                        shake();
                        return;
                    }
                    // Не ломаем чат, просто подсвечиваем ошибку над формой
                    if (cooldownEl) {
                        cooldownEl.textContent = 'Не удалось отправить сообщение. Попробуйте ещё раз чуть позже.';
                    }
                    shake();
                });
        });
    }

    // Клик по карточке объявления — делаем весь блок кликабельным
    document.querySelectorAll('.listing-card-link').forEach(function (el) {
        el.addEventListener('click', function (e) {
            if (e.target.closest('a, button')) return;
            var href = el.getAttribute('data-href');
            if (href) {
                window.location = href;
            }
        });
    });
});

