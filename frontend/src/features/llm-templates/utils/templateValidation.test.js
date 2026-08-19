import {
  validateTemplateData,
  validateExecutionPayload,
  isTemplateFormValid,
} from './templateValidation';

describe('validateTemplateData', () => {
  const valid = {
    title: 'My Template',
    ai_agent_role: 'role',
    ai_agent_task: 'task',
    payload_fields: [],
  };

  it('accepts a fully-populated template', () => {
    expect(validateTemplateData(valid)).toEqual({ isValid: true, errors: [] });
  });

  it('collects every missing required field, not just the first', () => {
    const result = validateTemplateData({ payload_fields: [] });

    expect(result.isValid).toBe(false);
    expect(result.errors).toEqual([
      'Title is required',
      'AI agent role is required',
      'AI agent task is required',
    ]);
  });

  it('rejects whitespace-only text fields', () => {
    const result = validateTemplateData({ ...valid, title: '   ' });
    expect(result.errors).toContain('Title is required');
  });

  it('rejects a non-array payload_fields', () => {
    const result = validateTemplateData({ ...valid, payload_fields: 'not-an-array' });
    expect(result.errors).toContain('Payload fields must be an array');
  });

  it('rejects a temperature outside 0-1', () => {
    expect(validateTemplateData({ ...valid, temperature: 1.5 }).errors).toContain(
      'Temperature must be between 0 and 1',
    );
    expect(validateTemplateData({ ...valid, temperature: -0.1 }).errors).toContain(
      'Temperature must be between 0 and 1',
    );
  });

  it('allows temperature to be omitted', () => {
    expect(validateTemplateData(valid).isValid).toBe(true);
  });
});

describe('validateExecutionPayload', () => {
  const template = {
    payload_fields: [
      { name: 'logs', required: true },
      { name: 'notes', required: false },
    ],
  };

  it('accepts a payload that satisfies every required field', () => {
    const result = validateExecutionPayload(template, { logs: 'some logs' });
    expect(result.isValid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it('rejects a missing template', () => {
    expect(validateExecutionPayload(null, {})).toEqual({
      isValid: false,
      errors: ['Template is required'],
      warnings: [],
    });
  });

  it('rejects non-object payload data', () => {
    const result = validateExecutionPayload(template, null);
    expect(result.isValid).toBe(false);
    expect(result.errors).toEqual(['Payload data must be an object']);
  });

  it('flags a required field that is missing entirely', () => {
    const result = validateExecutionPayload(template, {});
    expect(result.errors).toEqual(['Required field "logs" is missing or empty']);
  });

  it('flags a required field that is present but blank', () => {
    const result = validateExecutionPayload(template, { logs: '   ' });
    expect(result.errors).toEqual(['Required field "logs" is missing or empty']);
  });

  it('does not flag a missing optional field', () => {
    const result = validateExecutionPayload(template, { logs: 'x' });
    expect(result.isValid).toBe(true);
  });

  it('warns about (but does not error on) unexpected fields', () => {
    const result = validateExecutionPayload(template, { logs: 'x', extra_field: 'y' });
    expect(result.isValid).toBe(true);
    expect(result.warnings).toEqual(['Unexpected fields: extra_field']);
  });

  it('treats a template with no payload_fields as requiring nothing', () => {
    const result = validateExecutionPayload({}, {});
    expect(result.isValid).toBe(true);
  });
});

describe('isTemplateFormValid', () => {
  const base = { title: 't', ai_agent_role: 'r', ai_agent_task: 'k', payload_fields: [] };

  it('is true when title/role/task are set and all fields are valid', () => {
    expect(isTemplateFormValid(base)).toBe(true);
  });

  it('is false when the title is blank', () => {
    expect(isTemplateFormValid({ ...base, title: '  ' })).toBe(false);
  });

  it('is false when a required payload field has no name', () => {
    const template = { ...base, payload_fields: [{ name: '  ', required: true }] };
    expect(isTemplateFormValid(template)).toBe(false);
  });

  it('is true when an unnamed payload field is not required', () => {
    const template = { ...base, payload_fields: [{ name: '', required: false }] };
    expect(isTemplateFormValid(template)).toBe(true);
  });
});
