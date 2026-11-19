/* URM Creator Studio — motion runtime.
 *
 * Deterministic canvas renderer for creative-led ("motion") scenes. Python (urmstudio/motion.py) serves this
 * file to a headless Chromium on 127.0.0.1, together with a job spec. The page draws every frame from a pure
 * function of time (no wall clock, seeded randomness), so a render is reproducible frame-for-frame.
 *
 * Jobs (?job=…):
 *   layout     run every scene's layout once; report text boxes and sound-design events
 *   scene:N    render scene N frame by frame and POST each PNG frame
 *   score      synthesise the original soundtrack (score.js) and POST it as WAV
 *
 * Text is drawn with the canvas text engine (HarfBuzz shaping + Unicode bidi in Chromium), so Arabic letters
 * join and mixed Arabic/Latin runs are ordered correctly. Layout never reverses strings.
 */
"use strict";

const Q = new URLSearchParams(location.search);
const JOB = Q.get("job") || "layout";
let SPEC, W, H, FPS, S, LOOK, PAL, SAFE, R, cv, ctx;

// ---------------------------------------------------------------- math & colour
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, p) => a + (b - a) * p;
const prog = (t, a, d) => clamp((t - a) / Math.max(1e-6, d));
const E = {
  out: p => 1 - Math.pow(1 - p, 3),
  out5: p => 1 - Math.pow(1 - p, 5),
  inOut: p => (p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2),
  in: p => p * p * p,
  back: p => { const c1 = 1.4, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); },
  expo: p => (p >= 1 ? 1 : 1 - Math.pow(2, -10 * p)),
  sine: p => -(Math.cos(Math.PI * p) - 1) / 2,
};
function rng(seed) {
  let a = (seed >>> 0) || 1;
  return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
function hex2rgb(h) { h = String(h || "#000000").replace("#", ""); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); }
function rgba(h, a) { const [r, g, b] = hex2rgb(h); return `rgba(${r},${g},${b},${a})`; }
function mix(h1, h2, p) {
  const a = hex2rgb(h1), b = hex2rgb(h2);
  return "#" + a.map((v, i) => Math.round(lerp(v, b[i], p)).toString(16).padStart(2, "0")).join("");
}
const AR_RE = /[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]/;
const LAT_RE = /[A-Za-z]/;
const isAr = s => AR_RE.test(s || "");

// ---------------------------------------------------------------- reporting (QC + sound design)
let REG = [], EVENTS = [];
function reg(text, x1, y1, x2, y2, tFull, tEnd) {
  REG.push({ text, bbox: [Math.round(x1), Math.round(y1), Math.round(x2), Math.round(y2)],
    full_from: +tFull.toFixed(3), end: +tEnd.toFixed(3) });
}
function ev(t, type, strength = 1) { EVENTS.push({ t: +t.toFixed(3), type, strength }); }

// ---------------------------------------------------------------- fonts & text
function fontFor(text, role) {
  const f = LOOK.fonts;
  const head = role === "head";
  const prim = isAr(text) ? (head ? f.ar_head : f.ar_body) : (head ? f.lat_head : f.lat_body);
  const sec = isAr(text) ? (head ? f.lat_head : f.lat_body) : (head ? f.ar_head : f.ar_body);
  return `"${prim}", "${sec}", "Noto Naskh Arabic", "Inter", sans-serif`;
}
function setFont(size, weight, text, role) { ctx.font = `${weight} ${Math.round(size)}px ${fontFor(text, role)}`; }

/** Lay out a text block: greedy word wrap, shrink until it fits maxLines and maxW. */
function tb(text, o) {
  text = String(text || "");
  const rtl = isAr(text);
  const role = o.role || "head";
  const weight = o.weight || (role === "head" ? 800 : 500);
  let size = o.size;
  const maxW = o.maxW, maxLines = o.maxLines || 3, minSize = o.minSize || size * 0.45;
  let lines;
  const wrap = (lim) => {
    const out = [];
    for (const para of text.split("\n")) {
      const words = para.split(/\s+/).filter(Boolean);
      let cur = [];
      for (const w of words) {
        const cand = cur.concat([w]).join(" ");
        if (cur.length && ctx.measureText(cand).width > lim) { out.push(cur); cur = [w]; } else cur.push(w);
      }
      if (cur.length) out.push(cur);
    }
    return out;
  };
  for (let guard = 0; guard < 40; guard++) {
    setFont(size, weight, text, role);
    ctx.direction = rtl ? "rtl" : "ltr";
    const sp = ctx.measureText(" ").width;
    lines = wrap(maxW);
    if (lines.length > 1 && o.balance !== false) {
      // balanced lines: the narrowest width that keeps the same number of lines (no lone last word)
      let lo = maxW * 0.4, hi = maxW;
      for (let k = 0; k < 14; k++) { const mid = (lo + hi) / 2; if (wrap(mid).length > lines.length) lo = mid; else hi = mid; }
      lines = wrap(hi);
    }
    const widest = Math.max(...lines.map(l => ctx.measureText(l.join(" ")).width));
    if ((lines.length <= maxLines && widest <= maxW) || size <= minSize) {
      const lh = size * (o.lh || (rtl ? 1.42 : 1.12));
      const L = lines.map(ws => {
        const s = ws.join(" ");
        return { s, w: ctx.measureText(s).width, mixed: rtl && LAT_RE.test(s),
          words: ws.map(x => ({ s: x, w: ctx.measureText(x).width })) };
      });
      return { text, rtl, size, weight, role, lh, sp, lines: L, w: Math.max(...L.map(l => l.w)), h: L.length * lh,
        color: o.color || PAL.text, align: o.align || "center", hl: o.highlight || null };
    }
    size *= 0.93;
  }
}

/** Absolute box of a laid-out block whose anchor is (x, y=top). */
function blockBox(b, x, y) {
  let x1, x2;
  if (b.align === "center") { x1 = x - b.w / 2; x2 = x + b.w / 2; }
  else if (b.rtl) { x2 = x; x1 = x - b.w; } else { x1 = x; x2 = x + b.w; }
  return [x1, y, x2, y + b.h];
}

/**
 * Draw a block with a kinetic entrance.
 * a.type: rise (lines rise out of a mask) | words (word by word) | fade | pop | none
 * a.t0 start, a.stagger per line/word, a.out start of the exit (or null), a.dur entrance length
 */
function drawBlock(b, x, y, t, a) {
  if (!b) return;
  const type = a.type || "rise", t0 = a.t0 || 0, stg = a.stagger != null ? a.stagger : 0.09, dur = a.dur || 0.6;
  const outP = a.out != null ? E.in(prog(t, a.out, a.outDur || 0.3)) : 0;
  if (outP >= 1) return;
  ctx.save();
  ctx.direction = b.rtl ? "rtl" : "ltr";
  ctx.textBaseline = "middle";
  setFont(b.size, b.weight, b.text, b.role);
  if (a.shadow !== false) { ctx.shadowColor = "rgba(0,0,0,0.35)"; ctx.shadowBlur = 18 * S; ctx.shadowOffsetY = 4 * S; }
  let wordIndex = 0;
  b.lines.forEach((ln, i) => {
    let lx;
    if (b.align === "center") lx = x - ln.w / 2; else if (b.rtl) lx = x - ln.w; else lx = x;
    const cy = y + i * b.lh + b.lh / 2;
    const perWord = (type === "words" || b.hl) && !ln.mixed;
    const p = E.out5(prog(t, t0 + i * stg, dur));
    let alpha = 1, dy = 0, sc = 1;
    if (type === "rise") { dy = (1 - p) * b.lh * 0.95; alpha = clamp(p * 1.6); }
    else if (type === "fade") { alpha = p; dy = (1 - p) * 14 * S; }
    else if (type === "pop") { const q = E.back(prog(t, t0 + i * stg, dur)); sc = lerp(0.6, 1, q); alpha = clamp(p * 1.5); }
    else if (type === "words") { alpha = 1; }
    dy -= outP * b.lh * 0.35;
    alpha *= 1 - outP;
    ctx.save();
    if (type === "rise") { ctx.beginPath(); ctx.rect(lx - 60 * S, cy - b.lh * 0.62, ln.w + 120 * S, b.lh * 1.24); ctx.clip(); }
    if (sc !== 1) { ctx.translate(lx + ln.w / 2, cy); ctx.scale(sc, sc); ctx.translate(-(lx + ln.w / 2), -cy); }
    if (!perWord) {
      ctx.globalAlpha = alpha;
      ctx.fillStyle = (b.hl && ln.mixed && ln.s.includes(b.hl)) ? PAL.accent : b.color;
      ctx.textAlign = "left";
      ctx.direction = b.rtl ? "rtl" : "ltr";
      // with direction rtl and textAlign left the run still starts at lx: draw with explicit alignment instead
      if (b.rtl) { ctx.textAlign = "right"; ctx.fillText(ln.s, lx + ln.w, cy + dy); }
      else ctx.fillText(ln.s, lx, cy + dy);
      wordIndex += ln.words.length;
    } else {
      let cur = b.rtl ? lx + ln.w : lx;
      ln.words.forEach((wd) => {
        const wx1 = b.rtl ? cur - wd.w : cur;
        let wa = alpha, wdy = dy;
        if (type === "words") {
          const q = E.out5(prog(t, t0 + wordIndex * stg, 0.45));
          wa = clamp(q * 1.8) * (1 - outP); wdy = (1 - q) * b.lh * 0.45 - outP * b.lh * 0.35;
        }
        const isHl = b.hl && b.hl.split(/\s+/).includes(wd.s);
        if (isHl && wa > 0) {
          const hp = E.out(prog(t, (a.hlAt != null ? a.hlAt : t0 + 0.55), 0.5));
          ctx.save(); ctx.shadowColor = "transparent"; ctx.globalAlpha = wa * 0.9; ctx.fillStyle = PAL.accent;
          const mh = b.size * 0.11, my = cy + b.size * 0.5 + wdy;
          const mw = (wd.w + 16 * S) * hp;
          ctx.beginPath(); ctx.roundRect(b.rtl ? wx1 + wd.w + 8 * S - mw : wx1 - 8 * S, my, mw, mh, mh / 2); ctx.fill();
          ctx.restore();
        }
        ctx.globalAlpha = wa;
        ctx.fillStyle = isHl ? PAL.hl : b.color;
        ctx.textAlign = "left";
        ctx.direction = b.rtl ? "rtl" : "ltr";
        if (b.rtl) { ctx.textAlign = "right"; ctx.fillText(wd.s, wx1 + wd.w, cy + wdy); } else ctx.fillText(wd.s, wx1, cy + wdy);
        cur = b.rtl ? cur - wd.w - b.sp : cur + wd.w + b.sp;
        wordIndex++;
      });
    }
    ctx.restore();
  });
  ctx.restore();
}
/** Time at which the whole block is visible (for QC reading-time). */
function fullAt(b, a) {
  const n = a.type === "words" ? b.lines.reduce((s, l) => s + l.words.length, 0) : b.lines.length;
  return (a.t0 || 0) + Math.max(0, n - 1) * (a.stagger != null ? a.stagger : 0.09) + (a.dur || 0.6) * 0.8;
}
function place(b, x, y, a, D) { const bx = blockBox(b, x, y); reg(b.text, ...bx, fullAt(b, a), a.out != null ? a.out + 0.2 : D); }

// ---------------------------------------------------------------- shapes & icons
function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
function ring(x, y, r, lw, color, p = 1, rot = -Math.PI / 2, alpha = 1) {
  if (p <= 0) return;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.lineCap = "round";
  ctx.beginPath(); ctx.arc(x, y, r, rot, rot + Math.PI * 2 * clamp(p)); ctx.stroke(); ctx.restore();
}
function dot(x, y, r, color, alpha = 1) {
  const ga = ctx.globalAlpha; ctx.globalAlpha = ga * alpha; ctx.fillStyle = color;
  ctx.beginPath(); ctx.arc(x, y, Math.max(0.1, r), 0, Math.PI * 2); ctx.fill(); ctx.globalAlpha = ga;
}
function glow(x, y, r, color, a = 0.5) {
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, rgba(color, a)); g.addColorStop(1, rgba(color, 0));
  ctx.fillStyle = g; ctx.fillRect(x - r, y - r, 2 * r, 2 * r);
}
function dotGrid(x, y, cols, rows, gap, r, color, alpha) {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = color;
  for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) { ctx.beginPath(); ctx.arc(x + i * gap, y + j * gap, r, 0, 7); ctx.fill(); }
  ctx.restore();
}
function plus(x, y, s, lw, color, alpha = 1, rot = 0) {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y); ctx.rotate(rot); ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.lineCap = "round";
  ctx.beginPath(); ctx.moveTo(-s, 0); ctx.lineTo(s, 0); ctx.moveTo(0, -s); ctx.lineTo(0, s); ctx.stroke(); ctx.restore();
}

/** Line icons on a 24-unit grid. */
const ICONS = {
  globe: c => { c.arc(12, 12, 9.5, 0, 7); c.moveTo(12, 2.5); c.ellipse(12, 12, 4.2, 9.5, 0, -Math.PI / 2, Math.PI * 1.5); c.moveTo(2.5, 12); c.lineTo(21.5, 12); c.moveTo(4, 7.5); c.lineTo(20, 7.5); c.moveTo(4, 16.5); c.lineTo(20, 16.5); },
  book: c => { c.moveTo(12, 6); c.quadraticCurveTo(7.5, 3.5, 2.5, 5); c.lineTo(2.5, 19); c.quadraticCurveTo(7.5, 17.5, 12, 20); c.quadraticCurveTo(16.5, 17.5, 21.5, 19); c.lineTo(21.5, 5); c.quadraticCurveTo(16.5, 3.5, 12, 6); c.lineTo(12, 20); },
  chat: c => { c.roundRect(2.5, 3.5, 19, 13, 3.5); c.moveTo(7, 16.5); c.lineTo(6, 21); c.lineTo(11, 16.5); c.moveTo(8, 10); c.arc(8, 10, .3, 0, 7); c.moveTo(12, 10); c.arc(12, 10, .3, 0, 7); c.moveTo(16, 10); c.arc(16, 10, .3, 0, 7); },
  cap: c => { c.moveTo(12, 4); c.lineTo(22.5, 9); c.lineTo(12, 14); c.lineTo(1.5, 9); c.closePath(); c.moveTo(6, 11); c.lineTo(6, 16); c.quadraticCurveTo(12, 20, 18, 16); c.lineTo(18, 11); c.moveTo(22.5, 9); c.lineTo(22.5, 15); },
  award: c => { c.arc(12, 9, 6.2, 0, 7); c.moveTo(8.5, 14); c.lineTo(7, 21.5); c.lineTo(12, 19); c.lineTo(17, 21.5); c.lineTo(15.5, 14); c.moveTo(14.5, 9); c.arc(12, 9, 2.5, 0, 7); },
  users: c => { c.arc(9, 8, 3.6, 0, 7); c.moveTo(2.5, 20); c.quadraticCurveTo(2.5, 13.5, 9, 13.5); c.quadraticCurveTo(15.5, 13.5, 15.5, 20); c.moveTo(19.6, 8.8); c.arc(17, 8.8, 2.6, 0, 7); c.moveTo(17.5, 13.6); c.quadraticCurveTo(21.5, 14, 21.5, 19); },
  star: c => { for (let i = 0; i < 10; i++) { const r = i % 2 ? 4.3 : 10, a = -Math.PI / 2 + i * Math.PI / 5; const x = 12 + r * Math.cos(a), y = 12.5 + r * Math.sin(a); i ? c.lineTo(x, y) : c.moveTo(x, y); } c.closePath(); },
  check: c => { c.arc(12, 12, 9.5, 0, 7); c.moveTo(7.5, 12.5); c.lineTo(10.7, 15.5); c.lineTo(16.5, 9); },
  shield: c => { c.moveTo(12, 2.5); c.lineTo(20, 5.5); c.lineTo(20, 11.5); c.quadraticCurveTo(20, 18.5, 12, 21.5); c.quadraticCurveTo(4, 18.5, 4, 11.5); c.lineTo(4, 5.5); c.closePath(); c.moveTo(8.3, 12); c.lineTo(11, 14.6); c.lineTo(15.8, 9.4); },
  clock: c => { c.arc(12, 12, 9.5, 0, 7); c.moveTo(12, 6.5); c.lineTo(12, 12); c.lineTo(16, 14.2); },
  heart: c => { c.moveTo(12, 20); c.bezierCurveTo(-1, 11, 5, 1.5, 12, 7.5); c.bezierCurveTo(19, 1.5, 25, 11, 12, 20); },
  pin: c => { c.moveTo(12, 21.5); c.bezierCurveTo(5, 14, 4.5, 11, 4.5, 9.5); c.arc(12, 9.5, 7.5, Math.PI, 0); c.bezierCurveTo(19.5, 11, 19, 14, 12, 21.5); c.moveTo(14.8, 9.5); c.arc(12, 9.5, 2.8, 0, 7); },
  calendar: c => { c.roundRect(3, 5, 18, 16, 2.5); c.moveTo(3, 10); c.lineTo(21, 10); c.moveTo(8, 3); c.lineTo(8, 7); c.moveTo(16, 3); c.lineTo(16, 7); },
  phone: c => { c.roundRect(6.5, 2.5, 11, 19, 2.5); c.moveTo(10.5, 18.5); c.lineTo(13.5, 18.5); },
  spark: c => { c.moveTo(12, 2.5); c.quadraticCurveTo(13, 11, 21.5, 12); c.quadraticCurveTo(13, 13, 12, 21.5); c.quadraticCurveTo(11, 13, 2.5, 12); c.quadraticCurveTo(11, 11, 12, 2.5); },
  chart: c => { c.moveTo(3, 21); c.lineTo(21, 21); c.moveTo(6, 17); c.lineTo(6, 13); c.moveTo(11, 17); c.lineTo(11, 9); c.moveTo(16, 17); c.lineTo(16, 11); c.moveTo(4, 9); c.lineTo(10, 4.5); c.lineTo(14, 7); c.lineTo(20.5, 3); c.moveTo(16.5, 3); c.lineTo(20.5, 3); c.lineTo(20.5, 6.5); },
  plane: c => { c.moveTo(21, 3.5); c.lineTo(2.5, 11); c.lineTo(9.5, 13.5); c.lineTo(12, 20.5); c.lineTo(21, 3.5); c.moveTo(9.5, 13.5); c.lineTo(21, 3.5); },
  bulb: c => { c.moveTo(9, 17); c.bezierCurveTo(9, 13.5, 5, 12.5, 5, 9); c.arc(12, 9, 7, Math.PI, 0); c.bezierCurveTo(19, 12.5, 15, 13.5, 15, 17); c.closePath(); c.moveTo(9.5, 20.5); c.lineTo(14.5, 20.5); },
  trophy: c => { c.moveTo(7, 3.5); c.lineTo(17, 3.5); c.lineTo(17, 9); c.quadraticCurveTo(17, 14, 12, 14); c.quadraticCurveTo(7, 14, 7, 9); c.closePath(); c.moveTo(7, 5.5); c.quadraticCurveTo(2.5, 5.5, 3.5, 9); c.quadraticCurveTo(4.5, 11, 7.5, 11.5); c.moveTo(17, 5.5); c.quadraticCurveTo(21.5, 5.5, 20.5, 9); c.quadraticCurveTo(19.5, 11, 16.5, 11.5); c.moveTo(12, 14); c.lineTo(12, 18); c.moveTo(8, 20.5); c.lineTo(16, 20.5); c.lineTo(15, 18); c.lineTo(9, 18); c.closePath(); },
  briefcase: c => { c.roundRect(2.5, 7, 19, 13.5, 2.5); c.moveTo(8.5, 7); c.lineTo(8.5, 4.5); c.lineTo(15.5, 4.5); c.lineTo(15.5, 7); c.moveTo(2.5, 12.5); c.lineTo(21.5, 12.5); },
  home: c => { c.moveTo(3, 11); c.lineTo(12, 3.5); c.lineTo(21, 11); c.moveTo(5.5, 9); c.lineTo(5.5, 20.5); c.lineTo(18.5, 20.5); c.lineTo(18.5, 9); c.moveTo(10, 20.5); c.lineTo(10, 14.5); c.lineTo(14, 14.5); c.lineTo(14, 20.5); },
  laptop: c => { c.roundRect(4.5, 4.5, 15, 11, 1.5); c.moveTo(2, 19.5); c.lineTo(22, 19.5); c.lineTo(20.5, 15.5); c.moveTo(2, 19.5); c.lineTo(3.5, 15.5); },
  gift: c => { c.rect(3.5, 9, 17, 4); c.rect(5, 13, 14, 8); c.moveTo(12, 9); c.lineTo(12, 21); c.moveTo(12, 9); c.bezierCurveTo(9, 3, 4.5, 6, 8, 9); c.moveTo(12, 9); c.bezierCurveTo(15, 3, 19.5, 6, 16, 9); },
  mail: c => { c.roundRect(2.5, 5, 19, 14, 2); c.moveTo(3, 6); c.lineTo(12, 13); c.lineTo(21, 6); },
  play: c => { c.arc(12, 12, 9.5, 0, 7); c.moveTo(10, 8.5); c.lineTo(16, 12); c.lineTo(10, 15.5); c.closePath(); },
  leaf: c => { c.moveTo(4, 20); c.bezierCurveTo(4, 9, 11, 4, 20.5, 3.5); c.bezierCurveTo(20, 13, 15, 20, 4, 20); c.moveTo(4, 20); c.lineTo(13, 11); },
  rocket: c => { c.moveTo(12, 2.5); c.bezierCurveTo(17, 6, 17, 12, 15.5, 16); c.lineTo(8.5, 16); c.bezierCurveTo(7, 12, 7, 6, 12, 2.5); c.moveTo(13.6, 9); c.arc(12, 9, 1.6, 0, 7); c.moveTo(8.5, 13); c.lineTo(5.5, 17.5); c.lineTo(9, 17); c.moveTo(15.5, 13); c.lineTo(18.5, 17.5); c.lineTo(15, 17); c.moveTo(10.5, 19); c.lineTo(12, 22); c.lineTo(13.5, 19); },
  cart: c => { c.moveTo(2.5, 4); c.lineTo(5.5, 4); c.lineTo(8, 15.5); c.lineTo(18.5, 15.5); c.lineTo(20.5, 7.5); c.lineTo(6.3, 7.5); c.moveTo(10.7, 19.5); c.arc(9.5, 19.5, 1.2, 0, 7); c.moveTo(18.2, 19.5); c.arc(17, 19.5, 1.2, 0, 7); },
  camera: c => { c.roundRect(2.5, 7, 19, 13, 2.5); c.moveTo(8, 7); c.lineTo(9.5, 4.5); c.lineTo(14.5, 4.5); c.lineTo(16, 7); c.moveTo(16, 13.5); c.arc(12, 13.5, 4, 0, 7); },
  coffee: c => { c.moveTo(4, 9); c.lineTo(17, 9); c.lineTo(16, 19); c.quadraticCurveTo(15.8, 20.5, 14.3, 20.5); c.lineTo(6.7, 20.5); c.quadraticCurveTo(5.2, 20.5, 5, 19); c.closePath(); c.moveTo(17, 11); c.quadraticCurveTo(21, 11, 20.5, 14); c.quadraticCurveTo(20, 16.5, 16.5, 16.5); c.moveTo(8, 6.5); c.lineTo(8.8, 3.5); c.moveTo(12, 6.5); c.lineTo(12.8, 3.5); },
  music: c => { c.moveTo(9, 18); c.lineTo(9, 5); c.lineTo(20, 3); c.lineTo(20, 16); c.moveTo(9, 18); c.arc(6.5, 18, 2.5, 0, 7); c.moveTo(20, 16); c.arc(17.5, 16, 2.5, 0, 7); },
};
function icon(name, x, y, size, color, lw = 1.9, p = 1) {
  const f = ICONS[name] || ICONS.spark;
  ctx.save(); ctx.translate(x - size / 2, y - size / 2); ctx.scale(size / 24, size / 24);
  ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.lineJoin = "round"; ctx.lineCap = "round";
  ctx.globalAlpha *= clamp(p);
  const path = new Path2D(); f(path); ctx.stroke(path); ctx.restore();
}

// ---------------------------------------------------------------- images (user, AI-generated or stock)
const IMG = {};
async function loadImages(urls) {
  await Promise.all(urls.map(u => new Promise(res => { const im = new Image(); im.onload = () => { IMG[u] = im; res(); }; im.onerror = () => res(); im.src = u; })));
}
function drawCover(im, x, y, w, h, zoom = 1, fx = 0.5, fy = 0.5, ox = 0, oy = 0) {
  const s = Math.max(w / im.width, h / im.height) * zoom;
  const dw = im.width * s, dh = im.height * s;
  ctx.drawImage(im, x + (w - dw) * fx + ox, y + (h - dh) * fy + oy, dw, dh);
}

// ---------------------------------------------------------------- the continuous "world" behind every scene
let GRAIN = null, WORLD = null;
function setupWorld() {
  const r = rng(SPEC.seed || 7);
  GRAIN = document.createElement("canvas"); GRAIN.width = GRAIN.height = 256;
  const g = GRAIN.getContext("2d"), id = g.createImageData(256, 256);
  for (let i = 0; i < id.data.length; i += 4) { const v = r() * 255; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; }
  g.putImageData(id, 0, 0);
  const cols = [PAL.primary, PAL.secondary, PAL.accent, PAL.primary];
  WORLD = {
    blobs: cols.map((c, i) => ({ c, ax: r(), ay: r(), sx: 0.025 + r() * 0.03, sy: 0.02 + r() * 0.03, ph: r() * 6.28, rad: 0.55 + r() * 0.35, a: i === 2 ? 0.22 : 0.42 })),
    parts: Array.from({ length: 70 }, () => ({ x: r(), y: r(), z: 0.2 + r() * 0.8, tw: r() * 6.28, sp: 0.4 + r() })),
  };
}
function world(gt) {
  const bgGrad = ctx.createLinearGradient(0, 0, W * 0.3, H);
  bgGrad.addColorStop(0, PAL.bg2); bgGrad.addColorStop(1, PAL.bg);
  ctx.fillStyle = bgGrad; ctx.fillRect(0, 0, W, H);
  const M = Math.max(W, H);
  ctx.save(); ctx.globalCompositeOperation = PAL.light ? "multiply" : "screen";
  for (const b of WORLD.blobs) {
    const x = W * (0.5 + 0.55 * Math.sin(b.ph + gt * b.sx * 6.28 + b.ax * 6.28));
    const y = H * (0.5 + 0.5 * Math.cos(b.ph * 1.3 + gt * b.sy * 6.28 + b.ay * 6.28));
    glow(x, y, M * b.rad, b.c, PAL.light ? b.a * 0.45 : b.a);
  }
  ctx.restore();
  if (LOOK.grid) {
    ctx.save(); ctx.globalAlpha = PAL.light ? 0.06 : 0.07; ctx.strokeStyle = PAL.text; ctx.lineWidth = 1 * S;
    const gap = 90 * S, off = (gt * 12 * S) % gap;
    ctx.beginPath();
    for (let x = -gap + off; x < W + gap; x += gap) { ctx.moveTo(x, 0); ctx.lineTo(x, H); }
    for (let y = -gap + off; y < H + gap; y += gap) { ctx.moveTo(0, y); ctx.lineTo(W, y); }
    ctx.stroke(); ctx.restore();
  }
  // floating particles with depth (parallax drift upwards)
  for (const p of WORLD.parts) {
    const y = ((p.y - gt * 0.012 * p.sp * p.z) % 1 + 1) % 1;
    const x = p.x + 0.01 * Math.sin(gt * 0.5 + p.tw);
    const a = (0.15 + 0.35 * p.z) * (0.6 + 0.4 * Math.sin(gt * 1.7 + p.tw));
    dot(x * W, y * H, (1.2 + 3.2 * p.z) * S, PAL.light ? PAL.primary : PAL.particle, a);
  }
}
function finish(gt) {
  // vignette + film grain: glue every layer into one picture
  const v = ctx.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.35, W / 2, H / 2, Math.max(W, H) * 0.75);
  v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, PAL.light ? "rgba(40,30,20,0.18)" : "rgba(0,0,0,0.42)");
  ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
  if (LOOK.grain !== false) {
    ctx.save(); ctx.globalAlpha = PAL.light ? 0.035 : 0.05; ctx.globalCompositeOperation = "overlay";
    const f = Math.floor(gt * FPS);
    const ox = (f * 73) % 256, oy = (f * 151) % 256;
    const pat = ctx.createPattern(GRAIN, "repeat");
    ctx.translate(-ox, -oy); ctx.fillStyle = pat; ctx.fillRect(0, 0, W + 256, H + 256);
    ctx.restore();
  }
}

// ---------------------------------------------------------------- transitions (drawn inside the scenes, so a
// hard cut between two motion scenes is invisible: the world is continuous and the cut happens under cover)
function dirSign() { return SPEC.rtl ? 1 : -1; }  // direction the story moves on screen
function transitionCover(type, p, entering) {
  // p: 0 = no cover, 1 = fully covered
  if (p <= 0) return;
  const d = dirSign();
  if (type === "panels") {
    const cols = [PAL.accent, PAL.primary, PAL.bg2];
    cols.forEach((c, i) => {
      const q = E.inOut(clamp(p * 1.25 - i * 0.12));
      // entering: panels leave toward the story direction; exiting: they arrive from the opposite side
      const off = entering ? (1 - q) * d : -(1 - q) * d;
      ctx.save(); ctx.fillStyle = c; ctx.translate(W / 2 + off * W * 1.3, H / 2); ctx.rotate(-0.12 * d);
      ctx.fillRect(-W * 0.85, -H * 0.8, W * 1.7, H * 1.6); ctx.restore();
    });
  } else if (type === "circle") {
    const big = Math.hypot(W, H) * 0.62;
    ctx.save();
    if (!entering) {   // a disc grows from the centre until it covers the frame
      const r = E.inOut(p) * big;
      ctx.fillStyle = PAL.accent; ctx.beginPath(); ctx.arc(W / 2, H / 2, r, 0, 7); ctx.fill();
      ctx.fillStyle = PAL.primary; ctx.beginPath(); ctx.arc(W / 2, H / 2, Math.max(0, r - 70 * S), 0, 7); ctx.fill();
    } else {           // iris: a growing hole reveals the new scene
      const r = (1 - E.inOut(p)) * big;
      ctx.fillStyle = PAL.primary; ctx.beginPath(); ctx.rect(0, 0, W, H); ctx.arc(W / 2, H / 2, r + 70 * S * (1 - p), 0, 7, true); ctx.fill();
      ctx.fillStyle = PAL.accent; ctx.beginPath(); ctx.arc(W / 2, H / 2, r + 70 * S * (1 - p), 0, 7); ctx.arc(W / 2, H / 2, r, 0, 7, true); ctx.fill();
    }
    ctx.restore();
  }
}
/** Foreground transform for swap/slide transitions; returns alpha multiplier. */
function fgTransition(sc, t) {
  const D = sc.duration, ti = sc.tin || "swap", to = sc.tout || "swap";
  const d = dirSign();
  let alpha = 1;
  const pin = 1 - E.out5(prog(t, 0, 0.4)), pout = E.in(prog(t, D - 0.34, 0.34));
  if (ti === "slide") ctx.translate(-d * pin * W * 0.35, 0);
  if (ti === "swap" || ti === "slide") { const s = 1 + pin * 0.08; ctx.translate(W / 2, H / 2); ctx.scale(s, s); ctx.translate(-W / 2, -H / 2); alpha *= 1 - pin; }
  if (to === "slide") ctx.translate(d * pout * W * 0.4, 0);
  if (to === "swap" || to === "slide") { const s = 1 - pout * 0.06; ctx.translate(W / 2, H / 2); ctx.scale(s, s); ctx.translate(-W / 2, -H / 2); alpha *= 1 - pout; }
  return alpha;
}

// ---------------------------------------------------------------- scene templates
// Each template: init(sc) lays out text (registers boxes + events), draw(sc, t) paints the foreground.
const T = {};
const D_IN = 0.15;  // first text starts shortly after the scene starts

/** Vertical stack layout helper inside the safe rect. */
function stackY(blocks, gaps, top, bottom) {
  const total = blocks.reduce((s, b) => s + (b ? b.h : 0), 0) + gaps.reduce((s, g) => s + g, 0);
  return lerp(top, bottom - total, 0.5);
}

T.kinetic_title = {
  init(sc) {
    const p = sc.params, D = sc.duration;
    const big = R.wide ? 112 : 120;
    sc.k = p.kicker ? tb(p.kicker, { size: (R.tall ? 46 : 36) * S, weight: 700, role: "body", maxW: R.w * 0.8, maxLines: 1, color: PAL.accentText }) : null;
    sc.ti = tb(p.title, { size: (p.size || big) * S, maxW: R.w * (R.wide ? 0.78 : 0.92), maxLines: p.maxLines || 4, highlight: p.highlight, align: "center" });
    sc.su = p.subtitle ? tb(p.subtitle, { size: (R.tall ? 56 : 50) * S, role: "body", weight: 500, maxW: R.w * 0.86, maxLines: 3, color: PAL.muted }) : null;
    const gk = 34 * S, gs = 46 * S;
    const kh = sc.k ? sc.k.h + 28 * S : 0;
    let y = stackY([sc.ti, sc.su], [sc.su ? gs : 0], R.y1 + kh, R.y2) ;
    sc.ky = y - kh + 6 * S; sc.ty = y; sc.sy = y + sc.ti.h + gs;
    sc.aT = { type: p.animation || (sc.ti.rtl ? "rise" : "rise"), t0: D_IN + (sc.k ? 0.15 : 0), stagger: 0.1, out: D - 0.36, hlAt: 0.9 };
    sc.aS = { type: "fade", t0: 0.85, out: D - 0.36 };
    place(sc.ti, R.cx, sc.ty, sc.aT, D);
    if (sc.su) place(sc.su, R.cx, sc.sy, sc.aS, D);
    if (sc.k) reg(sc.k.text, R.cx - sc.k.w / 2 - 26 * S, sc.ky, R.cx + sc.k.w / 2 + 26 * S, sc.ky + sc.k.h + 12 * S, 0.5, D - 0.3);
    ev(D_IN + 0.05, "whoosh", 0.6); ev(0.75, "pop", 0.5);
    if (p.impact) ev(D_IN + 0.35, "hit", 0.8);
    const r = rng(sc.seed);
    sc.shapes = Array.from({ length: 9 }, (_, i) => ({ x: r(), y: r(), z: 0.3 + r() * 0.7, k: i % 3, rot: r() * 6, d: 0.2 + r() * 0.6 }));
  },
  draw(sc, t) {
    const D = sc.duration, p = sc.params;
    // orbit rings behind the title
    const cy = sc.ty + sc.ti.h / 2, rr0 = Math.min(R.w, R.h) * 0.46;
    const rp = E.out(prog(t, 0.05, 1.1));
    ring(R.cx, cy, rr0, 2.5 * S, PAL.primaryLight, rp * 0.82, -1.3 + t * 0.35, 0.55);
    ring(R.cx, cy, rr0 * 0.8, 1.5 * S, PAL.accent, rp * 0.4, 2 - t * 0.5, 0.65);
    dot(R.cx + rr0 * Math.cos(-1.3 + t * 0.35 + rp * 0.82 * 6.28), cy + rr0 * Math.sin(-1.3 + t * 0.35 + rp * 0.82 * 6.28), 7 * S, PAL.accent, rp);
    // floating geometric accents (parallax with depth)
    for (const s of sc.shapes) {
      const a = E.back(prog(t, s.d, 0.6)) * (1 - prog(t, D - 0.4, 0.34));
      if (a <= 0) continue;
      const x = R.x1 + s.x * R.w + Math.sin(t * 0.8 + s.rot) * 18 * S * s.z;
      const y = R.y1 + s.y * R.h - t * 22 * S * s.z;
      if (Math.abs(y - cy) < sc.ti.h * 0.65 && Math.abs(x - R.cx) < sc.ti.w * 0.55) continue;
      const sz = (10 + 16 * s.z) * S * a;
      if (s.k === 0) ring(x, y, sz, 2.5 * S, PAL.accent, 1, 0, 0.8 * s.z);
      else if (s.k === 1) plus(x, y, sz * 0.8, 3 * S, PAL.primaryLight, 0.8 * s.z, s.rot + t);
      else dot(x, y, sz * 0.45, PAL.text, 0.5 * s.z);
    }
    if (sc.k) {
      const kp = E.out5(prog(t, D_IN, 0.5)), ko = 1 - prog(t, D - 0.36, 0.3);
      ctx.save(); ctx.globalAlpha = kp * ko;
      const w = sc.k.w + 52 * S, h = sc.k.h + 12 * S;
      rr(R.cx - w / 2, sc.ky + (1 - kp) * 20 * S, w, h, h / 2); ctx.fillStyle = PAL.accent; ctx.fill();
      ctx.restore();
      drawBlock(sc.k, R.cx, sc.ky + 6 * S + (1 - kp) * 20 * S, t, { type: "fade", t0: D_IN + 0.05, out: D - 0.36, shadow: false });
    }
    drawBlock(sc.ti, R.cx, sc.ty, t, sc.aT);
    if (sc.su) drawBlock(sc.su, R.cx, sc.sy, t, sc.aS);
  },
};

T.word_cloud = {
  init(sc) {
    const p = sc.params, D = sc.duration;
    sc.ti = p.title ? tb(p.title, { size: (R.wide ? 96 : 112) * S, maxW: R.w * 0.8, maxLines: 3, highlight: p.highlight }) : null;
    sc.su = p.subtitle ? tb(p.subtitle, { size: (R.tall ? 54 : 46) * S, role: "body", maxW: R.w * 0.86, maxLines: 2, color: PAL.muted }) : null;
    const gap = 30 * S;
    const y0 = stackY([sc.ti, sc.su], [sc.su ? gap : 0], R.y1, R.y2);
    sc.ty = y0; sc.sy = y0 + (sc.ti ? sc.ti.h + gap : 0);
    const box = [R.cx - (sc.ti ? sc.ti.w : 300 * S) / 2 - 40 * S, y0 - 40 * S, R.cx + (sc.ti ? sc.ti.w : 300 * S) / 2 + 40 * S, sc.sy + (sc.su ? sc.su.h : 0) + 40 * S];
    sc.aT = { type: "rise", t0: 0.55, stagger: 0.1, out: D - 0.36, hlAt: 1.2 };
    if (sc.ti) place(sc.ti, R.cx, sc.ty, sc.aT, D);
    if (sc.su) place(sc.su, R.cx, sc.sy, { type: "fade", t0: 0.7, out: D - 0.36 }, D);
    const r = rng(sc.seed);
    const words = p.words || [];
    sc.items = [];
    const placed = [];
    words.forEach((w, i) => {
      const z = 0.35 + 0.65 * ((i * 0.618) % 1);
      const size = (34 + 46 * z) * S;
      setFont(size, 700, w, "head");
      const ww = ctx.measureText(w).width + 44 * S, hh = size * 1.6;
      for (let tries = 0; tries < 80; tries++) {
        const mx = ww / 2 + 30 * S, x = lerp(mx, W - mx, r()), y = lerp(0.05, 0.95, r()) * H;
        const bb = [x - ww / 2, y - hh / 2, x + ww / 2, y + hh / 2];
        const hit = (b2) => bb[0] < b2[2] && b2[0] < bb[2] && bb[1] < b2[3] && b2[1] < bb[3];
        if (hit(box) || placed.some(hit)) continue;
        placed.push(bb); sc.items.push({ w, x, y, z, size, ww, hh, d: 0.05 + i * 0.09, bubble: p.bubbles !== false && i % 3 === 0, ph: r() * 6.28 });
        break;
      }
    });
    sc.items.forEach(it => ev(it.d, "tick", 0.25));
    ev(0.5, "whoosh", 0.5);
  },
  draw(sc, t) {
    const D = sc.duration;
    const out = prog(t, D - 0.4, 0.36);
    for (const it of sc.items) {
      const a = E.out(prog(t, it.d, 0.5)) * (1 - out);
      if (a <= 0) continue;
      const push = 1 + t * 0.035 * it.z;  // dolly through the words: near words drift outward faster
      const x = R.cx + (it.x - R.cx) * push + Math.sin(t * 0.6 + it.ph) * 10 * S;
      const y = H / 2 + (it.y - H / 2) * push + Math.cos(t * 0.5 + it.ph) * 8 * S;
      const xm = it.ww / 2 + 16 * S, xc = Math.min(W - xm, Math.max(xm, x));
      ctx.save(); ctx.globalAlpha = a * (0.35 + 0.65 * it.z);
      const sc2 = lerp(0.7, 1, E.back(prog(t, it.d, 0.55)));
      ctx.translate(xc, y); ctx.scale(sc2, sc2);
      if (it.bubble) {
        rr(-it.ww / 2, -it.hh / 2, it.ww, it.hh, it.hh / 2); ctx.fillStyle = rgba(PAL.primary, 0.85); ctx.fill();
        ctx.beginPath(); ctx.moveTo(-it.ww * 0.18, it.hh / 2 - 2); ctx.lineTo(-it.ww * 0.28, it.hh / 2 + 16 * S); ctx.lineTo(-it.ww * 0.02, it.hh / 2 - 2); ctx.fill();
      } else {
        rr(-it.ww / 2, -it.hh / 2, it.ww, it.hh, it.hh / 2); ctx.strokeStyle = rgba(PAL.text, 0.35); ctx.lineWidth = 2 * S; ctx.stroke();
      }
      setFont(it.size, 700, it.w, "head"); ctx.fillStyle = PAL.text; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.direction = isAr(it.w) ? "rtl" : "ltr";
      ctx.fillText(it.w, 0, 2 * S);
      ctx.restore();
    }
    if (sc.ti) {
      const gp = E.out(prog(t, 0.4, 0.8)) * (1 - out);
      glow(R.cx, sc.ty + sc.ti.h / 2, Math.max(sc.ti.w, sc.ti.h) * 0.9, PAL.bg, 0.85 * gp);
      drawBlock(sc.ti, R.cx, sc.ty, t, sc.aT);
    }
    if (sc.su) drawBlock(sc.su, R.cx, sc.sy, t, { type: "fade", t0: 0.7, out: D - 0.36 });
  },
};

T.globe = {
  init(sc) {
    const p = sc.params, D = sc.duration;
    const r = rng(sc.seed);
    sc.R = R.wide ? Math.min(R.h * 0.46, R.w * 0.27) : Math.min(R.w * 0.46, R.h * 0.27);
    sc.ti = p.title ? tb(p.title, { size: (R.wide ? 92 : 104) * S, maxW: R.wide ? R.w * 0.46 : R.w * 0.94, maxLines: 3, highlight: p.highlight, align: R.wide ? "start" : "center" }) : null;
    sc.su = p.subtitle ? tb(p.subtitle, { size: (R.tall ? 54 : 46) * S, role: "body", maxW: R.wide ? R.w * 0.46 : R.w * 0.88, maxLines: 3, color: PAL.muted, align: R.wide ? "start" : "center" }) : null;
    if (R.wide) {
      sc.gx = SPEC.rtl ? R.x1 + R.w * 0.27 : R.x2 - R.w * 0.27; sc.gy = R.cy;
      sc.tx = SPEC.rtl ? R.x2 : R.x1;
      sc.ty = stackY([sc.ti, sc.su], [30 * S], R.y1, R.y2); sc.sy = sc.ty + (sc.ti ? sc.ti.h + 30 * S : 0);
    } else {
      const textH = (sc.ti ? sc.ti.h : 0) + (sc.su ? sc.su.h + 30 * S : 0);
      const gap = 70 * S;
      const top = lerp(R.y1, R.y2 - (sc.R * 2 + gap + textH), 0.42);
      sc.gx = R.cx; sc.gy = top + sc.R; sc.tx = R.cx;
      sc.ty = top + sc.R * 2 + gap; sc.sy = sc.ty + (sc.ti ? sc.ti.h + 30 * S : 0);
    }
    sc.aT = { type: "rise", t0: 0.6, stagger: 0.1, out: D - 0.36, hlAt: 1.3 };
    if (sc.ti) place(sc.ti, sc.tx, sc.ty, sc.aT, D);
    if (sc.su) place(sc.su, sc.tx, sc.sy, { type: "fade", t0: 0.75, out: D - 0.36 }, D);
    // fibonacci-sphere dots
    sc.pts = []; const N = 700;
    for (let i = 0; i < N; i++) { const y = 1 - (i / (N - 1)) * 2, rad = Math.sqrt(1 - y * y), th = i * 2.39996; sc.pts.push([Math.cos(th) * rad, y, Math.sin(th) * rad]); }
    const hub = p.hub || { lat: 25, lon: 10 };
    const cities = p.points || Array.from({ length: 7 }, () => ({ lat: lerp(-40, 60, r()), lon: lerp(-150, 150, r()) }));
    sc.hub = hub; sc.arcs = cities.map((c, i) => ({ c, d: 0.35 + i * 0.22 }));
    sc.arcs.forEach(a => ev(a.d + 0.7, "pop", 0.35));
    ev(0.1, "whoosh", 0.5);
  },
  draw(sc, t) {
    const D = sc.duration, out = prog(t, D - 0.4, 0.36);
    const appear = E.out5(prog(t, 0, 0.9));
    const RR = sc.R * lerp(0.8, 1, appear), rot = t * 0.28 + 0.6, tilt = 0.32;
    const proj = (v) => {
      let [x, y, z] = v; const cx = Math.cos(rot), sx = Math.sin(rot);
      [x, z] = [x * cx + z * sx, -x * sx + z * cx];
      const ct = Math.cos(tilt), st = Math.sin(tilt);
      [y, z] = [y * ct - z * st, y * st + z * ct];
      return [sc.gx + x * RR, sc.gy - y * RR, z];
    };
    const ll = (lat, lon) => { const la = lat * Math.PI / 180, lo = lon * Math.PI / 180; return [Math.cos(la) * Math.sin(lo), Math.sin(la), Math.cos(la) * Math.cos(lo)]; };
    ctx.save(); ctx.globalAlpha = appear * (1 - out);
    glow(sc.gx, sc.gy, RR * 1.5, PAL.primary, 0.5);
    ctx.fillStyle = rgba(PAL.bg, 0.55); ctx.beginPath(); ctx.arc(sc.gx, sc.gy, RR, 0, 7); ctx.fill();
    ctx.strokeStyle = rgba(PAL.primaryLight, 0.55); ctx.lineWidth = 2 * S; ctx.stroke();
    for (const v of sc.pts) { const [x, y, z] = proj(v); if (z < 0) continue; dot(x, y, (1.2 + 2.2 * z) * S, PAL.primaryLight, 0.25 + 0.6 * z); }
    const hp = proj(ll(sc.hub.lat, sc.hub.lon));
    for (const a of sc.arcs) {
      const pp = E.inOut(prog(t, a.d, 0.9));
      if (pp <= 0) continue;
      const cp = proj(ll(a.c.lat, a.c.lon));
      const mx = (cp[0] + hp[0]) / 2, my = (cp[1] + hp[1]) / 2;
      const dx = mx - sc.gx, dy = my - sc.gy, dl = Math.hypot(dx, dy) || 1;
      const lift = RR * 0.55 + Math.hypot(cp[0] - hp[0], cp[1] - hp[1]) * 0.25;
      const qx = mx + dx / dl * lift, qy = my + dy / dl * lift;
      ctx.save(); ctx.strokeStyle = PAL.accent; ctx.lineWidth = 3 * S; ctx.lineCap = "round"; ctx.globalAlpha *= 0.9;
      ctx.beginPath(); const n = 40; let hx = cp[0], hy = cp[1];
      for (let i = 0; i <= n * pp; i++) { const u = i / n; hx = (1 - u) * (1 - u) * cp[0] + 2 * (1 - u) * u * qx + u * u * hp[0]; hy = (1 - u) * (1 - u) * cp[1] + 2 * (1 - u) * u * qy + u * u * hp[1]; i ? ctx.lineTo(hx, hy) : ctx.moveTo(hx, hy); }
      ctx.stroke(); ctx.restore();
      if (cp[2] > -0.1) { dot(cp[0], cp[1], 7 * S, PAL.accent, 1); ring(cp[0], cp[1], (8 + 22 * ((t * 0.9 + a.d) % 1)) * S, 2 * S, PAL.accent, 1, 0, 1 - ((t * 0.9 + a.d) % 1)); }
      if (pp < 1) glow(hx, hy, 26 * S, PAL.accent, 0.9);
    }
    dot(hp[0], hp[1], 11 * S, PAL.text, 1); ring(hp[0], hp[1], (14 + 30 * ((t * 0.8) % 1)) * S, 3 * S, PAL.text, 1, 0, 1 - (t * 0.8) % 1);
    ctx.restore();
    if (sc.ti) drawBlock(sc.ti, sc.tx, sc.ty, t, sc.aT);
    if (sc.su) drawBlock(sc.su, sc.tx, sc.sy, t, { type: "fade", t0: 0.75, out: D - 0.36 });
  },
};

T.features = {
  init(sc) {
    const p = sc.params, D = sc.duration, items = (p.items || []).slice(0, 4);
    sc.ti = p.title ? tb(p.title, { size: (R.wide ? 84 : R.tall ? 108 : 92) * S, maxW: R.w * 0.92, maxLines: 2, highlight: p.highlight }) : null;
    const row = R.wide && items.length > 1;
    const gap = (R.tall ? 40 : 26) * S;
    const cw = row ? (R.w - gap * (items.length - 1)) / items.length : R.w * 0.98;
    const iconBox = (R.tall ? 136 : 104) * S;
    const big = R.tall ? 1.18 : 1;
    sc.cards = items.map((it, i) => {
      const title = tb(it.title || it.text || "", { size: (row ? 46 : 52) * big * S, weight: 800, maxW: row ? cw - 60 * S : cw - iconBox - 90 * S, maxLines: 2, align: row ? "center" : "start" });
      const body = it.text && it.title ? tb(it.text, { size: (row ? 32 : 36) * big * S, role: "body", weight: 500, maxW: row ? cw - 60 * S : cw - iconBox - 90 * S, maxLines: 3, color: PAL.muted, align: row ? "center" : "start" }) : null;
      const ch = row ? iconBox + 50 * S + title.h + (body ? body.h + 12 * S : 0) + 60 * S : Math.max(iconBox + (R.tall ? 90 : 44) * S, title.h + (body ? body.h + 10 * S : 0) + 70 * S);
      return { it, title, body, ch, d: 0.45 + i * 0.28 };
    });
    const titleGap = (R.tall ? 90 : 56) * S;
    const totalH = (sc.ti ? sc.ti.h + titleGap : 0) + (row ? Math.max(...sc.cards.map(c => c.ch)) : sc.cards.reduce((s, c) => s + c.ch, 0) + gap * (sc.cards.length - 1));
    let y = lerp(R.y1, R.y2 - totalH, 0.45);
    sc.ty = y; if (sc.ti) y += sc.ti.h + titleGap;
    sc.aT = { type: "rise", t0: D_IN, stagger: 0.1, out: D - 0.36 };
    if (sc.ti) place(sc.ti, R.cx, sc.ty, sc.aT, D);
    sc.cards.forEach((c, i) => {
      if (row) { c.x = SPEC.rtl ? R.x2 - (i + 1) * cw - i * gap : R.x1 + i * (cw + gap); c.y = y; c.w = cw; c.h = Math.max(...sc.cards.map(k => k.ch)); }
      else { c.x = R.cx - cw / 2; c.y = y; c.w = cw; c.h = c.ch; y += c.ch + gap; }
      const a = { type: "fade", t0: c.d + 0.15, out: D - 0.36 };
      if (row) {
        c.tx = c.x + c.w / 2; c.ty = c.y + 30 * S + iconBox + 24 * S; c.ix = c.x + c.w / 2; c.iy = c.y + 30 * S + iconBox / 2;
      } else {
        c.ix = SPEC.rtl ? c.x + c.w - 26 * S - iconBox / 2 : c.x + 26 * S + iconBox / 2; c.iy = c.y + c.h / 2;
        c.tx = SPEC.rtl ? c.x + c.w - iconBox - 56 * S : c.x + iconBox + 56 * S;
        const th = c.title.h + (c.body ? c.body.h + 10 * S : 0); c.ty = c.y + (c.h - th) / 2;
      }
      place(c.title, c.tx, c.ty, a, D);
      if (c.body) place(c.body, c.tx, c.ty + c.title.h + 10 * S, a, D);
      ev(c.d, "pop", 0.5);
    });
    sc.iconBox = iconBox; sc.row = row;
  },
  draw(sc, t) {
    const D = sc.duration, d = dirSign();
    if (sc.ti) drawBlock(sc.ti, R.cx, sc.ty, t, sc.aT);
    for (const c of sc.cards) {
      const p = E.back(prog(t, c.d, 0.65)), a = clamp(prog(t, c.d, 0.3)) * (1 - prog(t, D - 0.36, 0.3));
      if (a <= 0) continue;
      const bob = Math.sin(t * 1.4 + c.d * 3) * 4 * S;
      ctx.save(); ctx.globalAlpha = a; ctx.translate(-d * (1 - p) * 140 * S, bob);
      ctx.shadowColor = "rgba(0,0,0,0.28)"; ctx.shadowBlur = 40 * S; ctx.shadowOffsetY = 14 * S;
      rr(c.x, c.y, c.w, c.h, 34 * S); ctx.fillStyle = PAL.card; ctx.fill(); ctx.shadowColor = "transparent";
      ctx.strokeStyle = rgba(PAL.text, PAL.light ? 0.08 : 0.16); ctx.lineWidth = 2 * S; ctx.stroke();
      const ip = E.back(prog(t, c.d + 0.12, 0.6));
      ctx.save(); ctx.translate(c.ix, c.iy); ctx.scale(ip, ip);
      const ig = ctx.createLinearGradient(-sc.iconBox / 2, -sc.iconBox / 2, sc.iconBox / 2, sc.iconBox / 2);
      ig.addColorStop(0, PAL.accent); ig.addColorStop(1, mix(PAL.accent, PAL.primary, 0.35));
      rr(-sc.iconBox / 2, -sc.iconBox / 2, sc.iconBox, sc.iconBox, 28 * S); ctx.fillStyle = ig; ctx.fill();
      ctx.restore();
      icon(c.it.icon || "check", c.ix, c.iy, sc.iconBox * 0.56, PAL.accentText, 2.1, ip);
      ctx.restore();
      ctx.save(); ctx.translate(-d * (1 - p) * 140 * S, bob);
      drawBlock(c.title, c.tx, c.ty, t, { type: "fade", t0: c.d + 0.15, out: D - 0.36, shadow: false });
      if (c.body) drawBlock(c.body, c.tx, c.ty + c.title.h + 10 * S, t, { type: "fade", t0: c.d + 0.25, out: D - 0.36, shadow: false });
      ctx.restore();
    }
  },
};

T.stats = {
  init(sc) {
    const p = sc.params, D = sc.duration, items = (p.items || []).slice(0, 3);
    sc.ti = p.title ? tb(p.title, { size: 84 * S, maxW: R.w * 0.92, maxLines: 2 }) : null;
    const row = R.wide || items.length === 1 ? true : false;
    const rad = (row ? Math.min(R.w / items.length / 2 - 30 * S, R.h * 0.2) : Math.min(R.h / items.length / 2 - 60 * S, R.w * 0.2));
    sc.rad = Math.max(80 * S, Math.min(rad, 170 * S));
    sc.items = items.map((it, i) => ({ it, d: 0.35 + i * 0.3, lab: tb(it.label || "", { size: 40 * S, role: "body", weight: 600, maxW: row ? R.w / items.length - 30 * S : R.w * 0.5, maxLines: 2, color: PAL.muted, align: row ? "center" : "start" }) }));
    const titleGap = 60 * S;
    const unit = row ? sc.rad * 2 + 30 * S + Math.max(...sc.items.map(i => i.lab.h)) : sc.rad * 2 + 40 * S;
    const totalH = (sc.ti ? sc.ti.h + titleGap : 0) + (row ? unit : unit * items.length);
    let y = lerp(R.y1, R.y2 - totalH, 0.45); sc.ty = y; if (sc.ti) y += sc.ti.h + titleGap;
    if (sc.ti) place(sc.ti, R.cx, sc.ty, { type: "rise", t0: D_IN, out: D - 0.36 }, D);
    sc.items.forEach((c, i) => {
      if (row) { const cw = R.w / items.length; c.cx = SPEC.rtl ? R.x2 - cw * (i + 0.5) : R.x1 + cw * (i + 0.5); c.cy = y + sc.rad; c.lx = c.cx; c.ly = y + sc.rad * 2 + 30 * S; }
      else { c.cx = SPEC.rtl ? R.x2 - sc.rad - 20 * S : R.x1 + sc.rad + 20 * S; c.cy = y + i * unit + sc.rad; c.lx = SPEC.rtl ? c.cx - sc.rad - 50 * S : c.cx + sc.rad + 50 * S; c.ly = c.cy - c.lab.h / 2; }
      const num = String(c.it.prefix || "") + String(c.it.value) + String(c.it.suffix || "");
      reg(num, c.cx - sc.rad, c.cy - sc.rad, c.cx + sc.rad, c.cy + sc.rad, c.d + 1.3, D - 0.25);
      place(c.lab, c.lx, c.ly, { type: "fade", t0: c.d + 0.5, out: D - 0.36 }, D);
      ev(c.d + 1.3, "pop", 0.6);
    });
  },
  draw(sc, t) {
    const D = sc.duration, out = 1 - prog(t, D - 0.36, 0.3);
    if (sc.ti) drawBlock(sc.ti, R.cx, sc.ty, t, { type: "rise", t0: D_IN, out: D - 0.36 });
    for (const c of sc.items) {
      const p = E.out5(prog(t, c.d, 1.3)), a = clamp(prog(t, c.d, 0.25)) * out;
      if (a <= 0) continue;
      ctx.save(); ctx.globalAlpha = a;
      ring(c.cx, c.cy, sc.rad, 14 * S, rgba(PAL.text, 0.12), 1);
      const frac = c.it.ring != null ? c.it.ring : (String(c.it.suffix || "").includes("%") ? Number(c.it.value) / 100 : 0.78);
      ring(c.cx, c.cy, sc.rad, 14 * S, PAL.accent, frac * p);
      const raw = String(c.it.value), num = parseFloat(raw.replace(/[^\d.]/g, "")) || 0, dec = (raw.split(".")[1] || "").length;
      let shown = (num * p).toFixed(dec);
      if (SPEC.numerals === "arabic_indic" && SPEC.rtl) shown = shown.replace(/\d/g, d => "٠١٢٣٤٥٦٧٨٩"[d]);
      const txt = String(c.it.prefix || "") + shown + String(c.it.suffix || "");
      setFont(sc.rad * 0.62, 800, txt, "head"); ctx.fillStyle = PAL.text; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.direction = "ltr"; ctx.fillText(txt, c.cx, c.cy + 4 * S);
      ctx.restore();
      drawBlock(c.lab, c.lx, c.ly, t, { type: "fade", t0: c.d + 0.5, out: D - 0.36 });
    }
  },
};

T.journey = {
  init(sc) {
    const p = sc.params, D = sc.duration, steps = (p.steps || []).slice(0, 6);
    sc.ti = p.title ? tb(p.title, { size: (R.wide ? 84 : 96) * S, maxW: R.w * 0.92, maxLines: 2, highlight: p.highlight }) : null;
    sc.su = p.subtitle ? tb(p.subtitle, { size: 44 * S, role: "body", maxW: R.w * 0.86, maxLines: 2, color: PAL.muted }) : null;
    const titleGap = 50 * S;
    const head = (sc.ti ? sc.ti.h : 0) + (sc.su ? sc.su.h + 24 * S : 0);
    sc.ty = R.y1 + 10 * S; sc.sy = sc.ty + (sc.ti ? sc.ti.h + 24 * S : 0);
    const top = sc.ty + head + titleGap + 40 * S, bot = R.y2 - 40 * S;
    const n = steps.length, d = dirSign();
    sc.nodes = steps.map((s, i) => {
      const u = n === 1 ? 0.5 : i / (n - 1);
      let x, y;
      if (R.wide) { x = SPEC.rtl ? lerp(R.x2 - 60 * S, R.x1 + 60 * S, u) : lerp(R.x1 + 60 * S, R.x2 - 60 * S, u); y = lerp(bot, top, u * 0.85) + Math.sin(u * 6.28) * 40 * S; }
      else { y = lerp(bot, top + 30 * S, u); x = R.cx + (i % 2 ? 1 : -1) * R.w * 0.24 * (SPEC.rtl ? -1 : 1); }
      return { s, x, y, u };
    });
    sc.drawEnd = Math.max(0.9, Math.min(D - 2.1, 0.5 + 0.5 * n));
    sc.nodes.forEach((nd, i) => {
      nd.d = lerp(0.5, sc.drawEnd, n === 1 ? 1 : i / (n - 1));
      nd.lab = tb(nd.s, { size: (i === n - 1 ? 68 : 52) * (R.tall ? 1.1 : 1) * S, weight: 800, maxW: R.w * 0.36, maxLines: 2, align: "center", color: i === n - 1 ? PAL.accentText : PAL.text });
      nd.lx = nd.x; nd.ly = nd.y - nd.lab.h / 2;
      place(nd.lab, nd.lx, nd.ly, { type: "pop", t0: nd.d + 0.05, out: D - 0.36 }, D);
      ev(nd.d, i === n - 1 ? "hit" : "pop", i === n - 1 ? 0.8 : 0.4);
    });
    if (sc.ti) place(sc.ti, R.cx, sc.ty, { type: "rise", t0: D_IN, out: D - 0.36 }, D);
    if (sc.su) place(sc.su, R.cx, sc.sy, { type: "fade", t0: 0.5, out: D - 0.36 }, D);
  },
  draw(sc, t) {
    const D = sc.duration, out = 1 - prog(t, D - 0.36, 0.3), n = sc.nodes.length;
    if (sc.ti) drawBlock(sc.ti, R.cx, sc.ty, t, { type: "rise", t0: D_IN, out: D - 0.36, hlAt: 0.9 });
    if (sc.su) drawBlock(sc.su, R.cx, sc.sy, t, { type: "fade", t0: 0.5, out: D - 0.36 });
    const pathP = E.inOut(prog(t, 0.5, sc.drawEnd - 0.5 + 0.001));
    // smooth path through nodes (Catmull-Rom → bezier), drawn progressively
    const pts = sc.nodes.map(nd => [nd.x, nd.y]);
    const seg = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
      for (let k = 0; k <= 24; k++) { const u = k / 24, u2 = u * u, u3 = u2 * u;
        seg.push([0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * u + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3),
          0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * u + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3)]); }
    }
    ctx.save(); ctx.globalAlpha = out;
    if (seg.length) {
      ctx.setLineDash([2 * S, 16 * S]); ctx.lineCap = "round"; ctx.strokeStyle = rgba(PAL.text, 0.3); ctx.lineWidth = 5 * S;
      ctx.beginPath(); seg.forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); ctx.stroke(); ctx.setLineDash([]);
      const m = Math.floor((seg.length - 1) * pathP);
      const g = ctx.createLinearGradient(pts[0][0], pts[0][1], pts[pts.length - 1][0], pts[pts.length - 1][1]);
      g.addColorStop(0, PAL.primaryLight); g.addColorStop(1, PAL.accent);
      ctx.strokeStyle = g; ctx.lineWidth = 9 * S; ctx.beginPath();
      for (let i = 0; i <= m; i++) i ? ctx.lineTo(seg[i][0], seg[i][1]) : ctx.moveTo(seg[i][0], seg[i][1]);
      ctx.stroke();
      if (pathP > 0 && pathP < 1) { glow(seg[m][0], seg[m][1], 50 * S, PAL.accent, 0.9); dot(seg[m][0], seg[m][1], 9 * S, "#ffffff", 1); }
    }
    sc.nodes.forEach((nd, i) => {
      const q = E.back(prog(t, nd.d, 0.55)); if (q <= 0) return;
      const last = i === n - 1;
      const pad = 34 * S, w = nd.lab.w + pad * 2, h = nd.lab.h + 24 * S;
      ctx.save(); ctx.translate(nd.x, nd.y); ctx.scale(q, q);
      if (last) glow(0, 0, w * 0.9, PAL.accent, 0.45);
      rr(-w / 2, -h / 2, w, h, h / 2); ctx.fillStyle = last ? PAL.accent : PAL.card; ctx.fill();
      ctx.strokeStyle = last ? PAL.accent : rgba(PAL.text, 0.25); ctx.lineWidth = 2 * S; ctx.stroke();
      ctx.restore();
      drawBlock(nd.lab, nd.lx, nd.ly, t, { type: "pop", t0: nd.d + 0.05, out: D - 0.36, shadow: false });
    });
    ctx.restore();
  },
};

T.contrast = {
  init(sc) {
    const p = sc.params, D = sc.duration;
    sc.a = tb(p.from, { size: (R.wide ? 88 : 96) * S, maxW: R.w * 0.9, maxLines: 2, color: PAL.muted, weight: 700 });
    sc.b = tb(p.to, { size: (R.wide ? 120 : 140) * S, maxW: R.w * 0.94, maxLines: 3, color: PAL.text, highlight: p.highlight });
    sc.k = p.kicker ? tb(p.kicker, { size: 40 * S, role: "body", weight: 600, maxW: R.w * 0.8, maxLines: 1, color: PAL.muted }) : null;
    sc.swap = Math.max(1.3, Math.min(D - 2.75, 2.4));
    const gap = 50 * S;
    sc.by = stackY([sc.b], [], R.y1, R.y2);
    sc.ay = R.cy - sc.a.h / 2;
    sc.ky = sc.by - gap - (sc.k ? sc.k.h : 0);
    reg(sc.a.text, ...blockBox(sc.a, R.cx, sc.ay), D_IN + 0.3, sc.swap);
    place(sc.b, R.cx, sc.by, { type: "pop", t0: sc.swap + 0.1, stagger: 0.08, out: D - 0.25 }, D);
    if (sc.k) place(sc.k, R.cx, sc.ky, { type: "fade", t0: sc.swap + 0.3, out: D - 0.36 }, D);
    ev(sc.swap - 0.1, "whoosh", 0.7); ev(sc.swap + 0.15, "hit", 0.7);
  },
  draw(sc, t) {
    const D = sc.duration;
    const sp = prog(t, sc.swap - 0.25, 0.4);
    if (sp < 1) {
      ctx.save(); const k = 1 - E.in(sp); ctx.globalAlpha = k; const s = lerp(1, 0.82, E.in(sp));
      ctx.translate(R.cx, sc.ay + sc.a.h / 2); ctx.scale(s, s); ctx.translate(-R.cx, -(sc.ay + sc.a.h / 2));
      drawBlock(sc.a, R.cx, sc.ay, t, { type: "rise", t0: D_IN });
      const lp = E.out(prog(t, 0.75, 0.4));
      ctx.strokeStyle = PAL.accent; ctx.lineWidth = 10 * S; ctx.lineCap = "round"; ctx.beginPath();
      const [x1, , x2] = blockBox(sc.a, R.cx, sc.ay); const yy = sc.ay + sc.a.h / 2;
      const st = SPEC.rtl ? x2 + 12 * S : x1 - 12 * S, en = SPEC.rtl ? x1 - 12 * S : x2 + 12 * S;
      ctx.moveTo(st, yy); ctx.lineTo(lerp(st, en, lp), yy); ctx.stroke();
      ctx.restore();
    }
    const bp = E.out5(prog(t, sc.swap, 0.7));
    if (bp > 0) {
      ctx.save(); ctx.globalAlpha = (1 - prog(t, D - 0.36, 0.3));
      ring(R.cx, sc.by + sc.b.h / 2, lerp(sc.b.h * 0.4, Math.max(sc.b.w, sc.b.h) * 0.8, bp), 3 * S, PAL.accent, 1, 0, 1 - bp);
      ctx.restore();
    }
    drawBlock(sc.b, R.cx, sc.by, t, { type: "pop", t0: sc.swap + 0.1, stagger: 0.08, out: D - 0.25, hlAt: sc.swap + 0.6 });
    if (sc.k) drawBlock(sc.k, R.cx, sc.ky, t, { type: "fade", t0: sc.swap + 0.3, out: D - 0.36 });
  },
};

T.quote = {
  init(sc) {
    const p = sc.params, D = sc.duration;
    sc.q = tb(p.text, { size: (R.wide ? 66 : 72) * S, weight: 700, maxW: R.w * 0.88, maxLines: 5 });
    sc.au = p.author ? tb(p.author, { size: 40 * S, role: "body", weight: 600, maxW: R.w * 0.8, maxLines: 2, color: PAL.accent }) : null;
    sc.qy = stackY([sc.q, sc.au], [sc.au ? 50 * S : 0], R.y1 + 120 * S, R.y2);
    sc.ay = sc.qy + sc.q.h + 50 * S;
    place(sc.q, R.cx, sc.qy, { type: "rise", t0: 0.35, stagger: 0.12, out: D - 0.36 }, D);
    if (sc.au) place(sc.au, R.cx, sc.ay, { type: "fade", t0: 0.75, out: D - 0.36 }, D);
    sc.stars = p.stars || 0;
    for (let i = 0; i < sc.stars; i++) ev(1.2 + i * 0.12, "tick", 0.3);
  },
  draw(sc, t) {
    const D = sc.duration, out = 1 - prog(t, D - 0.36, 0.3);
    const qp = E.back(prog(t, 0.05, 0.6));
    ctx.save(); ctx.globalAlpha = 0.9 * out; setFont(360 * S * qp, 800, "“", "head"); ctx.fillStyle = PAL.accent; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(SPEC.rtl ? "”" : "“", R.cx, sc.qy - 70 * S); ctx.restore();
    drawBlock(sc.q, R.cx, sc.qy, t, { type: "rise", t0: 0.35, stagger: 0.12, out: D - 0.36 });
    if (sc.au) drawBlock(sc.au, R.cx, sc.ay, t, { type: "fade", t0: 0.75, out: D - 0.36 });
    for (let i = 0; i < sc.stars; i++) {
      const p = E.back(prog(t, 1.2 + i * 0.12, 0.45)); if (p <= 0) continue;
      const x = R.cx + (i - (sc.stars - 1) / 2) * 64 * S, y = sc.ay + (sc.au ? sc.au.h : 0) + 60 * S;
      ctx.save(); ctx.globalAlpha = out; ctx.translate(x, y); ctx.scale(p, p);
      const path = new Path2D(); ICONS.star(path); ctx.translate(-24 * S, -24 * S); ctx.scale(2 * S, 2 * S); ctx.fillStyle = PAL.accent; ctx.fill(path); ctx.restore();
    }
  },
};

T.showcase = {
  init(sc) {
    const p = sc.params, D = sc.duration;
    sc.im = IMG[p.image];
    sc.ti = p.title ? tb(p.title, { size: (R.wide ? 84 : 96) * S, maxW: R.wide ? R.w * 0.44 : R.w * 0.94, maxLines: 3, highlight: p.highlight, align: R.wide ? "start" : "center" }) : null;
    sc.su = p.subtitle ? tb(p.subtitle, { size: 44 * S, role: "body", maxW: R.wide ? R.w * 0.44 : R.w * 0.88, maxLines: 3, color: PAL.muted, align: R.wide ? "start" : "center" }) : null;
    if (R.wide) {
      sc.fw = R.w * 0.46; sc.fh = R.h * 0.92; sc.fx = SPEC.rtl ? R.x1 : R.x2 - sc.fw; sc.fy = R.cy - sc.fh / 2;
      sc.tx = SPEC.rtl ? R.x2 : R.x1; sc.ty = stackY([sc.ti, sc.su], [28 * S], R.y1, R.y2);
    } else {
      sc.fw = R.w * 0.86; const textH = (sc.ti ? sc.ti.h : 0) + (sc.su ? sc.su.h + 28 * S : 0);
      sc.fh = Math.min(R.h - textH - 90 * S, sc.fw * 1.2); sc.fx = R.cx - sc.fw / 2;
      sc.fy = lerp(R.y1, R.y2 - (sc.fh + 70 * S + textH), 0.35); sc.tx = R.cx; sc.ty = sc.fy + sc.fh + 70 * S;
    }
    sc.sy = sc.ty + (sc.ti ? sc.ti.h + 28 * S : 0);
    if (sc.ti) place(sc.ti, sc.tx, sc.ty, { type: "rise", t0: 0.45, out: D - 0.36 }, D);
    if (sc.su) place(sc.su, sc.tx, sc.sy, { type: "fade", t0: 0.75, out: D - 0.36 }, D);
    sc.chips = (p.chips || []).slice(0, 3).map((c, i) => ({ b: tb(c, { size: 36 * S, weight: 700, role: "body", maxW: sc.fw * 0.7, maxLines: 1, color: PAL.accentText }), d: 0.8 + i * 0.3, i }));
    sc.chips.forEach(c => {
      const side = (c.i % 2 === 0) !== SPEC.rtl;
      c.x = side ? sc.fx + 30 * S + c.b.w / 2 + 24 * S : sc.fx + sc.fw - 30 * S - c.b.w / 2 - 24 * S;
      c.y = sc.fy + sc.fh * (0.18 + c.i * 0.3);
      reg(c.b.text, c.x - c.b.w / 2 - 24 * S, c.y - c.b.h / 2, c.x + c.b.w / 2 + 24 * S, c.y + c.b.h / 2, c.d + 0.3, D - 0.25);
      ev(c.d, "pop", 0.4);
    });
    ev(0.05, "whoosh", 0.5);
  },
  draw(sc, t) {
    const D = sc.duration, p = sc.params, out = 1 - prog(t, D - 0.36, 0.3);
    const rp = E.out5(prog(t, 0, 0.9));
    ctx.save(); ctx.globalAlpha = out;
    // accent shapes behind the frame (depth)
    glow(sc.fx + sc.fw * 0.8, sc.fy + sc.fh * 0.2, sc.fw * 0.7, PAL.accent, 0.35 * rp);
    dotGrid(sc.fx - 30 * S, sc.fy + sc.fh - 120 * S, 6, 6, 26 * S, 3.5 * S, PAL.accent, 0.6 * rp);
    ctx.save();
    const shape = p.frame || "arch";
    const reveal = lerp(0.0, 1, rp);
    const fy = sc.fy + (1 - reveal) * sc.fh * 0.5, fh = sc.fh * reveal;
    ctx.beginPath();
    if (shape === "circle") { const r = Math.min(sc.fw, sc.fh) / 2 * reveal; ctx.arc(sc.fx + sc.fw / 2, sc.fy + sc.fh / 2, r, 0, 7); }
    else if (shape === "arch") { const r = sc.fw / 2; ctx.moveTo(sc.fx, fy + fh); ctx.lineTo(sc.fx, fy + Math.min(r, fh)); ctx.arc(sc.fx + r, fy + Math.min(r, fh), r, Math.PI, 0); ctx.lineTo(sc.fx + sc.fw, fy + fh); ctx.closePath(); }
    else ctx.roundRect(sc.fx, fy, sc.fw, fh, 46 * S);
    ctx.clip();
    if (sc.im) {
      const z = 1.12 + 0.08 * (t / D), px = (SPEC.rtl ? 1 : -1) * 30 * S * (t / D);
      drawCover(sc.im, sc.fx, sc.fy, sc.fw, sc.fh, z, 0.5, 0.5, px, 0);
      const gg = ctx.createLinearGradient(0, sc.fy, 0, sc.fy + sc.fh);
      gg.addColorStop(0, rgba(PAL.primary, 0.05)); gg.addColorStop(1, rgba(PAL.bg, 0.55));
      ctx.fillStyle = gg; ctx.fillRect(sc.fx, sc.fy, sc.fw, sc.fh);
    } else { ctx.fillStyle = PAL.card; ctx.fillRect(sc.fx, sc.fy, sc.fw, sc.fh); icon(p.icon || "spark", sc.fx + sc.fw / 2, sc.fy + sc.fh / 2, sc.fw * 0.35, PAL.accent, 1.4); }
    ctx.restore();
    for (const c of sc.chips) {
      const q = E.back(prog(t, c.d, 0.55)); if (q <= 0) continue;
      const fl = Math.sin(t * 1.6 + c.i) * 6 * S;
      ctx.save(); ctx.translate(c.x, c.y + fl); ctx.scale(q, q);
      ctx.shadowColor = "rgba(0,0,0,.3)"; ctx.shadowBlur = 24 * S;
      const w = c.b.w + 48 * S, h = c.b.h + 14 * S; rr(-w / 2, -h / 2, w, h, h / 2); ctx.fillStyle = PAL.accent; ctx.fill(); ctx.restore();
      ctx.save(); ctx.translate(0, fl); drawBlock(c.b, c.x, c.y - c.b.h / 2, t, { type: "fade", t0: c.d + 0.1, dur: 0.3, shadow: false }); ctx.restore();
    }
    ctx.restore();
    if (sc.ti) drawBlock(sc.ti, sc.tx, sc.ty, t, { type: "rise", t0: 0.45, out: D - 0.36, hlAt: 1.1 });
    if (sc.su) drawBlock(sc.su, sc.tx, sc.sy, t, { type: "fade", t0: 0.75, out: D - 0.36 });
  },
};

/** Brand mark: the user's logo, or a temporary monogram built from the name. */
function drawMark(x, y, size, p, t) {
  const id = SPEC.identity || {};
  const logo = id.logo && IMG[id.logo];
  if (logo) {
    const s = Math.min(Math.min(size * 2.6, R.w * 0.8) / logo.width, size / logo.height) * lerp(0.7, 1, E.back(p));
    ctx.save(); ctx.globalAlpha *= clamp(p * 2); ctx.drawImage(logo, x - logo.width * s / 2, y - logo.height * s / 2, logo.width * s, logo.height * s); ctx.restore();
    return;
  }
  const r = size / 2;
  ctx.save(); ctx.translate(x, y);
  const q = E.back(prog(p, 0.1, 0.9));
  ctx.scale(q, q);
  const g = ctx.createLinearGradient(-r, -r, r, r); g.addColorStop(0, PAL.primaryLight); g.addColorStop(1, PAL.primary);
  ctx.beginPath(); if (id.shape === "squircle") ctx.roundRect(-r, -r, 2 * r, 2 * r, r * 0.42); else ctx.arc(0, 0, r, 0, 7);
  ctx.fillStyle = g; ctx.fill();
  ctx.restore();
  ring(x, y, r * 1.18, 6 * S, PAL.accent, E.out(prog(p, 0, 1)), -Math.PI / 2 + t * 0.2);
  const ini = id.initials || "";
  if (ini) { ctx.save(); ctx.globalAlpha *= clamp((p - 0.3) * 2); setFont(r * (ini.length > 2 ? 0.62 : 0.8), 800, ini, "head"); ctx.fillStyle = "#ffffff"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.direction = isAr(ini) ? "rtl" : "ltr"; ctx.fillText(ini, x, y + r * 0.06); ctx.restore(); }
}

T.cta = {
  init(sc) {
    const p = sc.params, D = sc.duration, id = SPEC.identity || {};
    sc.mark = (p.mark !== false) && (id.initials || id.logo);
    const bg = R.tall ? 1.2 : 1;
    sc.ms = (R.wide ? 190 : 250) * bg * S;
    sc.nm = (p.name || id.name) ? tb(p.name || id.name, { size: (R.wide ? 72 : 84) * bg * S, maxW: R.w * 0.92, maxLines: 2, weight: 800 }) : null;
    sc.ti = p.title ? tb(p.title, { size: (R.wide ? 60 : 56) * bg * S, role: "body", weight: 600, maxW: R.w * 0.9, maxLines: 3, color: PAL.muted }) : null;
    sc.bt = p.button ? tb(p.button, { size: 52 * bg * S, weight: 800, maxW: R.w * 0.72, maxLines: 1, color: PAL.accentText }) : null;
    sc.sub = p.sub ? tb(p.sub, { size: 40 * bg * S, role: "body", weight: 600, maxW: R.w * 0.86, maxLines: 2, color: PAL.text }) : null;
    const gaps = [46 * bg * S, 40 * bg * S, 70 * bg * S, 44 * bg * S];
    const btH = sc.bt ? sc.bt.h + 44 * S : 0;
    const hs = [sc.mark ? sc.ms * 1.2 : 0, sc.nm ? sc.nm.h : 0, sc.ti ? sc.ti.h : 0, btH, sc.sub ? sc.sub.h : 0];
    const tot = hs.reduce((a, b) => a + b, 0) + gaps.reduce((a, g, i) => a + (hs[i + 1] ? g : 0), 0);
    let y = lerp(R.y1, R.y2 - tot, 0.45);
    sc.my = y + (sc.mark ? sc.ms * 0.6 : 0); y += hs[0] + (hs[0] ? gaps[0] : 0);
    sc.ny = y; y += hs[1] + (hs[1] ? gaps[1] : 0);
    sc.ty = y; y += hs[2] + (hs[2] ? gaps[2] : 0);
    sc.by = y; y += hs[3] + (hs[3] ? gaps[3] : 0);
    sc.sy = y;
    const D0 = sc.mark ? 0.55 : 0.2;
    sc.t = { nm: D0, ti: D0 + 0.35, bt: D0 + 0.7, sub: D0 + 0.95 };
    if (sc.nm) place(sc.nm, R.cx, sc.ny, { type: "rise", t0: sc.t.nm }, D);
    if (sc.ti) place(sc.ti, R.cx, sc.ty, { type: "fade", t0: sc.t.ti }, D);
    if (sc.bt) reg(sc.bt.text, R.cx - sc.bt.w / 2 - 50 * S, sc.by, R.cx + sc.bt.w / 2 + 50 * S, sc.by + btH, sc.t.bt + 0.4, D);
    if (sc.sub) place(sc.sub, R.cx, sc.sy, { type: "fade", t0: sc.t.sub }, D);
    if (sc.mark) ev(0.35, "hit", 1);
    ev(sc.t.bt, "pop", 0.6);
    ev(0.0, "riser_end", 1);
  },
  draw(sc, t) {
    const D = sc.duration;
    // light rays / rings converging on the mark
    const cy = sc.mark ? sc.my : R.cy;
    for (let i = 0; i < 3; i++) { const q = ((t * 0.35 + i / 3) % 1); ring(R.cx, cy, lerp(sc.ms * 0.7, Math.max(W, H) * 0.7, q), 2 * S, PAL.primaryLight, 1, 0, 0.4 * (1 - q)); }
    if (sc.mark) { glow(R.cx, sc.my, sc.ms * 1.6, PAL.primary, 0.55 * E.out(prog(t, 0.1, 0.8))); drawMark(R.cx, sc.my, sc.ms, prog(t, 0.05, 0.9), t); }
    if (sc.nm) drawBlock(sc.nm, R.cx, sc.ny, t, { type: "rise", t0: sc.t.nm });
    if (sc.ti) drawBlock(sc.ti, R.cx, sc.ty, t, { type: "fade", t0: sc.t.ti });
    if (sc.bt) {
      const q = E.back(prog(t, sc.t.bt, 0.6)); if (q > 0) {
        const pulse = 1 + 0.035 * Math.sin(Math.max(0, t - sc.t.bt - 0.6) * 5.5);
        const w = sc.bt.w + 100 * S, h = sc.bt.h + 44 * S;
        ctx.save(); ctx.translate(R.cx, sc.by + h / 2); ctx.scale(q * pulse, q * pulse);
        ctx.shadowColor = rgba(PAL.accent, 0.55); ctx.shadowBlur = 50 * S;
        rr(-w / 2, -h / 2, w, h, h / 2); ctx.fillStyle = PAL.accent; ctx.fill(); ctx.shadowColor = "transparent";
        // shine sweep across the button
        const sx = lerp(-w, w, prog((t - sc.t.bt - 0.8) % 2.2, 0, 0.7));
        ctx.clip(); const sg = ctx.createLinearGradient(sx - 60 * S, 0, sx + 60 * S, 0);
        sg.addColorStop(0, "rgba(255,255,255,0)"); sg.addColorStop(0.5, "rgba(255,255,255,0.45)"); sg.addColorStop(1, "rgba(255,255,255,0)");
        ctx.fillStyle = sg; ctx.fillRect(-w / 2, -h / 2, w, h);
        ctx.restore();
        ctx.save(); ctx.translate(R.cx, sc.by + h / 2); ctx.scale(q * pulse, q * pulse); ctx.translate(-R.cx, -(sc.by + h / 2));
        drawBlock(sc.bt, R.cx, sc.by + 22 * S, t, { type: "fade", t0: sc.t.bt + 0.1, dur: 0.3, shadow: false }); ctx.restore();
      }
    }
    if (sc.sub) drawBlock(sc.sub, R.cx, sc.sy, t, { type: "fade", t0: sc.t.sub });
  },
};

T.logo_reveal = {
  init(sc) {
    const p = sc.params, id = SPEC.identity || {}, D = sc.duration;
    sc.ms = (R.wide ? 220 : 260) * S;
    sc.nm = tb(p.name || id.name || "", { size: (R.wide ? 86 : 96) * S, maxW: R.w * 0.9, maxLines: 2 });
    sc.tg = p.tagline ? tb(p.tagline, { size: 44 * S, role: "body", maxW: R.w * 0.86, maxLines: 2, color: PAL.muted }) : null;
    const tot = sc.ms * 1.2 + 40 * S + sc.nm.h + (sc.tg ? sc.tg.h + 24 * S : 0);
    const y = lerp(R.y1, R.y2 - tot, 0.45);
    sc.my = y + sc.ms * 0.6; sc.ny = y + sc.ms * 1.2 + 40 * S; sc.ty = sc.ny + sc.nm.h + 24 * S;
    place(sc.nm, R.cx, sc.ny, { type: "rise", t0: 0.6, out: D - 0.36 }, D);
    if (sc.tg) place(sc.tg, R.cx, sc.ty, { type: "fade", t0: 0.7, out: D - 0.36 }, D);
    ev(0.3, "hit", 0.9);
  },
  draw(sc, t) {
    const D = sc.duration, out = 1 - prog(t, D - 0.36, 0.3);
    ctx.save(); ctx.globalAlpha = out;
    glow(R.cx, sc.my, sc.ms * 1.8, PAL.primary, 0.6 * E.out(prog(t, 0, 0.8)));
    drawMark(R.cx, sc.my, sc.ms, prog(t, 0.05, 0.9), t);
    ctx.restore();
    drawBlock(sc.nm, R.cx, sc.ny, t, { type: "rise", t0: 0.6, out: D - 0.36 });
    if (sc.tg) drawBlock(sc.tg, R.cx, sc.ty, t, { type: "fade", t0: 0.7, out: D - 0.36 });
  },
};

// ---------------------------------------------------------------- frame
function initScene(sc) {
  REG = []; EVENTS = [];
  const tpl = T[sc.template];
  if (!tpl) throw new Error("unknown motion template: " + sc.template);
  sc.params = sc.params || {};
  tpl.init(sc);
  if (sc.tin === "panels" || sc.tin === "circle") EVENTS.push({ t: 0.02, type: "whoosh", strength: 0.8 });
  sc.reg = REG; sc.events = EVENTS;
}
function drawFrame(sc, t) {
  const gt = sc.t0 + t;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = "source-over";
  if (!SPEC.alpha) world(gt); else ctx.clearRect(0, 0, W, H);
  ctx.save();
  // simulated camera: slow push-in and drift, different per scene
  const D = sc.duration, cam = sc.camera || "push";
  let cz = 1, cx = 0, cy = 0;
  if (cam === "push") cz = 1 + 0.045 * E.sine(t / D);
  else if (cam === "pull") cz = 1.05 - 0.045 * E.sine(t / D);
  else if (cam === "drift") { cz = 1.02; cx = (SPEC.rtl ? 1 : -1) * 22 * S * (t / D - 0.5); }
  cy = Math.sin(gt * 0.6) * 4 * S;
  ctx.translate(W / 2 + cx, H / 2 + cy); ctx.scale(cz, cz); ctx.translate(-W / 2, -H / 2);
  ctx.globalAlpha = fgTransition(sc, t);
  T[sc.template].draw(sc, t);
  ctx.restore();
  ctx.globalAlpha = 1;
  if (!SPEC.alpha) {
    if (sc.tin === "panels" || sc.tin === "circle") transitionCover(sc.tin, 1 - prog(t, 0, 0.5), true);
    if (sc.tout === "panels" || sc.tout === "circle") transitionCover(sc.tout, prog(t, D - 0.5, 0.5), false);
    finish(gt);
  }
}

// ---------------------------------------------------------------- boot
async function post(path, body) { const r = await fetch(path, { method: "POST", body }); if (!r.ok) throw new Error("server refused " + path); }
async function boot() {
  SPEC = await (await fetch("/spec.json")).json();
  W = SPEC.width; H = SPEC.height; FPS = SPEC.fps; S = Math.min(W, H) / 1080;
  LOOK = SPEC.look; PAL = LOOK.palette;
  PAL.hl = PAL.hl || (PAL.light ? PAL.primary : PAL.accent);   // highlighted words: accent colour, always readable
  const [t, r, b, l] = SPEC.safe;
  R = { x1: l * W, y1: t * H, x2: W - r * W, y2: H - b * H }; R.w = R.x2 - R.x1; R.h = R.y2 - R.y1; R.cx = (R.x1 + R.x2) / 2; R.cy = (R.y1 + R.y2) / 2; R.wide = W / H > 1.2;
  R.tall = H / W > 1.5;
  if (JOB === "score") { const wav = await renderScore(SPEC.score); await post("/score", wav); await post("/done/" + JOB, ""); return; }
  for (const f of SPEC.fonts) { try { const ff = new FontFace(f.family, `url(${f.url})`, { weight: f.weight || "100 900" }); await ff.load(); document.fonts.add(ff); } catch (e) { /* fallback fonts still render */ } }
  await document.fonts.ready;
  await loadImages(SPEC.images || []);
  cv = document.getElementById("c"); cv.width = W; cv.height = H;
  ctx = cv.getContext("2d", { alpha: !!SPEC.alpha, willReadFrequently: true });
  setupWorld();
  if (JOB === "layout") {
    const out = SPEC.scenes.map(sc => { initScene(sc); return { id: sc.id, texts: sc.reg, events: sc.events }; });
    await post("/layout", JSON.stringify(out)); await post("/done/" + JOB, ""); return;
  }
  const k = Number(JOB.split(":")[1]);
  const sc = SPEC.scenes[k];
  initScene(sc);
  const n = Math.round(sc.duration * FPS);
  const start = Number(Q.get("from") || 0), end = Math.min(n, Number(Q.get("to") || n));
  for (let i = start; i < end; i++) {
    drawFrame(sc, i / FPS);
    const px = ctx.getImageData(0, 0, W, H).data;
    await post(`/frame/${k}/${i}`, px);
  }
  await post("/done/" + JOB, "");
}
boot().catch(e => fetch("/error/" + JOB, { method: "POST", body: String((e && e.stack) || e) }));
