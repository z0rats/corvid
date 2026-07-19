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
import { useTranslation } from 'react-i18next';

const mapMetric = (category, value) => METRIC_MAPS[category]?.[value] || "Unknown";

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

  function exportCalculationJson() {
    const cvssJson = {
      vectorString: vectorString,
      baseScore: scores?.base_score || 0,
      baseSeverity: scores?.base_severity || t('common.severityNone'),
      baseMetrics: {
        attackVector: mapMetric("attack_vector", metrics.attack_vector),
        attackComplexity: mapMetric("attack_complexity", metrics.attack_complexity),
        attackRequirements: mapMetric("attack_requirements", metrics.attack_requirements),
        privilegesRequired: mapMetric("privileges_required", metrics.privileges_required),
        userInteraction: mapMetric("user_interaction", metrics.user_interaction),
        vulnerableSystemConfidentiality: mapMetric("vulnerable_system_confidentiality", metrics.vulnerable_system_confidentiality),
        vulnerableSystemIntegrity: mapMetric("vulnerable_system_integrity", metrics.vulnerable_system_integrity),
        vulnerableSystemAvailability: mapMetric("vulnerable_system_availability", metrics.vulnerable_system_availability),
        subsequentSystemConfidentiality: mapMetric("subsequent_system_confidentiality", metrics.subsequent_system_confidentiality),
        subsequentSystemIntegrity: mapMetric("subsequent_system_integrity", metrics.subsequent_system_integrity),
        subsequentSystemAvailability: mapMetric("subsequent_system_availability", metrics.subsequent_system_availability),
      },
      threatMetrics: {
        exploitMaturity: mapMetric("exploit_maturity", metrics.exploit_maturity),
      },
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
- ${t('cvss40.export.attackVector', { value: mapMetric("attack_vector", metrics.attack_vector) })}
- ${t('cvss40.export.attackComplexity', { value: mapMetric("attack_complexity", metrics.attack_complexity) })}
- ${t('cvss40.export.attackRequirements', { value: mapMetric("attack_requirements", metrics.attack_requirements) })}
- ${t('cvss40.export.privilegesRequired', { value: mapMetric("privileges_required", metrics.privileges_required) })}
- ${t('cvss40.export.userInteraction', { value: mapMetric("user_interaction", metrics.user_interaction) })}

### ${t('cvss40.export.vulnerableSystemImpactHeading')}
- ${t('cvss40.export.vulnerableSystemConfidentiality', { value: mapMetric("vulnerable_system_confidentiality", metrics.vulnerable_system_confidentiality) })}
- ${t('cvss40.export.vulnerableSystemIntegrity', { value: mapMetric("vulnerable_system_integrity", metrics.vulnerable_system_integrity) })}
- ${t('cvss40.export.vulnerableSystemAvailability', { value: mapMetric("vulnerable_system_availability", metrics.vulnerable_system_availability) })}

### ${t('cvss40.export.subsequentSystemImpactHeading')}
- ${t('cvss40.export.subsequentSystemConfidentiality', { value: mapMetric("subsequent_system_confidentiality", metrics.subsequent_system_confidentiality) })}
- ${t('cvss40.export.subsequentSystemIntegrity', { value: mapMetric("subsequent_system_integrity", metrics.subsequent_system_integrity) })}
- ${t('cvss40.export.subsequentSystemAvailability', { value: mapMetric("subsequent_system_availability", metrics.subsequent_system_availability) })}

__________

## ${t('cvss40.export.threatMetricsHeading')}
${t('cvss40.export.threatMetricsDescription')}

- ${t('cvss40.export.exploitMaturity', { value: mapMetric("exploit_maturity", metrics.exploit_maturity) })}

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
