import i18n from '../i18n';
import { buildCommandRegistry, resolveEntryPath } from './commandRegistry';
import { IOC_TYPES } from '../utils/iocTypeDetection';

const identityT = (key) => key;

describe('buildCommandRegistry — real i18n resolution (catches wrong-namespace `t`)', () => {
  it('resolves every label to real copy, not a raw nav.* key', () => {
    // sidebarConfig.jsx's i18nKeys live in the default 'common' namespace — callers that pass a
    // `t` bound to a different namespace (e.g. useTranslation('commandPalette')) would silently
    // render the untranslated key string instead. Regression coverage for that exact class of bug.
    const registry = buildCommandRegistry(i18n.getFixedT('en'));
    registry.forEach((entry) => {
      expect(entry.label).not.toMatch(/^nav\./);
    });
  });
});

describe('buildCommandRegistry — coverage (governance: no empty/garbage fields)', () => {
  const registry = buildCommandRegistry(identityT);

  it('is derived from sidebarConfig and non-empty', () => {
    expect(registry.length).toBeGreaterThan(0);
  });

  it('every entry has a unique id, path and label', () => {
    const ids = registry.map((e) => e.id);
    expect(new Set(ids).size).toBe(ids.length);
    registry.forEach((entry) => {
      expect(entry.id).toBeTruthy();
      expect(entry.path).toMatch(/^\//);
      expect(entry.label).toBeTruthy();
    });
  });

  it('every entry has a non-empty aliases array of strings', () => {
    registry.forEach((entry) => {
      expect(Array.isArray(entry.aliases)).toBe(true);
      expect(entry.aliases.length).toBeGreaterThan(0);
      entry.aliases.forEach((alias) => expect(typeof alias).toBe('string'));
    });
  });

  it('every entry has a non-empty tags array of strings', () => {
    registry.forEach((entry) => {
      expect(Array.isArray(entry.tags)).toBe(true);
      expect(entry.tags.length).toBeGreaterThan(0);
      entry.tags.forEach((tag) => expect(typeof tag).toBe('string'));
    });
  });

  it('every entry has an accepts array (possibly empty, never missing/garbage)', () => {
    registry.forEach((entry) => {
      expect(Array.isArray(entry.accepts)).toBe(true);
      entry.accepts.forEach((type) => expect(Object.values(IOC_TYPES)).toContain(type));
    });
  });

  it('acceptsRouting keys are a subset of the entry\'s own accepts list', () => {
    registry.forEach((entry) => {
      Object.keys(entry.acceptsRouting).forEach((type) => {
        expect(entry.accepts).toContain(type);
      });
    });
  });
});

describe('resolveEntryPath', () => {
  const registry = buildCommandRegistry(identityT);
  const iocTools = registry.find((e) => e.id === 'ioc_tools');

  it('routes a hash type to the entry\'s acceptsRouting override', () => {
    expect(resolveEntryPath(iocTools, IOC_TYPES.SHA256)).toBe('/ioc-tools/bulk');
  });

  it('falls back to the entry\'s default path when no override exists', () => {
    const dorkRunner = registry.find((e) => e.id === 'dork_runner');
    expect(resolveEntryPath(dorkRunner, IOC_TYPES.DOMAIN)).toBe('/dork-runner');
  });

  // Regression: ioc_tools' bare "/ioc-tools" root is a *relative* `<Navigate to="lookup"
  // replace />` redirect (IocTools.jsx), which drops the query string — so a prefilled value
  // silently vanishes unless every accepted type routes straight to a real leaf route.
  it('never resolves a prefillable type to the redirect-only "/ioc-tools" root', () => {
    iocTools.accepts.forEach((type) => {
      expect(resolveEntryPath(iocTools, type)).not.toBe('/ioc-tools');
    });
  });

  it('falls back to the default path when no type is given', () => {
    expect(resolveEntryPath(iocTools, undefined)).toBe('/ioc-tools');
  });
});
