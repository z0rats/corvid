import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import DescriptionIcon from '@mui/icons-material/Description';
import FingerprintIcon from '@mui/icons-material/Fingerprint';
import NetworkCheckIcon from '@mui/icons-material/NetworkCheck';
import SettingsIcon from '@mui/icons-material/Settings';

import { useSnortRuleState } from './hooks/state/useSnortRuleState';
import { useSnortRuleActions } from './hooks/ui/useSnortRuleActions';
import RuleHeader from './components/forms/RuleHeader';
import RuleOptions from './components/forms/RuleOptions';
import RuleContent from './components/forms/RuleContent';
import RuleMetadata from './components/forms/RuleMetadata';
import AccordionSection from '../shared/components/ui/AccordionSection';
import ActionButtons from '../shared/components/ui/ActionButtons';
import RulePreview from '../shared/components/ui/RulePreview';

export default function Snort() {
  const ruleState = useSnortRuleState();
  const actions = useSnortRuleActions(ruleState);

  const {
    ruleHeader, ruleOptions, ruleContent, ruleMetadata,
    setRuleHeader, setRuleOptions, setRuleContent, setRuleMetadata,
  } = ruleState;

  const {
    previewOpen, rulePreview,
    handlePreview, handleExport, handleReset, handleClosePreview, isRuleValid,
  } = actions;

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h5" align="center" gutterBottom>
        Snort/Suricata Rule Builder
      </Typography>

      <AccordionSection icon={<NetworkCheckIcon fontSize="small" sx={{ mr: 1 }} />} title="Rule Header" defaultExpanded>
        <RuleHeader ruleHeader={ruleHeader} handleRuleHeaderChange={setRuleHeader} />
      </AccordionSection>

      <AccordionSection icon={<SettingsIcon fontSize="small" sx={{ mr: 1 }} />} title="Rule Options" sx={{ mt: 1 }}>
        <RuleOptions ruleOptions={ruleOptions} handleRuleOptionsChange={setRuleOptions} />
      </AccordionSection>

      <AccordionSection icon={<FingerprintIcon fontSize="small" sx={{ mr: 1 }} />} title="Detection Content" sx={{ mt: 1 }}>
        <RuleContent ruleContent={ruleContent} handleRuleContentChange={setRuleContent} />
      </AccordionSection>

      <AccordionSection icon={<DescriptionIcon fontSize="small" sx={{ mr: 1 }} />} title="Enhanced Metadata" sx={{ mt: 1 }}>
        <RuleMetadata ruleMetadata={ruleMetadata} handleRuleMetadataChange={setRuleMetadata} />
      </AccordionSection>

      <ActionButtons
        onPreview={handlePreview}
        onExport={handleExport}
        onReset={handleReset}
        canPreview={isRuleValid()}
        canExport={isRuleValid()}
        ruleType="Snort"
      />

      <RulePreview
        open={previewOpen}
        onClose={handleClosePreview}
        rulePreview={rulePreview}
        title="Snort Rule Preview"
      />
    </Box>
  );
}
