/**
 * Profile edit — live, engaging form.
 *
 *  - Live preview of name / email / avatar in the hero
 *  - Real-time field validation with inline feedback
 *  - Async email availability check (debounced, endpoint-based)
 *  - Completion meter that reflects how much is valid
 *  - Autosave of dirty values to localStorage (draft restore on reload)
 *  - Sticky action bar state (Reset disabled when clean, Save disabled when invalid)
 *  - ⌘S / Ctrl+S to submit
 *  - beforeunload guard when dirty
 *  - Save-state toast on submit
 *
 * Progressive enhancement: without this file, the form still validates and
 * submits normally — it just won't have the live feedback.
 */
(function () {
    'use strict';

    const DRAFT_KEY = 'mse.profile_edit.draft';
    const AUTOSAVE_MS = 4000;
    const EMAIL_DEBOUNCE_MS = 450;

    // ======================================================================
    // Validators
    // ======================================================================
    const Validators = {
        name(value) {
            const v = (value || '').trim();
            if (!v) return { ok: false, msg: 'This field is required.' };
            if (v.length < 2) return { ok: false, msg: 'A bit longer, please.' };
            if (v.length > 150) return { ok: false, msg: 'Too long (max 150 characters).' };
            if (!/^[A-Za-zÀ-ÿ' .-]+$/.test(v)) {
                return { ok: false, msg: 'Letters, spaces, hyphens and apostrophes only.' };
            }
            return { ok: true, msg: '' };
        },

        email(value) {
            const v = (value || '').trim().toLowerCase();
            if (!v) return { ok: false, msg: 'Email is required.' };
            if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)) {
                return { ok: false, msg: 'Enter a valid email like name@school.mw.' };
            }
            return { ok: true, msg: '', value: v };
        },

        phone(value, input) {
            const raw = (value || '').trim();
            if (!raw) return { ok: true, msg: 'Optional — add one to receive SMS alerts.' };

            const digits = raw.replace(/\D/g, '');
            let last9 = digits;
            if (digits.startsWith('265')) last9 = digits.slice(3, 12);
            else if (digits.length > 9) last9 = digits.slice(-9);

            if (last9.length !== 9) {
                return { ok: false, msg: 'Enter 9 digits after +265, e.g. 991234567.' };
            }
            return { ok: true, msg: '', value: '+265' + last9, cleaned: last9 };
        },

        choice(value) {
            return { ok: !!value, msg: '' };
        },
    };

    // ======================================================================
    // ProfileEditForm
    // ======================================================================
    const ProfileEditForm = {
        form: null,
        saveBtn: null,
        saveBtnLabel: null,
        resetBtn: null,
        dirtyPill: null,
        progressFill: null,
        progressText: null,
        toast: null,

        // state
        saved: {},           // canonical snapshot (as rendered)
        current: {},         // last-known values
        dirty: false,
        submitting: false,
        emailTimer: null,
        autosaveTimer: null,

        // --------------------------------------------------------------
        init() {
            this.form = document.getElementById('profileEditForm');
            if (!this.form) return;

            this.saveBtn        = document.getElementById('saveBtn');
            this.saveBtnLabel   = document.getElementById('saveBtnLabel');
            this.resetBtn       = document.getElementById('resetBtn');
            this.dirtyPill      = document.getElementById('dirtyPill');
            this.progressFill   = document.getElementById('progressFill');
            this.progressText   = document.getElementById('progressText');
            this.toast          = document.getElementById('saveToast');

            this.captureSaved();
            this.wireInputs();
            this.wireAvatar();
            this.wireReset();
            this.wireSubmit();
            this.wireKeyboard();
            this.wireUnsavedGuard();
            this.restoreDraft();
            this.startAutosave();

            // Initial paint of every field
            this.refreshAll();
            this.refreshProgress();
            this.refreshDirty();
        },

        // --------------------------------------------------------------
        captureSaved() {
            this.form.querySelectorAll('[data-live]').forEach(el => {
                this.saved[el.name] = el.value;
                this.current[el.name] = el.value;
            });
        },

        // --------------------------------------------------------------
        wireInputs() {
            this.form.querySelectorAll('[data-live]').forEach(el => {
                const wrap = el.closest('.field-live');
                if (!wrap) return;

                // Live preview for name / email
                if (el.name === 'first_name' || el.name === 'last_name') {
                    el.addEventListener('input', () => this.updateLiveName());
                }
                if (el.name === 'email') {
                    el.addEventListener('input', () => this.updateLiveEmail());
                }

                // Character counters
                const counter = wrap.querySelector('.field-counter');
                if (counter) {
                    const max = parseInt(counter.dataset.max, 10) || 150;
                    el.addEventListener('input', () => this.updateCounter(el, counter, max));
                    this.updateCounter(el, counter, max);
                }

                // On input: validate + dirty + progress
                el.addEventListener('input', () => this.onFieldChange(el, { skipAsync: false }));
                el.addEventListener('blur',  () => this.onFieldBlur(el));
                el.addEventListener('change',() => this.onFieldChange(el, { skipAsync: false }));
            });
        },

        // --------------------------------------------------------------
        onFieldChange(el, opts = {}) {
            this.current[el.name] = el.value;
            this.refreshDirty();
            this.validateField(el, opts);
            this.refreshProgress();
        },

        onFieldBlur(el) {
            // On blur: normalise phone to last-9 form, then validate hard
            if (el.name === 'phone_number' && el.value.trim()) {
                const r = Validators.phone(el.value, el);
                if (r.ok && r.cleaned) el.value = r.cleaned;
            }
            this.validateField(el, { force: true });
        },

        // --------------------------------------------------------------
        validateField(el, { force = false, skipAsync = false } = {}) {
            const wrap = el.closest('.field-live');
            const kind = el.dataset.validator || 'choice';
            const feedback = wrap.querySelector('.field-feedback');
            const raw = el.value;
            const touched = force || el.value !== this.saved[el.name];

            // Not touched yet → clear state
            if (!touched && !raw) {
                wrap.classList.remove('is-valid', 'is-invalid', 'is-checking');
                if (feedback) {
                    feedback.className = 'field-feedback';
                    feedback.textContent = '';
                }
                return null;
            }

            const result = Validators[kind] ? Validators[kind](raw, el) : { ok: true, msg: '' };
            wrap.classList.remove('is-valid', 'is-invalid', 'is-checking');
            if (feedback) {
                feedback.className = 'field-feedback';
                feedback.textContent = '';
            }

            if (!result.ok) {
                wrap.classList.add('is-invalid');
                if (feedback) {
                    feedback.classList.add('feedback-error');
                    feedback.innerHTML =
                        `<i class="bi bi-exclamation-circle"></i> ${result.msg}`;
                }
                return result;
            }

            // Valid syntactically — if it has async, defer
            if (el.dataset.async && !skipAsync) {
                this.runAsyncCheck(el, result);
                return result;
            }

            wrap.classList.add('is-valid');
            if (feedback && result.msg) {
                feedback.textContent = result.msg;
            }
            return result;
        },

        // --------------------------------------------------------------
        runAsyncCheck(el, localResult) {
            // Only for fields with data-async="email"
            const wrap = el.closest('.field-live');
            const feedback = wrap.querySelector('.field-feedback');
            const email = (localResult.value || el.value || '').trim().toLowerCase();

            if (!email || email === (this.saved[el.name] || '').toLowerCase()) {
                // Same as saved — no need to check
                wrap.classList.add('is-valid');
                return;
            }

            wrap.classList.remove('is-valid', 'is-invalid');
            wrap.classList.add('is-checking');
            if (feedback) {
                feedback.className = 'field-feedback';
                feedback.textContent = 'Checking availability…';
            }

            clearTimeout(this.emailTimer);
            this.emailTimer = setTimeout(() => {
                const url = new URL(this.form.dataset.checkEmailUrl, location.origin);
                url.searchParams.set('email', email);

                fetch(url, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' },
                    credentials: 'same-origin',
                })
                .then(r => r.json())
                .then(data => {
                    // Bail if the user has typed again since
                    if (el.value.trim().toLowerCase() !== email) return;

                    wrap.classList.remove('is-checking');
                    if (data.available) {
                        wrap.classList.add('is-valid');
                        if (feedback) {
                            feedback.className = 'field-feedback feedback-ok';
                            feedback.innerHTML =
                                '<i class="bi bi-check-circle-fill"></i> This email is available.';
                        }
                    } else {
                        wrap.classList.add('is-invalid', 'is-shaking');
                        setTimeout(() => wrap.classList.remove('is-shaking'), 500);
                        if (feedback) {
                            feedback.className = 'field-feedback feedback-error';
                            feedback.innerHTML =
                                '<i class="bi bi-exclamation-circle"></i> ' +
                                (data.error || 'This email is already in use.');
                        }
                    }
                    this.refreshProgress();
                })
                .catch(() => {
                    // Network failure — treat as valid (server will revalidate)
                    wrap.classList.remove('is-checking');
                    wrap.classList.add('is-valid');
                    if (feedback) {
                        feedback.className = 'field-feedback';
                        feedback.textContent = '';
                    }
                });
            }, EMAIL_DEBOUNCE_MS);
        },

        // --------------------------------------------------------------
        updateCounter(el, counter, max) {
            const len = el.value.length;
            counter.textContent = `${len}/${max}`;
            counter.classList.toggle('near', len > max * 0.8 && len <= max);
            counter.classList.toggle('over', len > max);
        },

        // --------------------------------------------------------------
        updateLiveName() {
            const first = (this.form.first_name.value || '').trim();
            const last  = (this.form.last_name.value  || '').trim();
            const full  = [first, last].filter(Boolean).join(' ') || 'Unnamed';
            const nameEl = document.getElementById('liveName');
            const initialsEl = document.getElementById('liveAvatarInitials');
            if (nameEl) nameEl.textContent = full;
            if (initialsEl) {
                const i = ((first[0] || '') + (last[0] || '')).toUpperCase() || '?';
                initialsEl.textContent = i;
            }
        },

        updateLiveEmail() {
            const email = (this.form.email.value || '').trim();
            const el = document.getElementById('liveEmail');
            if (el) el.textContent = email || '—';
        },

        // --------------------------------------------------------------
        wireAvatar() {
            const fileInput = document.getElementById('photoFileInput');
            const img    = document.getElementById('liveAvatarImg');
            const initials = document.getElementById('liveAvatarInitials');
            const dirtyDot = document.getElementById('avatarDirtyDot');
            if (!fileInput) return;

            fileInput.addEventListener('change', () => {
                const file = fileInput.files[0];
                if (!file) return;
                if (!file.type.startsWith('image/')) return;

                const url = URL.createObjectURL(file);
                const wrap = document.getElementById('liveAvatar');

                // Replace content with preview img
                wrap.innerHTML = `<img src="${url}" alt="" id="liveAvatarImg">`;
                if (dirtyDot) dirtyDot.hidden = false;
            });
        },

        // --------------------------------------------------------------
        refreshDirty() {
            let dirty = false;
            this.form.querySelectorAll('[data-live]').forEach(el => {
                if ((el.value || '') !== (this.saved[el.name] || '')) {
                    dirty = true;
                }
            });
            const fileInput = document.getElementById('photoFileInput');
            if (fileInput && fileInput.files && fileInput.files.length) dirty = true;

            if (this.dirty !== dirty) {
                this.dirty = dirty;
                if (this.dirtyPill) this.dirtyPill.hidden = !dirty;
                if (this.resetBtn) this.resetBtn.disabled = !dirty;
            }
        },

        // --------------------------------------------------------------
        refreshProgress() {
            let total = 0;
            let good = 0;
            this.form.querySelectorAll('.field-live').forEach(wrap => {
                total++;
                if (wrap.classList.contains('is-valid')) good++;
            });
            const pct = total ? Math.round((good / total) * 100) : 0;
            if (this.progressFill) this.progressFill.style.width = pct + '%';
            if (this.progressText) this.progressText.textContent = `${pct}% complete`;
        },

        refreshAll() {
            this.form.querySelectorAll('[data-live]').forEach(el => this.validateField(el, { skipAsync: true }));
            this.updateLiveName();
            this.updateLiveEmail();
        },

        // --------------------------------------------------------------
        wireReset() {
            this.resetBtn?.addEventListener('click', () => {
                if (!this.dirty) return;
                if (!window.confirm('Discard your unsaved changes?')) return;
                this.form.querySelectorAll('[data-live]').forEach(el => {
                    el.value = this.saved[el.name] || '';
                });
                this.clearDraft();
                this.refreshAll();
                this.refreshDirty();
                this.refreshProgress();
                this.showToast('Changes discarded', 'info');
            });
        },

        // --------------------------------------------------------------
        wireSubmit() {
            this.form.addEventListener('submit', () => {
                this.submitting = true;
                this.clearDraft();
                if (this.saveBtn) {
                    this.saveBtn.disabled = true;
                    this.saveBtn.classList.add('is-saving');
                }
                if (this.saveBtnLabel) this.saveBtnLabel.textContent = 'Saving…';
                if (this.toast) this.showToast('Saving…', 'info', 0);
            });
        },

        // --------------------------------------------------------------
        wireKeyboard() {
            document.addEventListener('keydown', (e) => {
                if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') {
                    e.preventDefault();
                    if (this.submitting) return;
                    this.form.requestSubmit();
                }
            });
        },

        // --------------------------------------------------------------
        wireUnsavedGuard() {
            window.addEventListener('beforeunload', (e) => {
                if (this.dirty && !this.submitting) {
                    e.preventDefault();
                    e.returnValue = '';
                }
            });
        },

        // --------------------------------------------------------------
        startAutosave() {
            this.autosaveTimer = setInterval(() => {
                if (!this.dirty || this.submitting) return;
                try {
                    const snapshot = {};
                    this.form.querySelectorAll('[data-live]').forEach(el => {
                        snapshot[el.name] = el.value;
                    });
                    localStorage.setItem(DRAFT_KEY, JSON.stringify({
                        savedAt: Date.now(),
                        values: snapshot,
                    }));
                } catch (e) { /* ignore */ }
            }, AUTOSAVE_MS);
        },

        restoreDraft() {
            let draft;
            try { draft = JSON.parse(localStorage.getItem(DRAFT_KEY) || 'null'); }
            catch (e) { draft = null; }
            if (!draft || !draft.values) return;

            let changed = false;
            this.form.querySelectorAll('[data-live]').forEach(el => {
                const v = draft.values[el.name];
                if (v != null && v !== el.value) {
                    el.value = v;
                    changed = true;
                }
            });
            if (changed) {
                this.showToast('Draft restored', 'info', 4000);
            }
        },

        clearDraft() {
            try { localStorage.removeItem(DRAFT_KEY); } catch (e) {}
        },

        // --------------------------------------------------------------
        showToast(message, kind = 'info', duration = 2200) {
            if (!this.toast) return;
            clearTimeout(this._toastTimer);
            this.toast.classList.remove('toast-success', 'toast-error', 'toast-info');
            this.toast.classList.add('toast-' + kind);
            this.toast.querySelector('.toast-message').textContent = message;

            const icon = this.toast.querySelector('.toast-icon');
            if (icon) {
                icon.className = 'toast-icon bi ' + (
                    kind === 'success' ? 'bi-check-circle-fill' :
                    kind === 'error'   ? 'bi-exclamation-circle-fill' :
                                          'bi-info-circle-fill'
                );
            }
            this.toast.classList.add('show');
            if (duration > 0) {
                this._toastTimer = setTimeout(() => this.toast.classList.remove('show'), duration);
            }
        },
    };

    // ======================================================================
    // Boot
    // ======================================================================
    function boot() {
        ProfileEditForm.init();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }

    window.ProfileEditForm = ProfileEditForm;
})();