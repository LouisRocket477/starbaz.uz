document.addEventListener('DOMContentLoaded', function () {
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

