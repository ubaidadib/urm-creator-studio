# Interaction modes

Switching: the user may say «حوّل إلى وضع المبدع», "pro mode", «أريد تحكمًا أكثر», «بسّطها لي». Confirm in
one sentence and save: `studio.py settings --mode beginner|creator|pro`. Project-level override is stored
in `project.json` → `mode`.

## Beginner (default) — «وضع المبتدئ»
- One question per message, numbered choices, recommended option first, «اختر لي» always available.
- Never mention plan.json, fps, codecs, file paths (except the final folder in friendly words).
- Always: plan summary → approval → preview → approval → final.
- Offer at most 2 follow-up options after delivery.

## Creator — «وضع المبدع»
Adds choices for:
- Style: elegant / energetic / minimal / bold / playful (maps to motion presets in `motion-graphics.md`).
- Caption look: box / outline / brand colour; position bottom or lower.
- Text animations per scene: fade, slide up, side slide, zoom, word by word.
- Transitions: fade, slide (direction follows language), dissolve, fade to black, none.
- Music volume, ducking on/off, sound effects on transitions.
- Show the plan as a table: # | type | duration | on-screen text | animation.
- Can ask several related questions in one message (max 3).

## Professional — «وضع المحترف»
- Show and accept direct edits to `plan.json` (see `plan-reference.md`); frame-accurate `start`/`end`.
- Expose: fps (24/25/30/50/60), quality (`standard`/`high`), framing (`fill`/`fit_blur`/`fit_color`, focus),
  speed ramps per clip (0.25–4×), per-clip volume, LUFS target, intermediate retention (`keep_work`),
  multi-format exports, custom CSS per text (`style.css`), custom fonts.
- Provide shot lists, timing tables, creative-direction notes, and QC JSON on request.
- Optional advanced motion design with Remotion is out of scope for the bundled engine; if the user
  explicitly wants it and has Node.js, explain it is a separate install and ask before setting it up.
