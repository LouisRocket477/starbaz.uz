document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('images-input');
    const preview = document.getElementById('images-preview');
    const imagesLabel = document.getElementById('images-input-label');
    const form = document.querySelector('form.card');
    const deleteButtons = document.querySelectorAll('.delete-image-btn');
    const mainRadios = document.querySelectorAll('input[type="radio"][name="main_image"]');

    if (input && preview) {
        input.addEventListener('change', function () {
            preview.innerHTML = '';
            const files = Array.from(input.files || []);
            if (imagesLabel) {
                if (files.length) {
                    imagesLabel.textContent = 'Выбрано файлов: ' + files.length;
                } else {
                    imagesLabel.textContent = 'Файлы не выбраны';
                }
            }
            files.forEach(file => {
                if (!file.type.startsWith('image/')) return;
                const reader = new FileReader();
                reader.onload = e => {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.className = 'img-thumbnail';
                    img.style.width = '100px';
                    img.style.height = '100px';
                    img.style.objectFit = 'cover';
                    img.title = file.name;
                    preview.appendChild(img);
                };
                reader.readAsDataURL(file);
            });
        });
    }

    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            if (!form) return;
            const imageId = this.getAttribute('data-image-id');
            if (!imageId) return;
            const hidden = document.createElement('input');
            hidden.type = 'hidden';
            hidden.name = 'delete_images';
            hidden.value = imageId;
            form.appendChild(hidden);
            form.submit();
        });
    });

    mainRadios.forEach(radio => {
        radio.addEventListener('change', function () {
            if (!form) return;
            form.submit();
        });
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const titleInput = document.getElementById('listing-title');
    const categorySelect = document.getElementById('listing-category');
    const priceInput = document.getElementById('listing-price');
    const originalPriceInput = document.getElementById('listing-original-price');
    const imagesInput = document.getElementById('images-input');

    const previewTitle = document.getElementById('listing-preview-title');
    const previewCategory = document.getElementById('listing-preview-category');
    const previewBadge = document.getElementById('listing-preview-deal-badge');
    const previewBarterBadge = document.getElementById('listing-preview-barter-badge');
    const previewImageWrapper = document.querySelector('.listing-preview-image');
    const previewImageDefault = document.getElementById('listing-preview-image-default');
    const descriptionInput = document.querySelector('textarea[name="description"]');
    const previewDescription = document.getElementById('listing-preview-description');
    const barterCheckbox = document.getElementById('barter_allowed');
    const dealTypeHelp = document.getElementById('deal-type-help');
    const priceOrigWrapper = document.getElementById('listing-preview-price-original-wrapper');
    const priceOrigValue = document.getElementById('listing-preview-price-original');
    const priceCurrentWrapper = document.getElementById('listing-preview-price-current-wrapper');
    const priceCurrentValue = document.getElementById('listing-preview-price-current');
    const discountBadge = document.getElementById('listing-preview-discount-badge');
    const stepsRoot = document.getElementById('listing-steps');

    function updateTitle() {
        if (!previewTitle || !titleInput) return;
        const v = titleInput.value.trim();
        previewTitle.textContent = v || 'Название товара';
    }

    function updateCategory() {
        if (!previewCategory || !categorySelect) return;
        const selected = categorySelect.options[categorySelect.selectedIndex];
        const text = selected && selected.value ? selected.textContent : 'Категория не выбрана';
        previewCategory.textContent = text;
    }

    function formatNumber(val) {
        if (!val || isNaN(val)) return '0';
        try {
            return Number(val).toLocaleString('ru-RU');
        } catch (e) {
            return String(val);
        }
    }

    function updatePrice() {
        const origRaw = originalPriceInput && originalPriceInput.value
            ? originalPriceInput.value.replace(/\s+/g, '').replace(/,/g, '')
            : '';
        const priceRaw = priceInput && priceInput.value
            ? priceInput.value.replace(/\s+/g, '').replace(/,/g, '')
            : '';

        const origVal = origRaw ? parseFloat(origRaw) : null;
        const priceVal = priceRaw ? parseFloat(priceRaw) : null;

        let baseOrig = null;
        let baseCurrent = null;

        if (origVal !== null && !isNaN(origVal)) {
            baseOrig = origVal;
        }
        if (priceVal !== null && !isNaN(priceVal)) {
            baseCurrent = priceVal;
        }
        if (baseCurrent === null && baseOrig !== null) {
            baseCurrent = baseOrig;
        }
        if (baseCurrent === null) {
            baseCurrent = 0;
        }

        if (!priceCurrentValue || !priceCurrentWrapper || !priceOrigWrapper || !priceOrigValue || !discountBadge) {
            return;
        }

        priceCurrentValue.textContent = formatNumber(baseCurrent);

        if (baseOrig !== null && baseCurrent < baseOrig) {
            priceOrigValue.textContent = formatNumber(baseOrig);
            priceOrigWrapper.classList.remove('d-none');
            const percent = Math.floor((1 - baseCurrent / baseOrig) * 100);
            if (percent > 0) {
                discountBadge.textContent = '-' + percent + '%';
                discountBadge.classList.remove('d-none');
            } else {
                discountBadge.classList.add('d-none');
            }
        } else {
            priceOrigWrapper.classList.add('d-none');
            discountBadge.classList.add('d-none');
        }
    }

    function updateDealType() {
        if (!previewBadge && !dealTypeHelp) return;
        const checked = document.querySelector('input[name="deal_type"]:checked');
        let text = '';
        let cls = 'badge';
        let helpText = '';
        if (checked) {
            if (checked.value === 'buy') {
                text = 'Покупка';
                cls += ' bg-success';
                helpText = '«Покупаю» — вы ищете товар, продавцы будут предлагать свои варианты.';
            } else if (checked.value === 'trade') {
                text = 'Обмен';
                cls += ' bg-info text-dark';
                helpText = '«Обмен» — вы готовы обменять свой товар на другие позиции.';
            } else {
                text = 'Продажа';
                cls += ' bg-warning text-dark';
                helpText = '«Продаю» — обычное объявление о продаже товара.';
            }
        }
        if (text && previewBadge) {
            previewBadge.textContent = text;
            previewBadge.className = cls;
            previewBadge.classList.remove('d-none');
        } else if (previewBadge) {
            previewBadge.classList.add('d-none');
        }
        if (dealTypeHelp) {
            dealTypeHelp.textContent = helpText;
        }
    }

    function updateBarter() {
        if (!previewBarterBadge || !barterCheckbox) return;
        if (barterCheckbox.checked) {
            previewBarterBadge.classList.remove('d-none');
        } else {
            previewBarterBadge.classList.add('d-none');
        }
    }

    function updateDescription() {
        if (!previewDescription) return;
        if (!descriptionInput) {
            previewDescription.textContent = 'Краткое описание товара появится здесь.';
            return;
        }
        const text = (descriptionInput.value || '').trim();
        if (!text) {
            previewDescription.textContent = 'Краткое описание товара появится здесь.';
        } else {
            const short = text.length > 120 ? text.slice(0, 117) + '…' : text;
            previewDescription.textContent = short;
        }
    }

    function updateImagePreviewFromInput(inputEl) {
        if (!previewImageWrapper || !inputEl || !previewImageDefault) return;
        const files = Array.from(inputEl.files || []);
        if (!files.length) {
            return;
        }
        const file = files[0];
        if (!file.type.startsWith('image/')) return;
        const reader = new FileReader();
        reader.onload = function (e) {
            previewImageDefault.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    function setActiveStep(stepNumber) {
        if (!stepsRoot) return;
        const items = stepsRoot.querySelectorAll('.listing-steps-item');
        items.forEach(function (item) {
            const s = item.getAttribute('data-step');
            if (String(stepNumber) === s) {
                item.classList.add('listing-steps-item-active');
            } else {
                item.classList.remove('listing-steps-item-active');
            }
        });
    }

    function bindStepFocus(sectionId, stepNumber) {
        const section = document.getElementById(sectionId);
        if (!section) return;
        section.addEventListener('focusin', function () {
            setActiveStep(stepNumber);
        });
    }

    if (titleInput) {
        titleInput.addEventListener('input', updateTitle);
        updateTitle();
    }
    if (categorySelect) {
        categorySelect.addEventListener('change', updateCategory);
        updateCategory();
    }
    if (priceInput) {
        priceInput.addEventListener('input', updatePrice);
    }
    if (originalPriceInput) {
        originalPriceInput.addEventListener('input', updatePrice);
    }
    updatePrice();

    const dealTypeInputs = document.querySelectorAll('input[name="deal_type"]');
    dealTypeInputs.forEach(function (inp) {
        inp.addEventListener('change', updateDealType);
    });
    updateDealType();

    // Активный шаг по фокусу в блоках формы
    bindStepFocus('listing-step-1', 1);
    bindStepFocus('listing-step-2', 2);
    bindStepFocus('listing-step-3', 3);
    bindStepFocus('listing-step-4', 4);

    // Переход по клику на шаги
    if (stepsRoot) {
        stepsRoot.addEventListener('click', function (e) {
            const target = e.target.closest('.listing-steps-item');
            if (!target) return;
            const step = target.getAttribute('data-step');
            if (!step) return;
            const section = document.getElementById('listing-step-' + step);
            if (section) {
                section.scrollIntoView({behavior: 'smooth', block: 'start'});
                setActiveStep(step);
            }
        });
    }

    /* Переключение «Количество» / «Сколько хочу купить» по типу объявления */
    function updateQuantitySection() {
        const checked = document.querySelector('input[name="deal_type"]:checked');
        const value = checked ? checked.value : 'sell';
        const inStockRow = document.getElementById('in_stock_row');
        const inStockCheckbox = document.getElementById('in_stock');
        const qtyLabel = document.getElementById('quantity-label');
        const qtyInput = document.getElementById('quantity');
        const qtyHelp = document.getElementById('quantity-helptext');
        if (!qtyLabel || !qtyInput || !qtyHelp) return;
        if (value === 'buy') {
            // Для объявлений «Покупаю» показываем тот же чекбокс,
            // но он всегда включён и недоступен для изменения —
            // активность такого объявления управляется через кнопку
            // «Снять с публикации» / «Вернуть в публикацию».
            if (inStockRow) inStockRow.classList.remove('d-none');
            if (inStockCheckbox) {
                inStockCheckbox.checked = true;
                inStockCheckbox.disabled = true;
            }
            qtyLabel.textContent = 'Сколько хочу купить';
            qtyInput.min = 1;
            qtyInput.placeholder = '1';
            qtyHelp.textContent = 'Укажите нужное количество. Отобразится в карточке объявления.';
        } else {
            if (inStockRow) inStockRow.classList.remove('d-none');
            if (inStockCheckbox) {
                inStockCheckbox.disabled = false;
            }
            qtyLabel.textContent = 'Количество';
            qtyInput.min = 0;
            qtyInput.placeholder = '—';
            qtyHelp.textContent = 'Укажите количество, если товар в наличии. Можно оставить пустым.';
        }
    }
    dealTypeInputs.forEach(function (inp) {
        inp.addEventListener('change', updateQuantitySection);
    });
    updateQuantitySection();

    if (imagesInput) {
        imagesInput.addEventListener('change', function () {
            updateImagePreviewFromInput(imagesInput);
        });
    }

    if (descriptionInput) {
        descriptionInput.addEventListener('input', updateDescription);
        updateDescription();
    } else {
        updateDescription();
    }

    if (barterCheckbox) {
        barterCheckbox.addEventListener('change', updateBarter);
        updateBarter();
    }
});

