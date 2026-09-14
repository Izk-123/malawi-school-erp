/**
 * Profile interactions.
 *
 *  - Collapsible sections (persisted per user in localStorage)
 *  - Theme segmented control (light / dark / auto)
 *  - SMS + email switches (persisted locally; hook a backend endpoint to sync)
 *  - Photo sheet (bottom sheet → dialog)
 *  - Photo file input (camera + gallery)
 *  - Log out confirmation via a simple form is not needed — plain form
 *  - Delete account confirmation
 *
 * No dependencies. If this file fails to load, sections default to open
 * and every action falls back to a plain form/link.
 */
(function () {
    'use strict';

    const STORAGE_SECTIONS = 'mse.profile.sections';
    const STORAGE_THEME    = 'mse.theme';
    const STORAGE_PREFS    = 'mse.profile.prefs';

    // ======================================================================
    // Collapsible sections
    // ======================================================================
    const Sections = {
        load() {
            try { return JSON.parse(localStorage.getItem(STORAGE_SECTIONS) || '{}'); }
            catch (e) { return {}; }
        },
        save(state) {
            try { localStorage.setItem(STORAGE_SECTIONS, JSON.stringify(state)); }
            catch (e) { /* private mode — ignore */ }
        },
        init() {
            const saved = this.load();
            const isDesktop = window.matchMedia('(min-width: 840px)').matches;

            document.querySelectorAll('.profile-section[data-section]').forEach(section => {
                const key = section.dataset.section;
                const head = section.querySelector('.profile-section-head');
                const body = section.querySelector('.profile-section-body');
                if (!head || !body) return;

                // Priority: saved state → desktop default → mobile default
                let open;
                if (key in saved) {
                    open = !!saved[key];
                } else if (isDesktop) {
                    open = true;
                } else {
                    // Mobile default: only the first section is open
                    open = section.dataset.defaultOpen === 'true';
                }

                const apply = () => {
                    head.setAttribute('aria-expanded', open ? 'true' : 'false');
                    head.setAttribute('aria-controls', body.id);
                    body.hidden = !open;
                };
                apply();

                head.addEventListener('click', (e) => {
                    if (head.disabled) return;
                    e.preventDefault();
                    open = !open;
                    saved[key] = open;
                    this.save(saved);
                    apply();
                });
            });
        },
    };

    // ======================================================================
    // Theme segmented control
    // ======================================================================
    const ThemeSwitcher = {
        apply(mode) {
            let resolved = mode;
            if (mode === 'auto') {
                resolved = window.matchMedia &&
                    window.matchMedia('(prefers-color-scheme: dark)').matches
                    ? 'dark' : 'light';
            }
            document.documentElement.setAttribute('data-theme', resolved);
            document.documentElement.setAttribute('data-bs-theme', resolved);
            try { localStorage.setItem(STORAGE_THEME, mode); } catch (e) {}

            document.querySelectorAll('[data-theme-option]').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.themeOption === mode);
            });
        },
        current() {
            try { return localStorage.getItem(STORAGE_THEME) || 'auto'; }
            catch (e) { return 'auto'; }
        },
        init() {
            const current = this.current();
            document.querySelectorAll('[data-theme-option]').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.themeOption === current);
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.apply(btn.dataset.themeOption);
                });
            });
        },
    };

    // ======================================================================
    // Preference toggles (SMS / email)
    // ======================================================================
    const Prefs = {
        load() {
            try { return JSON.parse(localStorage.getItem(STORAGE_PREFS) || '{}'); }
            catch (e) { return {}; }
        },
        save(state) {
            try { localStorage.setItem(STORAGE_PREFS, JSON.stringify(state)); }
            catch (e) {}
        },
        init() {
            const saved = this.load();
            document.querySelectorAll('[data-pref-key]').forEach(input => {
                const key = input.dataset.prefKey;
                if (key in saved) input.checked = !!saved[key];
                input.addEventListener('change', () => {
                    saved[key] = input.checked;
                    this.save(saved);
                    // Optional: sync to server
                    // fetch('/accounts/preferences/', {method: 'POST', ...})
                });
            });
        },
    };

    // ======================================================================
    // Photo sheet
    // ======================================================================
    const PhotoSheet = {
        sheet: null,
        fileInput: null,
        form: null,
        init() {
            this.sheet = document.getElementById('photoSheet');
            this.fileInput = document.getElementById('photoFileInput');
            this.form = document.getElementById('photoUploadForm');
            if (!this.sheet) return;

            // Open triggers
            document.querySelectorAll('[data-open-photo-sheet]').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.open();
                });
            });

            // Close triggers
            this.sheet.querySelectorAll('[data-close-photo-sheet]').forEach(el => {
                el.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.close();
                });
            });

            // Escape closes
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.sheet.classList.contains('open')) {
                    this.close();
                }
            });

            // Camera / gallery triggers → click the hidden file input
            this.sheet.querySelectorAll('[data-photo-source]').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    if (!this.fileInput) return;
                    this.fileInput.setAttribute('capture', btn.dataset.photoSource === 'camera' ? 'environment' : '');
                    this.fileInput.click();
                });
            });

            // Change on hidden input → submit the upload form
            this.fileInput?.addEventListener('change', () => {
                if (this.fileInput.files.length && this.form) {
                    this.form.submit();
                }
            });
        },
        open() {
            this.sheet.classList.add('open');
            document.body.style.overflow = 'hidden';
        },
        close() {
            this.sheet.classList.remove('open');
            document.body.style.overflow = '';
        },
    };

    // ======================================================================
    // Delete account confirm
    // ======================================================================
    function initDeleteConfirm() {
        const btn = document.querySelector('[data-delete-account]');
        if (!btn) return;
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const ok = window.confirm(
                'Delete your account? This cannot be undone. ' +
                'All your data will be permanently removed.'
            );
            if (ok) {
                const form = document.getElementById('deleteAccountForm');
                if (form) form.submit();
            }
        });
    }

    // ======================================================================
    // Boot
    // ======================================================================
    function boot() {
        ThemeSwitcher.init();
        Sections.init();
        Prefs.init();
        PhotoSheet.init();
        initDeleteConfirm();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }

    window.ProfileUI = { Sections, ThemeSwitcher, PhotoSheet, Prefs };
})();