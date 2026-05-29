# Accessibility — UCSB Innovation Marketplace

**Conformance target:** WCAG 2.1 Level AA (per UC IT Accessibility Policy).
**Last reviewed:** 2026-05-29 · file: `UCSB Innovation Marketplace.html`

## What was implemented
- **Keyboard operability (2.1.1):** every interactive element is a real `<button>` or `<a>` — facet filters are `<button aria-pressed>` toggles, card titles and "Details" are buttons, CTAs are links. No click-only `<div>`/`<span>`.
- **Tabs (4.1.2):** the three views use the ARIA tab pattern — `role=tablist/tab/tabpanel`, `aria-selected`, roving `tabindex`, and Arrow/Home/End key navigation.
- **Dialog (4.1.2, 2.4.3):** the detail panel is `role=dialog aria-modal` with a labelled title, focus moved to it on open, a focus trap on Tab, Escape to close, and focus returned to the triggering control.
- **Labels (1.3.1, 3.3.2):** every search box and `<select>` has an associated `<label>` (visible or `sr-only`); filter groups use `<fieldset>/<legend>`.
- **Structure (1.3.1, 2.4.1):** skip link, `<header>`/`<nav>`/`<main>` landmarks, one `<h1>` plus section headings, semantic lists for cards/KPIs.
- **Status messages (4.1.3):** result counts use `role=status aria-live=polite`.
- **Non-text content (1.1.1):** charts are `aria-hidden` and paired with a visually-hidden text list of the same data; links that open new tabs say so.
- **Contrast (1.4.3, 1.4.11):** all text and UI-boundary pairs verified ≥4.5:1 (text) / ≥3:1 (controls) by calculation.
- **Focus visible (2.4.7):** 3px high-contrast focus ring on all controls.
- **Reduced motion (2.3.3):** `prefers-reduced-motion` disables transitions.
- **Language/title (3.1.1, 2.4.2):** `lang="en"` and a descriptive `<title>`.

## How it was tested
- **axe-core** (WCAG 2.0/2.1 A & AA rule sets) against the rendered DOM: **0 violations**, 23 passes.
- **Color contrast** verified independently by WCAG luminance math (axe can't compute it in the headless test harness).

## Before launch — recommended manual checks
Automated tools catch roughly a third to half of WCAG issues. Prior to going live on a campus site, do a manual pass:
1. Keyboard-only walkthrough (tab order, all actions reachable, dialog trap/return, tab arrows).
2. Screen reader smoke test (VoiceOver/Safari and NVDA/Firefox): card names, filter state announcements, dialog reading, chart text alternatives.
3. Zoom to 200% and 400% reflow; 320px-wide viewport.
4. Confirm against the campus's own template/CMS if the page is embedded (the campus shell brings its own header/nav, which must also conform).

A VPAT/accessibility statement can be drafted from this summary if your campus accessibility office requests one.
