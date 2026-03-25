function formatPrice(num) {
    if (num >= 1e12) return (num / 1e12).toFixed(2).replace(/\.?0+$/, '') + ' Tn';
    if (num >= 1e9) return (num / 1e9).toFixed(2).replace(/\.?0+$/, '') + ' Bn';
    if (num >= 1e6) return (num / 1e6).toFixed(2).replace(/\.?0+$/, '') + ' M';
    if (num >= 1e3) return (num / 1e3).toFixed(2).replace(/\.?0+$/, '') + ' k';
    return num % 1 ? num.toFixed(2) : String(num);
}

document.addEventListener('DOMContentLoaded', function () {
    // --- График активности по товару ---
    (function initListingActivityChart() {
        if (typeof Chart === 'undefined') return;

        var labelsEl = document.getElementById('listingChartLabels');
        var ordersEl = document.getElementById('listingChartOrders');
        var soldEl = document.getElementById('listingChartSold');
        var pricesEl = document.getElementById('listingChartPrices');
        var pricesMinEl = document.getElementById('listingChartPricesMin');
        var pricesMaxEl = document.getElementById('listingChartPricesMax');

        if (!labelsEl || !ordersEl || !pricesEl) return;

        var labels = labelsEl.value ? labelsEl.value.split(',') : [];
        var orders = ordersEl.value ? ordersEl.value.split(',').map(Number) : [];
        var sold = soldEl && soldEl.value ? soldEl.value.split(',').map(Number) : [];
        if (orders.length !== labels.length) orders = new Array(labels.length).fill(0);
        if (sold.length !== labels.length) sold = new Array(labels.length).fill(0);

        var prices = pricesEl.value ? pricesEl.value.split(',').map(parseFloat) : [];
        var pricesMin = pricesMinEl && pricesMinEl.value ? pricesMinEl.value.split(',').map(parseFloat) : [];
        var pricesMax = pricesMaxEl && pricesMaxEl.value ? pricesMaxEl.value.split(',').map(parseFloat) : [];
        if (pricesMin.length !== labels.length) pricesMin = prices.slice();
        if (pricesMax.length !== labels.length) pricesMax = prices.slice();
        if (!labels.length) return;

        var allQty = orders.concat(sold).filter(function (x) {
            return typeof x === 'number' && !isNaN(x) && x >= 0;
        });
        var suggestedMaxQty = allQty.length
            ? Math.max(5, Math.ceil(Math.max.apply(null, allQty) * 1.3) + 1)
            : 6;

        var allPriceVals = prices
            .concat(pricesMin)
            .concat(pricesMax)
            .filter(function (p) {
                return typeof p === 'number' && p > 0 && !isNaN(p);
            });
        var minPrice = allPriceVals.length ? Math.min.apply(null, allPriceVals) : 1;
        var maxPrice = allPriceVals.length ? Math.max.apply(null, allPriceVals) : 1;
        if (minPrice === maxPrice) {
            minPrice = minPrice * 0.99;
            maxPrice = maxPrice * 1.01;
        } else {
            var pad = (maxPrice - minPrice) * 0.1 || 1;
            minPrice = Math.max(1, minPrice - pad);
            maxPrice = maxPrice + pad;
        }

        var ctx = document.getElementById('listingActivityChart');
        if (!ctx) return;

        new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Диапазон цены',
                        data: pricesMin,
                        type: 'line',
                        borderColor: 'transparent',
                        backgroundColor: 'transparent',
                        fill: { target: '+1', color: 'rgba(34, 197, 94, 0.12)' },
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        yAxisID: 'y1',
                        order: 0,
                        spanGaps: false,
                    },
                    {
                        label: 'Диапазон макс',
                        data: pricesMax,
                        type: 'line',
                        borderColor: 'transparent',
                        backgroundColor: 'transparent',
                        fill: false,
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        yAxisID: 'y1',
                        order: 0,
                        spanGaps: false,
                    },
                    {
                        label: 'Заявки',
                        data: orders,
                        backgroundColor: 'rgba(148, 163, 184, 0.5)',
                        borderColor: 'rgba(148, 163, 184, 0.8)',
                        borderWidth: 1,
                        borderRadius: 4,
                        maxBarThickness: 12,
                        yAxisID: 'y',
                        order: 3,
                    },
                    {
                        label: 'Продано',
                        data: sold,
                        backgroundColor: 'rgba(56, 189, 248, 0.65)',
                        borderColor: 'rgba(56, 189, 248, 0.9)',
                        borderWidth: 1,
                        borderRadius: 4,
                        maxBarThickness: 12,
                        yAxisID: 'y',
                        order: 2,
                    },
                    {
                        label: 'Цена',
                        data: prices,
                        type: 'line',
                        borderColor: '#22c55e',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        fill: true,
                        tension: 0.35,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        borderWidth: 2,
                        yAxisID: 'y1',
                        order: 1,
                        spanGaps: false,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        grid: { color: 'rgba(148, 163, 184, 0.12)' },
                        ticks: {
                            color: 'rgba(148, 163, 184, 0.7)',
                            maxRotation: 0,
                            maxTicksLimit: 10,
                        },
                    },
                    y: {
                        type: 'linear',
                        position: 'left',
                        min: 0,
                        suggestedMax: suggestedMaxQty,
                        grid: { color: 'rgba(148, 163, 184, 0.12)' },
                        ticks: {
                            color: 'rgba(148, 163, 184, 0.7)',
                            stepSize: 1,
                        },
                        beginAtZero: true,
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        min: minPrice,
                        max: maxPrice,
                        grid: { drawOnChartArea: false },
                        ticks: {
                            color: 'rgba(34, 197, 94, 0.9)',
                            callback: function (v) {
                                if (v >= 1e9) return (v / 1e9).toFixed(0) + 'B';
                                if (v >= 1e6) return (v / 1e6).toFixed(0) + 'M';
                                if (v >= 1000) return (v / 1000).toFixed(1) + 'k';
                                return v;
                            },
                        },
                        beginAtZero: false,
                    },
                },
                interaction: { intersect: false, mode: 'index' },
            },
        });
    })();

    // --- Личный чат и действия ---
    var buyBlock = document.querySelector('.listing-chat-buy-block');
    var buyQty = document.getElementById('listing-chat-buy-qty');
    if (buyBlock && buyQty) {
        var unitPrice = parseFloat(buyBlock.dataset.unitPrice || 0);
        var currency = buyBlock.dataset.currency || 'AUEC';
        var totalSpan = buyBlock.querySelector('.listing-chat-total-display');
        function updateTotal() {
            var qty = parseInt(buyQty.value, 10) || 1;
            totalSpan.textContent = 'Итого: ' + formatPrice(unitPrice * qty) + ' ' + currency;
        }
        buyQty.addEventListener('input', updateTotal);
        buyQty.addEventListener('change', updateTotal);
        updateTotal();
    }

    document.querySelectorAll('.rating-stars').forEach(function (container) {
        const stars = Array.from(container.querySelectorAll('.star'));

        function setSelected(value) {
            stars.forEach(function (star) {
                const v = parseInt(star.dataset.value || '0', 10);
                star.classList.toggle('selected', v <= value);
            });
        }

        stars.forEach(function (star) {
            const value = parseInt(star.dataset.value || '0', 10);
            star.addEventListener('click', function () {
                const input = container.querySelector('#rating_' + value);
                if (input) {
                    input.checked = true;
                }
                setSelected(value);
            });
            star.addEventListener('mouseenter', function () {
                setSelected(value);
            });
        });

        container.addEventListener('mouseleave', function () {
            const checked = container.querySelector('input[type="radio"][name="rating"]:checked');
            const current = checked ? parseInt(checked.value || '0', 10) : 0;
            setSelected(current);
        });
    });

    const mainImage = document.querySelector('.js-listing-main-image');
    const thumbEls = document.querySelectorAll('.js-listing-thumb');

    const modalEl = document.createElement('div');
    modalEl.className = 'modal fade';
    modalEl.id = 'listingImageModal';
    modalEl.tabIndex = -1;
    modalEl.innerHTML = ''
        + '<div class="modal-dialog modal-dialog-centered modal-lg">'
        + '  <div class="modal-content bg-dark border-0">'
        + '    <div class="modal-body p-0">'
        + '      <img id="listingImageModalImg" src="" alt="" '
        + '           style="width: 100%; height: 100%; object-fit: contain; max-height: 80vh;">'
        + '    </div>'
        + '  </div>'
        + '</div>';
    document.body.appendChild(modalEl);
    const modalImg = modalEl.querySelector('#listingImageModalImg');

    function openImageModal(url) {
        if (!url || !modalImg || typeof bootstrap === 'undefined') return;
        modalImg.src = url;
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }

    if (mainImage) {
        mainImage.addEventListener('click', function () {
            const url = this.getAttribute('data-full-url') || this.src;
            openImageModal(url);
        });
    }

    thumbEls.forEach(function (thumb) {
        thumb.addEventListener('click', function () {
            const url = this.getAttribute('data-full-url') || this.src;
            if (mainImage && url) {
                mainImage.src = url;
                mainImage.setAttribute('data-full-url', url);
            }
            openImageModal(url);
        });
    });

    // Личный чат с продавцом: AJAX-отправка без перезагрузки, авто-прокрутка вниз
    const chatMessages = document.getElementById('listing-chat-messages');
    const chatForm = document.getElementById('listing-chat-form');
    const chatInput = document.getElementById('listing-chat-input');
    const chatSubmit = document.getElementById('listing-chat-submit');

    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    if (chatForm && chatInput && chatMessages) {
        chatInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.requestSubmit();
            }
        });
        const sendUrl = chatForm.dataset.sendUrl;
        if (sendUrl) {
            chatForm.addEventListener('submit', function (e) {
                e.preventDefault();
                const text = chatInput.value.trim();
                if (!text) return;

                const formData = new FormData(chatForm);

                if (chatSubmit) chatSubmit.disabled = true;

                fetch(sendUrl, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        if (data && data.message) {
                            const placeholder = chatMessages.querySelector('.listing-chat-empty');
                            if (placeholder) placeholder.remove();

                            const msg = data.message;
                            const wrap = document.createElement('div');
                            wrap.className = 'listing-chat-msg ' + (msg.is_me ? 'listing-chat-msg-me' : 'listing-chat-msg-them');
                            wrap.innerHTML = ''
                                + '<div class="listing-chat-msg-head">'
                                + '<span class="listing-chat-avatar listing-chat-avatar-placeholder">' + (msg.sender ? msg.sender.charAt(0).toUpperCase() : '?') + '</span>'
                                + '<span class="listing-chat-msg-meta">' + msg.sender + ' · ' + msg.created_at + '</span>'
                                + '</div>'
                                + '<div class="listing-chat-bubble">' + (msg.content || '').replace(/\n/g, '<br>') + '</div>';
                            chatMessages.appendChild(wrap);
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                            chatInput.value = '';
                        }
                    })
                    .catch(function () {})
                    .finally(function () {
                        if (chatSubmit) chatSubmit.disabled = false;
                    });
            });
        }
    }
});

