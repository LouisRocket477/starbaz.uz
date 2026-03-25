document.addEventListener('DOMContentLoaded', function () {
    const avatarEls = document.querySelectorAll('.js-avatar-zoom');
    if (!avatarEls.length || typeof bootstrap === 'undefined') return;

    let modalEl = document.getElementById('avatarZoomModal');
    if (!modalEl) {
        modalEl = document.createElement('div');
        modalEl.id = 'avatarZoomModal';
        modalEl.className = 'modal fade';
        modalEl.tabIndex = -1;
        modalEl.innerHTML = ''
            + '<div class="modal-dialog modal-dialog-centered">'
            + '  <div class="modal-content bg-dark border-0">'
            + '    <div class="modal-body p-0">'
            + '      <img id="avatarZoomImg" src="" alt="" '
            + '           style="width: 100%; height: 100%; object-fit: contain; max-height: 80vh;">'
            + '    </div>'
            + '  </div>'
            + '</div>';
        document.body.appendChild(modalEl);
    }
    const modalImg = modalEl.querySelector('#avatarZoomImg');
    const modal = new bootstrap.Modal(modalEl);

    avatarEls.forEach(function (el) {
        el.addEventListener('click', function () {
            const url = el.getAttribute('data-full-url') || el.src;
            if (!url) return;
            modalImg.src = url;
            modal.show();
        });
    });

    const avatarInput = document.getElementById('avatar-input');
    const avatarLabel = document.getElementById('avatar-input-label');
    const previewImg = document.getElementById('profile-avatar-preview-img');
    const previewFallback = document.getElementById('profile-avatar-preview-fallback');

    function setPreviewToOriginal() {
        if (!previewImg) return;
        const originalSrc = previewImg.getAttribute('data-original-src') || '';
        if (originalSrc) {
            previewImg.src = originalSrc;
            previewImg.classList.remove('d-none');
            if (previewFallback) previewFallback.classList.add('d-none');
        } else {
            previewImg.src = '';
            previewImg.classList.add('d-none');
            if (previewFallback) previewFallback.classList.remove('d-none');
        }
    }

    if (avatarInput && avatarLabel) {
        avatarInput.addEventListener('change', function () {
            const files = Array.from(avatarInput.files || []);
            if (files.length) {
                const file = files[0];
                avatarLabel.textContent = 'Выбран файл: ' + (file.name || 'картинка');

                if (previewImg && file && file.type && file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function (ev) {
                        const dataUrl = ev && ev.target ? ev.target.result : null;
                        if (typeof dataUrl === 'string') {
                            previewImg.src = dataUrl;
                            previewImg.classList.remove('d-none');
                            if (previewFallback) previewFallback.classList.add('d-none');
                        }
                    };
                    reader.readAsDataURL(file);
                }
            } else {
                avatarLabel.textContent = 'Файл не выбран';
                setPreviewToOriginal();
            }
        });
    }
});

