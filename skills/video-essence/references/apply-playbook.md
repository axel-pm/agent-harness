# apply-playbook.md — translating essence into a target medium

The essence spec is medium-agnostic. Applying it means re-expressing each dimension in the target's
own vocabulary. The target changes which dimensions carry literally, which translate, and which drop.

## → Another video
The most direct transfer.
- **Carry literally:** visual style, motion/pacing, transitions, structure, audio feel.
- **Translate:** the topic (new subject, same beats/energy curve).
- **Build:** if rendering in code (Remotion/CSS/SVG animation), specify per-scene timing, easing, and
  transition types from the spec. Keep the signature move.

## → Landing page / web
Motion becomes interaction; time becomes scroll.
- **Visual style → design tokens:** palette, type scale, spacing, treatment. If the site has a brand
  system, brand wins — use essence for *mood*, not to override tokens.
- **Motion/pacing → transitions & scroll:** cut rhythm → section reveal cadence; easing → CSS easing;
  energy curve → where you place emphasis / animation density.
- **Structure/beats → section order:** hook = hero, arc = section flow, ending = CTA.
- **Tone → copy voice.**

## → Slide deck
- **Beats → slides:** one beat per slide (or per build). Beat timing → talk pacing.
- **Visual style → template:** master slide palette/type/composition.
- **Motion → build/transition choices** (restrained — decks aren't films).
- **Signature move → a recurring slide device** (a repeated layout, a running visual).

## → Document / proposal
Literal motion drops; structure and tone do the work.
- **Structure/beats → section architecture + narrative order.**
- **Tone/voice → prose register.**
- **Visual style → light touches:** rule style, type hierarchy, accent — within the doc's system.
- Do **not** force animation metaphors into static copy.

## → Animation / motion graphic
- **Motion/pacing + signature technique are the point** — specify easing curves, transition types,
  element choreography, and the energy curve frame-accurately.
- **Visual style → the asset look.**
- **Structure → the timeline.**

## Reconciling with a house style
When the target already has a design system (brand tokens, voice), treat **essence as direction and
the house style as law**: borrow the reference's *rhythm, structure, and mood*, express them through
the target's own colors/type/components. Never let a reference override an owned brand.

## Then: fidelity check
For each spec dimension, record **match / adapted / dropped** and the reason. That comparison is part
of the deliverable — it shows the transfer was deliberate.
