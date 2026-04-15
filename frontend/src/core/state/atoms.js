import { atom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import { selectAtom } from 'jotai/vanilla/utils';

export const appVersionAtom = atom('');
appVersionAtom.debugLabel = 'appVersionAtom';

export const apiKeysState = atom({});
apiKeysState.debugLabel = 'apiKeysState';

export const modulesState = atom({});
modulesState.debugLabel = 'modulesState';

export const generalSettingsState = atom({});
generalSettingsState.debugLabel = 'generalSettingsState';

export const aiSettingsState = atom({});
aiSettingsState.debugLabel = 'aiSettingsState';

export const hasLlmKeyAtom = atom((get) => {
  const keys = get(apiKeysState);
  return Boolean(keys.openai || keys.anthropic);
});
hasLlmKeyAtom.debugLabel = 'hasLlmKeyAtom';

const shallowObjEqual = (a, b) => {
  if (a === b) return true;
  const keysA = Object.keys(a);
  const keysB = Object.keys(b);
  if (keysA.length !== keysB.length) return false;
  return keysA.every((k) => a[k] === b[k]);
};

export const apiKeyAvailabilityAtom = selectAtom(
  apiKeysState,
  (keys) => Object.fromEntries(
    Object.entries(keys).map(([key, val]) => [key, Boolean(val)])
  ),
  shallowObjEqual,
);
apiKeyAvailabilityAtom.debugLabel = 'apiKeyAvailabilityAtom';

export const enabledModulesMapAtom = atom((get) => {
  const modules = get(modulesState);
  return Object.fromEntries(
    Object.entries(modules).map(([key, val]) => [key, val?.enabled ?? true])
  );
});
enabledModulesMapAtom.debugLabel = 'enabledModulesMapAtom';

const validatedThemeStorage = {
  getItem: (key, initialValue) => {
    const value = localStorage.getItem(key);
    return value === 'light' || value === 'dark' ? value : initialValue;
  },
  setItem: (key, value) => {
    localStorage.setItem(key, value);
  },
  removeItem: (key) => {
    localStorage.removeItem(key);
  },
};

export const themeModeAtom = atomWithStorage('themeMode', 'light', validatedThemeStorage, { getOnInit: true });
themeModeAtom.debugLabel = 'themeModeAtom';
