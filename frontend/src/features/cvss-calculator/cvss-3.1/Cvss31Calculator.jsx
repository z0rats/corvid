import React from "react";
import BaseScore from "./components/ui/BaseScore";
import TemporalScore from "./components/ui/TemporalScore";
import EnvironmentalScore from "./components/ui/EnvironmentalScore";
import Circle from "../shared/components/Circle";
import ExportCalculation from "./components/ui/ExportCalculation";
import EnhancedSpiderChart from "../shared/components/EnhancedSpiderChart";
import { useCvss31 } from "../shared/hooks/useCvss31";
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import DataUsageIcon from '@mui/icons-material/DataUsage';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

export default function Cvss31Calculator() {
  const theme = useTheme();
  const { state } = useCvss31();

  return (
    <Box sx={{ width: '100%', minHeight: '100vh' }}>

      {state.error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {state.error}
        </Alert>
      )}

      <BaseScore />
      <TemporalScore />
      <EnvironmentalScore />
      
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
            <Typography variant="subtitle2">Overall CVSS 3.1 Score</Typography>
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
                  <Circle value={state.scores.environmental.environmentalScore} />
                </Box>
                <Typography
                  variant="h6"
                  gutterBottom
                  sx={{ 
                    mt: 2,
                    fontWeight: state.scores.environmental.environmentalScore >= 9.0 ? "bold" : "normal",
                    color: state.scores.environmental.environmentalScore >= 7.0
                      ? "error.main"
                      : state.scores.environmental.environmentalScore >= 4.0
                      ? "warning.main"
                      : "success.main"
                  }}
                >
                  {state.scores.environmental.environmentalSeverity}
                </Typography>
              </Grid>
              
              <Grid size={{ xs: 12, md: 6 }} sx={{ height: 300 }}>
                <EnhancedSpiderChart
                  version="3.1"
                  metrics={state.metrics}
                  scores={state.scores}
                  title="CVSS 3.1 Metrics"
                  height={300}
                />
              </Grid>
              
              <Grid size={12}>
                <Typography variant="h6" align="center" gutterBottom>
                  Vector String: {state.vectorString}
                </Typography>
              </Grid>
            </Grid>
            <ExportCalculation cvssScores={state} vectorString={state.vectorString} />
          </Box>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
}
