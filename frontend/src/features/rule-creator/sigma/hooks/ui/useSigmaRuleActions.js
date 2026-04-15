import { useState } from 'react';
import { generateSigmaRule, exportSigmaRule } from '../../services/sigmaRuleService';
import { useConfirmDialog } from '../../../shared/hooks/useConfirmDialog';
import { useErrorAlert } from '../../../shared/hooks/useErrorAlert';

/**
 * Custom hook for managing Sigma rule UI actions
 * @param {Object} ruleState - Rule state from useSigmaRuleState
 * @returns {Object} UI actions and state
 */
export const useSigmaRuleActions = (ruleState) => {
  const [previewOpen, setPreviewOpen] = useState(false);
  const [rulePreview, setRulePreview] = useState('');
  const { dialogState: confirmDialog, requestConfirmation, handleConfirm: onConfirmReset, handleCancel: onCancelReset } = useConfirmDialog();
  const { errorAlert, showError, hideError } = useErrorAlert();

  const {
    metadata,
    logSource,
    detections,
    conditionsList,
    fields,
    references,
    tags,
    falsePositives,
    resetAll,
  } = ruleState;

  /**
   * Check if rule is valid for preview/export
   * @returns {boolean} Validation result
   */
  const isRuleValid = () => {
    return metadata.title.trim() && metadata.id.trim();
  };

  /**
   * Handle rule preview
   */
  const handlePreview = () => {
    try {
      const rule = generateSigmaRule(
        metadata,
        logSource,
        conditionsList,
        detections,
        fields,
        references,
        tags,
        falsePositives
      );
      setRulePreview(rule);
      setPreviewOpen(true);
    } catch (error) {
      showError(error.message);
    }
  };

  /**
   * Handle rule export
   */
  const handleExport = () => {
    try {
      const rule = generateSigmaRule(
        metadata,
        logSource,
        conditionsList,
        detections,
        fields,
        references,
        tags,
        falsePositives
      );
      exportSigmaRule(rule, metadata.title);
    } catch (error) {
      showError(error.message);
    }
  };

  /**
   * Handle form reset
   */
  const handleReset = () => {
    requestConfirmation(
      'Reset Form',
      'Are you sure you want to reset the form? All data will be lost.',
      () => {
        resetAll();
        setRulePreview('');
        setPreviewOpen(false);
      }
    );
  };

  /**
   * Handle preview dialog close
   */
  const handleClosePreview = () => {
    setPreviewOpen(false);
    setRulePreview('');
  };

  return {
    // UI State
    previewOpen,
    rulePreview,
    confirmDialog,
    onConfirmReset,
    onCancelReset,
    errorAlert,
    hideError,

    // Actions
    handlePreview,
    handleExport,
    handleReset,
    handleClosePreview,
    isRuleValid,
  };
};
