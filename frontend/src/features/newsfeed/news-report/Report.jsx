import React from "react";
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
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";

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
    { stepIndex: 1, label: "Fetch all news articles of the last 7 days", Icon: SearchIcon, renderContent: () => null },
    { stepIndex: 2, label: "Rank news articles by relevance", Icon: AnalyticsIcon, renderContent: () => null },
    {
      stepIndex: 3,
      label: "Show 10 most relevant articles",
      Icon: ListAltIcon,
      renderContent: () => {
        if (step < 3) return null;
        return (
          <Box>
            {ranking.length === 0 && (
              <Typography variant="body2" color="text.secondary">No articles found or none returned.</Typography>
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
      label: "Analyze most relevant articles and create reports",
      Icon: AssessmentOutlinedIcon,
      renderContent: () => {
        if (step < 4) return null;
        return (
          <Box>
            <Typography variant="h6" sx={{ fontWeight: "bold", mb: 1 }}>Detailed Analysis</Typography>
            {analysisResults.length === 0 && (
              <Typography variant="body2" color="text.secondary">Waiting for the first analysis result...</Typography>
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
      label: "Completed analysis and report creation",
      Icon: CheckCircleOutlineIcon,
      renderContent: () => {
        if (step < 5) return null;
        return (
          <Box>
            <Typography variant="h6" sx={{ fontWeight: "bold", mb: 1 }}>Analysis Complete</Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              All articles have been analyzed. You may restart if you wish to run another analysis.
            </Typography>
            <Button variant="contained" onClick={handleExportMarkdown}>
              Download Markdown Report
            </Button>
          </Box>
        );
      },
    },
  ];

  return (
    <Box sx={{ width: "100%", py: 4, px: 2 }}>
      <Typography variant="h4" gutterBottom>News Report Generator</Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        This tool fetches all cybersecurity news from the last 7 days, ranks the top 10 relevant news by headline,
        and then provides a detailed analysis of each article.
      </Typography>

      {!showStopButton && step !== 5 && (
        <Box sx={{ mb: 2 }}>
          <Button variant="contained" onClick={startAnalysis}>Start Analysis</Button>
        </Box>
      )}
      {showStopButton && (
        <Box sx={{ mb: 2 }}>
          <Button variant="outlined" color="error" onClick={stopAnalysis}>Stop Analysis</Button>
        </Box>
      )}

      {isLoading && (
        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
          <CircularProgress size={24} sx={{ mr: 2 }} />
          <Typography>Fetching / Analyzing...</Typography>
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
