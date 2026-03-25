/**
 * Карточки «Купить» и «Завершить сделку» — обновление итоговой суммы
 */
(function () {
    function init() {
        var formatPriceFull = window.formatPriceFull;
        if (typeof formatPriceFull !== 'function') return;

        var buyCard = document.querySelector('.conv-buy-card');
        var buyQty = document.getElementById('conv-buy-qty');
        if (buyCard && buyQty) {
            var unitPrice = parseFloat(buyCard.dataset.unitPrice || 0);
            var currency = buyCard.dataset.currency || 'AUEC';
            var totalSpan = buyCard.querySelector('.conv-total-display');
            function updateTotal() {
                var qty = parseInt(buyQty.value, 10) || 1;
                var total = unitPrice * qty;
                if (totalSpan) totalSpan.textContent = 'Итого: ' + formatPriceFull(total) + ' ' + currency;
            }
            buyQty.addEventListener('input', updateTotal);
            buyQty.addEventListener('change', updateTotal);
            updateTotal();
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
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
