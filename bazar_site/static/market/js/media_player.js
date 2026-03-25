/**
 * Упрощённый глобальный плеер:
 * - окно плеера скрыто;
 * - кнопка-нота в навбаре работает как play/pause.
 */
(function () {
    'use strict';

    var STORAGE_KEY = 'starbaz_media_player';
    var scriptEl = document.getElementById('media-playlist-data');
    var PLAYLIST = scriptEl && scriptEl.textContent ? JSON.parse(scriptEl.textContent) : [];

    function getState() {
        try {
            var raw = localStorage.getItem(STORAGE_KEY);
            if (!raw) return null;
            return JSON.parse(raw);
        } catch (e) {
            return null;
        }
    }

    function saveState(state) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        } catch (e) {}
    }

    function getDefaultState() {
        return {
            trackIndex: 0,
            isPlaying: false,
            volume: 0.2,
            shufflePool: []
        };
    }

    var state = getState() || getDefaultState();
    state.volume = Math.max(0, Math.min(1, Number(state.volume || 0.2)));
    state.trackIndex = Math.max(0, Math.min(Number(state.trackIndex || 0), Math.max(PLAYLIST.length - 1, 0)));
    state.isPlaying = !!state.isPlaying;
    if (!Array.isArray(state.shufflePool)) {
        state.shufflePool = [];
    }

    var audio = document.getElementById('media-audio');
    var toggleBtn = document.getElementById('media-player-toggle');
    var eqContainer = document.querySelector('.site-equalizer');
    var eqCanvas = document.getElementById('site-equalizer-canvas');
    var eqCtx = eqCanvas ? eqCanvas.getContext('2d') : null;
    var EQ_BARS_COUNT = 512;
    if (!audio || !toggleBtn || !PLAYLIST.length) return;

    var audioCtx = null;
    var analyser = null;
    var sourceNode = null;
    var freqData = null;
    var rafId = null;
    var eqSmoothingTimer = null;
    var volumeHudHideTimer = null;
    var volumeHud = null;

    function ensureVolumeHud() {
        if (volumeHud) return volumeHud;
        volumeHud = document.createElement('div');
        volumeHud.className = 'media-volume-hud';
        volumeHud.setAttribute('aria-hidden', 'true');
        document.body.appendChild(volumeHud);
        return volumeHud;
    }

    function getVolumePercent() {
        return Math.round(Math.max(0, Math.min(1, state.volume)) * 100);
    }

    function showVolumeHud() {
        var hud = ensureVolumeHud();
        var rect = toggleBtn.getBoundingClientRect();
        hud.textContent = 'Громкость: ' + getVolumePercent() + '%';
        hud.style.left = Math.round(rect.left + rect.width / 2) + 'px';
        hud.style.top = Math.round(rect.bottom + 10) + 'px';
        hud.classList.add('is-visible');
        if (volumeHudHideTimer) {
            clearTimeout(volumeHudHideTimer);
        }
        volumeHudHideTimer = setTimeout(function () {
            hud.classList.remove('is-visible');
        }, 900);
    }

    function refillShufflePool() {
        var pool = [];
        for (var i = 0; i < PLAYLIST.length; i++) {
            if (i !== state.trackIndex) {
                pool.push(i);
            }
        }
        // Fisher-Yates shuffle
        for (var j = pool.length - 1; j > 0; j--) {
            var r = Math.floor(Math.random() * (j + 1));
            var tmp = pool[j];
            pool[j] = pool[r];
            pool[r] = tmp;
        }
        state.shufflePool = pool;
    }

    function normalizeShufflePool() {
        var maxIndex = PLAYLIST.length - 1;
        state.shufflePool = state.shufflePool
            .map(function (v) { return Number(v); })
            .filter(function (v) { return Number.isInteger(v) && v >= 0 && v <= maxIndex && v !== state.trackIndex; });
        if (PLAYLIST.length > 1 && state.shufflePool.length === 0) {
            refillShufflePool();
        }
    }

    function getNextShuffleIndex() {
        if (PLAYLIST.length <= 1) return 0;
        normalizeShufflePool();
        if (state.shufflePool.length === 0) {
            refillShufflePool();
        }
        return state.shufflePool.shift();
    }

    function moveToNextShuffleTrack() {
        if (PLAYLIST.length <= 1) return;
        state.trackIndex = getNextShuffleIndex();
        saveState(state);
        loadTrack();
        applyStateToUI();
    }

    function applyStateToUI() {
        var track = PLAYLIST[state.trackIndex];
        var trackName = track && track.name ? track.name : 'Трек не выбран';
        toggleBtn.classList.toggle('is-playing', !!state.isPlaying);
        document.body.classList.toggle('music-active', !!state.isPlaying);
        toggleBtn.setAttribute('aria-label', state.isPlaying ? 'Остановить музыку' : 'Включить музыку');
        toggleBtn.setAttribute('title', state.isPlaying ? 'Выключить музыку' : 'Включить музыку');
        toggleBtn.setAttribute('data-track-title', trackName);
        audio.volume = state.volume;
    }

    function updateMediaSessionMetadata() {
        if (!('mediaSession' in navigator) || typeof window.MediaMetadata !== 'function') return;
        var track = PLAYLIST[state.trackIndex];
        var trackName = track && track.name ? track.name : 'Музыка';
        try {
            navigator.mediaSession.metadata = new window.MediaMetadata({
                title: trackName,
                artist: 'StarBaz',
            });
        } catch (e) {}
    }

    function resizeEqCanvas() {
        if (!eqCanvas || !eqContainer) return;
        var rect = eqContainer.getBoundingClientRect();
        eqCanvas.width = Math.max(1, Math.floor(rect.width * window.devicePixelRatio));
        eqCanvas.height = Math.max(1, Math.floor(rect.height * window.devicePixelRatio));
        if (eqCtx) {
            eqCtx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
        }
    }

    function clearVisualizer() {
        if (!eqCtx || !eqCanvas) return;
        eqCtx.clearRect(0, 0, eqCanvas.width, eqCanvas.height);
    }

    function initAudioAnalysis() {
        if (analyser || !eqCtx) return;
        var AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return;
        try {
            audioCtx = new AC();
            analyser = audioCtx.createAnalyser();
            analyser.fftSize = 2048;
            analyser.smoothingTimeConstant = 0.86;
            sourceNode = audioCtx.createMediaElementSource(audio);
            sourceNode.connect(analyser);
            analyser.connect(audioCtx.destination);
            freqData = new Uint8Array(analyser.frequencyBinCount);
            resizeEqCanvas();
        } catch (e) {
            analyser = null;
        }
    }

    function stopVisualizerLoop() {
        if (rafId) {
            cancelAnimationFrame(rafId);
            rafId = null;
        }
        if (eqSmoothingTimer) {
            clearTimeout(eqSmoothingTimer);
            eqSmoothingTimer = null;
        }
        clearVisualizer();
    }

    function runVisualizerFrame() {
        if (!analyser || !state.isPlaying || audio.paused) {
            stopVisualizerLoop();
            return;
        }
        if (!eqCtx || !eqCanvas) return;
        analyser.getByteFrequencyData(freqData);
        var cw = eqCanvas.width / window.devicePixelRatio;
        var ch = eqCanvas.height / window.devicePixelRatio;
        eqCtx.clearRect(0, 0, cw, ch);
        var visibleBars = Math.max(1, EQ_BARS_COUNT);
        var barWidth = cw / visibleBars;
        var drawWidth = Math.max(0.9, barWidth * 0.5);
        for (var i = 0; i < visibleBars; i++) {
            // Нелинейное распределение полос по частотам (больше акцента на низ/середину),
            // чтобы движение было заметным и "музыкальным".
            var ratioStart = i / visibleBars;
            var ratioEnd = (i + 1) / visibleBars;
            var startIdx = Math.floor(Math.pow(ratioStart, 1.7) * (freqData.length - 1));
            var endIdx = Math.max(startIdx + 1, Math.floor(Math.pow(ratioEnd, 1.7) * (freqData.length - 1)));
            var sum = 0;
            var count = 0;
            for (var b = startIdx; b <= endIdx && b < freqData.length; b++) {
                sum += freqData[b];
                count++;
            }
            var avg = count ? (sum / count) : 0;
            var value = avg / 255; // 0..1
            // Усиливаем чувствительность к краям, чтобы крайние зоны не выглядели "тихими".
            var edgeRatio = i / Math.max(1, (visibleBars - 1)); // 0 слева -> 1 на правом краю
            var edgeBoost = 1 + edgeRatio * 0.32; // до +32% на самом краю
            var boostedValue = Math.min(1, value * edgeBoost);
            var minHeight = 0.08 + edgeRatio * 0.08;
            var h = Math.max(1, ch * (minHeight + boostedValue * (1 - minHeight)));
            var x = i * barWidth + (barWidth - drawWidth) * 0.5;
            var y = 0;
            var grad = eqCtx.createLinearGradient(0, y, 0, y + h);
            grad.addColorStop(0, 'rgba(49, 46, 129, 0.62)');
            grad.addColorStop(0.5, 'rgba(79, 70, 229, 0.72)');
            grad.addColorStop(1, 'rgba(56, 189, 248, 0.85)');
            eqCtx.fillStyle = grad;
            eqCtx.globalAlpha = 0.24 + boostedValue * 0.72;
            eqCtx.fillRect(x, y, drawWidth, h);
        }
        eqCtx.globalAlpha = 1;
        rafId = requestAnimationFrame(runVisualizerFrame);
    }

    function startVisualizerLoop() {
        if (!eqCtx) return;
        if (audioCtx && audioCtx.state === 'suspended') {
            audioCtx.resume().catch(function () {});
        }
        if (!rafId) {
            rafId = requestAnimationFrame(runVisualizerFrame);
        }
    }

    function loadTrack() {
        var track = PLAYLIST[state.trackIndex];
        if (!track || !track.url) return;
        if (audio.src !== track.url) {
            audio.src = track.url;
            audio.load();
        }
        updateMediaSessionMetadata();
    }

    function startPlayback() {
        loadTrack();
        initAudioAnalysis();
        audio.play().then(function () {
            state.isPlaying = true;
            saveState(state);
            applyStateToUI();
            updateMediaSessionMetadata();
            startVisualizerLoop();
        }).catch(function () {
            state.isPlaying = false;
            saveState(state);
            applyStateToUI();
            stopVisualizerLoop();
        });
    }

    function stopPlayback() {
        audio.pause();
        audio.currentTime = 0;
        state.isPlaying = false;
        // После stop подготавливаем следующий трек без повторов.
        moveToNextShuffleTrack();
        saveState(state);
        applyStateToUI();
        stopVisualizerLoop();
    }

    toggleBtn.addEventListener('click', function () {
        if (state.isPlaying) {
            stopPlayback();
        } else {
            startPlayback();
        }
    });
    toggleBtn.addEventListener('wheel', function (e) {
        e.preventDefault();
        var delta = e.deltaY < 0 ? 0.04 : -0.04;
        state.volume = Math.max(0, Math.min(1, state.volume + delta));
        audio.volume = state.volume;
        saveState(state);
        showVolumeHud();
    }, { passive: false });

    audio.addEventListener('ended', function () {
        if (state.isPlaying) {
            moveToNextShuffleTrack();
            startPlayback();
        }
    });
    audio.addEventListener('pause', function () {
        if (!state.isPlaying) {
            stopVisualizerLoop();
        }
    });
    window.addEventListener('resize', resizeEqCanvas);

    // При каждом обновлении страницы подготавливаем следующий трек без повторов.
    if (PLAYLIST.length > 1) {
        state.trackIndex = getNextShuffleIndex();
        saveState(state);
    }

    // Если пользователь включил музыку ранее, продолжаем играть после обновления.
    if (state.isPlaying) {
        startPlayback();
    } else {
        loadTrack();
        applyStateToUI();
        stopVisualizerLoop();
    }
})();
