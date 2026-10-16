export const SYSTEM_CATEGORY_IDS = {
  FAVORITES: '00000000-0000-0000-0000-000000000001',
  DEFAULT: '00000000-0000-0000-0000-000000000002',
};

export const DEFAULT_TEMPLATE_STATE = {
  title: '',
  description: '',
  ai_agent_role: '',
  ai_agent_task: '',
  payload_fields: [],
  static_contexts: [],
  web_contexts: [],
  example_input_output: '',
  is_public: true,
  temperature: 0.7,
  model: '',
  category_id: SYSTEM_CATEGORY_IDS.DEFAULT,
};

export const DEFAULT_PAYLOAD_FIELD = { name: '', description: '', required: true };
export const DEFAULT_STATIC_CONTEXT = { name: '', description: '', content: '' };
export const DEFAULT_WEB_CONTEXT = { name: '', description: '', url: '' };
