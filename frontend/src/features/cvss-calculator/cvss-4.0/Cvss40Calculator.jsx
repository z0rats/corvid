import React from "react";
import BaseScore from "./components/ui/BaseScore";
import ThreatScore from "./components/ui/ThreatScore";
import SupplementalScore from "./components/ui/SupplementalScore";
import EnvironmentalScore from "./components/ui/EnvironmentalScore";
import Circle from "../shared/components/Circle";
import ExportCalculation from "./components/ui/ExportCalculation";
import EnhancedSpiderChart from "../shared/components/EnhancedSpiderChart";
import { useCvss40 } from "../shared/hooks/useCvss40";
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Grid from '@mui/material/Grid2';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import DataUsageIcon from '@mui/icons-material/DataUsage';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

export default function Cvss40Calculator() {
  const theme = useTheme();
  const { state, updateSingleMetric } = useCvss40();

  const flattenedMetrics = {
    ...state.metrics.base,
    ...state.metrics.threat,
    ...state.metrics.supplemental,
    ...state.metrics.environmental,
  };

  return (
    <Box sx={{ width: '100%', minHeight: '100vh' }}>

      {state.error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {state.error}
        </Alert>
      )}

      {state.loading && (
        <Box display="flex" justifyContent="center" sx={{ mb: 2 }}>
          <CircularProgress size={24} />
        </Box>
      )}

      <BaseScore 
        metrics={flattenedMetrics} 
        onMetricChange={updateSingleMetric} 
        scores={state.scores}
      />
      <ThreatScore 
        metrics={flattenedMetrics} 
        onMetricChange={updateSingleMetric}
      />
      <SupplementalScore 
        metrics={flattenedMetrics} 
        onMetricChange={updateSingleMetric}
      />
      <EnvironmentalScore 
        metrics={flattenedMetrics} 
        onMetricChange={updateSingleMetric}
      />
      
      <Accordion 
        defaultExpanded
        sx={{ 
          border: 'none', 
          boxShadow: 'none',
          mt: 1
        }}
      >
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          sx={{
            px: 1,
            py: 0.5,
            minHeight: '40px',
            '& .MuiAccordionSummary-content': {
              margin: 0,
            },
          }}
        >
          <Box display="flex" alignItems="center">
            <DataUsageIcon fontSize="small" sx={{ mr: 1 }} />
            <Typography variant="subtitle2">Overall CVSS 4.0 Score</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails sx={{ px: 1, py: 1 }}>
          <Box>
            <Grid container spacing={2} alignItems="center">
              <Grid size={{ xs: 12, md: 6 }} sx={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                <Typography variant="h5" gutterBottom>Overall Score</Typography>
                <Box sx={{
                  width: 160,
                  height: 160,
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  backgroundColor: theme.palette.background.cvssCircle,
                  borderRadius: "50%",
                }}>
                  <Circle value={state.scores.base_score || 0} />
                </Box>
                <Typography
                  variant="h6"
                  gutterBottom
                  sx={{ 
                    mt: 2,
                    fontWeight: (state.scores.base_score || 0) >= 9.0 ? "bold" : "normal",
                    color: (state.scores.base_score || 0) >= 7.0
                      ? "error.main"
                      : (state.scores.base_score || 0) >= 4.0
                      ? "warning.main"
                      : "success.main"
                  }}
                >
                  {state.scores.base_severity || "None"}
                </Typography>
              </Grid>
              
              <Grid size={{ xs: 12, md: 6 }} sx={{ height: 300 }}>
                <EnhancedSpiderChart
                  version="4.0"
                  metrics={state.metrics}
                  scores={state.scores}
                  title="CVSS 4.0 Metrics"
                  height={300}
                />
              </Grid>
              
              <Grid size={12}>
                <Typography variant="h6" align="center" gutterBottom>
                  Vector String: {state.vectorString}
                </Typography>
              </Grid>
            </Grid>
            <ExportCalculation 
              metrics={flattenedMetrics} 
              scores={state.scores} 
              vectorString={state.vectorString} 
            />
          </Box>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
}
