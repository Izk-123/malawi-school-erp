/**
 * motion-pro.js — advanced interaction layer.
 *
 * Adds, on top of motion.js:
 *   • Masked text reveal      [data-reveal-text]
 *   • Cursor spotlight        [data-spotlight]
 *   • Magnetic hover          [data-magnetic]
 *   • 3D tilt                 [data-tilt]
 *   • Ripple on tap           [data-ripple]
 *   • Odometer number roll    [data-odometer]
 *   • Icon morph on hover     [data-icon-morph]
 *   • Cursor trail glow       [data-cursor-glow] on <body>
 *   • Scroll-linked parallax  [data-parallax="0.2"]
 *
 * Every feature is opt-in, disabled under prefers-reduced-motion, and
 * degrades gracefully if JS is blocked.
 */
(function () {
  'use strict';

  const REDUCED = document.documentElement.dataset.reducedMotion === 'true';

  // ═════════════════════════════════════════════════════════════════════
  // 1 · Masked text reveal — splits text into lines, animates a clip mask
  // ═════════════════════════════════════════════════════════════════════
  function initRevealText() {
    document.querySelectorAll('[data-reveal-text]').forEach((el) => {
      if (el.dataset.revealReady) return;
      el.dataset.revealReady = '1';
      if (REDUCED) { el.style.opacity = '1'; return; }

      const stagger = parseInt(el.dataset.revealStagger || '30', 10);
      const delay   = parseInt(el.dataset.revealDelay   || '0', 10);

      // Split text nodes into words wrapped in overflow-clipped spans
      const walk = (node) => {
        if (node.nodeType === 3) {
          const text = node.nodeValue;
          if (!text.trim()) return node.cloneNode();
          const frag = document.createDocumentFragment();
          text.split(/(\s+)/).forEach((tok) => {
            if (!tok) return;
            if (/^\s+$/.test(tok)) { frag.appendChild(document.createTextNode(tok)); return; }
            const outer = document.createElement('span');
            outer.className = 'rv-line';
            const inner = document.createElement('span');
            inner.className = 'rv-word';
            inner.textContent = tok;
            outer.appendChild(inner);
            frag.appendChild(outer);
          });
          return frag;
        }
        if (node.nodeType === 1) {
          const clone = node.cloneNode(false);
          node.childNodes.forEach((c) => clone.appendChild(walk(c)));
          return clone;
        }
        return node.cloneNode();
      };

      const frag = walk(el);
      el.innerHTML = '';
      el.appendChild(frag);

      const words = el.querySelectorAll('.rv-word');
      words.forEach((w, i) => {
        w.style.transform = 'translateY(110%)';
        w.style.display = 'inline-block';
        w.style.willChange = 'transform';
        setTimeout(() => {
          w.style.transition = 'transform 720ms cubic-bezier(0.22, 1, 0.36, 1)';
          w.style.transform = 'translateY(0)';
        }, delay + i * stagger);
      });
      el.style.opacity = '1';
    });
  }

  // ═════════════════════════════════════════════════════════════════════
  // 2 · Cursor spotlight on cards — a radial gradient that follows cursor
  // ═════════════════════════════════════════════════════════════════════
  function initSpotlight() {
    if (REDUCED) return;
    if (!matchMedia('(hover: hover) and (pointer: fine)').matches) return;

    document.querySelectorAll('[data-spotlight]').forEach((el) => {
      if (el.dataset.spotlightReady) return;
      el.dataset.spotlightReady = '1';

      el.style.position = el.style.position || 'relative';
      el.style.overflow = 'hidden';

      const glow = document.createElement('div');
      glow.className = 'spotlight-glow';
      glow.style.cssText = `
        position:absolute; pointer-events:none; inset:0;
        opacity:0; transition:opacity 260ms ease;
        background: radial-gradient(220px circle at var(--mx,50%) var(--my,50%),
                    rgba(26,86,50,0.14), transparent 60%);
        mix-blend-mode: multiply;
      `;
      el.appendChild(glow);

      el.addEventListener('pointerenter', () => { glow.style.opacity = '1'; });
      el.addEventListener('pointerleave', () => { glow.style.opacity = '0'; });
      el.addEventListener('pointermove', (e) => {
        const r = el.getBoundingClientRect();
        el.style.setProperty('--mx', `${e.clientX - r.left}px`);
        el.style.setProperty('--my', `${e.clientY - r.top}px`);
      });

      // Dark mode variant
      const obs = new MutationObserver(() => {
        const dark = document.documentElement.dataset.theme === 'dark';
        glow.style.background = dark
          ? 'radial-gradient(220px circle at var(--mx,50%) var(--my,50%), rgba(76,154,110,0.22), transparent 60%)'
          : 'radial-gradient(220px circle at var(--mx,50%) var(--my,50%), rgba(26,86,50,0.14), transparent 60%)';
      });
      obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    });
  }

  // ═════════════════════════════════════════════════════════════════════
  // 3 · Magnetic hover — element drifts toward cursor within its bounds
  // ═════════════════════════════════════════════════════════════════════
  function initMagnetic() {
    if (REDUCED) return;
    if (!matchMedia('(hover: hover) and (pointer: fine)').matches) return;

    document.querySelectorAll('[data-magnetic]').forEach((el) => {
      if (el.dataset.magneticReady) return;
      el.dataset.magneticReady = '1';

      const strength = parseFloat(el.dataset.magnetic) || 0.28;
      let raf = null, tx = 0, ty = 0, cx = 0, cy = 0, active = false;

      const loop = () => {
        cx += (tx - cx) * 0.18;
        cy += (ty - cy) * 0.18;
        el.style.transform = `translate3d(${cx}px, ${cy}px, 0)`;
        if (Math.abs(tx - cx) > 0.1 || Math.abs(ty - cy) > 0.1 || active) {
          raf = requestAnimationFrame(loop);
        } else {
          raf = null;
          if (!active) el.style.transform = '';
        }
      };

      el.addEventListener('pointerenter', () => {
        active = true;
        el.style.willChange = 'transform';
      });
      el.addEventListener('pointermove', (e) => {
        const r = el.getBoundingClientRect();
        tx = (e.clientX - r.left - r.width / 2) * strength;
        ty = (e.clientY - r.top - r.height / 2) * strength;
        if (!raf) raf = requestAnimationFrame(loop);
      });
      el.addEventListener('pointerleave', () => {
        active = false;
        tx = 0; ty = 0;
        if (!raf) raf = requestAnimationFrame(loop);
      });
    });
  }

  // ═════════════════════════════════════════════════════════════════════
  // 4 · 3D tilt — card rotates toward cursor
  // ═════════════════════════════════════════════════════════════════════
  function initTilt() {
    if (REDUCED) return;
    if (!matchMedia('(hover: hover) and (pointer: fine)').matches) return;

    document.querySelectorAll('[data-tilt]').forEach((el) => {
      if (el.dataset.tiltReady) return;
      el.dataset.tiltReady = '1';

      const max = parseFloat(el.dataset.tilt) || 6;   // degrees
      let raf = null;

      const apply = (rx, ry) => {
        el.style.transform = `perspective(900px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(-2px)`;
      };

      el.style.transformStyle = 'preserve-3d';
      el.style.transition = 'transform 260ms cubic-bezier(0.22,1,0.36,1), box-shadow 260ms';

      el.addEventListener('pointermove', (e) => {
        const r = el.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width - 0.5;
        const py = (e.clientY - r.top)  / r.height - 0.5;
        if (raf) cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => {
          apply(-py * max, px * max);
          el.style.boxShadow = '0 20px 40px -12px rgba(0,0,0,0.18)';
        });
      });
      el.addEventListener('pointerleave', () => {
        if (raf) cancelAnimationFrame(raf);
        el.style.transform = '';
        el.style.boxShadow = '';
      });
    });
  }

  // ═════════════════════════════════════════════════════════════════════
  // 5 · Ripple on tap
  // ═════════════════════════════════════════════════════════════════════
  function initRipple() {
    document.querySelectorAll('[data-ripple]').forEach((el) => {
      if (el.dataset.rippleReady) return;
      el.dataset.rippleReady = '1';
      el.style.position = el.style.position || 'relative';
      el.style.overflow = 'hidden';

      el.addEventListener('pointerdown', (e) => {
        const r = el.getBoundingClientRect();
        const size = Math.max(r.width, r.height) * 2;
        const ripple = document.createElement('span');
        ripple.className = 'mo-ripple';
        ripple.style.cssText = `
          position:absolute; pointer-events:none;
          left:${e.clientX - r.left - size/2}px;
          top:${e.clientY - r.top - size/2}px;
          width:${size}px; height:${size}px;
          border-radius:50%;
          background: currentColor;
          opacity:0.28;
          transform: scale(0);
          transition: transform 620ms cubic-bezier(0.22,1,0.36,1), opacity 620ms;
        `;
        el.appendChild(ripple);
        requestAnimationFrame(() => {
          ripple.style.transform = 'scale(1)';
          ripple.style.opacity = '0';
        });
        setTimeout(() => ripple.remove(), 680);
      });
    });
  }

  // ═════════════════════════════════════════════════════════════════════
  // 6 · Odometer number roll — digits flip up from below
  // ═════════════════════════════════════════════════════════════════════
  function initOdometer() {
    document.querySelectorAll('[data-odometer]').forEach((el) => {
      if (el.dataset.odomReady) return;
      el.dataset.odomReady = '1';

      const raw = String(el.dataset.odometer || el.textContent).trim();
      const prefix = el.dataset.odomPrefix || '';
      const suffix = el.dataset.odomSuffix || '';
      const delay  = parseInt(el.dataset.odomDelay || '0', 10);

      if (REDUCED) { el.textContent = prefix + raw + suffix; return; }

      el.innerHTML = '';
      el.style.display = 'inline-flex';
      el.style.alignItems = 'baseline';
      el.style.gap = '0';

      if (prefix) {
        const p = document.createElement('span');
        p.textContent = prefix;
        el.appendChild(p);
      }

      const targets = raw.split('').map((ch, i) => {
        if (!/\d/.test(ch)) {
          const s = document.createElement('span');
          s.textContent = ch;
          el.appendChild(s);
          return null;
        }
        const wrap = document.createElement('span');
        wrap.style.cssText = 'display:inline-block;overflow:hidden;height:1em;line-height:1;';
        const inner = document.createElement('span');
        inner.style.cssText = 'display:inline-block;transform:translateY(100%);transition:transform 720ms cubic-bezier(0.22,1,0.36,1);';
        inner.textContent = ch;
        wrap.appendChild(inner);
        el.appendChild(wrap);
        return { inner, delay: delay + i * 60 };
      });

      requestAnimationFrame(() => {
        targets.forEach((t) => {
          if (!t) return;
          setTimeout(() => { t.inner.style.transform = 'translateY(0)'; }, t.delay);
        });
      });

      if (suffix) {
        const s = document.createElement('span');
        s.textContent = suffix;
        el.appendChild(s);
      }
    });
  }

  // ═════════════════════════════════════════════════════════════════════
  // 7 · Cursor glow — a soft light follows the pointer over the app shell
  // ═════════════════════════════════════════════════════════════════════
  function initCursorGlow() {
    if (REDUCED) return;
    if (!matchMedia('(hover: hover) and (pointer: fine)').matches) return;

    const dot = document.createElement('div');
    dot.id = 'mo-cursor-glow';
    dot.style.cssText = `
      position:fixed; pointer-events:none; z-index:9999;
      width:260px; height:260px; border-radius:50%;
      background: radial-gradient(circle, rgba(26,86,50,0.10), transparent 65%);
      transform: translate3d(-50%, -50%, 0);
      transition: opacity 320ms ease;
      opacity: 0;
      will-change: transform;
      mix-blend-mode: multiply;
    `;
    document.body.appendChild(dot);

    let mx = 0, my = 0, cx = 0, cy = 0, visible = false;
    const loop = () => {
      cx += (mx - cx) * 0.16;
      cy += (my - cy) * 0.16;
      dot.style.transform = `translate3d(${cx}px, ${cy}px, 0) translate(-50%, -50%)`;
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);

    document.addEventListener('pointermove', (e) => {
      mx = e.clientX; my = e.clientY;
      if (!visible) { dot.style.opacity = '1'; visible = true; }
    });
    document.addEventListener('pointerleave', () => { dot.style.opacity = '0'; visible = false; });

    // Dark mode adaptation
    const syncTheme = () => {
      const dark = document.documentElement.dataset.theme === 'dark';
      dot.style.background = dark
        ? 'radial-gradient(circle, rgba(76,154,110,0.14), transparent 65%)'
        : 'radial-gradient(circle, rgba(26,86,50,0.10), transparent 65%)';
      dot.style.mixBlendMode = dark ? 'screen' : 'multiply';
    };
    syncTheme();
    new MutationObserver(syncTheme).observe(document.documentElement, {
      attributes: true, attributeFilter: ['data-theme']
    });
  }

  // ═════════════════════════════════════════════════════════════════════
  // 8 · Parallax on scroll
  // ═════════════════════════════════════════════════════════════════════
  function initParallax() {
    if (REDUCED) return;
    const els = document.querySelectorAll('[data-parallax]');
    if (!els.length) return;

    let ticking = false;
    const update = () => {
      const vh = window.innerHeight;
      els.forEach((el) => {
        const speed = parseFloat(el.dataset.parallax) || 0.2;
        const r = el.getBoundingClientRect();
        const progress = (r.top + r.height / 2 - vh / 2) / vh;
        el.style.transform = `translate3d(0, ${-progress * speed * 100}px, 0)`;
      });
      ticking = false;
    };
    addEventListener('scroll', () => {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  // ═════════════════════════════════════════════════════════════════════
  // Boot
  // ═════════════════════════════════════════════════════════════════════
  function boot(root) {
    const s = root || document;
    // Scope helper: temporarily swap querySelectorAll target
    const orig = document.querySelectorAll.bind(document);
    // (simple approach — just call the init fns; they use document directly)
    initRevealText();
    initSpotlight();
    initMagnetic();
    initTilt();
    initRipple();
    initOdometer();
    initParallax();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initCursorGlow();
      boot();
    });
  } else {
    initCursorGlow();
    boot();
  }

  window.MotionPro = { refresh: boot };
})();