/**
 * Утилиты форматирования цен для чата и карточек.
 */
(function (global) {
    'use strict';

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

    global.formatPrice = formatPrice;
    global.formatPriceFull = formatPriceFull;
})(typeof window !== 'undefined' ? window : this);
