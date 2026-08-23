# CivicAI Design Direction

## Three initial approaches

### Theme Name: Civic Editorial
Very Brief Intro: A warm, newspaper-inspired civic service with strong typography, thin rules, and intentional asymmetry. It makes complex systems feel legible, human, and grounded.
Probability: 0.07

### Theme Name: Quiet Utility
Very Brief Intro: A restrained productivity workspace with pale surfaces, compact navigation, and highly legible information hierarchy. It feels dependable and efficient without becoming corporate.
Probability: 0.03

### Theme Name: Public Signal
Very Brief Intro: A slightly bolder civic identity using a vivid vermilion accent, oversized numerals, and directional lines to turn public information into momentum. It feels optimistic, direct, and action-oriented.
Probability: 0.08

## Chosen approach: Civic Editorial

### Design Movement
Contemporary editorial design informed by public-interest publishing, Swiss information design, and premium productivity software.

### Core Principles
1. **Clarity before decoration:** every visual element must reduce uncertainty or make the next action more obvious.
2. **Typography as interface:** large type, measured line lengths, and editorial contrast carry the personality.
3. **Calm authority:** warm neutrals, charcoal text, hairline dividers, and restrained motion establish trust.
4. **Progressive disclosure:** show only the amount of complexity needed for the user's current decision.

### Color Philosophy
The canvas is a warm ivory rather than stark white, so the product feels human and paper-adjacent. Charcoal provides authority without severity. A single saffron-orange accent signals action and attention, echoing public notices and high-visibility wayfinding while remaining mature and accessible. Muted sage is reserved for confirmed or understood states.

### Layout Paradigm
Use an editorial column system with a generous left text rail, wide asymmetric content fields, and numbered sequences that run vertically through the experience. Avoid centered hero stacks and dashboard card mosaics; content should feel placed on a page, with rules and offsets providing structure.

### Signature Elements
- Oversized section numbers in a condensed display face.
- Hairline horizontal rules with small uppercase labels.
- A saffron action marker used as a short bar, underline, or arrow rather than a pill.

### Interaction Philosophy
Interactions should feel like turning a page or making a considered selection. Hover reveals context through color and a slight vertical shift; focus states are clear and warm; progress is explicit but never gamified. The interface should always answer: what just happened, what is understood, and what can I do next?

### Animation
Use 180–260ms ease-out transitions for hover, focus, and panel reveals. Page content enters with a subtle upward 8px translate and fade, staggered by 40ms across editorial rows. Assistant results reveal in sections, not as a simulated typing spectacle. Respect reduced-motion preferences and keep primary navigation immediate.

### Typography System
Use **Manrope** for UI, labels, and body copy, with 400/500/600/700 weights. Use **Newsreader** italic selectively for major statements and editorial emphasis. Use **Space Mono** for section numbering, metadata, and source labels. Headlines use tight tracking and a short measure; body copy stays at 1.55 line height.

### Brand Essence
CivicAI is a calm civic companion for ordinary people who need to understand a complicated situation and take a practical next step. Personality: **clear, grounded, quietly encouraging**.

### Brand Voice
Headlines are direct and useful. CTAs describe the next action rather than the technology. Microcopy removes intimidation and never overpromises legal certainty.

Example lines:
- “You do not need the right words. Start with what happened.”
- “Here is what your situation may mean — and what you can do next.”

### Wordmark & Logo
The mark is a compact open doorway made from two offset vertical strokes and a short saffron threshold line, suggesting access, a civic office, and movement forward. The wordmark pairs a custom-tightened Manrope wordmark with a small editorial dot between “Civic” and “AI”; it should not be rendered as a default logo treatment.

### Signature Brand Color
**Civic Saffron — #E1A12A**, used sparingly for action, emphasis, and the visual cue that the user has reached a practical next step.

## Style Decisions
- No gradients, glassmorphism, neon, robot imagery, or generic AI dashboard conventions.
- Prefer editorial lists, rules, numbered progressions, and asymmetrical columns over card grids.
- Use mock/example source labels clearly; do not imply prototype sources are real government citations.
- Keep the main story visible throughout: **From confusion to action.**
