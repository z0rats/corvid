import { getMainMenuItems } from './sidebarConfig';

/**
 * Command palette registry — derived from MAIN_MENU_ITEMS_CONFIG in sidebarConfig.jsx rather
 * than hand-maintained, so a new top-level feature can't land in the nav without also being
 * reachable from search (see docs/command-palette-plan.md's governance table).
 */
export function buildCommandRegistry(t) {
  return getMainMenuItems(t).map((item) => ({
    id: item.moduleId,
    label: item.label,
    icon: item.icon,
    path: item.path,
    moduleId: item.moduleId,
    aliases: item.aliases ?? [],
    tags: item.tags ?? [],
    accepts: item.accepts ?? [],
    acceptsRouting: item.acceptsRouting ?? {},
  }));
}

/** Resolves the path a registry entry should open for a given detected IOC type. */
export function resolveEntryPath(entry, iocType) {
  if (iocType && entry.acceptsRouting[iocType]) {
    return entry.acceptsRouting[iocType];
  }
  return entry.path;
}
