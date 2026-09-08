---
name: vue-perf-audit
description: Analyze this app's Vue 3 component structure and report concrete performance and code-reuse optimizations (unnecessary reactivity, missing memoization, duplicated templates/logic across views and components, non-unique v-for keys, oversized watchers, etc.), with an optional follow-up to implement the fixes. Use when the user asks to audit, review, or optimize Vue components/frontend performance, or to find duplication/reuse opportunities across views and components.
---

# Vue 3 Performance & Reuse Audit

Produces a prioritized, file:line-referenced report on this app's Vue component structure, covering two axes: **runtime performance** and **code reuse**. This is a **report-first** skill — always finish the audit and show findings before changing any code. Only implement fixes if the user explicitly asks after reviewing the report.

## Scope

Audit these locations:
- `client/src/views/*.vue` — Dashboard, Demand, Inventory, Orders, Reports, Spending, Backlog, Restocking
- `client/src/components/*.vue` — Sidebar, FilterBar, ProfileMenu, LanguageSwitcher, and the modal components (*DetailModal.vue, PurchaseOrderModal.vue, TasksModal.vue)
- `client/src/composables/*.js` — useFilters, useI18n, useAuth
- `client/src/App.vue` — root shell and global styles
- `client/src/api.js`, `client/src/utils/currency.js` — shared logic that views/components call into

Do not audit `server/` or `tests/` — this skill is frontend-only.

## Step 1 — Read before judging

Read every file in scope (or use `Explore` for a first pass if the component count is large, but read the actual `.vue` file contents yourself before flagging anything — don't infer issues from filenames). For each view/component, note:
- What reactive state it owns (`ref`, `reactive`, `computed`) vs. what it derives from props or a composable
- What it renders in loops (`v-for`) and what keys those loops use
- What watchers/lifecycle hooks it registers and what triggers them
- What markup, computed logic, or styling looks structurally similar to another file already read

## Step 2 — Performance checks

For each component, check for:

1. **Non-unique or index-based `v-for` keys** — per this project's own documented pitfall (`CLAUDE.md` "Common Issues" #1), grep for `v-for` and confirm keys use a stable field (`sku`, `id`, `month`) not `index` or the loop variable itself.
2. **Unmemoized derived values computed in the template or inside `v-for`** — expressions like `items.filter(...)` or `.reduce(...)` written inline in `<template>` re-run every render; flag these for extraction into a `computed`.
3. **Overly broad watchers** — `watch` on a whole `reactive` object or with `{ deep: true }` where a narrower `computed`-backed source or a specific field watch would do.
4. **Large static/lookup data stored in `ref`/`reactive` when it never changes** — e.g. static category/status maps — flag for `markRaw` or moving outside the component (module scope) so Vue doesn't proxy it.
5. **Missing `v-once`/`v-memo`** on genuinely static subtrees (rare in this app, but check modal headers/legends that never change after mount).
6. **Props/computed re-derivation duplicated across sibling components** instead of being lifted into a shared composable or computed once in a parent and passed down.
7. **Unnecessary full-list re-filtering on every keystroke/filter change** — check whether `FilterBar` interactions trigger a full re-fetch (`api.js` call) when a client-side filter of already-fetched data would do, and vice versa (don't recommend client-side filtering of data that must come from the server for correctness).
8. **Eagerly loaded views/modals that could be lazy** — check `main.js` route definitions for `import Foo from './views/Foo.vue'` (static) vs `() => import(...)` (lazy); flag heavy, rarely-visited views (e.g. Reports) as lazy-load candidates. Same check for modals that are conditionally rendered — confirm they use `v-if` (unmounted when closed) not `v-show` if they carry expensive setup logic.

## Step 3 — Code reuse checks

1. **Repeated markup blocks** across views — e.g. stat-card grids, `.table-container` tables, loading/error state blocks, page-header layout — already meant to share `App.vue`'s global classes (per `CLAUDE.md` Design System); flag any view that reimplements this markup/styles locally instead of using the shared classes, and any shared pattern used 3+ times that isn't already a component (candidate for extraction into `client/src/components/`).
2. **Repeated logic** across `<script setup>` blocks — date formatting, currency formatting (cross-check against `utils/currency.js` — flag any view doing its own currency math instead of importing it), status→color/badge mapping, or filter-application logic not already going through `useFilters.js` — flag for extraction into a composable or shared util.
3. **Duplicated modal scaffolding** — the five `*Modal.vue` components likely share open/close/backdrop/Teleport structure; check for a common pattern that could become a base `Modal.vue` wrapper (or a `useModal` composable) rather than each modal reimplementing it.
4. **Prop-drilling** — state passed through 2+ intermediate components untouched; flag for `provide`/`inject` or lifting into a composable instead.
5. **Duplicated i18n key lookups or fallback logic** outside `useI18n.js`.

## Step 4 — Report

Present findings grouped by category (Performance / Reuse), each with:
- File path and line number(s)
- One-sentence description of the issue
- Concrete suggested fix (name the composable/component to extract, the specific memoization to add, etc.)
- Rough impact/effort so the user can prioritize (e.g. "high impact, low effort")

Do not silently skip a category with nothing to report — say "no findings" for it so the user knows it was checked.

## Step 5 — Optional implementation

After presenting the report, ask the user which findings (if any) to act on. If they want fixes applied:
- Any change that creates or significantly modifies a `.vue` file **must** be delegated to the `vue-expert` subagent (mandatory project rule in root `CLAUDE.md`) — hand it the specific finding(s) to fix, not the whole report, so changes stay incremental and reviewable.
- Composable/util-only changes (`.js` files with no `.vue` edits) can be made directly.
- After applying fixes, start the dev servers and manually verify the affected views still render and behave correctly (per `CLAUDE.md` Quick Start / the project's Playwright testing convention) before reporting the work done.
