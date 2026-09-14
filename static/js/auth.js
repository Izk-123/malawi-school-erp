/**
 * Auth interactions — mobile-first, no dependencies.
 *
 *  - Password visibility toggle (data-pwd-toggle="<input-id>")
 *  - Password strength meter (data-strength-target="<input-id>")
 *  - Six-digit OTP input (auto-advance, paste, backspace)
 *  - Submit protection (disable + spinner on submit)
 *  - Slow-network feedback after 8 s
 *
 * Progressive enhancement: all forms submit normally without this file.
 */
(function () {
    'use strict';

    // ======================================================================
    // Password visibility toggle
    // ======================================================================
    function initPasswordToggles(root) {
        (root || document).querySelectorAll('[data-pwd-toggle]').forEach(btn => {
            if (btn.dataset.pwdReady) return;
            btn.dataset.pwdReady = '1';
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const input = document.getElementById(btn.dataset.pwdToggle);
                if (!input) return;
                const show = input.type === 'password';
                input.type = show ? 'text' : 'password';
                const icon = btn.querySelector('i');
                if (icon) icon.className = show ? 'bi bi-eye-slash' : 'bi bi-eye';
                btn.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
            });
        });
    }

    // ======================================================================
    // Password strength meter
    // ======================================================================
    function scorePassword(pwd) {
        let score = 0;
        if (!pwd) return 0;
        if (pwd.length >= 8) score++;
        if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) score++;
        if (/\d/.test(pwd)) score++;
        if (/[^A-Za-z0-9]/.test(pwd)) score++;
        return Math.min(score, 4);
    }

    const STRENGTH_LABELS = ['', 'Weak', 'Fair', 'Good', 'Strong'];

    function initStrengthMeters(root) {
        (root || document).querySelectorAll('[data-strength-target]').forEach(el => {
            if (el.dataset.strengthReady) return;
            el.dataset.strengthReady = '1';

            const input = document.getElementById(el.dataset.strengthTarget);
            if (!input) return;

            // Ensure bars exist
            if (!el.querySelector('.password-strength-bar')) {
                el.innerHTML = '<div class="password-strength-bar"></div>'.repeat(4);
            }

            input.addEventListener('input', () => {
                const score = scorePassword(input.value);
                const labels = ['', 'weak', 'fair', 'good', 'strong'];
                el.dataset.strength = labels[score] || '';
                let label = el.parentElement.querySelector('.password-strength-label');
                if (!label) {
                    label = document.createElement('div');
                    label.className = 'password-strength-label';
                    el.parentElement.insertBefore(label, el.nextSibling);
                }
                label.textContent = score === 0 ? '' : `${STRENGTH_LABELS[score]} password`;
            });
        });
    }

    // ======================================================================
    // OTP input — one digit per box
    // ======================================================================
    function initOTP(root) {
        (root || document).querySelectorAll('.otp-form').forEach(form => {
            if (form.dataset.otpReady) return;
            form.dataset.otpReady = '1';

            const digits = Array.from(form.querySelectorAll('.otp-digit'));
            if (!digits.length) return;

            // Hidden field that receives the joined code
            let hidden = form.querySelector('input[name="otp_code"]');
            if (!hidden) {
                hidden = document.createElement('input');
                hidden.type = 'hidden';
                hidden.name = 'otp_code';
                form.appendChild(hidden);
            }

            const sync = () => {
                hidden.value = digits.map(d => d.value).join('');
            };

            digits.forEach((d, i) => {
                // Android autofill: only the first box accepts the auto-fill hint
                if (i === 0) d.setAttribute('autocomplete', 'one-time-code');

                d.addEventListener('input', (e) => {
                    const v = e.target.value.replace(/\D/g, '').slice(-1);
                    e.target.value = v;
                    d.classList.toggle('filled', !!v);
                    if (v && i < digits.length - 1) digits[i + 1].focus();
                    sync();
                    if (hidden.value.length === digits.length) {
                        // auto-submit only if the form has data-otp-autosubmit
                        if (form.dataset.otpAutosubmit !== undefined) {
                            form.requestSubmit();
                        }
                    }
                });

                d.addEventListener('keydown', (e) => {
                    if (e.key === 'Backspace') {
                        if (d.value) {
                            d.value = '';
                            d.classList.remove('filled');
                            sync();
                        } else if (i > 0) {
                            digits[i - 1].focus();
                            digits[i - 1].value = '';
                            digits[i - 1].classList.remove('filled');
                            sync();
                        }
                        e.preventDefault();
                    } else if (e.key === 'ArrowLeft' && i > 0) {
                        digits[i - 1].focus();
                        e.preventDefault();
                    } else if (e.key === 'ArrowRight' && i < digits.length - 1) {
                        digits[i + 1].focus();
                        e.preventDefault();
                    } else if (e.key === 'Escape') {
                        digits.forEach(x => { x.value = ''; x.classList.remove('filled'); });
                        digits[0].focus();
                        sync();
                    }
                });

                d.addEventListener('paste', (e) => {
                    e.preventDefault();
                    const pasted = (e.clipboardData.getData('text') || '')
                        .replace(/\D/g, '')
                        .slice(0, digits.length - i);
                    pasted.split('').forEach((ch, j) => {
                        const target = digits[i + j];
                        if (target) {
                            target.value = ch;
                            target.classList.add('filled');
                        }
                    });
                    const last = Math.min(i + pasted.length, digits.length - 1);
                    digits[last].focus();
                    sync();
                });

                d.addEventListener('focus', () => d.select());
            });

            sync();
        });
    }

    // ======================================================================
    // Submit protection + slow-network feedback
    // ======================================================================
    function initSubmitProtection(root) {
        (root || document).querySelectorAll('form.auth-form, form.otp-form').forEach(form => {
            if (form.dataset.submitReady) return;
            form.dataset.submitReady = '1';

            form.addEventListener('submit', () => {
                const btn = form.querySelector('button[type="submit"]');
                if (!btn || btn.disabled) return;
                btn.disabled = true;
                btn.dataset.originalHtml = btn.innerHTML;
                btn.innerHTML = '<span class="spinner"></span>Please wait…';

                setTimeout(() => {
                    if (!btn.disabled) return;
                    btn.innerHTML = '<span class="spinner"></span>Still working — slow network…';
                }, 8000);
            });
        });
    }

    // ======================================================================
    // OTP resend countdown
    // ======================================================================
    function initResendCountdown(root) {
        (root || document).querySelectorAll('[data-resend-seconds]').forEach(el => {
            if (el.dataset.resendReady) return;
            el.dataset.resendReady = '1';

            const btn = el.querySelector('#resendBtn') || el.querySelector('button');
            const label = el.querySelector('#countdown');
            let remaining = parseInt(el.dataset.resendSeconds, 10) || 60;

            const tick = () => {
                if (remaining <= 0) {
                    if (btn) btn.disabled = false;
                    if (label) label.textContent = '';
                    return;
                }
                const m = String(Math.floor(remaining / 60)).padStart(2, '0');
                const s = String(remaining % 60).padStart(2, '0');
                if (label) label.textContent = `${m}:${s}`;
                remaining--;
                setTimeout(tick, 1000);
            };
            tick();
        });
    }

    // ======================================================================
    // Boot
    // ======================================================================
    function boot() {
        initPasswordToggles();
        initStrengthMeters();
        initOTP();
        initSubmitProtection();
        initResendCountdown();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }

    // Allow re-initialising after dynamic content swaps
    window.AuthUI = {
        refresh(root) {
            initPasswordToggles(root);
            initStrengthMeters(root);
            initOTP(root);
            initSubmitProtection(root);
            initResendCountdown(root);
        },
    };
})();