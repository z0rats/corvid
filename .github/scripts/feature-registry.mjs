// Shared helpers for the CI scripts that treat frontend's MAIN_MENU_ITEMS_CONFIG as the
// registry of top-level features (check-docs-coverage.mjs, check-feature-completeness.mjs).

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

export const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
export const sidebarConfigPath = path.join(repoRoot, "frontend/src/core/config/sidebarConfig.jsx");

export function readSidebarSource() {
  return readFileSync(sidebarConfigPath, "utf8");
}

function mainMenuArrayText(source) {
  const startMarker = "const MAIN_MENU_ITEMS_CONFIG = [";
  const startIdx = source.indexOf(startMarker);
  if (startIdx === -1) {
    throw new Error(`Could not find "${startMarker}" in ${sidebarConfigPath}`);
  }

  // Walk bracket depth from the array's opening "[" to find its matching close, rather than
  // assuming a fixed line count - the array's contents (accepts/acceptsRouting) nest their own.
  const arrayStart = startIdx + startMarker.length - 1;
  let depth = 0;
  for (let i = arrayStart; i < source.length; i++) {
    if (source[i] === "[") depth++;
    else if (source[i] === "]") {
      depth--;
      if (depth === 0) return source.slice(arrayStart, i + 1);
    }
  }
  throw new Error(`Could not find the closing bracket for MAIN_MENU_ITEMS_CONFIG in ${sidebarConfigPath}`);
}

/** `[{ moduleId, path }]` for every entry of MAIN_MENU_ITEMS_CONFIG (`path` is e.g. "/steam-recon"). */
export function extractMainMenuItems(source) {
  const arrayText = mainMenuArrayText(source);
  const items = [...arrayText.matchAll(/path:\s*["']([^"']+)["'],\s*moduleId:\s*["']([a-z0-9_]+)["']/g)].map(
    (m) => ({ path: m[1], moduleId: m[2] })
  );
  const idCount = [...arrayText.matchAll(/moduleId:\s*["']([a-z0-9_]+)["']/g)].length;
  if (items.length === 0 || items.length !== idCount) {
    throw new Error(
      "MAIN_MENU_ITEMS_CONFIG entries no longer match `path: ..., moduleId: ...` (adjacent, in that order) - update feature-registry.mjs."
    );
  }
  return items;
}

export function extractMainMenuModuleIds(source) {
  return extractMainMenuItems(source).map((item) => item.moduleId);
}
