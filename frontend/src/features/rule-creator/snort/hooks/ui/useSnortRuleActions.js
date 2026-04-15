import { useState } from 'react';
import { generateSnortRule, exportSnortRule } from '../../services/snortRuleService';
import { useConfirmDialog } from '../../../shared/hooks/useConfirmDialog';
import { useErrorAlert } from '../../../shared/hooks/useErrorAlert';

export const useSnortRuleActions = (ruleState) => {
  const [previewOpen, setPreviewOpen] = useState(false);
  const [rulePreview, setRulePreview] = useState('');
  const { dialogState: confirmDialog, requestConfirmation, handleConfirm: onConfirmReset, handleCancel: onCancelReset } = useConfirmDialog();
  const { errorAlert, showError, hideError } = useErrorAlert();

  const {
    ruleHeader,
    ruleOptions,
    ruleContent,
    ruleMetadata,
    resetAll,
  } = ruleState;

  const isRuleValid = () => {
    return ruleOptions.msg.trim() && ruleOptions.sid.trim();
  };

  const handlePreview = () => {
    try {
      const rule = generateSnortRule(ruleHeader, ruleOptions, ruleContent, ruleMetadata);
      setRulePreview(rule);
      setPreviewOpen(true);
    } catch (error) {
      showError(error.message);
    }
  };

  const handleExport = () => {
    try {
      const rule = generateSnortRule(ruleHeader, ruleOptions, ruleContent, ruleMetadata);
      exportSnortRule(rule, ruleOptions.sid);
    } catch (error) {
      showError(error.message);
    }
  };

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

  const handleClosePreview = () => {
    setPreviewOpen(false);
    setRulePreview('');
  };

  return {
    previewOpen,
    rulePreview,
    confirmDialog,
    onConfirmReset,
    onCancelReset,
    errorAlert,
    hideError,

    handlePreview,
    handleExport,
    handleReset,
    handleClosePreview,
    isRuleValid,
  };
};
