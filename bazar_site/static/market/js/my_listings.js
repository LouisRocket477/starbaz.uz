document.addEventListener('DOMContentLoaded', function () {
    const timers = document.querySelectorAll('.my-listings-boost-timer[data-boost-until]');
    if (!timers.length) {
        return;
    }

    function updateTimers() {
        const now = new Date();
        timers.forEach(function (el) {
            const iso = el.getAttribute('data-boost-until');
            if (!iso) return;
            const until = new Date(iso);
            if (isNaN(until.getTime())) return;

            let diffMs = until.getTime() - now.getTime();
            if (diffMs <= 0) {
                el.textContent = '00:00:00';
                return;
            }
            const totalSeconds = Math.floor(diffMs / 1000);
            const hours = Math.floor(totalSeconds / 3600);
            const minutes = Math.floor((totalSeconds % 3600) / 60);
            const seconds = totalSeconds % 60;

            const pad = function (n) { return String(n).padStart(2, '0'); };
            el.textContent = pad(hours) + ':' + pad(minutes) + ':' + pad(seconds);
        });
    }

    updateTimers();
    setInterval(updateTimers, 1000);
});

