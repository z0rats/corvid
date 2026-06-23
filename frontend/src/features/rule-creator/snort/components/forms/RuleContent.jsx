import React from 'react';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import ContentMatching from './ContentMatching';
import PcreSection from './PcreSection';
import FlowbitsSection from './FlowbitsSection';

export default function RuleContent({ ruleContent, handleRuleContentChange }) {
  const handleContentChange = (newContent) => {
    handleRuleContentChange(prev => ({ ...prev, content: newContent }));
  };

  const handlePcreChange = (newPcre) => {
    handleRuleContentChange(prev => ({ ...prev, pcre: newPcre }));
  };

  const handleFlowbitsChange = (newFlowbits) => {
    handleRuleContentChange(prev => ({ ...prev, flowbits: newFlowbits }));
  };

  const handleFieldChange = (field, value) => {
    handleRuleContentChange(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Box>
      <ContentMatching contentList={ruleContent.content} onContentChange={handleContentChange} />
      <PcreSection pcreList={ruleContent.pcre} onPcreChange={handlePcreChange} />
      <FlowbitsSection flowbitsList={ruleContent.flowbits} onFlowbitsChange={handleFlowbitsChange} />

      <Box>
        <Typography variant="subtitle2" gutterBottom>
          Rate Limiting
        </Typography>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="Threshold"
              value={ruleContent.threshold}
              onChange={(e) => handleFieldChange('threshold', e.target.value)}
              size="small"
              variant="outlined"
              placeholder="type limit, track by_src, count 5, seconds 60"
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="Detection Filter"
              value={ruleContent.detection_filter}
              onChange={(e) => handleFieldChange('detection_filter', e.target.value)}
              size="small"
              variant="outlined"
              placeholder="track by_src, count 10, seconds 60"
            />
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
}
