/**
 * Admissions form enhancements.
 *
 *  - Conditional field reveal (data-show-when="<inputName>=<value>")
 *  - Live validation on required fields
 *  - Dropzone preview (image + file name + size)
 *  - Simple completion meter for multi-section forms
 *
 * Progressive enhancement: without JS, forms still submit.
 */
(function () {
    'use strict';

    // ======================================================================
    // Conditional reveal
    // ======================================================================
    function initConditionalReveal(root) {
        (root || document).querySelectorAll('[data-show-when]').forEach(wrapper => {
            if (wrapper.dataset.conditionalReady) return;
            wrapper.dataset.conditionalReady = '1';

            const rules = wrapper.dataset.showWhen.split('|').map(s => s.trim());
            // each rule: "inputName=value" (case-insensitive on the value)
            const applies = () => {
                return rules.some(rule => {
                    const [name, value] = rule.split('=');
                    const inputs = document.querySelectorAll(`[name="${name}"]`);
                    for (const input of inputs) {
                        if (input.type === 'radio' || input.type === 'checkbox') {
                            if (input.checked && String(input.value).toLowerCase() === value.toLowerCase()) return true;
                        } else if (String(input.value).toLowerCase() === value.toLowerCase()) {
                            return true;
                        }
                    }
                    return false;
                });
            };

            const update = () => {
                wrapper.hidden = !applies();
                if (!wrapper.hidden) {
                    wrapper.classList.add('field-reveal');
                }
            };

            // Listen on any input/select/radio that shares the trigger name
            rules.forEach(rule => {
                const [name] = rule.split('=');
                document.querySelectorAll(`[name="${name}"]`).forEach(el => {
                    el.addEventListener('change', update);
                    el.addEventListener('input', update);
                });
            });

            update();
        });
    }

    // ======================================================================
    // Live validation on required fields
    // ======================================================================
    function initLiveValidation(root) {
        (root || document).querySelectorAll('form[data-live-form] .field-input[required]').forEach(el => {
            if (el.dataset.liveReady) return;
            el.dataset.liveReady = '1';

            const wrap = el.closest('.field');
            if (!wrap) return;

            const tick = () => {
                const v = (el.value || '').trim();
                if (!v) {
                    wrap.classList.remove('is-valid', 'is-invalid');
                } else if (el.checkValidity()) {
                    wrap.classList.add('is-valid');
                    wrap.classList.remove('is-invalid');
                } else {
                    wrap.classList.add('is-invalid');
                    wrap.classList.remove('is-valid');
                }
            };
            el.addEventListener('input', tick);
            el.addEventListener('blur', tick);
        });
    }

    // ======================================================================
    // Dropzone preview
    // ======================================================================
    function humanSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        const units = ['KB', 'MB', 'GB'];
        let i = -1;
        do { bytes /= 1024; i++; } while (bytes >= 1024 && i < units.length - 1);
        return bytes.toFixed(1) + ' ' + units[i];
    }

    function initUploads(root) {
        (root || document).querySelectorAll('[data-upload]').forEach(zone => {
            if (zone.dataset.uploadReady) return;
            zone.dataset.uploadReady = '1';

            const input = zone.querySelector('input[type="file"]');
            const preview = zone.parentElement.querySelector('.field-upload-preview');
            if (!input || !preview) return;

            const show = (file) => {
                if (!file) {
                    preview.hidden = true;
                    preview.innerHTML = '';
                    return;
                }
                const isImage = file.type.startsWith('image/');
                preview.innerHTML = `
                    ${isImage ? '<img alt="">' : '<i class="bi bi-file-earmark-text" style="font-size:24px;color:var(--md-primary);"></i>'}
                    <div style="flex:1; min-width:0;">
                        <div class="file-name">${file.name}</div>
                        <div class="file-size">${humanSize(file.size)}</div>
                    </div>
                    <button type="button" class="remove" aria-label="Remove file">
                        <i class="bi bi-x-circle"></i>
                    </button>`;
                if (isImage) {
                    const img = preview.querySelector('img');
                    const url = URL.createObjectURL(file);
                    img.src = url;
                    img.onload = () => URL.revokeObjectURL(url);
                }
                preview.hidden = false;
                preview.querySelector('.remove').addEventListener('click', (e) => {
                    e.preventDefault();
                    input.value = '';
                    show(null);
                });
            };

            input.addEventListener('change', () => show(input.files[0]));

            ['dragenter', 'dragover'].forEach(evt => {
                zone.addEventListener(evt, (e) => {
                    e.preventDefault();
                    zone.classList.add('drag');
                });
            });
            ['dragleave', 'drop'].forEach(evt => {
                zone.addEventListener(evt, (e) => {
                    e.preventDefault();
                    zone.classList.remove('drag');
                });
            });
            zone.addEventListener('drop', (e) => {
                const files = e.dataTransfer.files;
                if (files.length) {
                    input.files = files;
                    show(files[0]);
                }
            });
        });
    }

    // ======================================================================
    // Star ratings (interview scores)
    // ======================================================================
    function initStars(root) {
        (root || document).querySelectorAll('[data-stars]').forEach(group => {
            if (group.dataset.starsReady) return;
            group.dataset.starsReady = '1';

            const targetId = group.dataset.stars;
            const target = document.getElementById(targetId);
            if (!target) return;

            const max = parseInt(group.dataset.max || '10', 10);
            const valueEl = group.querySelector('.stars-value');

            // Render stars (each star = max/5 of the scale)
            const starsHtml = Array.from({ length: 5 }, (_, i) => {
                const points = Math.round(((i + 1) / 5) * max);
                return `<button type="button" data-points="${points}" aria-label="${points} out of ${max}">
                    <i class="bi bi-star-fill"></i>
                </button>`;
            }).join('');
            group.innerHTML = `<div class="stars">${starsHtml}</div>
                <span class="stars-value"></span>`;

            const paint = (value) => {
                const buttons = group.querySelectorAll('.stars button');
                buttons.forEach(b => {
                    b.classList.toggle('on', parseInt(b.dataset.points, 10) <= value);
                });
                if (valueEl) valueEl.textContent = value ? `${value}/${max}` : '—';
            };

            group.querySelectorAll('.stars button').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const points = parseInt(btn.dataset.points, 10);
                    target.value = points;
                    paint(points);
                });
            });

            // Preserve existing value
            paint(parseFloat(target.value) || 0);
        });
    }

    // ======================================================================
    // Boot
    // ======================================================================
    function boot() {
        initConditionalReveal();
        initLiveValidation();
        initUploads();
        initStars();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }

    window.AdmissionsForm = {
        refresh: (root) => {
            initConditionalReveal(root);
            initLiveValidation(root);
            initUploads(root);
            initStars(root);
        },
    };
})();