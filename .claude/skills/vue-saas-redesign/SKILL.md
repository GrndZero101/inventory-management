---
name: vue-saas-redesign
description: Redesign this Vue 3 app's UI into a modern SaaS-style interface — a vertical left sidebar nav instead of the top nav bar, a consistent spacing/elevation scale, and a polished professional look. Use when the user asks to redesign, modernize, restyle, "make it look more SaaS/professional", or move the app to sidebar navigation.
---

# Vue 3 SaaS Redesign

Restructures this app's layout and visual language into a modern SaaS look — vertical sidebar navigation, a consistent spacing/typography/elevation system, and polished card/table treatments — while preserving the app's existing brand colors, all data logic, and every current feature.

This is a **plan-first** skill: always produce and get sign-off on a design plan before touching any component. A sidebar/layout rework touches every view in the app; retrofitting after the fact is much more expensive than agreeing the spec up front.

## Non-negotiable constraints

- **Preserve existing brand colors and status semantics.** This app's palette is documented in the root `CLAUDE.md` (`Colors: Slate/gray (#0f172a, #64748b, #e2e8f0)`, `Status: green/blue/yellow/red`). Do not introduce a new color scheme — modernize structure, spacing, and polish, not the palette. Reuse the exact hex values already in use (grep for them in `client/src/App.vue`'s global `<style>` block and in each view's scoped styles) rather than inventing new ones.
- **No functional or data changes.** Filtering logic (`useFilters.js`), API calls (`api.js`), i18n (`useI18n.js`, `locales/*.js`), and every route's underlying behavior must work identically after the redesign. This is a visual/structural pass only.
- **No emojis in the UI**, per the project's design system rule.
- **Every `.vue` file created or significantly modified must be delegated to the `vue-expert` subagent** — this is a mandatory project rule (see root `CLAUDE.md`), not optional for this skill.
- Keep the redesign **incremental and reviewable**: land the shell (sidebar + layout scaffold) first, verify it, then migrate views — don't rewrite everything in one unreviewable pass.

## Step 1 — Audit the current UI

Before proposing anything, read and understand the current structure:

- `client/src/App.vue` — the current top nav (`<nav class="nav-tabs">` with `<router-link>` tabs), the global unscoped `<style>` block (this is where most shared classes live: `.page-header`, `.stats-grid`/`.stat-card`, `.card`, `.table-container`/table styles, `.badge` variants, `.loading`, `.error`), and where `FilterBar`, `ProfileMenu`, `LanguageSwitcher` currently mount.
- `client/src/components/FilterBar.vue` — the global filter bar, currently rendered as a full-width strip below the top nav on every route.
- `client/src/main.js` — the full route list (source of truth for what goes in the new sidebar's nav items).
- Every file in `client/src/views/` — skim each for its own scoped styles, to catch view-specific spacing/color choices that should either fold into the new shared system or stay as legitimate per-view exceptions.
- `client/src/components/*.vue` (modals especially) — note anything relying on the current layout's z-index/positioning assumptions (e.g. `Teleport to="body"` modals), since sidebar layouts can change stacking contexts.

Extract and write down (for use in the plan): the current color tokens in use, the current spacing values in use (they're likely inconsistent — that inconsistency is exactly what this redesign fixes), and the full list of nav destinations.

## Step 2 — Produce the design plan

Write a concrete plan and get the user's sign-off before implementing (use plan mode if available; otherwise write the plan out and explicitly pause for confirmation). The plan must specify:

**Layout shell:**
- A fixed-width vertical sidebar (suggest 240–260px, collapsible to an icon-only rail if the user wants that) containing: brand/logo at top, nav items (reuse the exact route list from `main.js`) as a vertical stack with icons, active-route highlighting, and a footer area for profile/language controls (currently in the top-right of the nav bar).
- A main content region to the right of the sidebar containing: a slim top bar for page title + `FilterBar` (filters are page-level controls, not primary nav — they belong in the content region's header, not the sidebar), then the routed view content below.
- How this maps onto the existing component tree: a new `Sidebar.vue` component, `App.vue` restructured into a `sidebar + main` flex/grid shell instead of `header (nav) + main`, `FilterBar` relocated but otherwise unchanged internally.

**Design tokens (spacing, elevation, radius):**
- Define a spacing scale as CSS custom properties (e.g. `--space-1: 4px` through `--space-8: 64px`, doubling or using a 4/8px base grid) and a radius scale (`--radius-sm/md/lg`) and shadow scale (`--shadow-sm/md/lg`) for card elevation — add these to `App.vue`'s global `:root` so every view can consume them.
- Reuse the existing color values as named tokens too (e.g. `--color-ink: #0f172a`, `--color-muted: #64748b`, `--color-border: #e2e8f0`, `--color-accent: #3b82f6`) so the palette is centralized without changing any actual color.
- Note every place spacing/radius is currently inconsistent across views (from the Step 1 audit) and confirm the target values to converge on.

**Component polish:**
- `.card` treatment: consistent padding (from the new spacing scale), border-radius, subtle shadow, hover state if cards are interactive.
- `.table-container`/table treatment: consistent row padding/height, header styling, zebra-striping or hover-row highlight if not already present.
- `.badge` variants: keep the existing status→color mapping, just tighten padding/radius/font-weight to match the new system.
- Typography: confirm a consistent heading scale (page title, card title, body, label/caption sizes) — check current inconsistencies across views during the audit.

**What's explicitly out of scope:** don't restyle modals' internal form logic, don't change chart rendering logic (SVG structure), don't touch backend/API/test files.

Present this plan to the user and wait for explicit approval before Step 3.

## Step 3 — Implement (only after plan approval)

1. Build the shell first: new `Sidebar.vue`, restructured `App.vue`, new global CSS custom properties. Delegate this to the `vue-expert` subagent with the approved plan's exact specs (sidebar width, nav item list with routes, token values). Verify the shell renders correctly (nav highlights active route, all existing routes still reachable, FilterBar/ProfileMenu/LanguageSwitcher relocated but functional) before moving on.
2. Migrate views to the new spacing/token system one at a time or in small batches, again via `vue-expert` — updating scoped styles to reference the new CSS custom properties instead of hardcoded one-off values, and adjusting card/table/badge markup only where needed to pick up the new shared classes. Do not touch each view's `<script>` logic.
3. Keep commits/changes reviewable — don't let "redesign the UI" become an undifferentiated rewrite of every file in one shot.

## Step 4 — Verify

- Start both dev servers (backend + frontend) and click through **every route** (check `main.js` for the full list) to confirm: sidebar nav works and highlights correctly, FilterBar still filters data correctly, all modals still open/close/position correctly, language switcher and profile menu still work from their new location, no visual regressions on any page (tables, charts, forms).
- Check responsive behavior at a narrow viewport if the plan included a collapsed/mobile sidebar state.
- Run the existing backend test suite (`cd server && uv run pytest ../tests/backend/ -v` or equivalent) to confirm this frontend-only change didn't somehow break anything, and manually confirm no data/API behavior changed.
- Use Playwright MCP tools per the project's testing convention (`http://localhost:3000`) to capture before/after screenshots of a couple of key views (Dashboard, Orders) if useful for showing the user the result.
