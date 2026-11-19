/* URM Creator Studio — original soundtrack synthesiser.
 *
 * Composes and renders an original music bed plus sound design with the Web Audio API in an
 * OfflineAudioContext (faster than real time, deterministic, no samples, no downloads, no licence questions:
 * every sound is generated here). The arrangement follows the edit: it builds through the video, lands a hit
 * on the brand/CTA reveal and rings out at the end. Sound effects sit on the visual events the motion
 * templates report (transitions, pops, reveals).
 *
 * spec = { duration, bpm, mood, seed, cuts:[t…], events:[{t,type,strength}], climax:t|null, sfx:true }
 */
"use strict";

const MOODS = {
  // root midi note, scale degrees for chords (as semitone offsets), instrumentation switches
  inspiring: { bpm: 104, root: 50, prog: [[0, 4, 7, 11], [7, 11, 14, 17], [9, 12, 16, 19], [5, 9, 12, 16]], drums: "soft", arp: true, pad: 0.8, bright: 1 },
  corporate: { bpm: 98, root: 48, prog: [[0, 4, 7, 14], [9, 12, 16, 19], [5, 9, 12, 16], [7, 11, 14, 17]], drums: "soft", arp: true, pad: 0.7, bright: 0.9 },
  energetic: { bpm: 122, root: 45, prog: [[0, 3, 7, 10], [8, 12, 15, 19], [3, 7, 10, 14], [10, 14, 17, 21]], drums: "four", arp: true, pad: 0.6, bright: 1.2 },
  calm: { bpm: 80, root: 52, prog: [[0, 4, 7, 11], [5, 9, 12, 16], [9, 12, 16, 19], [7, 11, 14, 17]], drums: "none", arp: true, pad: 1, bright: 0.7 },
  luxury: { bpm: 84, root: 45, prog: [[0, 3, 7, 10], [5, 8, 12, 15], [10, 14, 17, 20], [7, 10, 14, 17]], drums: "pulse", arp: false, pad: 1, bright: 0.6 },
  playful: { bpm: 116, root: 53, prog: [[0, 4, 7, 12], [5, 9, 12, 17], [7, 11, 14, 19], [0, 4, 7, 12]], drums: "bounce", arp: true, pad: 0.6, bright: 1.2 },
};
const mtof = m => 440 * Math.pow(2, (m - 69) / 12);

function noiseBuffer(ac, seconds, seed) {
  const r = rng(seed || 3), n = Math.floor(ac.sampleRate * seconds), b = ac.createBuffer(1, n, ac.sampleRate), d = b.getChannelData(0);
  for (let i = 0; i < n; i++) d[i] = r() * 2 - 1;
  return b;
}
function reverbIR(ac, seconds, seed) {
  const r = rng(seed || 11), n = Math.floor(ac.sampleRate * seconds), b = ac.createBuffer(2, n, ac.sampleRate);
  for (let c = 0; c < 2; c++) { const d = b.getChannelData(c); for (let i = 0; i < n; i++) d[i] = (r() * 2 - 1) * Math.pow(1 - i / n, 3.2); }
  return b;
}
function env(g, t, a, peak, d, sus, rel, end) {
  g.gain.setValueAtTime(0.0001, t);
  g.gain.linearRampToValueAtTime(peak, t + a);
  g.gain.exponentialRampToValueAtTime(Math.max(0.0001, peak * sus), t + a + d);
  g.gain.setValueAtTime(Math.max(0.0001, peak * sus), Math.max(t + a + d, end));
  g.gain.exponentialRampToValueAtTime(0.0001, Math.max(t + a + d, end) + rel);
}

async function renderScore(spec) {
  const SR = 48000, dur = spec.duration, tail = 0.05;
  const ac = new OfflineAudioContext(2, Math.ceil(SR * (dur + tail)), SR);
  const mood = MOODS[spec.mood] || MOODS.inspiring;
  const bpm = spec.bpm || mood.bpm, beat = 60 / bpm, bar = beat * 4;
  const r = rng(spec.seed || 5);
  const noise = noiseBuffer(ac, 2, spec.seed);

  // ---- buses: music (with reverb) and sfx, then a gentle master glue compressor
  const master = ac.createDynamicsCompressor(); master.threshold.value = -16; master.ratio.value = 3; master.attack.value = 0.01; master.release.value = 0.25;
  const out = ac.createGain(); out.gain.value = 0.9; master.connect(out); out.connect(ac.destination);
  const music = ac.createGain(); music.connect(master);
  const verb = ac.createConvolver(); verb.buffer = reverbIR(ac, 2.6, spec.seed); const verbGain = ac.createGain(); verbGain.gain.value = 0.32; verb.connect(verbGain); verbGain.connect(master);
  const sfx = ac.createGain(); sfx.gain.value = spec.sfx === false ? 0 : 0.85; sfx.connect(master);
  // global music envelope: fade in, duck slightly under the final reveal, ring out
  music.gain.setValueAtTime(0.0001, 0); music.gain.linearRampToValueAtTime(1, 0.35);
  music.gain.setValueAtTime(1, Math.max(0.4, dur - 1.6)); music.gain.linearRampToValueAtTime(0.0001, dur);

  const climax = spec.climax != null ? spec.climax : dur * 0.8;
  const buildIn = Math.min(bar * 2, Math.max(bar, dur * 0.12));   // drums enter after the hook
  const nBars = Math.ceil(dur / bar) + 1;

  // ---- pad: detuned saws through a slowly opening low-pass filter
  for (let b = 0; b < nBars; b++) {
    const t0 = b * bar; if (t0 >= dur) break;
    const ch = mood.prog[b % mood.prog.length];
    const lp = ac.createBiquadFilter(); lp.type = "lowpass"; lp.Q.value = 0.7;
    const open = 600 + 1800 * mood.bright * Math.min(1, t0 / Math.max(1, climax));
    lp.frequency.setValueAtTime(open * 0.7, t0); lp.frequency.linearRampToValueAtTime(open, t0 + bar);
    const g = ac.createGain(); env(g, Math.max(0, t0 - 0.12), 0.3, 0.05 * mood.pad, 0.8, 0.85, 0.5, t0 + bar + 0.05);  // chords overlap: no gap at the bar line
    lp.connect(g); g.connect(music); g.connect(verb);
    ch.forEach((semi, i) => {
      for (const det of [-7, 6]) {
        const o = ac.createOscillator(); o.type = "sawtooth"; o.frequency.value = mtof(mood.root + 12 + semi); o.detune.value = det + i;
        o.connect(lp); o.start(Math.max(0, t0 - 0.12)); o.stop(t0 + bar + 1);
      }
    });
    // bass on the root (sub sine + soft triangle)
    const bg = ac.createGain(); env(bg, t0, 0.02, b * bar < buildIn ? 0.09 : 0.16, 0.4, 0.7, 0.12, t0 + bar - 0.08); bg.connect(music);
    for (const [type, mul] of [["sine", 1], ["triangle", 2]]) {
      const o = ac.createOscillator(); o.type = type; o.frequency.value = mtof(mood.root - 12 + ch[0]) * mul; const og = ac.createGain(); og.gain.value = type === "sine" ? 1 : 0.25;
      o.connect(og); og.connect(bg); o.start(t0); o.stop(t0 + bar + 0.6);
    }
  }

  // ---- arpeggio pluck (sixteenths in the energetic moods, eighths otherwise)
  if (mood.arp) {
    const step = mood.drums === "four" ? beat / 4 : beat / 2;
    const dl = ac.createDelay(1); dl.delayTime.value = beat * 0.75; const fb = ac.createGain(); fb.gain.value = 0.28; const dlw = ac.createGain(); dlw.gain.value = 0.25;
    dl.connect(fb); fb.connect(dl); dl.connect(dlw); dlw.connect(music);
    const pattern = [0, 1, 2, 3, 2, 1, 2, 3];
    for (let t = 0, i = 0; t < dur - 0.3; t += step, i++) {
      const b = Math.floor(t / bar), ch = mood.prog[b % mood.prog.length];
      const semi = ch[pattern[i % pattern.length]] + (i % 16 >= 8 ? 12 : 0);
      const o = ac.createOscillator(); o.type = "triangle"; o.frequency.value = mtof(mood.root + 24 + semi);
      const o2 = ac.createOscillator(); o2.type = "sine"; o2.frequency.value = mtof(mood.root + 36 + semi);
      const g = ac.createGain(); const lvl = (0.045 + (t > buildIn ? 0.02 : 0)) * (i % 2 ? 0.75 : 1);
      env(g, t, 0.004, lvl, 0.18, 0.15, 0.12, t + 0.05);
      const g2 = ac.createGain(); g2.gain.value = 0.25;
      o.connect(g); o2.connect(g2); g2.connect(g); g.connect(music); g.connect(dl); g.connect(verb);
      o.start(t); o2.start(t); o.stop(t + 0.6); o2.stop(t + 0.6);
    }
  }

  // ---- drums (synthesised)
  function kick(t, v = 1) {
    const o = ac.createOscillator(); o.type = "sine"; o.frequency.setValueAtTime(150, t); o.frequency.exponentialRampToValueAtTime(42, t + 0.14);
    const g = ac.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(0.55 * v, t + 0.004); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.38);
    o.connect(g); g.connect(music); o.start(t); o.stop(t + 0.4);
  }
  function hat(t, v = 1, open = false) {
    const s = ac.createBufferSource(); s.buffer = noise; const hp = ac.createBiquadFilter(); hp.type = "highpass"; hp.frequency.value = 8000;
    const g = ac.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(0.06 * v, t + 0.002); g.gain.exponentialRampToValueAtTime(0.0001, t + (open ? 0.22 : 0.05));
    s.connect(hp); hp.connect(g); g.connect(music); s.start(t, r() * 1.5); s.stop(t + 0.3);
  }
  function clap(t, v = 1) {
    const s = ac.createBufferSource(); s.buffer = noise; const bp = ac.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 1500; bp.Q.value = 0.9;
    const g = ac.createGain(); g.gain.setValueAtTime(0.0001, t);
    for (const k of [0, 0.012, 0.024]) { g.gain.linearRampToValueAtTime(0.16 * v, t + k + 0.002); g.gain.exponentialRampToValueAtTime(0.02, t + k + 0.011); }
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.2);
    s.connect(bp); bp.connect(g); g.connect(music); g.connect(verb); s.start(t, r() * 1.5); s.stop(t + 0.3);
  }
  if (mood.drums !== "none") {
    for (let t = buildIn, i = 0; t < dur - 1.2; t += beat / 2, i++) {
      const onBeat = i % 2 === 0, beatN = Math.floor(i / 2) % 4;
      if (mood.drums === "four") { if (onBeat) kick(t); hat(t + (onBeat ? 0 : 0), onBeat ? 0.5 : 1, !onBeat); if (onBeat && beatN % 2 === 1) clap(t); }
      else if (mood.drums === "soft") { if (onBeat && (beatN === 0 || beatN === 2)) kick(t, 0.8); if (onBeat && beatN % 2 === 1 && t > buildIn + bar) clap(t, 0.8); hat(t, onBeat ? 0.35 : 0.6); }
      else if (mood.drums === "pulse") { if (onBeat && beatN === 0) kick(t, 0.7); if (!onBeat) hat(t, 0.35); }
      else if (mood.drums === "bounce") { if (onBeat && beatN !== 3) kick(t, 0.75); if (onBeat && beatN % 2 === 1) clap(t, 0.9); hat(t, 0.5); }
    }
  }

  // ---- sound design on the visual events
  function whoosh(t, v) {
    const t0 = Math.max(0, t - 0.3);   // the swell starts before the cut it belongs to
    const s = ac.createBufferSource(); s.buffer = noise; const bp = ac.createBiquadFilter(); bp.type = "bandpass"; bp.Q.value = 1.2;
    bp.frequency.setValueAtTime(300, t0); bp.frequency.exponentialRampToValueAtTime(4200, t + 0.12); bp.frequency.exponentialRampToValueAtTime(900, t + 0.4);
    const g = ac.createGain(); g.gain.setValueAtTime(0.0001, t0); g.gain.linearRampToValueAtTime(0.32 * v, t + 0.05); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.45);
    const pan = ac.createStereoPanner(); pan.pan.setValueAtTime(-0.6, t0); pan.pan.linearRampToValueAtTime(0.6, t + 0.4);
    s.connect(bp); bp.connect(g); g.connect(pan); pan.connect(sfx); s.start(t0, r()); s.stop(t + 0.5);
  }
  function pop(t, v) {
    const o = ac.createOscillator(); o.type = "sine"; o.frequency.setValueAtTime(900 + r() * 500, t); o.frequency.exponentialRampToValueAtTime(320, t + 0.08);
    const g = ac.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(0.16 * v, t + 0.003); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.12);
    o.connect(g); g.connect(sfx); g.connect(verb); o.start(t); o.stop(t + 0.15);
  }
  function tick(t, v) {
    const o = ac.createOscillator(); o.type = "triangle"; o.frequency.value = 2200 + r() * 800;
    const g = ac.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(0.07 * v, t + 0.002); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.05);
    o.connect(g); g.connect(sfx); o.start(t); o.stop(t + 0.06);
  }
  function hit(t, v) {
    kick(t, 1.1 * v);
    const s = ac.createBufferSource(); s.buffer = noise; const lp = ac.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 2400;
    const g = ac.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(0.22 * v, t + 0.005); g.gain.exponentialRampToValueAtTime(0.0001, t + 1.4);
    s.connect(lp); lp.connect(g); g.connect(sfx); g.connect(verb); s.start(t, r()); s.stop(t + 1.5);
    // shimmer chord
    const ch = mood.prog[0];
    ch.forEach(semi => { const o = ac.createOscillator(); o.type = "triangle"; o.frequency.value = mtof(mood.root + 24 + semi); const og = ac.createGain(); env(og, t, 0.01, 0.05 * v, 0.4, 0.4, 1.4, t + 0.5); o.connect(og); og.connect(music); og.connect(verb); o.start(t); o.stop(t + 2.4); });
  }
  function riser(tEnd, len, v) {
    const t = Math.max(0, tEnd - len);
    const s = ac.createBufferSource(); s.buffer = noise; s.loop = true; const bp = ac.createBiquadFilter(); bp.type = "bandpass"; bp.Q.value = 2;
    bp.frequency.setValueAtTime(400, t); bp.frequency.exponentialRampToValueAtTime(6000, tEnd);
    const g = ac.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.14 * v, tEnd - 0.02); g.gain.linearRampToValueAtTime(0.0001, tEnd + 0.03);
    s.connect(bp); bp.connect(g); g.connect(sfx); s.start(t); s.stop(tEnd + 0.1);
  }
  const fx = { whoosh, pop, tick, hit };
  for (const e of spec.events || []) {
    if (e.t < 0 || e.t > dur) continue;
    if (e.type === "riser_end") riser(e.t, Math.min(1.6, Math.max(0.5, e.t)), e.strength || 1);
    else if (fx[e.type]) fx[e.type](Math.max(0.01, e.t), e.strength || 1);
  }

  const buf = await ac.startRendering();
  return toWav(buf, Math.round(dur * SR));
}

function toWav(buf, frames) {
  const ch = buf.numberOfChannels, n = Math.min(frames, buf.length), bytes = 44 + n * ch * 2;
  const ab = new ArrayBuffer(bytes), v = new DataView(ab);
  const w = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
  w(0, "RIFF"); v.setUint32(4, bytes - 8, true); w(8, "WAVE"); w(12, "fmt "); v.setUint32(16, 16, true); v.setUint16(20, 1, true);
  v.setUint16(22, ch, true); v.setUint32(24, buf.sampleRate, true); v.setUint32(28, buf.sampleRate * ch * 2, true); v.setUint16(32, ch * 2, true);
  v.setUint16(34, 16, true); w(36, "data"); v.setUint32(40, n * ch * 2, true);
  const data = []; for (let c = 0; c < ch; c++) data.push(buf.getChannelData(c));
  let o = 44;
  for (let i = 0; i < n; i++) for (let c = 0; c < ch; c++) { const s = Math.max(-1, Math.min(1, data[c][i])); v.setInt16(o, s < 0 ? s * 0x8000 : s * 0x7FFF, true); o += 2; }
  return new Blob([ab], { type: "audio/wav" });
}
