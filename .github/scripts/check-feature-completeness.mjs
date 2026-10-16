#!/usr/bin/env node
// Fails CI when a top-level feature in frontend's MAIN_MENU_ITEMS_CONFIG is missing one of the
// places a feature has to be wired into, and prints ONE checklist per feature instead of a
// message per gate. Complements check-docs-coverage.mjs (doc drift), test_ssrf_guard_coverage.py
// and test_canary_coverage.py (Python gates) - those are not repeated here.

import { readFileSync, existsSync, readdirSync } from "node:fs";
import path from "node:path";

import { repoRoot, readSidebarSource, extractMainMenuItems } from "./feature-registry.mjs";

// Deliberate gaps, each with its reason. A feature listed here is skipped for that check only.
const EXEMPT = {
  rule_creator: { backend: "frontend-only, no backend module", router: "frontend-only, no backend module" },
  ru_business_check: { i18n: "UI text is Russian-only by design" },
};

const read = (rel) => readFileSync(path.join(repoRoot, rel), "utf8");
const camelCase = (id) => id.replace(/_([a-z0-9])/g, (_, c) => c.toUpperCase());

function declaresScanFeature(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (declaresScanFeature(full)) return true;
    } else if (entry.name.endsWith(".py") && /\bScanFeature\(/.test(readFileSync(full, "utf8"))) {
      return true;
    }
  }
  return false;
}

const routerRegistry = read("backend/app/utils/router_registry.py");
const routes = read("frontend/src/core/config/featureRoutes.js");
const historyPaths = read("frontend/src/core/utils/historyPaths.js");
const sidebar = readSidebarSource();
const localesDir = path.join(repoRoot, "frontend/src/core/i18n/locales/en");

const failures = [];
const items = extractMainMenuItems(sidebar);
for (const { moduleId, path: routePath } of items) {
  const exempt = EXEMPT[moduleId] ?? {};
  const missing = [];
  const check = (key, label, ok) => {
    if (!exempt[key] && !ok()) missing.push(label);
  };

  const backendDir = path.join(repoRoot, "backend/app/features", moduleId);
  check("backend", `backend/app/features/${moduleId}/`, () => existsSync(backendDir));
  check("router", `router import (app.features.${moduleId}.) in router_registry.py`, () =>
    routerRegistry.includes(`app.features.${moduleId}.`)
  );
  check("route", `FEATURE_ROUTES entry '${routePath.slice(1)}/*' in featureRoutes.js`, () =>
    routes.includes(`path: '${routePath.slice(1)}/*'`)
  );
  check("i18n", `i18n namespace locales/en/${camelCase(moduleId)}.json`, () =>
    existsSync(path.join(localesDir, `${camelCase(moduleId)}.json`))
  );
  check("docs", `website/src/content/docs/features/${moduleId.replace(/_/g, "-")}.md`, () =>
    existsSync(path.join(repoRoot, "website/src/content/docs/features", `${moduleId.replace(/_/g, "-")}.md`))
  );

  if (existsSync(backendDir) && declaresScanFeature(backendDir)) {
    check("history", `historyPaths.js entry "${moduleId}"`, () => new RegExp(`^\\s*${moduleId}:`, "m").test(historyPaths));
    check("tabs", `TAB_ROUTES entry prefix "${routePath}" in sidebarConfig.jsx`, () =>
      sidebar.includes(`prefix: "${routePath}"`)
    );
  }

  if (missing.length > 0) failures.push({ moduleId, missing });
}

if (failures.length > 0) {
  console.error("Feature completeness check failed:\n");
  for (const { moduleId, missing } of failures) {
    console.error(`  ${moduleId}: missing -> ${missing.join(", ")}`);
  }
  console.error(
    "\nSee 'New top-level features' in AGENTS.md. A deliberate gap goes in EXEMPT in this script, with a reason."
  );
  process.exit(1);
}

console.log(`Feature completeness check passed - all ${items.length} features in MAIN_MENU_ITEMS_CONFIG are fully wired.`);
