import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useYaraRuleState } from './hooks/state/useYaraRuleState';
import { useYaraRuleActions } from './hooks/ui/useYaraRuleActions';
import MetadataForm from './components/forms/MetadataForm';
import TagsForm from './components/forms/TagsForm';
import StringsForm from './components/forms/StringsForm';
import StringsList from './components/ui/StringsList';
import ConditionsForm from './components/forms/ConditionsForm';
import ActionButtons from '../shared/components/ui/ActionButtons';
import RulePreview from '../shared/components/ui/RulePreview';

export default function Yara() {
  const ruleState = useYaraRuleState();
  const actions = useYaraRuleActions(ruleState);

  const {
    metadata, strings, conditions, currentString, tags, currentTag,
    updateMetadata, updateCurrentString, updateConditions, setStringMatchCondition, updateCurrentTag,
  } = ruleState;

  const {
    previewOpen, rulePreview, errors,
    handleAddString, handleDeleteString, handleAddTag, handleDeleteTag,
    handlePreview, handleClosePreview, handleExport, handleReset,
    isValidForPreview, isValidForExport, canAddString, canAddTag, clearError,
  } = actions;

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h5" align="center" gutterBottom>
        YARA Rule Builder
      </Typography>

      <MetadataForm
        metadata={metadata}
        onMetadataChange={updateMetadata}
        errors={errors}
        onClearError={clearError}
      />

      <TagsForm
        tags={tags}
        currentTag={currentTag}
        onCurrentTagChange={updateCurrentTag}
        onAddTag={handleAddTag}
        onDeleteTag={handleDeleteTag}
        canAddTag={canAddTag}
      />

      <StringsForm
        currentString={currentString}
        onCurrentStringChange={updateCurrentString}
        onAddString={handleAddString}
        canAddString={canAddString}
        errors={errors}
        onClearError={clearError}
      />

      <StringsList
        strings={strings}
        onDeleteString={handleDeleteString}
      />

      <ConditionsForm
        conditions={conditions}
        onConditionsChange={updateConditions}
        onStringMatchChange={setStringMatchCondition}
      />

      <ActionButtons
        onPreview={handlePreview}
        onExport={handleExport}
        onReset={handleReset}
        canPreview={isValidForPreview()}
        canExport={isValidForExport()}
        ruleType="YARA"
      />

      <RulePreview
        open={previewOpen}
        onClose={handleClosePreview}
        rulePreview={rulePreview}
        title="YARA Rule Preview"
      />
    </Box>
  );
}
