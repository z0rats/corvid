import React from "react";
import { useTranslation } from "react-i18next";
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import SearchIcon from "@mui/icons-material/SearchOutlined";
import AnalyticsIcon from "@mui/icons-material/AnalyticsOutlined";
import ListAltIcon from "@mui/icons-material/ListAltOutlined";
import AssessmentOutlinedIcon from "@mui/icons-material/AssessmentOutlined";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutlined";

import { useReportAnalysis } from "../hooks/api/useReportAnalysis";
import { generateMarkdown, downloadMarkdown } from "../utils/reportUtils";
import RankingCard from "./components/ui/RankingCard";
import AnalysisCard from "./components/ui/AnalysisCard";

// A minimal vertical timeline: label column | dot + connectors | content.
const TimelineConnector = () => <Box sx={{ width: 2, flexGrow: 1, bgcolor: "divider" }} />;

const TimelineDot = ({ children }) => (
  <Box
    sx={{
      display: "flex",
      p: 0.5,
      my: 1.5,
      borderRadius: "50%",
      bgcolor: "primary.main",
      color: "primary.contrastText",
      boxShadow: 1,
    }}
  >
    {children}
  </Box>
);

function getTimelineDotIcon(step, stepIndex, DefaultIcon) {
  if (step === stepIndex) return <DefaultIcon />;
  if (step > stepIndex) return <CheckCircleOutlineIcon />;
  return null;
}

export default function Report() {
  const { t } = useTranslation('newsfeed');
  const {
    step,
    isLoading,
    error,
    infoMessage,
    ranking,
    analysisResults,
    showStopButton,
    startAnalysis,
    stopAnalysis,
  } = useReportAnalysis();

  const handleExportMarkdown = () => {
    const content = generateMarkdown(ranking, analysisResults);
    downloadMarkdown(content);
  };

  const steps = [
    { stepIndex: 1, label: t('report.steps.fetch'), Icon: SearchIcon, renderContent: () => null },
    { stepIndex: 2, label: t('report.steps.rank'), Icon: AnalyticsIcon, renderContent: () => null },
    {
      stepIndex: 3,
      label: t('report.steps.showTop'),
      Icon: ListAltIcon,
      renderContent: () => {
        if (step < 3) return null;
        return (
          <Box>
            {ranking.length === 0 && (
              <Typography variant="body2" color="text.secondary">{t('report.noArticlesFound')}</Typography>
            )}
            {ranking.map((article, idx) => (
              <RankingCard key={article.id} article={article} index={idx} />
            ))}
          </Box>
        );
      },
    },
    {
      stepIndex: 4,
      label: t('report.steps.analyze'),
      Icon: AssessmentOutlinedIcon,
      renderContent: () => {
        if (step < 4) return null;
        return (
          <Box>
            <Typography variant="h6" sx={{ fontWeight: "bold", mb: 1 }}>{t('report.detailedAnalysis')}</Typography>
            {analysisResults.length === 0 && (
              <Typography variant="body2" color="text.secondary">{t('report.waitingForFirstResult')}</Typography>
            )}
            {analysisResults.map((res, i) => (
              <AnalysisCard key={`${res.article_id}-${i}`} result={res} index={i} />
            ))}
          </Box>
        );
      },
    },
    {
      stepIndex: 5,
      label: t('report.steps.completed'),
      Icon: CheckCircleOutlineIcon,
      renderContent: () => {
        if (step < 5) return null;
        return (
          <Box>
            <Typography variant="h6" sx={{ fontWeight: "bold", mb: 1 }}>{t('report.analysisComplete')}</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('report.restartMessage')}
            </Typography>
            <Button variant="contained" onClick={handleExportMarkdown}>
              {t('report.downloadMarkdown')}
            </Button>
          </Box>
        );
      },
    },
  ];

  return (
    <Box sx={{ width: "100%", py: 4, px: 2 }}>
      <Typography variant="h4" gutterBottom>{t('report.pageTitle')}</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
        {t('report.pageDescription')}
      </Typography>

      {!showStopButton && step !== 5 && (
        <Box sx={{ mb: 2 }}>
          <Button variant="contained" onClick={startAnalysis}>{t('report.startAnalysis')}</Button>
        </Box>
      )}
      {showStopButton && (
        <Box sx={{ mb: 2 }}>
          <Button variant="outlined" color="error" onClick={stopAnalysis}>{t('report.stopAnalysis')}</Button>
        </Box>
      )}

      {isLoading && (
        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
          <CircularProgress size={24} sx={{ mr: 2 }} />
          <Typography>{t('report.fetchingAnalyzing')}</Typography>
        </Box>
      )}

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {infoMessage && <Alert severity="info" sx={{ mb: 2 }}>{infoMessage}</Alert>}

      <Divider sx={{ mb: 3 }} />

      <Box sx={{ display: "flex", flexDirection: "column", px: 2, py: 0.75 }}>
        {steps
          .filter((item) => step >= item.stepIndex)
          .map((item, idx, arr) => {
            const { stepIndex, label, Icon, renderContent } = item;
            const DotIcon = getTimelineDotIcon(step, stepIndex, Icon);

            return (
              <Box key={stepIndex} sx={{ display: "flex", alignItems: "stretch", minHeight: 70 }}>
                <Box sx={{ flex: 0.18, px: 2, py: 0.75, textAlign: "right", color: "text.secondary" }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>{label}</Typography>
                </Box>

                <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                  {idx > 0 && <TimelineConnector />}
                  <TimelineDot>{DotIcon}</TimelineDot>
                  {idx < arr.length - 1 && <TimelineConnector />}
                </Box>

                <Box sx={{ flex: 1, px: 2, display: "flex", flexDirection: "column", justifyContent: "flex-start" }}>
                  {renderContent()}
                </Box>
              </Box>
            );
          })}
      </Box>
    </Box>
  );
}
