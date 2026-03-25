/**
 * Чат — форма отправки, paste-скриншот, эмодзи, appendMessage.
 * Требует загрузки utils/formatPrice.js (для cards) — порядок скриптов в шаблоне.
 */
(function () {
    'use strict';

    function initChatForm() {
        const hadUnread = window.CONVERSATION_HAD_UNREAD === true;
        const audioEl = document.getElementById('msg-sound');
        if (hadUnread && audioEl && audioEl.play) {
            audioEl.play().catch(function () {});
        }

        const messagesBox = document.getElementById('messages-box');
        const textarea = document.getElementById('chat-message-input');
        const fileInput = document.getElementById('chat-image-input');
        const imageLabel = document.getElementById('chat-image-label');
        const emojiToggle = document.getElementById('chat-emoji-toggle');
        const emojiPanel = document.getElementById('chat-emoji-panel');
        const form = document.getElementById('chat-form');
        const submitBtn = document.getElementById('chat-submit-btn');
        const cooldownHint = document.getElementById('chat-cooldown-hint');

        if (messagesBox) {
            messagesBox.scrollTop = messagesBox.scrollHeight;
        }

        if (fileInput && imageLabel) {
            fileInput.addEventListener('change', function () {
                if (fileInput.files && fileInput.files.length > 0) {
                    imageLabel.style.display = 'inline';
                    imageLabel.textContent = 'Прикреплено: ' + (fileInput.files[0].name || 'картинка');
                } else {
                    imageLabel.style.display = 'none';
                }
            });
        }

        if (textarea && fileInput && window.DataTransfer) {
            textarea.addEventListener('paste', function (e) {
                const items = e.clipboardData && e.clipboardData.items;
                if (!items) return;
                for (let i = 0; i < items.length; i++) {
                    const item = items[i];
                    if (item.kind === 'file' && item.type.startsWith('image/')) {
                        const file = item.getAsFile();
                        if (!file) continue;
                        const dt = new DataTransfer();
                        dt.items.add(file);
                        fileInput.files = dt.files;
                        if (imageLabel) {
                            imageLabel.style.display = 'inline';
                            imageLabel.textContent = 'Прикреплён скриншот (' + (file.name || 'image') + ')';
                        }
                        break;
                    }
                }
            });
        }

        if (emojiToggle && emojiPanel) {
            emojiToggle.addEventListener('click', function () {
                emojiPanel.style.display = emojiPanel.style.display === 'block' ? 'none' : 'block';
            });
            emojiPanel.addEventListener('click', function (e) {
                const btn = e.target.closest('.chat-emoji-btn');
                if (!btn || !textarea) return;
                const emoji = btn.textContent || '';
                const start = textarea.selectionStart || 0;
                const end = textarea.selectionEnd || 0;
                const value = textarea.value || '';
                textarea.value = value.slice(0, start) + emoji + value.slice(end);
                const pos = start + emoji.length;
                textarea.focus();
                textarea.setSelectionRange(pos, pos);
            });
        }

        if (form && textarea && messagesBox) {
            const sendUrl = form.dataset.sendUrl || (window.location.pathname.replace(/\/$/, '') + '/send/');
            let cooldownTimerId = null;
            let cooldownRemaining = 0;

            function startCooldown(seconds) {
                if (!cooldownHint) return;
                if (cooldownTimerId) clearInterval(cooldownTimerId);
                cooldownRemaining = seconds;
                function tick() {
                    if (!cooldownHint) return;
                    if (cooldownRemaining <= 0) {
                        cooldownHint.textContent = '';
                        clearInterval(cooldownTimerId);
                        cooldownTimerId = null;
                        return;
                    }
                    cooldownHint.textContent = 'Слишком часто. Попробуйте ещё раз через ' + cooldownRemaining + ' с.';
                    cooldownRemaining -= 1;
                }
                tick();
                cooldownTimerId = setInterval(tick, 1000);
            }

            function appendMessage(msg) {
                const wrapper = document.createElement('div');
                wrapper.className = 'conv-msg ' + (msg.is_me ? 'conv-msg-me' : 'conv-msg-them');
                const head = document.createElement('div');
                head.className = 'conv-msg-head';
                head.innerHTML = (msg.avatar_url
                    ? '<img src="' + msg.avatar_url + '" alt="" class="conv-msg-avatar">'
                    : '<span class="conv-msg-avatar conv-msg-avatar-placeholder">' + (msg.sender ? msg.sender.charAt(0).toUpperCase() : '?') + '</span>'
                ) + '<span class="conv-msg-meta">' + msg.sender + ' · ' + msg.created_at + '</span>';
                wrapper.appendChild(head);
                const bubbleWrap = document.createElement('div');
                bubbleWrap.className = 'conv-bubble-wrap';
                if (msg.image_url) {
                    const imgWrap = document.createElement('div');
                    imgWrap.className = 'conv-bubble-image mb-1';
                    const img = document.createElement('img');
                    img.src = msg.image_url;
                    img.alt = 'Вложение';
                    img.className = 'chat-image-zoom';
                    img.dataset.fullUrl = msg.image_url;
                    imgWrap.appendChild(img);
                    bubbleWrap.appendChild(imgWrap);
                }
                if (msg.content) {
                    const bubble = document.createElement('div');
                    bubble.className = 'conv-bubble';
                    bubble.innerHTML = msg.content.replace(/\n/g, '<br>');
                    bubbleWrap.appendChild(bubble);
                }
                wrapper.appendChild(bubbleWrap);
                messagesBox.appendChild(wrapper);
                messagesBox.scrollTop = messagesBox.scrollHeight;
                const zoomImages = wrapper.querySelectorAll('.chat-image-zoom');
                if (zoomImages.length && typeof bootstrap !== 'undefined') {
                    let modalEl = document.getElementById('chatImageModal');
                    if (!modalEl) {
                        modalEl = document.createElement('div');
                        modalEl.id = 'chatImageModal';
                        modalEl.className = 'modal fade';
                        modalEl.tabIndex = -1;
                        modalEl.innerHTML = '<div class="modal-dialog modal-dialog-centered modal-lg"><div class="modal-content bg-dark border-0"><div class="modal-body p-0"><img id="chatImageModalImg" src="" alt="" style="width:100%;height:100%;object-fit:contain;max-height:80vh;"></div></div></div>';
                        document.body.appendChild(modalEl);
                    }
                    const modalImg = document.getElementById('chatImageModalImg');
                    zoomImages.forEach(function (img) {
                        img.addEventListener('click', function () {
                            if (modalImg) modalImg.src = img.getAttribute('data-full-url') || img.src;
                            new bootstrap.Modal(modalEl).show();
                        });
                    });
                }
            }

            form.addEventListener('submit', function (e) {
                e.preventDefault();
                const text = textarea.value.trim();
                const hasFile = fileInput && fileInput.files && fileInput.files.length > 0;
                if (!text && !hasFile) return;
                const formData = new FormData(form);
                if (submitBtn) submitBtn.disabled = true;
                fetch(sendUrl, { method: 'POST', body: formData })
                    .then(function (r) { return r.json().then(function (data) { if (!r.ok) throw data; return data; }); })
                    .then(function (data) {
                        if (data && data.message) {
                            appendMessage(data.message);
                            textarea.value = '';
                            if (fileInput) fileInput.value = '';
                            if (imageLabel) imageLabel.textContent = 'Файл не выбран';
                        }
                    })
                    .catch(function (err) {
                        if (err && err.error === 'cooldown') {
                            let seconds = 5;
                            if (typeof err.detail === 'string') {
                                const m = err.detail.match(/(\d+)/);
                                if (m) { const p = parseInt(m[1], 10); if (!Number.isNaN(p)) seconds = p; }
                            }
                            startCooldown(seconds);
                        }
                    })
                    .finally(function () { if (submitBtn) submitBtn.disabled = false; });
            });

            textarea.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.altKey) {
                    e.preventDefault();
                    form.requestSubmit();
                }
            });
        }

        const chatImages = document.querySelectorAll('.chat-image-zoom');
        if (chatImages.length && typeof bootstrap !== 'undefined') {
            let modalEl = document.getElementById('chatImageModal');
            if (!modalEl) {
                modalEl = document.createElement('div');
                modalEl.id = 'chatImageModal';
                modalEl.className = 'modal fade';
                modalEl.tabIndex = -1;
                modalEl.innerHTML = '<div class="modal-dialog modal-dialog-centered modal-lg"><div class="modal-content bg-dark border-0"><div class="modal-body p-0"><img id="chatImageModalImg" src="" alt="" style="width:100%;height:100%;object-fit:contain;max-height:80vh;"></div></div></div>';
                document.body.appendChild(modalEl);
            }
            const modalImg = document.getElementById('chatImageModalImg');
            const modal = new bootstrap.Modal(modalEl);
            chatImages.forEach(function (img) {
                img.addEventListener('click', function () {
                    if (modalImg) modalImg.src = img.getAttribute('data-full-url') || img.src;
                    modal.show();
                });
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initChatForm);
    } else {
        initChatForm();
    }
})();
