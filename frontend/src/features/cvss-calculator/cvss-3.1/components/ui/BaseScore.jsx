import React, { useState } from "react";
import { useCvss31 } from "../../../shared/hooks/useCvss31";
import Circle from "../../../shared/components/Circle";
import BarChartIcon from '@mui/icons-material/BarChart';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import InfoModal from "../../../shared/components/InfoModal";
import MetricSelect from "../../../shared/components/MetricSelect";
import { getSeverityColor } from "../../../shared/utils/scoreUtils";
import { exploitabilityMetrics, impactMetrics } from "../../constants/metricsConfig";
import { useTranslation } from 'react-i18next';

export default function BaseScore() {
  const theme = useTheme();
  const chart = theme.palette.chart;
  const { state, updateMetric } = useCvss31();
  const { t } = useTranslation('cvssCalculator');
  const [openModal, setOpenModal] = useState(false);
  const [modalContent, setModalContent] = useState({ title: "", text: "" });

  const handleOpenModal = (title, text) => {
    setModalContent({ title, text });
    setOpenModal(true);
  };

  const handleCloseModal = () => {
    setOpenModal(false);
  };

  const handleSelectChange = (key) => (e) => {
    updateMetric('base', key, e.target.value);
  };

  const renderCard = (title, metrics) => (
    <Grid size={6}>
      <Typography variant="h6" align="center">
        {title}
      </Typography>
      {metrics.map((metric) => (
        <MetricSelect
          key={metric.key}
          label={metric.label}
          value={state.metrics.base[metric.key]}
          options={metric.options}
          onChange={handleSelectChange(metric.key)}
          onInfoClick={() => handleOpenModal(metric.label, metric.info)}
        />
      ))}
    </Grid>
  );

  return (
    <Accordion 
      defaultExpanded
      sx={{ 
        border: 'none', 
        boxShadow: 'none'
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
          <BarChartIcon fontSize="small" sx={{ mr: 1 }} />
          <Typography variant="subtitle2">{t('cvss31.base.accordionTitle')}</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 1, py: 1 }}>
        <Grid container spacing={2} sx={{ alignItems: "stretch" }}>
          <Box
            sx={{
              m: 1,
              p: 1,
              flex: 1,
              minWidth: 0,
            }}
          >
            <Typography variant="body1">
              {t('cvss31.base.description')}
            </Typography>
          </Box>
          <Box
            sx={{
              mb: 1,
              mt: 1,
              p: 1,
              minWidth: 0,
            }}
          >
            <Box
              sx={{
                width: 120,
                height: 120,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: theme.palette.background.cvssCircle,
                borderRadius: "50%",
                mx: "auto",
              }}
            >
              <Circle value={state.scores.base.baseScore} />
            </Box>
            <Typography
              variant="h6"
              fontWeight={state.scores.base.baseScore >= 9.0 ? "bold" : "normal"}
              sx={{ display: "block", marginBottom: 1, color: getSeverityColor(state.scores.base.baseScore, chart) }}
              align="center"
              gutterBottom
            >
              {state.scores.base.baseSeverity || t('common.severityNone')}
            </Typography>
          </Box>
        </Grid>

        <Box
          sx={{
            minWidth: 0,
          }}
        >
          <Grid container spacing={2}>
            {renderCard(
              t('cvss31.base.exploitabilityMetrics'),
              exploitabilityMetrics
            )}
            {renderCard(
              t('cvss31.base.impactMetrics'),
              impactMetrics
            )}
            <Box sx={{ mx: "auto", width: "40%" }}>
              <MetricSelect
                label={t('cvss31.base.scopeLabel')}
                value={state.metrics.base.scope}
                options={[
                  { value: "U", label: t('cvss31.base.scopeUnchanged') },
                  { value: "C", label: t('cvss31.base.scopeChanged') },
                ]}
                onChange={handleSelectChange("scope")}
                onInfoClick={() =>
                  handleOpenModal(
                    t('cvss31.base.scopeLabel'),
                    t('cvss31.base.scopeInfo')
                  )
                }
              />
            </Box>
          </Grid>
        </Box>
      </AccordionDetails>
      {openModal && (
        <InfoModal
          open={openModal}
          onClose={handleCloseModal}
          title={modalContent.title}
          text={modalContent.text}
        />
      )}
    </Accordion>
  );
}
