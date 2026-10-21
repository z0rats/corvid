import React from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import ButtonGroup from "@mui/material/ButtonGroup";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDownOutlined";
import DownloadIcon from "@mui/icons-material/DownloadOutlined";
import ClickAwayListener from "@mui/material/ClickAwayListener";
import Grow from "@mui/material/Grow";
import MenuItem from "@mui/material/MenuItem";
import MenuList from "@mui/material/MenuList";
import Paper from "@mui/material/Paper";
import Popper from "@mui/material/Popper";
import { downloadBlob } from "../../../shared/utils/fileUtils";
import { METRIC_MAPS } from "../../constants/exportMaps";
import {
  exploitabilityMetrics,
  vulnerableSystemImpactMetrics,
  subsequentSystemImpactMetrics,
  threatMetrics,
  supplementalMetrics,
  modifiedExploitabilityMetrics,
  modifiedVulnerableSystemImpactMetrics,
  modifiedSubsequentSystemImpactMetrics,
} from "../../constants/metricsConfig";
import { useTranslation } from 'react-i18next';

const BASE_METRICS = [...exploitabilityMetrics, ...vulnerableSystemImpactMetrics, ...subsequentSystemImpactMetrics];
const ENVIRONMENTAL_METRICS = [
  ...modifiedExploitabilityMetrics,
  ...modifiedVulnerableSystemImpactMetrics,
  ...modifiedSubsequentSystemImpactMetrics,
];

// Display label of a metric's current value; unset optional metrics read as "Not Defined".
const metricValueLabel = (key, metrics) => METRIC_MAPS[key]?.[metrics[key] || "X"] || "Unknown";

// metric key -> export field name and i18n key suffix: "attack_vector" -> "attackVector"
const toExportName = (key) => key.replace(/_([a-z])/g, (_, c) => c.toUpperCase());

const metricGroupJson = (group, metrics) =>
  Object.fromEntries(group.map(({ key }) => [toExportName(key), metricValueLabel(key, metrics)]));

export default function ExportCalculation({ metrics, scores, vectorString }) {
  const { t } = useTranslation('cvssCalculator');
  const options = [t('common.exportAsMarkdown'), t('common.exportAsJson')];
  const [open, setOpen] = React.useState(false);
  const anchorRef = React.useRef(null);
  const [selectedIndex] = React.useState(0);

  const handleClick = () => {
    exportCalculationMarkdown();
  };

  const handleMenuItemClick = (event, index) => {
    if (index === 0) {
      exportCalculationMarkdown();
    } else if (index === 1) {
      exportCalculationJson();
    }
    setOpen(false);
  };

  const handleToggle = () => {
    setOpen((prevOpen) => !prevOpen);
  };

  const handleClose = (event) => {
    if (anchorRef.current && anchorRef.current.contains(event.target)) {
      return;
    }
    setOpen(false);
  };

  const metricLines = (group) => group
    .map(({ key }) => `- ${t(`cvss40.export.${toExportName(key)}`, { value: metricValueLabel(key, metrics) })}`)
    .join("\n");

  function exportCalculationJson() {
    const cvssJson = {
      vectorString: vectorString,
      baseScore: scores?.base_score || 0,
      baseSeverity: scores?.base_severity || t('common.severityNone'),
      baseMetrics: metricGroupJson(BASE_METRICS, metrics),
      threatMetrics: metricGroupJson(threatMetrics, metrics),
      environmentalMetrics: metricGroupJson(ENVIRONMENTAL_METRICS, metrics),
      supplementalMetrics: metricGroupJson(supplementalMetrics, metrics),
    };

    const fileData = JSON.stringify(cvssJson, null, 2);
    const blob = new Blob([fileData], { type: "application/json" });
    downloadBlob(blob, "cvss_4.0_calculation.json");
  }

  function exportCalculationMarkdown() {
    const baseSeverity = scores?.base_severity || t('common.severityNone');
    const cvssMarkdown = `${t('cvss40.export.markdownTitle')}
${t('common.vectorString', { vector: vectorString })}
__________
## ${t('cvss40.export.baseScoreHeading', { score: scores?.base_score || 0, severity: baseSeverity })}

${t('cvss40.export.baseDescription')}

### ${t('cvss40.export.exploitabilityMetricsHeading')}
${metricLines(exploitabilityMetrics)}

### ${t('cvss40.export.vulnerableSystemImpactHeading')}
${metricLines(vulnerableSystemImpactMetrics)}

### ${t('cvss40.export.subsequentSystemImpactHeading')}
${metricLines(subsequentSystemImpactMetrics)}

__________

## ${t('cvss40.export.threatMetricsHeading')}
${t('cvss40.export.threatMetricsDescription')}

${metricLines(threatMetrics)}

__________

## ${t('cvss40.export.environmentalMetricsHeading')}
${t('cvss40.environmental.description')}

### ${t('cvss40.export.exploitabilityMetricsHeading')}
${metricLines(modifiedExploitabilityMetrics)}

### ${t('cvss40.export.vulnerableSystemImpactHeading')}
${metricLines(modifiedVulnerableSystemImpactMetrics)}

### ${t('cvss40.export.subsequentSystemImpactHeading')}
${metricLines(modifiedSubsequentSystemImpactMetrics)}

__________

## ${t('cvss40.export.supplementalMetricsHeading')}
${t('cvss40.supplemental.description')}

${metricLines(supplementalMetrics)}

__________

# ${t('cvss40.export.overallScoreHeading', { score: scores?.base_score || 0, severity: baseSeverity })}
`;

    const blob = new Blob([cvssMarkdown], { type: "text/markdown" });
    downloadBlob(blob, "cvss_4.0_calculation.md");
  }

  return (
    <Box sx={{ display: "flex", justifyContent: "center", mt: 2.5, mb: 2 }}>
      <ButtonGroup variant="contained" ref={anchorRef} aria-label="split button">
        <Button onClick={handleClick} startIcon={<DownloadIcon />}>
          {t('common.exportCalculation')}
        </Button>
        <Button
          size="small"
          onClick={handleToggle}
          aria-label={t('common.exportOptions')}
        >
          <ArrowDropDownIcon />
        </Button>
      </ButtonGroup>
      <Popper
        sx={{ zIndex: 1 }}
        open={open}
        anchorEl={anchorRef.current}
        role={undefined}
        transition
        disablePortal
      >
        {({ TransitionProps, placement }) => (
          <Grow
            {...TransitionProps}
            style={{
              transformOrigin:
                placement === "bottom" ? "center top" : "center bottom",
            }}
          >
            <Paper>
              <ClickAwayListener onClickAway={handleClose}>
                <MenuList id="export-split-button-menu" autoFocusItem>
                  {options.map((option, index) => (
                    <MenuItem
                      key={option}
                      selected={index === selectedIndex}
                      onClick={(event) => handleMenuItemClick(event, index)}
                    >
                      {option}
                    </MenuItem>
                  ))}
                </MenuList>
              </ClickAwayListener>
            </Paper>
          </Grow>
        )}
      </Popper>
    </Box>
  );
}
