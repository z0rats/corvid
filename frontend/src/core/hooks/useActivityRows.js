import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { getMainMenuItems } from '../config/sidebarConfig';
import { getRunPath } from '../utils/historyPaths';
import { useVisibleModuleIds } from './useVisibleModuleIds';

// Activity `feature` values that aren't a sidebar moduleId themselves.
const FEATURE_MODULE = {
  social_analyzer: 'username_search',
  threat_actor_usernames: 'username_search',
  ioc_lookup: 'ioc_tools',
};

/**
 * Activity items (backend features/activity/) paired with their sidebar module and run link,
 * dropping runs of disabled modules or features without a history page. Shared by the start
 * screen's feed and the AppBar's active-scans menu.
 */
export function useActivityRows(items) {
  const { t } = useTranslation();
  const visibleModuleIds = useVisibleModuleIds();

  const modules = useMemo(
    () => Object.fromEntries(getMainMenuItems(t).map((item) => [item.moduleId, item])),
    [t],
  );

  return useMemo(
    () => items
      .map((item) => ({
        item,
        module: modules[FEATURE_MODULE[item.feature] ?? item.feature],
        path: getRunPath(item.feature, item.id),
      }))
      .filter(({ module, path }) => module && visibleModuleIds.has(module.moduleId) && path),
    [items, modules, visibleModuleIds],
  );
}
