function formatPrice(num) {
    if (num >= 1e12) return (num / 1e12).toFixed(2).replace(/\.?0+$/, '') + ' Tn';
    if (num >= 1e9) return (num / 1e9).toFixed(2).replace(/\.?0+$/, '') + ' Bn';
    if (num >= 1e6) return (num / 1e6).toFixed(2).replace(/\.?0+$/, '') + ' M';
    if (num >= 1e3) return (num / 1e3).toFixed(2).replace(/\.?0+$/, '') + ' k';
    return num % 1 ? num.toFixed(2) : String(num);
}

function formatPriceFull(num) {
    var n = parseFloat(num);
    if (isNaN(n)) return '0';
    var str = n >= 1 ? String(Math.round(n)) : n.toFixed(2);
    var parts = str.split('.');
    var intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    return parts[1] ? intPart + ',' + parts[1] : intPart;
}

document.addEventListener('DOMContentLoaded', function () {
    const messagesBox = document.getElementById('messages-box');
    const hadUnread =
        messagesBox &&
        messagesBox.getAttribute('data-had-unread') === 'true';
    const audioEl = document.getElementById('msg-sound');
    if (hadUnread && audioEl && audioEl.play) {
        audioEl.play().catch(function () {});
    }

    var buyCard = document.querySelector('.conv-buy-card');
    var buyQty = document.getElementById('conv-buy-qty');
    if (buyCard && buyQty && buyCard.dataset.unitPrice !== undefined) {
        // Карточка покупки "Купить"
        var unitPrice = parseFloat(buyCard.dataset.unitPrice || 0);
        var currency = buyCard.dataset.currency || 'AUEC';
        var totalSpan = buyCard.querySelector('.conv-total-display');
        function updateTotal() {
            var qty = parseInt(buyQty.value, 10) || 1;
            var total = unitPrice * qty;
            totalSpan.textContent = 'Итого: ' + formatPriceFull(total) + ' ' + currency;
        }
        buyQty.addEventListener('input', updateTotal);
        buyQty.addEventListener('change', updateTotal);
        updateTotal();
    }

    // Карточка "Продать" по объявлению-покупке: показываем разницу цен
    var sellOfferCard = document.querySelector('.conv-buy-card[data-base-price]');
    if (sellOfferCard) {
        var basePrice = parseFloat(sellOfferCard.dataset.basePrice || 0);
        var baseCurrency = sellOfferCard.dataset.baseCurrency || 'AUEC';
        var selectEl = sellOfferCard.querySelector('.conv-sell-offer-select');
        var qtyInput = sellOfferCard.querySelector('.conv-sell-offer-qty');
        var stockEl = sellOfferCard.querySelector('.conv-sell-offer-stock');
        var diffEl = sellOfferCard.querySelector('.conv-sell-offer-diff');

        function updateDiff() {
            if (!selectEl || !selectEl.options.length) return;
            var opt = selectEl.options[selectEl.selectedIndex];
            var qtyAttr = opt.getAttribute('data-qty');
            var maxQty = qtyAttr ? parseInt(qtyAttr, 10) : null;

            if (stockEl) {
                if (maxQty && maxQty > 0) {
                    stockEl.textContent = 'В наличии у вас: ' + maxQty + ' шт.';
                } else {
                    stockEl.textContent = '';
                }
            }

            if (qtyInput) {
                if (maxQty && maxQty > 0) {
                    qtyInput.max = String(maxQty);
                    if (!qtyInput.value || parseInt(qtyInput.value, 10) < 1) {
                        qtyInput.value = '1';
                    }
                    if (parseInt(qtyInput.value, 10) > maxQty) {
                        qtyInput.value = String(maxQty);
                    }
                } else {
                    qtyInput.removeAttribute('max');
                }
            }

            if (!diffEl) return;
            var myPrice = parseFloat(opt.getAttribute('data-price') || '0');
            var myCurrency = opt.getAttribute('data-currency') || baseCurrency;

            if (!basePrice || isNaN(basePrice) || isNaN(myPrice)) {
                diffEl.textContent = '';
                return;
            }

            // Разницу считаем по абсолютной величине, валюты должны совпадать
            if (myCurrency !== baseCurrency) {
                diffEl.textContent = 'Разные валюты: ' + myCurrency + ' / ' + baseCurrency + '. Обсудите условия в чате.';
                return;
            }

            var diff = myPrice - basePrice;
            if (Math.abs(diff) < 0.01) {
                diffEl.textContent = 'Цены за 1 шт. совпадают — сделка без доплаты (' + formatPriceFull(basePrice) + ' ' + baseCurrency + ').';
            } else if (diff > 0) {
                diffEl.textContent = 'За 1 шт. ваш товар дороже на ' + formatPriceFull(diff) + ' ' + baseCurrency + '. Обсудите доплату в вашу пользу.';
            } else {
                diffEl.textContent = 'За 1 шт. товар покупателя дороже на ' + formatPriceFull(Math.abs(diff)) + ' ' + baseCurrency + '. Обсудите доплату в его пользу.';
            }
        }

        if (selectEl && diffEl) {
            selectEl.addEventListener('change', updateDiff);
            updateDiff();
        }
    }

    var sellerCard = document.querySelector('.conv-complete-deal-card');
    if (sellerCard) {
        var unitPrice = parseFloat(sellerCard.dataset.unitPrice || 0);
        var currency = sellerCard.dataset.currency || 'AUEC';
        sellerCard.querySelectorAll('.conv-req-total').forEach(function (el) {
            var qty = parseInt(el.dataset.qty || 0, 10);
            el.textContent = formatPriceFull(unitPrice * qty) + ' ' + currency;
        });
        sellerCard.querySelectorAll('.conv-seller-qty').forEach(function (input) {
            var row = input.closest('.conv-seller-deal-row');
            if (row) {
                var totalEl = row.querySelector('.conv-req-total');
                if (totalEl) {
                    input.addEventListener('input', function () {
                        var qty = parseInt(input.value, 10) || 0;
                        totalEl.textContent = formatPriceFull(unitPrice * qty) + ' ' + currency;
                        totalEl.dataset.qty = qty;
                    });
                }
            }
        });
        var manualQty = document.getElementById('conv-seller-qty-manual');
        var manualTotal = sellerCard.querySelector('.conv-seller-total-display');
        if (manualQty && manualTotal) {
            function upd() {
                var qty = parseInt(manualQty.value, 10) || 1;
                manualTotal.textContent = '= ' + formatPriceFull(unitPrice * qty) + ' ' + currency;
            }
            manualQty.addEventListener('input', upd);
            manualQty.addEventListener('change', upd);
            upd();
        }
    }


    const textarea = document.getElementById('chat-message-input');
    const fileInput = document.getElementById('chat-image-input');
    const imageLabel = document.getElementById('chat-image-label');
    const emojiToggle = document.getElementById('chat-emoji-toggle');
    const emojiPanel = document.getElementById('chat-emoji-panel');
    const form = document.getElementById('chat-form');
    const submitBtn = document.getElementById('chat-submit-btn');
    const cooldownHint = document.getElementById('chat-cooldown-hint');

    if (messagesBox) {
        // При загрузке страницы сразу прокручиваем историю в самый низ
        messagesBox.scrollTop = messagesBox.scrollHeight;
    }

    if (fileInput && imageLabel) {
        fileInput.addEventListener('change', function () {
            if (fileInput.files && fileInput.files.length > 0) {
                imageLabel.style.display = 'inline';
                const name = fileInput.files[0].name || 'картинка';
                imageLabel.textContent = 'Прикреплено: ' + name;
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
            const isVisible = emojiPanel.style.display === 'block';
            emojiPanel.style.display = isVisible ? 'none' : 'block';
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
            if (cooldownTimerId) {
                clearInterval(cooldownTimerId);
            }
            cooldownRemaining = seconds;

            function tick() {
                if (!cooldownHint) return;
                if (cooldownRemaining <= 0) {
                    cooldownHint.textContent = '';
                    clearInterval(cooldownTimerId);
                    cooldownTimerId = null;
                    return;
                }
                cooldownHint.textContent = `Слишком часто. Попробуйте ещё раз через ${cooldownRemaining} с.`;
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
            let avatarHtml;
            if (msg.avatar_url) {
                avatarHtml = '<img src="' + msg.avatar_url + '" alt="" class="conv-msg-avatar">';
            } else {
                avatarHtml = '<span class="conv-msg-avatar conv-msg-avatar-placeholder">' + (msg.sender ? msg.sender.charAt(0).toUpperCase() : '?') + '</span>';
            }
            head.innerHTML = avatarHtml + '<span class="conv-msg-meta">' + msg.sender + ' · ' + msg.created_at + '</span>';
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

            var zoomImages = wrapper.querySelectorAll('.chat-image-zoom');
            if (zoomImages.length && typeof bootstrap !== 'undefined') {
                var modalEl = document.getElementById('chatImageModal');
                if (!modalEl) {
                    modalEl = document.createElement('div');
                    modalEl.id = 'chatImageModal';
                    modalEl.className = 'modal fade';
                    modalEl.tabIndex = -1;
                    modalEl.innerHTML = '<div class="modal-dialog modal-dialog-centered modal-lg"><div class="modal-content bg-dark border-0"><div class="modal-body p-0"><img id="chatImageModalImg" src="" alt="" style="width:100%;height:100%;object-fit:contain;max-height:80vh;"></div></div></div>';
                    document.body.appendChild(modalEl);
                }
                var modalImg = document.getElementById('chatImageModalImg');
                zoomImages.forEach(function (img) {
                    img.addEventListener('click', function () {
                        var fullUrl = img.getAttribute('data-full-url') || img.src;
                        if (modalImg) modalImg.src = fullUrl;
                        new bootstrap.Modal(modalEl).show();
                    });
                });
            }
        }

        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const text = textarea.value.trim();
            const hasFile = fileInput && fileInput.files && fileInput.files.length > 0;
            if (!text && !hasFile) {
                return;
            }

            const formData = new FormData(form);

            if (submitBtn) {
                submitBtn.disabled = true;
            }

            fetch(sendUrl, {
                method: 'POST',
                body: formData,
            })
                .then(function (r) {
                    return r.json().then(function (data) {
                        if (!r.ok) {
                            throw data;
                        }
                        return data;
                    });
                })
                .then(function (data) {
                    if (data && data.message) {
                        appendMessage(data.message);
                        textarea.value = '';
                        if (fileInput) {
                            fileInput.value = '';
                        }
                        if (imageLabel) {
                            imageLabel.textContent = 'Файл не выбран';
                        }
                    }
                })
                .catch(function (err) {
                    if (err && err.error === 'cooldown') {
                        let seconds = 5;
                        if (typeof err.detail === 'string') {
                            const match = err.detail.match(/(\d+)/);
                            if (match) {
                                const parsed = parseInt(match[1], 10);
                                if (!Number.isNaN(parsed)) {
                                    seconds = parsed;
                                }
                            }
                        }
                        startCooldown(seconds);
                    }
                    // Не ломаем страницу и не чистим поле, чтобы пользователь не терял текст
                })
                .finally(function () {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                    }
                });
        });

        // Отправка по Enter (Shift+Enter — перенос строки)
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
            modalEl.innerHTML = ''
                + '<div class="modal-dialog modal-dialog-centered modal-lg">'
                + '  <div class="modal-content bg-dark border-0">'
                + '    <div class="modal-body p-0">'
                + '      <img id="chatImageModalImg" src="" alt="" '
                + '           style="width: 100%; height: 100%; object-fit: contain; max-height: 80vh;">'
                + '    </div>'
                + '  </div>'
                + '</div>';
            document.body.appendChild(modalEl);
        }
        const modalImg = document.getElementById('chatImageModalImg');
        const modal = new bootstrap.Modal(modalEl);

        chatImages.forEach(function (img) {
            img.addEventListener('click', function () {
                const fullUrl = img.getAttribute('data-full-url') || img.src;
                if (modalImg) {
                    modalImg.src = fullUrl;
                }
                modal.show();
            });
        });
    }
});

