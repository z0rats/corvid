import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import DescriptionIcon from '@mui/icons-material/Description';
import LinkIcon from '@mui/icons-material/Link';
import TagIcon from '@mui/icons-material/Tag';
import SecurityIcon from '@mui/icons-material/Security';
import FingerprintIcon from '@mui/icons-material/Fingerprint';
import CodeIcon from '@mui/icons-material/Code';
import WarningIcon from '@mui/icons-material/Warning';

import { useSigmaRuleState } from './hooks/state/useSigmaRuleState';
import { useSigmaRuleActions } from './hooks/ui/useSigmaRuleActions';
import Metadata from './components/forms/Metadata';
import References from './components/forms/References';
import Tags from './components/forms/Tags';
import LogSource from './components/forms/LogSource';
import Detection from './components/forms/Detection';
import Fields from './components/forms/Fields';
import FalsePositives from './components/forms/FalsePositives';
import AccordionSection from '../shared/components/ui/AccordionSection';
import ActionButtons from '../shared/components/ui/ActionButtons';
import RulePreview from '../shared/components/ui/RulePreview';

export default function Sigma() {
  const ruleState = useSigmaRuleState();
  const actions = useSigmaRuleActions(ruleState);

  const {
    metadata, logSource, detections, conditionsList,
    fields, references, tags, falsePositives,
    setMetadata, setLogSource, setDetections, setConditionsList,
    setFields, setReferences, setTags, setFalsePositives,
  } = ruleState;

  const {
    previewOpen, rulePreview,
    handlePreview, handleExport, handleReset, handleClosePreview, isRuleValid,
  } = actions;

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h5" align="center" gutterBottom>
        Sigma Rule Builder
      </Typography>

      <AccordionSection icon={<DescriptionIcon fontSize="small" sx={{ mr: 1 }} />} title="Rule Metadata" defaultExpanded>
        <Metadata metadata={metadata} handleMetadataChange={setMetadata} />
      </AccordionSection>

      <AccordionSection icon={<LinkIcon fontSize="small" sx={{ mr: 1 }} />} title="References" sx={{ mt: 1 }}>
        <References references={references} handleReferencesChange={setReferences} />
      </AccordionSection>

      <AccordionSection icon={<TagIcon fontSize="small" sx={{ mr: 1 }} />} title="Tags" sx={{ mt: 1 }}>
        <Tags tags={tags} handleTagsChange={setTags} />
      </AccordionSection>

      <AccordionSection icon={<SecurityIcon fontSize="small" sx={{ mr: 1 }} />} title="Log Source" sx={{ mt: 1 }}>
        <LogSource logSource={logSource} handleLogSourceChange={setLogSource} />
      </AccordionSection>

      <AccordionSection icon={<FingerprintIcon fontSize="small" sx={{ mr: 1 }} />} title="Detection" sx={{ mt: 1 }}>
        <Detection
          detections={detections}
          handleDetectionsChange={setDetections}
          conditionsList={conditionsList}
          handleConditionsListChange={setConditionsList}
        />
      </AccordionSection>

      <AccordionSection icon={<CodeIcon fontSize="small" sx={{ mr: 1 }} />} title="Fields" sx={{ mt: 1 }}>
        <Fields fields={fields} handleFieldsChange={setFields} />
      </AccordionSection>

      <AccordionSection icon={<WarningIcon fontSize="small" sx={{ mr: 1 }} />} title="False Positives" sx={{ mt: 1 }}>
        <FalsePositives falsePositives={falsePositives} handleFalsePositivesChange={setFalsePositives} />
      </AccordionSection>

      <ActionButtons
        onPreview={handlePreview}
        onExport={handleExport}
        onReset={handleReset}
        canPreview={isRuleValid()}
        canExport={isRuleValid()}
        ruleType="Sigma"
      />

      <RulePreview open={previewOpen} onClose={handleClosePreview} rulePreview={rulePreview} />
    </Box>
  );
}
