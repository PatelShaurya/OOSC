# Premium dark-mode refinement

- [x] Simplify the visual hierarchy and reduce the overly busy decorative treatment.
- [x] Add an accessible theme control with persistent light and premium dark preferences.
- [x] Define premium graphite, slate, ivory, and amber tokens for both themes.
- [x] Apply restrained technical details consistently across all routes.
- [x] Verify responsive layouts, contrast, navigation, and production build quality.

# Complete local-ready civic workflows

- [x] Audit every requested CivicAI route and identify missing interactions or states.
- [x] Expand the dashboard, rights navigator, assistant, and document workflows with complete mock journeys.
- [x] Add concise local development instructions for running the site on localhost.
- [x] Verify every route in both themes and confirm the local server responds correctly.

# Interaction repair

- [x] Reproduce navigation, theme, case, rights, and document-workflow interactions.
- [x] Inspect client errors and state-handling paths for the failing actions.
- [x] Repair broken interactions and add clear fallbacks where an action is not implemented.
- [x] Verify the repaired flows in the browser and production build.

# Typography and motion refinement

- [x] Increase content type scale and improve density on large surfaces.
- [x] Add purposeful entrance, transition, and interaction animations.
- [x] Preserve accessibility with reduced-motion behavior and readable mobile hierarchy.
- [x] Verify typography, animation, and responsive balance across key routes.

# Nyaya rebrand and navigation repair

- [x] Identify why the menu control is not opening on the affected viewport.
- [x] Replace the current menu control with an accessible, clearly clickable navigation drawer.
- [x] Update visible brand naming, page metadata, and local copy from CivicAI to Nyaya.
- [x] Verify the menu and rebranded interface on desktop and mobile.

# Specification alignment

- [x] Map the new brief against existing landing, assistant, rights, document, and source experiences.
- [x] Add a concise value-story and final action section to the landing page.
- [x] Strengthen continuity from a submitted problem through assistant, rights, action, and document generation.
- [x] Add form validation, loading, error, success, empty, and disabled states to core interactions.
- [x] Verify the refined user journey across desktop and mobile in both themes.

# Keyboard form progression

- [x] Make Enter advance single-line document form steps on laptops.
- [x] Keep Enter available for line breaks in multiline issue and context fields.
- [x] Verify the keyboard interaction and production build.

# Public landing and authentication entry

- [x] Review the supplied public-service reference and record transferable design patterns.
- [x] Add authenticated entry capability and preserve the existing civic workflow routes.
- [x] Create a distinct public landing page with product context, authentication entry, and dashboard handoff.
- [x] Add polished, reference-informed motion while retaining Nyaya’s brand and accessibility.
- [x] Verify landing, authentication entry, and responsive dashboard transition.

# Separate animated landing page

- [x] Define a dedicated public landing route separate from the authenticated application home.
- [x] Build a clear landing-to-sign-in and landing-to-dashboard handoff.
- [x] Add scroll-driven story reveals and progress cues with reduced-motion support.
- [x] Verify the separate landing route, motion, navigation, and mobile layout.

# Registration entry

- [x] Identify all public sign-in controls and authentication gates.
- [x] Add a visible Create account action alongside Sign in.
- [x] Route account creation through the secure Nyaya OAuth provider flow.
- [x] Verify registration and sign-in entry visibility across desktop and mobile.

# Extended landing motion

- [x] Add layered scroll reveals for landmark landing sections.
- [x] Add subtle wayfinding-line and editorial-marker movement tied to scroll.
- [x] Preserve reduced-motion behavior and avoid layout-shifting animations.
- [x] Verify enhanced motion, visual clarity, and mobile responsiveness.

# Route separation repair

- [x] Reproduce the repeated-page behavior across public and protected Nyaya routes.
- [x] Ensure landing remains a standalone public page with its scroll animations.
- [x] Ensure Dashboard, Assistant, Rights, Documents, and document creation render distinct workflows.
- [x] Verify all routes and mobile navigation after the repair.

# All-section scroll motion

- [x] Map scroll-triggered reveal points across dashboard and workflow routes.
- [x] Add consistent section, row, panel, and document reveals across all routes.
- [x] Preserve performance and reduced-motion behavior for every new effect.
- [x] Verify motion and readability across desktop and mobile workflows.

# Google authentication migration — superseded by temporary auth removal

- [x] Replace the Manus OAuth entry controls with Google sign-in messaging and controls. Superseded: Nyaya now has no authentication layer.
- [x] Add secure Google OAuth callback, token validation, and Nyaya session creation. Superseded: authentication is intentionally deferred.
- [x] Store the required Google OAuth client configuration securely. Superseded: no Google credentials are required while auth is disabled.
- [x] Verify Google entry points, callback behavior, logout, and dashboard handoff. Superseded: all Nyaya routes are now directly accessible.

# Temporary auth removal

- [x] Remove sign-in, registration, account, and logout controls from the Nyaya interface.
- [x] Replace authentication-dependent landing copy with direct civic-workspace entry actions.
- [x] Confirm every landing and workflow route is directly available without authentication.

# Theme contrast and visibility repair

- [x] Audit light and dark mode for low-contrast text, controls, and section surfaces.
- [x] Repair the invisible light-mode final landing section and related theme-specific styling flaws.
- [x] Ensure theme controls, primary actions, and editorial labels remain readable in both modes.
- [x] Verify contrast and layout across desktop and mobile routes in light and dark modes.

# Landing hero enrichment

- [x] Add a crafted visual composition to balance the hero’s open right side.
- [x] Add subtle ambient animation with reduced-motion support.
- [x] Preserve hero copy contrast, actions, and responsive clarity.
- [x] Verify the enriched hero in light and dark desktop/mobile views.

# Theme-toggle indicator

- [x] Update the theme toggle to show the active mode’s icon and label.
- [x] Verify the light and dark indicators at desktop and mobile sizes.

# Theme transition

- [x] Add a smooth visual transition layer for theme changes.
- [x] Respect reduced-motion preferences and avoid blocking theme controls.
- [x] Verify light-to-dark and dark-to-light transitions at desktop and mobile sizes.

# Cinematic theme transition

- [x] Replace the basic circular reveal with a layered premium transition.
- [x] Keep the effect fast, non-blocking, and reduced-motion safe.
- [x] Verify both theme directions and responsive behavior after the upgrade.

# Bold theme-transition redesign

- [x] Replace the current theme visual with a bolder, clearly legible transition sequence.
- [x] Preserve immediate state updates, theme indicator semantics, and reduced-motion fallback.
- [x] Verify the redesigned effect at desktop and mobile widths.

# Landing scroll-motion refinement

- [x] Audit the existing landing motion for abrupt, repetitive, or disconnected sections.
- [x] Replace it with a smoother narrative sequence that maintains hierarchy and readability.
- [x] Verify the landing scroll experience on desktop and mobile, including reduced-motion behavior.

# Replayable cross-route scroll motion

- [x] Make landing reveal states reset and replay when users scroll sections out of and back into view.
- [x] Apply the same restrained scroll-reveal vocabulary to core dashboard and workflow route sections.
- [x] Verify replay behavior, desktop/mobile routes, and reduced-motion fallback.
- [x] Verify replayable scroll motion on mobile widths for dashboard, assistant, rights, documents, and document preview routes.
- [x] Scroll through mobile dashboard, assistant, rights, documents, and document preview routes to confirm offscreen motion targets reveal on entry.
- [x] Confirm replay/reset behavior for a multi-section mobile workflow route after scrolling away and returning.
- [x] Demonstrate offscreen reveal-on-entry behavior on the mobile Rights, Documents, and Document Preview routes.
- [x] Verify a specifically offscreen mobile Document Preview motion target reveals when it enters the viewport.

# Landing headline wrap consistency

- [x] Prevent the “too much” phrase from splitting across lines at common desktop zoom levels and responsive widths.
- [x] Preserve the existing landing hierarchy, light/dark contrast, and mobile headline behavior.
- [x] Verify headline wrapping across both themes and representative desktop/mobile widths.

# Cross-device hero typography consistency

- [x] Compare the hero headline on wide, compact-laptop, and mobile viewport profiles.
- [x] Stabilize the desktop headline composition across differing display scaling and aspect ratios.
- [x] Verify Light and Dark headline composition across representative device profiles.
- [x] Measure the rendered headline line composition at wide, compact-laptop, and mobile viewports in both themes.

# Approved narrow hero composition

- [x] Change the desktop hero heading to the approved four-line composition: “When the” / “system” / “feels too much,” / “start here.”
- [x] Keep the approved composition consistent across wide and compact laptop profiles without affecting mobile readability.
- [x] Verify Light and Dark views at representative laptop and mobile sizes.
