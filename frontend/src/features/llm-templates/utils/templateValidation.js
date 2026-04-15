export function validateTemplateData(data) {
  const errors = [];

  if (!data.title?.trim()) {
    errors.push('Title is required');
  }
  if (!data.ai_agent_role?.trim()) {
    errors.push('AI agent role is required');
  }
  if (!data.ai_agent_task?.trim()) {
    errors.push('AI agent task is required');
  }
  if (!Array.isArray(data.payload_fields)) {
    errors.push('Payload fields must be an array');
  }
  if (data.temperature !== undefined && (data.temperature < 0 || data.temperature > 1)) {
    errors.push('Temperature must be between 0 and 1');
  }

  return { isValid: errors.length === 0, errors };
}

export function validateExecutionPayload(template, payloadData) {
  const errors = [];
  const warnings = [];

  if (!template) {
    return { isValid: false, errors: ['Template is required'], warnings };
  }
  if (!payloadData || typeof payloadData !== 'object') {
    return { isValid: false, errors: ['Payload data must be an object'], warnings };
  }

  const payloadFields = Array.isArray(template.payload_fields) ? template.payload_fields : [];
  const providedFields = Object.keys(payloadData);

  const requiredFields = payloadFields.filter(field => field.required);
  for (const field of requiredFields) {
    const value = payloadData[field.name];
    if (!value || typeof value !== 'string' || !value.trim()) {
      errors.push(`Required field "${field.name}" is missing or empty`);
    }
  }

  const expectedFields = payloadFields.map(field => field.name);
  const unexpectedFields = providedFields.filter(field => !expectedFields.includes(field));
  if (unexpectedFields.length > 0) {
    warnings.push(`Unexpected fields: ${unexpectedFields.join(', ')}`);
  }

  return { isValid: errors.length === 0, errors, warnings };
}

export function isTemplateFormValid(template) {
  const hasTitle = Boolean(template.title.trim());
  const hasRole = Boolean(template.ai_agent_role.trim());
  const hasTask = Boolean(template.ai_agent_task.trim());
  const fieldsValid = template.payload_fields.every(f => !f.required || f.name.trim());
  return hasTitle && hasRole && hasTask && fieldsValid;
}
