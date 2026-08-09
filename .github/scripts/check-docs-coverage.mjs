#!/usr/bin/env node
// Fails CI if a top-level feature registered in frontend's MAIN_MENU_ITEMS_CONFIG has no
// matching website docs page under features/. The registry is the source of truth; docs
// pages with no registry entry (e.g. browser-extension, which lives outside the SPA
// entirely) are never iterated, so they need no exception list.

import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const sidebarConfigPath = path.join(repoRoot, "frontend/src/core/config/sidebarConfig.jsx");
const docsFeaturesDir = path.join(repoRoot, "website/src/content/docs/features");

function extractMainMenuModuleIds(source) {
  const startMarker = "const MAIN_MENU_ITEMS_CONFIG = [";
  const startIdx = source.indexOf(startMarker);
  if (startIdx === -1) {
    throw new Error(`Could not find "${startMarker}" in ${sidebarConfigPath}`);
  }

  // Walk bracket depth from the array's opening "[" to find its matching close, rather than
  // assuming a fixed line count - the array's contents (accepts/acceptsRouting) nest their own.
  const arrayStart = startIdx + startMarker.length - 1;
  let depth = 0;
  let endIdx = -1;
  for (let i = arrayStart; i < source.length; i++) {
    if (source[i] === "[") depth++;
    else if (source[i] === "]") {
      depth--;
      if (depth === 0) {
        endIdx = i;
        break;
      }
    }
  }
  if (endIdx === -1) {
    throw new Error(`Could not find the closing bracket for MAIN_MENU_ITEMS_CONFIG in ${sidebarConfigPath}`);
  }

  const arrayText = source.slice(arrayStart, endIdx + 1);
  const moduleIds = [...arrayText.matchAll(/moduleId:\s*["']([a-z0-9_]+)["']/g)].map((m) => m[1]);
  if (moduleIds.length === 0) {
    throw new Error("Found MAIN_MENU_ITEMS_CONFIG but extracted zero moduleId values - the regex may no longer match its shape.");
  }
  return moduleIds;
}

const source = readFileSync(sidebarConfigPath, "utf8");
const moduleIds = extractMainMenuModuleIds(source);

const missing = [];
for (const moduleId of moduleIds) {
  const slug = moduleId.replace(/_/g, "-");
  const docPath = path.join(docsFeaturesDir, `${slug}.md`);
  if (!existsSync(docPath)) {
    missing.push({ moduleId, slug, docPath });
  }
}

if (missing.length > 0) {
  console.error("Doc coverage check failed - every top-level feature in frontend's MAIN_MENU_ITEMS_CONFIG needs a docs page:\n");
  for (const { moduleId, slug, docPath } of missing) {
    console.error(`  - moduleId "${moduleId}" -> expected ${path.relative(repoRoot, docPath)} (not found)`);
  }
  console.error(
    "\nAdd a stub page under website/src/content/docs/features/ (with a sidebar.order in its frontmatter) - it'll appear in the nav automatically."
  );
  process.exit(1);
}

console.log(`Doc coverage check passed - all ${moduleIds.length} features in MAIN_MENU_ITEMS_CONFIG have a docs page.`);
