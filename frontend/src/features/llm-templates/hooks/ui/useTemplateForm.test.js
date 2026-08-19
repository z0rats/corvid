import { act, renderHook } from '@testing-library/react';
import { useSetAtom } from 'jotai';
import { useTemplateForm } from './useTemplateForm';
import { aiSettingsState } from '../../../../core/state/atoms';
import {
  DEFAULT_TEMPLATE_STATE,
  DEFAULT_PAYLOAD_FIELD,
} from '../../constants/templateConstants';

function useTestHarness(initialState) {
  const form = useTemplateForm(initialState);
  const setAiSettings = useSetAtom(aiSettingsState);
  return { ...form, setAiSettings };
}

// aiSettingsState is module-scoped, so it doesn't reset between tests on its
// own - every test that touches it needs a clean slate, since useTemplateForm
// reads it at mount time.
function resetAiSettings() {
  const { result } = renderHook(() => useSetAtom(aiSettingsState));
  act(() => result.current({}));
}

describe('useTemplateForm', () => {
  beforeEach(resetAiSettings);

  it('uses the default template state when no initial state is given', () => {
    const { result } = renderHook(() => useTestHarness());

    expect(result.current.template).toEqual(DEFAULT_TEMPLATE_STATE);
  });

  it("fills in the model from ai settings already loaded before the form mounts", () => {
    // The model default is resolved only in useState's initializer (a
    // one-time snapshot, not a live subscription) - setting aiSettings
    // *before* the form's first render is the only way it takes effect.
    // See the note below for what happens if aiSettings arrives after.
    const { result: settings } = renderHook(() => useSetAtom(aiSettingsState));
    act(() => settings.current({ llm_templates_model: 'gpt-4o' }));

    const { result } = renderHook(() => useTestHarness());

    expect(result.current.template.model).toBe('gpt-4o');
  });

  it('falls back to the global default_model when no per-module override is set', () => {
    const { result: settings } = renderHook(() => useSetAtom(aiSettingsState));
    act(() => settings.current({ default_model: 'claude-sonnet-4-5' }));

    const { result } = renderHook(() => useTestHarness());

    expect(result.current.template.model).toBe('claude-sonnet-4-5');
  });

  it('does not retroactively fill in the model once ai settings arrive after the form has already mounted', () => {
    // Documents a real timing gap: useAppSettings fetches aiSettingsState
    // asynchronously (core/hooks/api/useAppSettings.js) - if CreateTemplateForm
    // mounts before that fetch resolves, the model field silently stays empty
    // for the rest of the form's lifetime, since nothing re-syncs it once
    // aiSettingsState updates post-mount.
    const { result } = renderHook(() => useTestHarness());

    act(() => result.current.setAiSettings({ llm_templates_model: 'gpt-4o' }));

    expect(result.current.template.model).toBe('');
  });

  it('keeps an explicitly-given model over the ai-settings default', () => {
    const { result } = renderHook(() =>
      useTestHarness({ ...DEFAULT_TEMPLATE_STATE, model: 'explicit-model' }),
    );

    act(() => result.current.setAiSettings({ default_model: 'claude-sonnet-4-5' }));

    expect(result.current.template.model).toBe('explicit-model');
  });

  it('updateField sets a single field without touching the rest', () => {
    const { result } = renderHook(() => useTestHarness());

    act(() => result.current.updateField('title', 'My Template'));

    expect(result.current.template.title).toBe('My Template');
    expect(result.current.template.ai_agent_role).toBe(DEFAULT_TEMPLATE_STATE.ai_agent_role);
  });

  it('resetForm restores the default state', () => {
    const { result } = renderHook(() => useTestHarness());

    act(() => result.current.updateField('title', 'Changed'));
    act(() => result.current.resetForm());

    expect(result.current.template.title).toBe('');
  });

  describe('payloadFields', () => {
    it('add appends a new field with a generated id', () => {
      const { result } = renderHook(() => useTestHarness());

      act(() => result.current.payloadFields.add());

      expect(result.current.template.payload_fields).toHaveLength(1);
      expect(result.current.template.payload_fields[0]).toMatchObject(DEFAULT_PAYLOAD_FIELD);
      expect(result.current.template.payload_fields[0].id).toBeTruthy();
    });

    it('update replaces only the field at the given index', () => {
      const { result } = renderHook(() => useTestHarness());
      act(() => result.current.payloadFields.add());
      act(() => result.current.payloadFields.add());

      act(() => result.current.payloadFields.update(0, { name: 'logs', description: 'd', required: true }));

      expect(result.current.template.payload_fields[0].name).toBe('logs');
      expect(result.current.template.payload_fields[1]).toMatchObject(DEFAULT_PAYLOAD_FIELD);
    });

    it('delete removes only the field at the given index', () => {
      const { result } = renderHook(() => useTestHarness());
      act(() => result.current.payloadFields.add());
      act(() => result.current.payloadFields.add());

      act(() => result.current.payloadFields.delete(0));

      expect(result.current.template.payload_fields).toHaveLength(1);
    });
  });

  describe('staticContexts', () => {
    it('add/update/delete manage the static_contexts array', () => {
      const { result } = renderHook(() => useTestHarness());

      act(() => result.current.staticContexts.add());
      expect(result.current.template.static_contexts).toHaveLength(1);

      act(() => result.current.staticContexts.update(0, { name: 'ctx', description: '', content: 'c' }));
      expect(result.current.template.static_contexts[0].name).toBe('ctx');

      act(() => result.current.staticContexts.delete(0));
      expect(result.current.template.static_contexts).toHaveLength(0);
    });
  });

  describe('webContexts', () => {
    it('add/update/delete manage the web_contexts array', () => {
      const { result } = renderHook(() => useTestHarness());

      act(() => result.current.webContexts.add());
      expect(result.current.template.web_contexts).toHaveLength(1);

      act(() => result.current.webContexts.update(0, { name: 'ctx', description: '', url: 'https://x' }));
      expect(result.current.template.web_contexts[0].url).toBe('https://x');

      act(() => result.current.webContexts.delete(0));
      expect(result.current.template.web_contexts).toHaveLength(0);
    });
  });
});
