import { useState } from 'react';
import { generateYaraRule, exportYaraRule } from '../../services/yaraRuleService';
import { validateStringIdentifier, validateStringValue, validateRuleName } from '../../utils/yaraUtils';
import { useConfirmDialog } from '../../../shared/hooks/useConfirmDialog';
import { useErrorAlert } from '../../../shared/hooks/useErrorAlert';

export const useYaraRuleActions = (ruleState) => {
  const [previewOpen, setPreviewOpen] = useState(false);
  const [rulePreview, setRulePreview] = useState('');
  const [errors, setErrors] = useState({});
  const { dialogState: confirmDialog, requestConfirmation, handleConfirm: onConfirmReset, handleCancel: onCancelReset } = useConfirmDialog();
  const { errorAlert, hideError } = useErrorAlert();

  const {
    metadata,
    strings,
    conditions,
    currentString,
    tags,
    currentTag,
    addString,
    removeString,
    resetCurrentString,
    addTag,
    removeTag,
    resetCurrentTag,
    resetAll,
  } = ruleState;

  const handleAddString = () => {
    setErrors({});

    const identifierValidation = validateStringIdentifier(currentString.identifier, strings);
    if (!identifierValidation.isValid) {
      setErrors({ identifier: identifierValidation.error });
      return false;
    }

    const valueValidation = validateStringValue(currentString.value, currentString.type);
    if (!valueValidation.isValid) {
      setErrors({ value: valueValidation.error });
      return false;
    }

    const stringToAdd = {
      ...currentString,
      identifier: currentString.identifier.trim(),
      value: currentString.value.trim(),
    };

    addString(stringToAdd);
    resetCurrentString();
    return true;
  };

  const handleDeleteString = (idToRemove) => {
    removeString(idToRemove);
  };

  const handleAddTag = () => {
    if (currentTag.trim()) {
      addTag(currentTag);
      resetCurrentTag();
    }
  };

  const handleDeleteTag = (idToDelete) => {
    removeTag(idToDelete);
  };

  const handlePreview = () => {
    const ruleNameValidation = validateRuleName(metadata.ruleName);
    if (!ruleNameValidation.isValid) {
      setErrors({ ruleName: ruleNameValidation.error });
      return;
    }

    setErrors({});
    const rule = generateYaraRule(metadata, strings, conditions, tags);
    setRulePreview(rule);
    setPreviewOpen(true);
  };

  const handleClosePreview = () => {
    setPreviewOpen(false);
    setRulePreview('');
  };

  const handleExport = () => {
    const ruleNameValidation = validateRuleName(metadata.ruleName);
    if (!ruleNameValidation.isValid) {
      setErrors({ ruleName: ruleNameValidation.error });
      return;
    }

    setErrors({});
    const rule = generateYaraRule(metadata, strings, conditions, tags);
    exportYaraRule(rule, metadata.ruleName);
  };

  const handleReset = () => {
    requestConfirmation(
      'Reset Form',
      'Are you sure you want to reset the form? All data will be lost.',
      () => {
        resetAll();
        setErrors({});
        setPreviewOpen(false);
        setRulePreview('');
      }
    );
  };

  const isValidForPreview = () => {
    const ruleNameValidation = validateRuleName(metadata.ruleName);
    return ruleNameValidation.isValid;
  };

  const isValidForExport = () => {
    return isValidForPreview();
  };

  const canAddString = () => {
    return currentString.identifier.trim() !== '' && currentString.value.trim() !== '';
  };

  const canAddTag = () => {
    return currentTag.trim() !== '' && !tags.some((tag) => tag.value === currentTag.trim());
  };

  const clearError = (field) => {
    setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[field];
      return newErrors;
    });
  };

  return {
    previewOpen,
    rulePreview,
    errors,
    confirmDialog,
    onConfirmReset,
    onCancelReset,
    errorAlert,
    hideError,

    handleAddString,
    handleDeleteString,

    handleAddTag,
    handleDeleteTag,

    handlePreview,
    handleClosePreview,
    handleExport,
    handleReset,

    isValidForPreview,
    isValidForExport,
    canAddString,
    canAddTag,

    clearError,
  };
};
