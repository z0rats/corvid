import { useState, useMemo } from 'react';
import { useAtomValue } from 'jotai';
import { aiSettingsState } from '../../../../core/state/atoms';

import {
  DEFAULT_TEMPLATE_STATE,
  DEFAULT_PAYLOAD_FIELD,
  DEFAULT_STATIC_CONTEXT,
  DEFAULT_WEB_CONTEXT,
} from '../../constants/templateConstants';

export function useTemplateForm(initialState = DEFAULT_TEMPLATE_STATE) {
  const aiSettings = useAtomValue(aiSettingsState);
  const defaultModel = aiSettings.llm_templates_model || aiSettings.default_model || '';

  const resolvedInitial = useMemo(() => ({
    ...initialState,
    model: initialState.model || defaultModel,
  }), [initialState, defaultModel]);

  const [template, setTemplate] = useState(resolvedInitial);

  const updateField = (key, value) => {
    setTemplate(prev => ({ ...prev, [key]: value }));
  };

  const resetForm = () => setTemplate({ ...DEFAULT_TEMPLATE_STATE, model: defaultModel });

  const addPayloadField = () => {
    setTemplate(prev => ({
      ...prev,
      payload_fields: [...prev.payload_fields, { ...DEFAULT_PAYLOAD_FIELD, id: crypto.randomUUID() }],
    }));
  };

  const updatePayloadField = (idx, updated) => {
    setTemplate(prev => ({
      ...prev,
      payload_fields: prev.payload_fields.map((f, i) => (i === idx ? updated : f)),
    }));
  };

  const deletePayloadField = (idx) => {
    setTemplate(prev => ({
      ...prev,
      payload_fields: prev.payload_fields.filter((_, i) => i !== idx),
    }));
  };

  const addStaticContext = () => {
    setTemplate(prev => ({
      ...prev,
      static_contexts: [...prev.static_contexts, { ...DEFAULT_STATIC_CONTEXT, id: crypto.randomUUID() }],
    }));
  };

  const updateStaticContext = (idx, updated) => {
    setTemplate(prev => ({
      ...prev,
      static_contexts: prev.static_contexts.map((c, i) => (i === idx ? updated : c)),
    }));
  };

  const deleteStaticContext = (idx) => {
    setTemplate(prev => ({
      ...prev,
      static_contexts: prev.static_contexts.filter((_, i) => i !== idx),
    }));
  };

  const addWebContext = () => {
    setTemplate(prev => ({
      ...prev,
      web_contexts: [...prev.web_contexts, { ...DEFAULT_WEB_CONTEXT, id: crypto.randomUUID() }],
    }));
  };

  const updateWebContext = (idx, updated) => {
    setTemplate(prev => ({
      ...prev,
      web_contexts: prev.web_contexts.map((c, i) => (i === idx ? updated : c)),
    }));
  };

  const deleteWebContext = (idx) => {
    setTemplate(prev => ({
      ...prev,
      web_contexts: prev.web_contexts.filter((_, i) => i !== idx),
    }));
  };

  return {
    template,
    setTemplate,
    updateField,
    resetForm,
    payloadFields: {
      add: addPayloadField,
      update: updatePayloadField,
      delete: deletePayloadField,
    },
    staticContexts: {
      add: addStaticContext,
      update: updateStaticContext,
      delete: deleteStaticContext,
    },
    webContexts: {
      add: addWebContext,
      update: updateWebContext,
      delete: deleteWebContext,
    },
  };
}
