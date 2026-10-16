import { useMemo } from 'react';
import { useAtomValue } from 'jotai';
import { enabledModulesMapAtom, llmAvailableAtom } from '../state/atoms';
import { getMainMenuItems } from '../config/sidebarConfig';

/**
 * moduleIds the user can currently reach: enabled in Settings → Modules, and (for AI Templates)
 * backed by a configured LLM key. The left panel, command palette and start screen all filter
 * the tool registry through this, so a disabled module can't resurface through search.
 */
export function useVisibleModuleIds() {
  const enabledModules = useAtomValue(enabledModulesMapAtom);
  const llmAvailable = useAtomValue(llmAvailableAtom);

  return useMemo(() => new Set(
    getMainMenuItems((key) => key)
      .filter((item) => (enabledModules[item.moduleId] ?? true)
        && (item.moduleId !== 'llm_templates' || llmAvailable))
      .map((item) => item.moduleId),
  ), [enabledModules, llmAvailable]);
}
