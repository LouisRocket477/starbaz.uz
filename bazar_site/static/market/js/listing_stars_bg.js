document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('listing-stars-bg');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    let stars = [];
    const DENSITY = 0.00035; // плотность фоновых звёзд на пиксель

    function createStars(width, height) {
        stars = [];
        const count = Math.floor(width * height * DENSITY);

        for (let i = 0; i < count; i++) {
            stars.push({
                x: Math.random() * width,
                y: Math.random() * height,
                size: Math.random() * 1.4 + 0.3,
                alpha: Math.random(),
                twinkle: Math.random() * 0.02 + 0.003,
            });
        }
    }

    function resize() {
        const width = window.innerWidth;
        const height = window.innerHeight;

        canvas.width = width;
        canvas.height = height;

        createStars(width, height);
    }

    let resizeTimeout = null;
    window.addEventListener('resize', function () {
        if (resizeTimeout) {
            clearTimeout(resizeTimeout);
        }
        resizeTimeout = setTimeout(resize, 150);
    });

    function draw() {
        const width = canvas.width;
        const height = canvas.height;
        if (!width || !height) {
            requestAnimationFrame(draw);
            return;
        }

        ctx.clearRect(0, 0, width, height);

        for (const s of stars) {
            s.alpha += s.twinkle;

            if (s.alpha >= 1 || s.alpha <= 0) {
                s.twinkle = -s.twinkle;
            }

            ctx.globalAlpha = s.alpha;
            ctx.fillStyle = '#ffffff';
            ctx.beginPath();
            ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
            ctx.fill();
        }

        ctx.globalAlpha = 1;

        // Только статичное мерцание — без пролетающих комет
        requestAnimationFrame(draw);
    }

    resize();
    draw();
});


