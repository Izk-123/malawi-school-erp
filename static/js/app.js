/**
 * Mobile-first app shell.
 *
 *  - Theme manager (light/dark, persisted)
 *  - Command palette / mobile full-screen search (⌘K, /, or tap)
 *  - Sequence shortcuts (g s, g f, …) — desktop only
 *  - Sidebar collapse ([) — desktop only
 *
 * No dependencies. Progressive enhancement: without this file the app
 * still works — bottom nav, sidebar, and links all render server-side.
 */
(function () {
    'use strict';

    const DESKTOP_BP = 840;
    const isDesktop = () => window.innerWidth >= DESKTOP_BP;
    const isTouchOnly = () =>
        !window.matchMedia('(hover: hover) and (pointer: fine)').matches;

    // ======================================================================
    // Theme
    // ======================================================================
    const ThemeManager = {
        KEY: 'mse.theme',
        init() {
            const saved = localStorage.getItem(this.KEY);
            const prefersDark = window.matchMedia &&
                window.matchMedia('(prefers-color-scheme: dark)').matches;
            this.apply(saved || (prefersDark ? 'dark' : 'light'));
        },
        apply(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            document.documentElement.setAttribute('data-bs-theme', theme);
            localStorage.setItem(this.KEY, theme);
            document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
                btn.innerHTML = theme === 'dark'
                    ? '<i class="bi bi-sun"></i>'
                    : '<i class="bi bi-moon-stars"></i>';
            });
        },
        toggle() {
            const cur = document.documentElement.getAttribute('data-theme') || 'light';
            this.apply(cur === 'dark' ? 'light' : 'dark');
        },
    };

    // ======================================================================
    // Sidebar collapse (desktop only; on tablet/mobile the shell is rail/none)
    // ======================================================================
    const Sidebar = {
        KEY: 'mse.sidebar.collapsed',
        el() { return document.getElementById('sidebar'); },
        init() {
            if (localStorage.getItem(this.KEY) === '1') {
                this.el()?.classList.add('collapsed');
            }
        },
        toggle() {
            const el = this.el();
            if (!el) return;
            el.classList.toggle('collapsed');
            localStorage.setItem(this.KEY,
                el.classList.contains('collapsed') ? '1' : '0');
        },
    };

    // ======================================================================
    // Command palette — full-screen on mobile, centered dialog on desktop
    // ======================================================================
    const CommandPalette = {
        backdrop: null,
        input: null,
        results: null,
        items: [],
        filtered: [],
        activeIndex: 0,

        init() {
            this.backdrop = document.getElementById('command-palette');
            if (!this.backdrop) return;
            this.input   = this.backdrop.querySelector('.cmdk-input');
            this.results = this.backdrop.querySelector('.cmdk-results');

            const dataEl = document.getElementById('command-data');
            if (dataEl) {
                try { this.items = JSON.parse(dataEl.textContent); }
                catch (e) { this.items = []; }
            }

            this.backdrop.addEventListener('click', (e) => {
                if (e.target === this.backdrop) this.close();
            });
            this.backdrop.querySelectorAll('[data-cmdk-close]').forEach(el => {
                el.addEventListener('click', () => this.close());
            });

            this.input.addEventListener('input', () => this.render());
            this.input.addEventListener('keydown', (e) => this.onKey(e));
        },

        open() {
            if (!this.backdrop) return;
            this.backdrop.classList.add('open');
            document.body.style.overflow = 'hidden';
            this.input.value = '';
            this.activeIndex = 0;
            this.render();
            requestAnimationFrame(() => this.input.focus());
        },

        close() {
            this.backdrop?.classList.remove('open');
            document.body.style.overflow = '';
        },

        isOpen() { return this.backdrop?.classList.contains('open'); },

        render() {
            const q = this.input.value.trim().toLowerCase();
            this.filtered = !q
                ? this.items
                : this.items.filter(it =>
                    it.label.toLowerCase().includes(q) ||
                    (it.keywords || '').toLowerCase().includes(q));

            if (this.filtered.length === 0) {
                this.results.innerHTML = '<div class="cmdk-empty">No results</div>';
                return;
            }

            const groups = {};
            this.filtered.forEach(it => {
                const s = it.section || 'Commands';
                (groups[s] = groups[s] || []).push(it);
            });

            let html = '';
            let idx = 0;
            Object.keys(groups).forEach(section => {
                html += `<div class="cmdk-section">${section}</div>`;
                groups[section].forEach(item => {
                    const active = idx === this.activeIndex ? ' active' : '';
                    html += `
                        <div class="cmdk-item${active}" data-index="${idx}" data-url="${item.url || ''}">
                            <i class="bi ${item.icon || 'bi-arrow-right'}"></i>
                            <span class="cmdk-item-label">${item.label}</span>
                            ${item.hint ? `<span class="cmdk-hint">${item.hint}</span>` : ''}
                        </div>`;
                    idx++;
                });
            });
            this.results.innerHTML = html;

            this.results.querySelectorAll('.cmdk-item').forEach(el => {
                el.addEventListener('click', () =>
                    this.execute(parseInt(el.dataset.index, 10)));
            });
        },

        onKey(e) {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                this.activeIndex = Math.min(this.activeIndex + 1, this.filtered.length - 1);
                this.render();
                this.scrollActiveIntoView();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                this.activeIndex = Math.max(this.activeIndex - 1, 0);
                this.render();
                this.scrollActiveIntoView();
            } else if (e.key === 'Enter') {
                e.preventDefault();
                this.execute(this.activeIndex);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                this.close();
            }
        },

        scrollActiveIntoView() {
            this.results.querySelector('.cmdk-item.active')
                ?.scrollIntoView({ block: 'nearest' });
        },

        execute(index) {
            const item = this.filtered[index];
            if (!item || !item.url) return;
            this.close();
            window.location.href = item.url;
        },
    };

    // ======================================================================
    // Global keyboard shortcuts — desktop only
    // ======================================================================
    const Shortcuts = {
        buffer: '',
        timer: null,
        sequences: {
            'gs': '/students/',
            'gt': '/teachers/',
            'ga': '/attendance/',
            'gf': '/fees/',
            'gr': '/reports/',
            'gp': '/payments/',
            'gn': '/notifications/',
            'gh': '/',
        },

        isEditable(el) {
            if (!el) return false;
            const t = el.tagName;
            return t === 'INPUT' || t === 'TEXTAREA' || el.isContentEditable;
        },

        init() {
            document.addEventListener('keydown', (e) => this.onKey(e));
        },

        onKey(e) {
            // ⌘K / Ctrl+K — always available
            if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                CommandPalette.isOpen() ? CommandPalette.close() : CommandPalette.open();
                return;
            }
            if (e.key === 'Escape' && CommandPalette.isOpen()) {
                e.preventDefault();
                CommandPalette.close();
                return;
            }

            // Everything below is keyboard-only — no touch devices
            if (isTouchOnly()) return;
            if (this.isEditable(e.target) || CommandPalette.isOpen()) return;
            if (e.metaKey || e.ctrlKey || e.altKey) return;

            if (e.key === '[' && isDesktop()) {
                e.preventDefault();
                Sidebar.toggle();
                return;
            }
            if (e.key === '/') {
                e.preventDefault();
                CommandPalette.open();
                return;
            }
            if (/^[a-z]$/i.test(e.key)) {
                this.buffer += e.key.toLowerCase();
                clearTimeout(this.timer);
                this.timer = setTimeout(() => { this.buffer = ''; }, 1000);

                const url = this.sequences[this.buffer];
                if (url) {
                    e.preventDefault();
                    window.location.href = url;
                    this.buffer = '';
                }
                if (this.buffer.length > 2) this.buffer = this.buffer.slice(-2);
            }
        },
    };

    // ======================================================================
    // Breadcrumb — copy the mobile title into the desktop breadcrumb
    // ======================================================================
    function hydrateBreadcrumb() {
        const title = document.querySelector('.app-bar-title');
        const crumb = document.querySelector('.app-bar-breadcrumb-current');
        if (title && crumb && !crumb.textContent.trim()) {
            crumb.textContent = title.textContent.trim();
        }
    }

    // ======================================================================
    // Boot
    // ======================================================================
    function boot() {
        ThemeManager.init();
        Sidebar.init();
        CommandPalette.init();
        Shortcuts.init();
        hydrateBreadcrumb();

        document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                ThemeManager.toggle();
            });
        });
        document.querySelectorAll('[data-sidebar-toggle]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                if (isDesktop()) Sidebar.toggle();
            });
        });
        document.querySelectorAll('[data-cmdk-open]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                CommandPalette.open();
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }

    window.ThemeManager   = ThemeManager;
    window.CommandPalette = CommandPalette;
    window.Sidebar        = Sidebar;
})();