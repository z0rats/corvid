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
import { downloadBlob, round } from "../../../shared/utils/fileUtils";
import { METRIC_MAPS } from "../../constants/exportMaps";
import { useTranslation } from 'react-i18next';

const mapMetric = (category, value) => METRIC_MAPS[category]?.[value] || value || 'Not Defined';

export default function ExportCalculation({ cvssScores, vectorString }) {
  const { t } = useTranslation('cvssCalculator');
  const options = [t('common.exportAsMarkdown'), t('common.exportAsJson')];
  const [open, setOpen] = React.useState(false);
  const anchorRef = React.useRef(null);
  const [selectedIndex] = React.useState(0);

  const metrics = cvssScores.metrics;
  const scores = cvssScores.scores;

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
      overallScore: round(scores.environmental.environmentalScore),
      base: {
        baseScore: scores.base.baseScore,
        exploitabilityScore: round(scores.base.exploitabilityScore),
        impactScore: round(scores.base.impactScore),
        attackVector: mapMetric('attackVector', metrics.base.attackVector),
        attackComplexity: mapMetric('attackComplexity', metrics.base.attackComplexity),
        privilegesRequired: mapMetric('privilegesRequired', metrics.base.privilegesRequired),
        userInteraction: mapMetric('userInteraction', metrics.base.userInteraction),
        scope: mapMetric('scope', metrics.base.scope),
      },
      temporal: {
        temporalScore: round(scores.temporal.temporalScore),
        exploitCodeMaturity: mapMetric('exploitCodeMaturity', metrics.temporal.exploitCodeMaturity),
        remediationLevel: mapMetric('remediationLevel', metrics.temporal.remediationLevel),
        reportConfidence: mapMetric('reportConfidence', metrics.temporal.reportConfidence),
      },
      environmental: {
        environmentalScore: round(scores.environmental.environmentalScore),
        modifiedExploitabilityScore: round(scores.environmental.modifiedExploitabilityScore),
        modifiedImpactScore: round(scores.environmental.modifiedImpactScore),
        modifiedImpactSubScore: round(scores.environmental.modifiedImpactSubScore),
        modifiedAttackVector: mapMetric('modifiedAttackVector', metrics.environmental.modifiedAttackVector),
        modifiedAttackComplexity: mapMetric('modifiedAttackComplexity', metrics.environmental.modifiedAttackComplexity),
        modifiedPrivilegesRequired: mapMetric('modifiedPrivilegesRequired', metrics.environmental.modifiedPrivilegesRequired),
        modifiedUserInteraction: mapMetric('modifiedUserInteraction', metrics.environmental.modifiedUserInteraction),
        modifiedScope: mapMetric('modifiedScope', metrics.environmental.modifiedScope),
        modifiedConfidentialityImpact: mapMetric('modifiedConfidentialityImpact', metrics.environmental.modifiedConfidentialityImpact),
        modifiedIntegrityImpact: mapMetric('modifiedIntegrityImpact', metrics.environmental.modifiedIntegrityImpact),
        modifiedAvailabilityImpact: mapMetric('modifiedAvailabilityImpact', metrics.environmental.modifiedAvailabilityImpact),
        confidentialityRequirement: mapMetric('confidentialityRequirement', metrics.environmental.confidentialityRequirement),
        integrityRequirement: mapMetric('integrityRequirement', metrics.environmental.integrityRequirement),
        availabilityRequirement: mapMetric('availabilityRequirement', metrics.environmental.availabilityRequirement),
      },
    };

    const fileData = JSON.stringify(cvssJson);
    const blob = new Blob([fileData], { type: "text/plain" });
    downloadBlob(blob, "cvss_calculation.json");
  }

  function exportCalculationMarkdown() {
    const cvssMarkdown = `${t('cvss31.export.markdownTitle')}
${t('common.vectorString', { vector: vectorString })}
__________
## ${t('cvss31.export.baseScoreMetricsHeading', { score: scores.base.baseScore })}
${t('cvss31.base.description')}

### ${t('cvss31.export.exploitabilityMetricsHeading', { score: round(scores.base.exploitabilityScore) })}
- ${t('cvss31.export.attackVector', { value: mapMetric('attackVector', metrics.base.attackVector) })}
- ${t('cvss31.export.attackComplexity', { value: mapMetric('attackComplexity', metrics.base.attackComplexity) })}
- ${t('cvss31.export.privilegesRequired', { value: mapMetric('privilegesRequired', metrics.base.privilegesRequired) })}
- ${t('cvss31.export.userInteraction', { value: mapMetric('userInteraction', metrics.base.userInteraction) })}

### ${t('cvss31.export.impactMetricsHeading', { score: round(scores.base.impactScore) })}
- ${t('cvss31.export.confidentialityImpact', { value: mapMetric('confidentialityImpact', metrics.base.confidentialityImpact) })}
- ${t('cvss31.export.integrityImpact', { value: mapMetric('integrityImpact', metrics.base.integrityImpact) })}
- ${t('cvss31.export.availabilityImpact', { value: mapMetric('availabilityImpact', metrics.base.availabilityImpact) })}

#### ${t('cvss31.export.scopeHeading', { value: mapMetric('scope', metrics.base.scope) })}
__________

## ${t('cvss31.export.temporalScoreHeading', { score: round(scores.temporal.temporalScore) })}
${t('cvss31.temporal.description')}

- ${t('cvss31.export.exploitCodeMaturity', { value: mapMetric('exploitCodeMaturity', metrics.temporal.exploitCodeMaturity) })}
- ${t('cvss31.export.remediationLevel', { value: mapMetric('remediationLevel', metrics.temporal.remediationLevel) })}
- ${t('cvss31.export.reportConfidence', { value: mapMetric('reportConfidence', metrics.temporal.reportConfidence) })}
__________

## ${t('cvss31.export.environmentalScoreHeading', { score: round(scores.environmental.environmentalScore) })}
${t('cvss31.environmental.description')}

### ${t('cvss31.export.exploitabilityMetricsHeading', { score: round(scores.environmental.modifiedExploitabilityScore) })}
- ${t('cvss31.export.modifiedAttackVector', { value: mapMetric('modifiedAttackVector', metrics.environmental.modifiedAttackVector) })}
- ${t('cvss31.export.modifiedAttackComplexity', { value: mapMetric('modifiedAttackComplexity', metrics.environmental.modifiedAttackComplexity) })}
- ${t('cvss31.export.modifiedPrivilegesRequired', { value: mapMetric('modifiedPrivilegesRequired', metrics.environmental.modifiedPrivilegesRequired) })}
- ${t('cvss31.export.modifiedUserInteraction', { value: mapMetric('modifiedUserInteraction', metrics.environmental.modifiedUserInteraction) })}
- ${t('cvss31.export.modifiedScope', { value: mapMetric('modifiedScope', metrics.environmental.modifiedScope) })}

### ${t('cvss31.export.impactMetricsHeading', { score: round(scores.environmental.modifiedImpactScore) })}
- ${t('cvss31.export.modifiedConfidentialityImpact', { value: mapMetric('modifiedConfidentialityImpact', metrics.environmental.modifiedConfidentialityImpact) })}
- ${t('cvss31.export.modifiedIntegrityImpact', { value: mapMetric('modifiedIntegrityImpact', metrics.environmental.modifiedIntegrityImpact) })}
- ${t('cvss31.export.modifiedAvailabilityImpact', { value: mapMetric('modifiedAvailabilityImpact', metrics.environmental.modifiedAvailabilityImpact) })}

### ${t('cvss31.export.impactSubscoreModifiersHeading', { score: round(scores.environmental.modifiedImpactSubScore) })}
- ${t('cvss31.export.confidentialityRequirement', { value: mapMetric('confidentialityRequirement', metrics.environmental.confidentialityRequirement) })}
- ${t('cvss31.export.integrityRequirement', { value: mapMetric('integrityRequirement', metrics.environmental.integrityRequirement) })}
- ${t('cvss31.export.availabilityRequirement', { value: mapMetric('availabilityRequirement', metrics.environmental.availabilityRequirement) })}
__________

# ${t('cvss31.export.overallScoreHeading', { score: round(scores.environmental.environmentalScore) })}
`;

    const blob = new Blob([cvssMarkdown], { type: "text/markdown" });
    downloadBlob(blob, "cvss_calculation.md");
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
