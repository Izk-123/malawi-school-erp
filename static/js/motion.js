/**
 * motion.js — a compact Framer-Motion-like animation engine.
 *
 * Declarative, HTML-driven. Reads data-motion* attributes and animates with
 * real springs (numerical integration), keyframes, variants, orchestration,
 * gestures, layout FLIP, and AnimatePresence-style exit transitions.
 *
 * HTML API
 * ────────
 *   data-motion="fade-up"                          preset
 *   data-motion-variant="heroCard"                 variant name (from JSON)
 *   data-motion-initial="hidden"                   variant state name
 *   data-motion-animate="visible"
 *   data-motion-exit="hidden"
 *   data-motion-while-hover="hovered"              variant-state on hover
 *   data-motion-while-tap="pressed"
 *   data-motion-transition='{"type":"spring","stiffness":260,"damping":24}'
 *   data-motion-delay="120"                        ms
 *   data-motion-duration="500"                     ms (tween only)
 *   data-motion-once="false"                       replay on re-entry
 *   data-motion-keyframes='[{"opacity":0,"y":24},{...}]'
 *   data-motion-orchestrate='{"when":"beforeChildren","delayChildren":0.05,"staggerChildren":0.06}'
 *   data-motion-while-hover='{"scale":1.03}'       inline gesture values
 *   data-motion-while-tap='{"scale":0.97}'
 *   data-motion-layout                             FLIP on resize/mount
 *   data-motion-drag                               pointer drag with constraints
 *
 * Progressive: without this file, motion.css provides basic entrance presets.
 *
 * Slow-connection / reduced-motion: the engine short-circuits entirely.
 * base.html detects save-data / 2G and adds `.no-motion` to <html> before
 * this script even loads; if we see that, we reveal everything and exit
 * without hydrating a single element.
 */
(function () {
'use strict';

// ═══════════════════════════════════════════════════════════════════════════
// 0 · Slow-connection / no-motion short-circuit
// ---------------------------------------------------------------------------
// On save-data or 2G, skip the entire engine. Every element is already
// visible because base.html set html.no-motion (which the CSS treats as a
// global escape hatch). This saves CPU, memory, and battery on devices that
// can least afford them. Also covers OS-level prefers-reduced-motion.
// ═══════════════════════════════════════════════════════════════════════════
const _html = document.documentElement;
const _conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
const _isSlowConn = _conn && (
  _conn.saveData === true ||
  /(^|-)2g$/.test(_conn.effectiveType || '')
);
const _isReduced = _html.dataset.reducedMotion === 'true';

if (_isSlowConn || _isReduced || _html.classList.contains('no-motion')) {
  const revealAll = () => {
    document.querySelectorAll(
      '[data-motion],[data-motion-variant],[data-reveal-text],.sidebar-logout-form'
    ).forEach((el) => {
      el.setAttribute('data-motion-ready', '1');
      el.style.opacity = '1';
      el.style.transform = 'none';
      el.style.filter = 'none';
    });
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', revealAll);
  } else {
    revealAll();
  }

  // No-op API so other scripts that call window.Motion.* don't throw.
  window.Motion = {
    refresh: () => {},
    registerVariants: () => {},
    animate: () => Promise.resolve(),
    reduce: () => true,
  };
  window.__moBooted = true;   // stand the safety-net timer down
  return;                     // ← skip the rest of the engine
}

// ═══════════════════════════════════════════════════════════════════════════
// 1 · Utilities
// ═══════════════════════════════════════════════════════════════════════════
const REDUCED = false;   // we already exited above if reduced
const raf = requestAnimationFrame.bind(window);
const caf = cancelAnimationFrame.bind(window);
const clamp = (n, a, b) => Math.min(Math.max(n, a), b);
const lerp  = (a, b, t) => a + (b - a) * t;
const isNum = (v) => typeof v === 'number' && !isNaN(v);
const parse = (v) => {
  if (isNum(v)) return { n: v, u: '' };
  if (typeof v !== 'string') return { n: 0, u: '' };
  const m = v.match(/^([+-]?(?:\d+\.?\d*|\.\d+))(px|%|em|rem|deg|rad|turn|vh|vw|s|ms)?$/);
  return m ? { n: parseFloat(m[1]), u: m[2] || '' } : { n: parseFloat(v) || 0, u: '' };
};
const readJSON = (attr, el) => {
  const raw = el?.getAttribute?.(attr) ?? attr;
  if (!raw) return null;
  if (typeof raw === 'object') return raw;
  try { return JSON.parse(raw); } catch { return null; }
};

// ═══════════════════════════════════════════════════════════════════════════
// 2 · Easing — cubic bezier evaluator (Newton–Raphson + bisection fallback)
// ═══════════════════════════════════════════════════════════════════════════
const EASING_PRESETS = {
  linear:        [0, 0, 1, 1],
  ease:          [0.25, 0.1, 0.25, 1],
  'ease-in':     [0.42, 0, 1, 1],
  'ease-out':    [0, 0, 0.58, 1],
  'ease-in-out': [0.42, 0, 0.58, 1],
  anticipate:    [0.36, 0, 0.66, -0.56],
  backOut:       [0.34, 1.56, 0.64, 1],
  circOut:       [0, 0.55, 0.45, 1],
  circIn:        [0.55, 0, 1, 0.45],
  expoOut:       [0.16, 1, 0.3, 1],
  expoIn:        [0.7, 0, 0.84, 0],
};

function cubicBezier(p1x, p1y, p2x, p2y) {
  const A = (a, b) => 1 - 3 * b + 3 * a;
  const B = (a, b) => 3 * b - 6 * a;
  const C = (a) => 3 * a;
  const calc = (t, a, b) => ((A(a,b) * t + B(a,b)) * t + C(a)) * t;
  const slope = (t, a, b) => 3 * A(a,b) * t * t + 2 * B(a,b) * t + C(a);
  return function (t) {
    if (t <= 0) return 0;
    if (t >= 1) return 1;
    let u = t;
    for (let i = 0; i < 8; i++) {
      const s = slope(u, p1x, p2x);
      if (Math.abs(s) < 1e-6) break;
      u -= (calc(u, p1x, p2x) - t) / s;
    }
    if (u < 0 || u > 1) {
      let lo = 0, hi = 1;
      for (let i = 0; i < 20; i++) {
        const mid = (lo + hi) / 2;
        if (calc(mid, p1x, p2x) < t) lo = mid; else hi = mid;
      }
      u = (lo + hi) / 2;
    }
    return calc(u, p1y, p2y);
  };
}
const EASING_FNS = Object.fromEntries(
  Object.entries(EASING_PRESETS).map(([k, v]) => [k, cubicBezier(...v)])
);
const resolveEase = (e) =>
  Array.isArray(e) && e.length === 4 ? cubicBezier(...e)
  : (typeof e === 'string' && EASING_FNS[e]) ? EASING_FNS[e]
  : EASING_FNS.ease;

// ═══════════════════════════════════════════════════════════════════════════
// 3 · Spring solver — semi-implicit Euler, real overshoot
// ═══════════════════════════════════════════════════════════════════════════
function makeSpring({ stiffness = 260, damping = 26, mass = 1, velocity = 0 }) {
  let pos = 0, vel = velocity;
  const REST_V = 0.05;
  const REST_P = 0.001;
  return function step(dt) {
    const F = -stiffness * (pos - 1) - damping * vel;
    vel += (F / mass) * dt;
    pos += vel * dt;
    const done = Math.abs(vel) < REST_V && Math.abs(1 - pos) < REST_P;
    return { pos: done ? 1 : pos, vel, done };
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// 4 · Property handling — transforms are batched, others set individually
// ═══════════════════════════════════════════════════════════════════════════
const TRANSFORM_PROPS = new Set([
  'x','y','z','scale','scaleX','scaleY','rotate','rotateX','rotateY','skewX','skewY',
]);
const UNITLESS = new Set(['opacity','scale','scaleX','scaleY','zIndex','rotate','rotateX','rotateY','skewX','skewY']);

const buildTransform = (v) => {
  const parts = [];
  if (v.x != null || v.y != null || v.z != null) {
    parts.push(`translate3d(${v.x || 0}px, ${v.y || 0}px, ${v.z || 0}px)`);
  }
  if (v.scale != null || v.scaleX != null || v.scaleY != null) {
    const sx = v.scale ?? v.scaleX ?? 1;
    const sy = v.scale ?? v.scaleY ?? 1;
    parts.push(`scale(${sx}, ${sy})`);
  }
  if (v.rotate  != null) parts.push(`rotate(${v.rotate}deg)`);
  if (v.rotateX != null) parts.push(`rotateX(${v.rotateX}deg)`);
  if (v.rotateY != null) parts.push(`rotateY(${v.rotateY}deg)`);
  if (v.skewX   != null) parts.push(`skewX(${v.skewX}deg)`);
  if (v.skewY   != null) parts.push(`skewY(${v.skewY}deg)`);
  return parts.join(' ');
};

function applyStyle(el, prop, value) {
  if (prop === 'opacity')      el.style.opacity = String(value);
  else if (prop === 'filter')  el.style.filter  = String(value);
  else if (TRANSFORM_PROPS.has(prop)) { /* flushed separately */ }
  else if (prop.startsWith('--')) el.style.setProperty(prop, String(value));
  else el.style[prop] = isNum(value) && !UNITLESS.has(prop) ? `${value}px` : String(value);
}

// ═══════════════════════════════════════════════════════════════════════════
// 5 · MotionElement — per-element animator with spring / tween / keyframes
// ═══════════════════════════════════════════════════════════════════════════
class MotionElement {
  constructor(el) {
    this.el = el;
    this.t = {};       // current transform state
    this.s = {};       // current non-transform state
    this.a = {};       // active animations (per prop)
    this.raf = null;
    this.last = 0;
    this.hoverState = null;
    this.tapState = null;
    this._base = null;
  }

  seed(values) {
    if (!values) return;
    Object.entries(values).forEach(([p, v]) => {
      if (p === 'transition') return;
      if (TRANSFORM_PROPS.has(p)) this.t[p] = parse(v).n;
      else { this.s[p] = v; applyStyle(this.el, p, v); }
    });
    this.flush();
  }

  flush() {
    const s = buildTransform(this.t);
    if (s || Object.keys(this.t).length) this.el.style.transform = s || 'none';
  }

  snapshot() {
    return {
      transform: Object.assign({}, this.t),
      style: Object.assign({}, this.s),
    };
  }

  restore(snap) {
    this.t = Object.assign({}, snap.transform);
    this.s = Object.assign({}, snap.style);
    this.flush();
    Object.keys(this.s).forEach((p) => applyStyle(this.el, p, this.s[p]));
  }

  animate(target, transition, opts = {}) {
    if (!target) return Promise.resolve();
    if (REDUCED) { this.seed(target); this.el.setAttribute('data-motion-ready','1'); return Promise.resolve(); }

    this.el.removeAttribute('data-mo-init');
    this.el.setAttribute('data-motion-ready', '1');

    const tr = Object.assign({}, transition || {});
    if (opts.delay) tr.delay = opts.delay;
    if (opts.duration != null && tr.duration == null) tr.duration = opts.duration;

    const delayMs = (tr.delay || 0) * 1000;

    Object.entries(target).forEach(([prop, to]) => {
      if (prop === 'transition') return;
      const targetN = TRANSFORM_PROPS.has(prop) ? parse(to).n : parse(to).n;
      const from = TRANSFORM_PROPS.has(prop)
        ? (this.t[prop] ?? 0)
        : (this.s[prop] != null ? parse(this.s[prop]).n : parse(getComputedStyle(this.el)[prop]).n);

      if (from === targetN) {
        if (TRANSFORM_PROPS.has(prop)) this.t[prop] = targetN;
        else { this.s[prop] = to; applyStyle(this.el, prop, to); }
        return;
      }

      const type = tr.type || (isNum(tr.duration) ? 'tween' : 'spring');

      if (type === 'spring') {
        this.a[prop] = {
          kind: 'spring', from, to: targetN, raw: to,
          spring: makeSpring({
            stiffness: tr.stiffness ?? 260,
            damping:   tr.damping   ?? 26,
            mass:      tr.mass      ?? 1,
            velocity:  tr.velocity  ?? 0,
          }),
          start: performance.now() + delayMs,
          transform: TRANSFORM_PROPS.has(prop),
        };
      } else {
        this.a[prop] = {
          kind: 'tween', from, to: targetN, raw: to,
          ease: resolveEase(tr.ease),
          dur: (tr.duration ?? 0.35) * 1000,
          start: performance.now() + delayMs,
          transform: TRANSFORM_PROPS.has(prop),
        };
      }
    });

    this.start();
    return this.settled();
  }

  start() {
    if (this.raf) return;
    this.last = performance.now();
    const tick = (t) => {
      const dt = Math.min((t - this.last) / 1000, 0.064);
      this.last = t;
      const active = this.step(t, dt);
      this.flush();
      this.raf = active ? raf(tick) : null;
    };
    this.raf = raf(tick);
  }

  step(now, dt) {
    let active = false;
    for (const prop in this.a) {
      const a = this.a[prop];
      if (now < a.start) { active = true; continue; }

      let v, done = false;
      if (a.kind === 'spring') {
        const r = a.spring(dt);
        v = lerp(a.from, a.to, r.pos);
        done = r.done;
      } else {
        const p = clamp((now - a.start) / a.dur, 0, 1);
        v = lerp(a.from, a.to, a.ease(p));
        done = p >= 1;
      }

      if (a.transform) this.t[prop] = v;
      else { this.s[prop] = v; applyStyle(this.el, prop, v); }

      if (done) {
        if (a.transform) this.t[prop] = a.to;
        else { this.s[prop] = a.raw; applyStyle(this.el, prop, a.raw); }
        delete this.a[prop];
      } else active = true;
    }
    return active;
  }

  settled() {
    return new Promise((res) => {
      const chk = () => this.raf ? raf(chk) : res();
      chk();
    });
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// 6 · Presets & Variants
// ═══════════════════════════════════════════════════════════════════════════
const SPRING   = { type: 'spring', stiffness: 260, damping: 26, mass: 1 };
const SPRING_B = { type: 'spring', stiffness: 400, damping: 15, mass: 1 };
const SPRING_G = { type: 'spring', stiffness: 180, damping: 28, mass: 1 };
const TWEEN    = { type: 'tween',  duration: 0.4, ease: [0.16, 1, 0.3, 1] };

const PRESETS = {
  'fade-up':     { initial: { opacity: 0, y: 24 },  animate: { opacity: 1, y: 0 },  transition: SPRING },
  'fade-down':   { initial: { opacity: 0, y: -24 }, animate: { opacity: 1, y: 0 },  transition: SPRING },
  'fade-in':     { initial: { opacity: 0 },         animate: { opacity: 1 },        transition: TWEEN  },
  'slide-right': { initial: { opacity: 0, x: -32 }, animate: { opacity: 1, x: 0 },  transition: SPRING },
  'slide-left':  { initial: { opacity: 0, x: 32 },  animate: { opacity: 1, x: 0 },  transition: SPRING },
  'scale-in':    { initial: { opacity: 0, scale: 0.94 }, animate: { opacity: 1, scale: 1 }, transition: SPRING },
  'scale-up':    { initial: { opacity: 0, scale: 0.88 }, animate: { opacity: 1, scale: 1 }, transition: SPRING_B },
  'pop':         { initial: { opacity: 0, scale: 0.6 },  animate: { opacity: 1, scale: 1 }, transition: SPRING_B },
  'blur-in':     { initial: { opacity: 0, y: 8, filter: 'blur(12px)' },
                   animate: { opacity: 1, y: 0, filter: 'blur(0px)' }, transition: TWEEN },
  'notice-in':   { initial: { opacity: 0, y: -12, scale: 0.98 },
                   animate: { opacity: 1, y: 0, scale: 1 }, transition: SPRING_B },
};

const VARIANTS = {};

function registerVariants(obj) {
  if (!obj || typeof obj !== 'object') return;
  Object.assign(VARIANTS, obj);
}

function resolveVariant(name, state) {
  const v = VARIANTS[name];
  if (!v) return null;
  return v[state] || null;
}

// ═══════════════════════════════════════════════════════════════════════════
// 7 · Orchestrator — parent staggers children
// ═══════════════════════════════════════════════════════════════════════════
function orchestrate(parent, cfg) {
  const children = Array.from(parent.children).filter(
    (c) => c.matches('[data-motion], [data-motion-variant]')
  );
  if (!children.length) return;

  const {
    when = 'beforeChildren',
    delayChildren = 0,
    staggerChildren = 0,
    staggerDirection = 1,
  } = cfg || {};

  if (when === 'afterChildren') {
    const total = delayChildren + staggerChildren * (children.length - 1);
    if (parent._mo) parent._mo.animate(
      resolveVariant(parent.dataset.motionVariant, parent.dataset.motionAnimate) || {},
      readJSON(parent.dataset.motionTransition, parent),
      { delay: total }
    );
    return;
  }

  children.forEach((child, i) => {
    const d = delayChildren + staggerChildren * (staggerDirection >= 0 ? i : children.length - 1 - i);
    if (child._mo) {
      const tgt = child._moTarget || {};
      const tr  = child._moTransition || {};
      child._mo.animate(tgt, tr, { delay: d });
    } else {
      (child._moDeferred = child._moDeferred || []).push({ delay: d });
    }
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// 8 · Hydrate one element from its data-* attributes
// ═══════════════════════════════════════════════════════════════════════════
function hydrate(el, deferredCfg) {
  if (el._mo) return el._mo;
  const mo = new MotionElement(el);
  el._mo = mo;

  const variantName   = el.dataset.motionVariant;
  const inlinePreset  = el.dataset.motion;
  const inlineInitial = readJSON(el.dataset.motionInitial, el);
  const inlineAnimate = readJSON(el.dataset.motionAnimate, el);
  const keyframes     = readJSON(el.dataset.motionKeyframes, el);
  const transition    = readJSON(el.dataset.motionTransition, el)
    || (el.dataset.motionDelay || el.dataset.motionDuration ? {
      delay:    el.dataset.motionDelay    ? parseFloat(el.dataset.motionDelay) / 1000    : undefined,
      duration: el.dataset.motionDuration ? parseFloat(el.dataset.motionDuration) / 1000 : undefined,
    } : null);

  const once  = el.dataset.motionOnce !== 'false';
  const threshold = parseFloat(el.dataset.motionThreshold ?? '0.08');

  // ── Resolve the "animate" target ──
  let initial, animate, exit;
  if (variantName) {
    const initialName = el.dataset.motionInitial || 'hidden';
    const animateName = el.dataset.motionAnimate || 'visible';
    const exitName    = el.dataset.motionExit    || initialName;
    initial = resolveVariant(variantName, initialName);
    animate = resolveVariant(variantName, animateName);
    exit    = resolveVariant(variantName, exitName);
  } else if (inlinePreset && PRESETS[inlinePreset]) {
    initial = PRESETS[inlinePreset].initial;
    animate = PRESETS[inlinePreset].animate;
    exit    = { opacity: 0, y: -8, transition: { duration: 0.18 } };
  } else if (inlineAnimate) {
    initial = inlineInitial || {};
    animate = inlineAnimate;
    exit    = { opacity: 0 };
  } else if (keyframes) {
    initial = keyframes[0];
    animate = keyframes;
    exit    = { opacity: 0 };
  } else {
    el.setAttribute('data-motion-ready', '1');
    return mo;
  }

  const mergedTransition = Object.assign(
    {},
    (animate && animate.transition) || (initial && initial.transition) || {},
    transition || {}
  );

  // ── Seed initial state before first paint (prevents FOUC) ──
  if (initial) {
    const initVals = Object.assign({}, initial);
    delete initVals.transition;
    mo.seed(initVals);
  }
  el.setAttribute('data-motion-ready', '1');

  // Stash targets for orchestration
  mo._initial = initial;
  mo._animate = animate;
  mo._exit    = exit;
  mo._transition = mergedTransition;
  el._moTarget = animate;
  el._moTransition = mergedTransition;

  // ── Visibility trigger ──
  const inView = () => {
    const r = el.getBoundingClientRect();
    return r.top < innerHeight * 0.9 && r.bottom > 0;
  };

  const play = (delay = 0) => {
    if (Array.isArray(animate)) {
      playKeyframes(mo, animate, mergedTransition);
    } else {
      mo.animate(animate, mergedTransition, { delay });
    }
  };

  // Deferred by orchestration?
  const deferred = deferredCfg && deferredCfg.length ? deferredCfg.shift() : null;

  if (inView() || !('IntersectionObserver' in window)) {
    const d = deferred ? deferred.delay : 0;
    raf(() => play(d));
  } else {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          const d = deferred ? deferred.delay : 0;
          play(d);
          if (once) io.unobserve(el);
        } else if (!once) {
          mo.seed(mo._initial);
        }
      });
    }, { threshold, rootMargin: '0px 0px -6% 0px' });
    io.observe(el);
    el._moIO = io;
  }

  // Orchestration: this element staggers its children
  const orchCfg = readJSON(el.dataset.motionOrchestrate, el);
  if (orchCfg) {
    const waitAndOrchestrate = () => {
      const delay = (mergedTransition.delay || 0) * 1000 + 30;
      setTimeout(() => orchestrate(el, orchCfg), delay);
    };
    if (inView()) waitAndOrchestrate();
    else {
      const io2 = new IntersectionObserver((entries) => {
        entries.forEach((e) => { if (e.isIntersecting) { waitAndOrchestrate(); io2.disconnect(); } });
      }, { threshold });
      io2.observe(el);
    }
  }

  // ── Gestures: whileHover / whileTap ──
  wireGestures(el, mo);

  // ── Layout FLIP ──
  if (el.hasAttribute('data-motion-layout')) wireLayout(el);

  // ── Drag ──
  if (el.hasAttribute('data-motion-drag')) wireDrag(el, mo);

  return mo;
}

// ─── Keyframes ───
async function playKeyframes(mo, frames, tr) {
  const times = tr.times || frames.map((_, i) => i / (frames.length - 1));
  const total = tr.duration || 0.6;
  for (let i = 1; i < frames.length; i++) {
    const segDuration = (times[i] - times[i - 1]) * total;
    const target = Object.assign({}, frames[i]);
    delete target.transition;
    await mo.animate(target, Object.assign({}, tr, { duration: segDuration, type: 'tween' }));
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// 9 · Gestures
// ═══════════════════════════════════════════════════════════════════════════
function wireGestures(el, mo) {
  const hoverTarget = readJSON(el.dataset.motionWhileHover, el)
    || (el.dataset.motionWhileHoverVariant
        ? resolveVariant(el.dataset.motionVariant, el.dataset.motionWhileHoverVariant) : null);
  const tapTarget = readJSON(el.dataset.motionWhileTap, el)
    || (el.dataset.motionWhileTapVariant
        ? resolveVariant(el.dataset.motionVariant, el.dataset.motionWhileTapVariant) : null);

  if (!hoverTarget && !tapTarget) return;

  const gestureTransition = readJSON(el.dataset.motionGestureTransition, el) || SPRING_B;

  let baseSnap = null;
  const snapshotBase = () => {
    if (!baseSnap) baseSnap = mo.snapshot();
  };
  const restoreBase = () => {
    if (!baseSnap) return;
    mo.animate({
      ...baseSnap.transform,
      ...baseSnap.style,
    }, gestureTransition);
    baseSnap = null;
  };

  if (hoverTarget) {
    const hEnter = () => { snapshotBase(); mo.animate(hoverTarget, gestureTransition); };
    const hLeave = () => { restoreBase(); };
    if (matchMedia('(hover: hover) and (pointer: fine)').matches) {
      el.addEventListener('pointerenter', hEnter);
      el.addEventListener('pointerleave', hLeave);
      el.addEventListener('focusin',  hEnter);
      el.addEventListener('focusout', hLeave);
    }
  }

  if (tapTarget) {
    el.addEventListener('pointerdown', () => {
      if (!baseSnap) snapshotBase();
      mo.animate(tapTarget, gestureTransition);
    });
    ['pointerup','pointercancel','pointerleave'].forEach((ev) =>
      el.addEventListener(ev, () => {
        if (!el.matches(':hover') && hoverTarget) { restoreBase(); return; }
        if (hoverTarget) mo.animate(hoverTarget, gestureTransition);
        else restoreBase();
      })
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// 10 · Layout FLIP
// ═══════════════════════════════════════════════════════════════════════════
function wireLayout(el) {
  let prev = el.getBoundingClientRect();
  const measure = () => {
    const next = el.getBoundingClientRect();
    const dx = prev.left - next.left;
    const dy = prev.top  - next.top;
    const sx = prev.width  / Math.max(next.width, 1);
    const sy = prev.height / Math.max(next.height, 1);
    prev = next;
    if (Math.abs(dx) < 0.5 && Math.abs(dy) < 0.5 &&
        Math.abs(sx - 1) < 0.005 && Math.abs(sy - 1) < 0.005) return;
    el.style.transformOrigin = 'top left';
    el.style.transform = `translate(${dx}px, ${dy}px) scale(${sx}, ${sy})`;
    el.setAttribute('data-mo-flip', '');
    raf(() => {
      el.style.transform = '';
      el.style.transition = 'transform 420ms cubic-bezier(0.22, 1, 0.36, 1)';
      setTimeout(() => { el.style.transition = ''; el.removeAttribute('data-mo-flip'); }, 440);
    });
  };
  new ResizeObserver(measure).observe(el);
  addEventListener('resize', measure, { passive: true });
}

// ═══════════════════════════════════════════════════════════════════════════
// 11 · Drag
// ═══════════════════════════════════════════════════════════════════════════
function wireDrag(el, mo) {
  const c = readJSON(el.dataset.motionDragConstraints, el) || { left: -Infinity, right: Infinity, top: -Infinity, bottom: Infinity };
  const axis = el.dataset.motionDragAxis || 'both';
  let dragging = false, sx = 0, sy = 0, ox = 0, oy = 0;

  el.style.touchAction = axis === 'x' ? 'pan-y' : axis === 'y' ? 'pan-x' : 'none';
  el.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    dragging = true;
    el.setPointerCapture(e.pointerId);
    sx = e.clientX; sy = e.clientY;
    ox = mo.t.x || 0; oy = mo.t.y || 0;
    el.style.cursor = 'grabbing';
  });
  el.addEventListener('pointermove', (e) => {
    if (!dragging) return;
    let x = ox + (e.clientX - sx);
    let y = oy + (e.clientY - sy);
    x = clamp(x, c.left ?? -Infinity, c.right ?? Infinity);
    y = clamp(y, c.top  ?? -Infinity, c.bottom ?? Infinity);
    if (axis === 'x') y = 0;
    if (axis === 'y') x = 0;
    mo.animate({ x, y }, { type: 'spring', stiffness: 1200, damping: 60, mass: 0.4 });
  });
  const end = () => {
    if (!dragging) return;
    dragging = false;
    el.style.cursor = '';
    const snap = el.dataset.motionDragSnap;
    if (snap === 'true' || snap === '') {
      mo.animate({ x: 0, y: 0 }, { type: 'spring', stiffness: 300, damping: 22 });
    }
  };
  ['pointerup','pointercancel','lostpointercapture'].forEach((ev) => el.addEventListener(ev, end));
}

// ═══════════════════════════════════════════════════════════════════════════
// 12 · AnimatePresence — exit before navigation
// ═══════════════════════════════════════════════════════════════════════════
const EXIT_DEFAULT = { opacity: 0, y: -8, transition: { duration: 0.18, ease: 'expoIn' } };
const EXIT_MS_CAP = 500;

function runExits() {
  const els = Array.from(document.querySelectorAll('[data-motion], [data-motion-variant]'))
    .filter((el) => el._mo && !el.hasAttribute('data-mo-exit-done'));
  const promises = els.map((el) => {
    el.setAttribute('data-mo-exit-done', '');
    const exitTarget = el._mo._exit || EXIT_DEFAULT;
    const tr = Object.assign({}, exitTarget.transition || {}, { type: 'tween', duration: 0.18 });
    return el._mo.animate(exitTarget, tr);
  });
  return Promise.race([
    Promise.all(promises),
    new Promise((r) => setTimeout(r, EXIT_MS_CAP)),
  ]);
}

function shouldIntercept(link) {
  if (!link || !link.href) return false;
  if (link.target && link.target !== '_self') return false;
  if (link.hasAttribute('download')) return false;
  if (link.dataset.noMotion !== undefined) return false;
  if (link.host !== location.host) return false;
  const h = link.getAttribute('href');
  if (!h || h.startsWith('#') || h.startsWith('mailto:') || h.startsWith('tel:')) return false;
  return true;
}

document.addEventListener('click', async (e) => {
  if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
  const link = e.target.closest('a');
  if (!shouldIntercept(link)) return;
  e.preventDefault();
  document.documentElement.classList.add('mo-exiting');
  const href = link.href;
  const go = () => { window.location.href = href; };
  if (document.startViewTransition && !REDUCED) {
    const p = runExits();
    // View Transitions can throw InvalidStateError if a previous transition
    // is still active — wrap in try/catch and fall back to a normal nav.
    try {
      document.startViewTransition(async () => { await p; go(); });
    } catch (err) {
      await p;
      go();
    }
  } else {
    await runExits();
    go();
  }
});

document.addEventListener('submit', (e) => {
  const form = e.target;
  if (form.dataset.noMotion !== undefined) return;
  document.documentElement.classList.add('mo-exiting');
  runExits();
}, true);

// ═══════════════════════════════════════════════════════════════════════════
// 13 · Boot
// ═══════════════════════════════════════════════════════════════════════════
function loadVariants() {
  const node = document.getElementById('motion-variants');
  if (!node) return;
  try { registerVariants(JSON.parse(node.textContent)); }
  catch (err) { console.warn('[motion] invalid variants JSON:', err); }
}

function boot(root) {
  loadVariants();
  const scope = root || document;
  scope.querySelectorAll('[data-motion], [data-motion-variant]').forEach((el) => hydrate(el));
}

window.Motion = {
  refresh: (root) => boot(root),
  registerVariants,
  animate: (el, target, transition) => {
    const m = el._mo || hydrate(el);
    return m.animate(target, transition);
  },
  reduce: () => REDUCED,
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => boot());
} else {
  boot();
}
})();