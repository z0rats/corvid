#!/usr/bin/env node
// Fails CI when the website's docs drift from the code they describe:
//   1. a top-level feature registered in frontend's MAIN_MENU_ITEMS_CONFIG has no matching
//      page under features/. The registry is the source of truth; docs pages with no registry
//      entry (e.g. browser-extension, which lives outside the SPA entirely) are never
//      iterated, so they need no exception list.
//   2. a scan `source: Literal[...]` value in a backend schema isn't mentioned on its
//      feature's page (a new engine shipping undocumented).
//   3. a Settings tab in SETTINGS_TABS_CONFIG has no matching heading in settings-reference.md.

import { readFileSync, existsSync, readdirSync } from "node:fs";
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

// "threat_actor_usernames" / "Threat Actor Usernames" / "threatactorusernames.com" all compare equal.
const normalize = (text) => text.toLowerCase().replace(/[^a-z0-9]/g, "");

// Backend feature dirs (snake_case) map to docs pages (kebab-case) by name.
function findSourceLiterals() {
  const featuresDir = path.join(repoRoot, "backend/app/features");
  const found = [];
  for (const feature of readdirSync(featuresDir, { withFileTypes: true })) {
    if (!feature.isDirectory()) continue;
    const schemasDir = path.join(featuresDir, feature.name, "schemas");
    if (!existsSync(schemasDir)) continue;
    for (const file of readdirSync(schemasDir)) {
      if (!file.endsWith(".py")) continue;
      const text = readFileSync(path.join(schemasDir, file), "utf8");
      for (const m of text.matchAll(/^\s*source:\s*Literal\[([^\]]+)\]/gm)) {
        const values = [...m[1].matchAll(/["']([a-z0-9_]+)["']/g)].map((v) => v[1]);
        found.push({ feature: feature.name.replace(/_/g, "-"), values, file });
      }
    }
  }
  return found;
}

const undocumentedSources = [];
for (const { feature, values, file } of findSourceLiterals()) {
  const docPath = path.join(docsFeaturesDir, `${feature}.md`);
  if (!existsSync(docPath)) continue; // reported by check 1 if the feature is in the menu
  const doc = normalize(readFileSync(docPath, "utf8"));
  for (const value of values) {
    if (!doc.includes(normalize(value))) undocumentedSources.push({ feature, value, file });
  }
}

const settingsReference = readFileSync(
  path.join(repoRoot, "website/src/content/docs/getting-started/settings-reference.md"),
  "utf8"
);
const settingsHeadings = [...settingsReference.matchAll(/^#{2,3}\s+(.+)$/gm)].map((m) => normalize(m[1]));
const settingsTabPaths = [...source.matchAll(/path:\s*["']\/settings\/([a-z0-9-]+)["']/g)].map((m) => m[1]);
const undocumentedTabs = [...new Set(settingsTabPaths)].filter(
  (tab) => !settingsHeadings.includes(normalize(tab))
);

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

if (undocumentedSources.length > 0 || undocumentedTabs.length > 0) {
  console.error("Doc drift check failed:\n");
  for (const { feature, value, file } of undocumentedSources) {
    console.error(`  - source "${value}" (backend ${feature}/schemas/${file}) isn't mentioned in features/${feature}.md`);
  }
  for (const tab of undocumentedTabs) {
    console.error(`  - Settings tab "/settings/${tab}" has no matching heading in getting-started/settings-reference.md`);
  }
  process.exit(1);
}

console.log(`Doc coverage check passed - all ${moduleIds.length} features in MAIN_MENU_ITEMS_CONFIG have a docs page; source engines and Settings tabs are documented.`);
