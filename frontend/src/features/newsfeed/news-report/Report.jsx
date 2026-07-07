import React from "react";
import { useTranslation } from "react-i18next";
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import Timeline from '@mui/lab/Timeline';
import TimelineItem from '@mui/lab/TimelineItem';
import TimelineSeparator from '@mui/lab/TimelineSeparator';
import TimelineDot from '@mui/lab/TimelineDot';
import TimelineConnector from '@mui/lab/TimelineConnector';
import TimelineContent from '@mui/lab/TimelineContent';
import TimelineOppositeContent from '@mui/lab/TimelineOppositeContent';
import { timelineOppositeContentClasses } from '@mui/lab/TimelineOppositeContent';
import SearchIcon from "@mui/icons-material/Search";
import AnalyticsIcon from "@mui/icons-material/Analytics";
import ListAltIcon from "@mui/icons-material/ListAlt";
import AssessmentOutlinedIcon from "@mui/icons-material/AssessmentOutlined";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutlined";

import { useReportAnalysis } from "../hooks/api/useReportAnalysis";
import { generateMarkdown, downloadMarkdown } from "../utils/reportUtils";
import RankingCard from "./components/ui/RankingCard";
import AnalysisCard from "./components/ui/AnalysisCard";

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

      <Timeline sx={{ [`& .${timelineOppositeContentClasses.root}`]: { flex: 0.18 } }}>
        {steps
          .filter((item) => step >= item.stepIndex)
          .map((item, idx, arr) => {
            const { stepIndex, label, Icon, renderContent } = item;
            const DotIcon = getTimelineDotIcon(step, stepIndex, Icon);

            return (
              <TimelineItem key={stepIndex} sx={{ alignItems: "flex-start" }}>
                <TimelineOppositeContent
                  sx={{ display: "flex", flexDirection: "column", justifyContent: "flex-start", textAlign: "right" }}
                  color="text.secondary"
                >
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>{label}</Typography>
                </TimelineOppositeContent>

                <TimelineSeparator>
                  {idx > 0 && <TimelineConnector />}
                  <TimelineDot color="primary">{DotIcon}</TimelineDot>
                  {idx < arr.length - 1 && <TimelineConnector />}
                </TimelineSeparator>

                <TimelineContent sx={{ py: 0, display: "flex", flexDirection: "column", justifyContent: "flex-start" }}>
                  {renderContent()}
                </TimelineContent>
              </TimelineItem>
            );
          })}
      </Timeline>
    </Box>
  );
}
