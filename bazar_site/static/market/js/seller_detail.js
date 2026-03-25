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
});

