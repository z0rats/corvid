import React, { useState, useMemo } from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import BugReportIcon from '@mui/icons-material/BugReport';
import AssessmentIcon from '@mui/icons-material/Assessment';

import NoDetails from '../NoDetails';
import MandiantSummary from './MandiantSummary';
import MandiantIndicators from './MandiantIndicators';
import MandiantReports from './MandiantReports';
import { buildCategoryStats, buildTimelineData, transformCategoryDataForPie } from './utils/mandiantDataUtils';

export default function MandiantDetails({ result: dataFromParent }) {
  const [indicatorsPage, setIndicatorsPage] = useState(1);
  const [reportsPage, setReportsPage] = useState(1);
  const theme = useTheme();
  const currentTheme = theme.palette.mode;

  const { indicators, reports, categoryStats, lineChartData, riskScore } = useMemo(() => {
    if (!dataFromParent) {
      return { indicators: [], reports: [], categoryStats: {}, lineChartData: [], riskScore: null };
    }

    const currentIndicators = dataFromParent.indicators || [];
    const currentReports = dataFromParent.reports?.objects || [];

    if (currentIndicators.length > 0) {
      const avgScore = currentIndicators.reduce((acc, ind) => acc + (ind.mscore || 0), 0) / currentIndicators.length;
      return {
        indicators: currentIndicators,
        reports: currentReports,
        categoryStats: buildCategoryStats(currentIndicators),
        lineChartData: buildTimelineData(currentIndicators),
        riskScore: Math.round(avgScore),
      };
    }

    return { indicators: currentIndicators, reports: currentReports, categoryStats: {}, lineChartData: [], riskScore: 0 };
  }, [dataFromParent]);

  const pieData = useMemo(() => transformCategoryDataForPie(categoryStats), [categoryStats]);

  const chartTheme = useMemo(() => ({
    tooltip: { container: { background: theme.palette.background.paper, color: theme.palette.text.primary, fontSize: '14px' } },
    labels: { text: { fill: theme.palette.text.primary } },
    legends: { text: { fill: theme.palette.text.primary } },
    axis: { ticks: { line: { stroke: theme.palette.divider }, text: { fill: theme.palette.text.secondary } }, legend: { text: { fill: theme.palette.text.secondary } } },
    grid: { line: { stroke: theme.palette.divider } },
  }), [theme]);

  if (!dataFromParent || (indicators.length === 0 && reports.length === 0)) {
    return <NoDetails message="No detailed intelligence information found for this indicator in Mandiant." />;
  }

  return (
    <Box sx={{ pt: 1 }}>
      <MandiantSummary
        categoryStats={categoryStats}
        pieData={pieData}
        lineChartData={lineChartData}
        riskScore={riskScore}
        indicatorCount={indicators.length}
        reportCount={reports.length}
        chartTheme={chartTheme}
        currentTheme={currentTheme}
      />

      {indicators.length > 0 && (
        <Accordion sx={{ borderRadius: 1, mb: 1, '&::before': { display: 'none' } }} defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} aria-controls="indicators-content" id="indicators-header">
            <Box display="flex" alignItems="center">
              <BugReportIcon sx={{ mr: 1 }} />
              <Typography variant="h6">Indicators ({indicators.length})</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: { xs: 1, sm: 2 } }}>
            <MandiantIndicators
              indicators={indicators}
              page={indicatorsPage}
              onPageChange={(_, value) => setIndicatorsPage(value)}
            />
          </AccordionDetails>
        </Accordion>
      )}

      {reports.length > 0 && (
        <Accordion sx={{ borderRadius: 1, '&::before': { display: 'none' } }} defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} aria-controls="reports-content" id="reports-header">
            <Box display="flex" alignItems="center">
              <AssessmentIcon sx={{ mr: 1 }} />
              <Typography variant="h6">Reports ({reports.length})</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: { xs: 1, sm: 2 } }}>
            <MandiantReports
              reports={reports}
              page={reportsPage}
              onPageChange={(_, value) => setReportsPage(value)}
            />
          </AccordionDetails>
        </Accordion>
      )}
    </Box>
  );
}
