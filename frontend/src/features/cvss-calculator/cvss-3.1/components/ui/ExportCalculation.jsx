import React from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import ButtonGroup from "@mui/material/ButtonGroup";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import DownloadIcon from "@mui/icons-material/Download";
import ClickAwayListener from "@mui/material/ClickAwayListener";
import Grow from "@mui/material/Grow";
import MenuItem from "@mui/material/MenuItem";
import MenuList from "@mui/material/MenuList";
import Paper from "@mui/material/Paper";
import Popper from "@mui/material/Popper";
import { downloadBlob, round } from "../../../shared/utils/fileUtils";
import { METRIC_MAPS } from "../../constants/exportMaps";

const mapMetric = (category, value) => METRIC_MAPS[category]?.[value] || value || 'Not Defined';

export default function ExportCalculation({ cvssScores, vectorString }) {
  const options = ["Export as markdown", "Export as JSON"];
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
    const cvssMarkdown = `# CVSS 3.1 score
Vector String: ${vectorString}
__________
## Base Score Metrics (Score: ${scores.base.baseScore})
The Base metric group represents the intrinsic characteristics of a vulnerability that are constant over time and across user environments. It is composed of two sets of metrics: the Exploitability metrics and the Impact metrics. The Exploitability metrics reflect the ease and technical means by which the vulnerability can be exploited. That is, they represent characteristics of the thing that is vulnerable, which we refer to formally as the vulnerable component. On the other hand, the Impact metrics reflect the direct consequence of a successful exploit, and represent the consequence to the thing that suffers the impact, which we refer to formally as the impacted component.

###  Exploitability Metrics (Score: ${round(scores.base.exploitabilityScore)})
- Attack Vector (AV): ${mapMetric('attackVector', metrics.base.attackVector)}
- Attack Complexity (AC): ${mapMetric('attackComplexity', metrics.base.attackComplexity)}
- Privileges Required (PR): ${mapMetric('privilegesRequired', metrics.base.privilegesRequired)}
- User Interaction (UI): ${mapMetric('userInteraction', metrics.base.userInteraction)}

### Impact Metrics (Score: ${round(scores.base.impactScore)})
- Confidentiality Impact (CI): ${mapMetric('confidentialityImpact', metrics.base.confidentialityImpact)}
- Integrity Impact (I): ${mapMetric('integrityImpact', metrics.base.integrityImpact)}
- Availability Impact (AI): ${mapMetric('availabilityImpact', metrics.base.availabilityImpact)}

#### Scope (S): ${mapMetric('scope', metrics.base.scope)}
__________

## Temporal Score Metrics (Score: ${round(scores.temporal.temporalScore)})
The Temporal metrics measure the current state of exploit techniques or code availability, the existence of any patches or workarounds, or the confidence that one has in the description of a vulnerability. Temporal metrics will almost certainly change over time.

- Exploit Code Maturity (E): ${mapMetric('exploitCodeMaturity', metrics.temporal.exploitCodeMaturity)}
- Remediation Level (RL): ${mapMetric('remediationLevel', metrics.temporal.remediationLevel)}
- Report Confidence (RC): ${mapMetric('reportConfidence', metrics.temporal.reportConfidence)}
__________

## Environmental Score Metrics (Score: ${round(scores.environmental.environmentalScore)})
These metrics enable the analyst to customize the CVSS score depending on the importance of the affected IT asset to a user's organization, measured in terms of complementary/alternative security controls in place, Confidentiality, Integrity, and Availability. The metrics are the modified equivalent of base metrics and are assigned metrics value based on the component placement in organization infrastructure.

### Exploitability Metrics (Score: ${round(scores.environmental.modifiedExploitabilityScore)})
- Attack Vector (MAV): ${mapMetric('modifiedAttackVector', metrics.environmental.modifiedAttackVector)}
- Attack Complexity (MAC): ${mapMetric('modifiedAttackComplexity', metrics.environmental.modifiedAttackComplexity)}
- Privileges Required (MPR): ${mapMetric('modifiedPrivilegesRequired', metrics.environmental.modifiedPrivilegesRequired)}
- User Interaction (MUI): ${mapMetric('modifiedUserInteraction', metrics.environmental.modifiedUserInteraction)}
- Scope (MS): ${mapMetric('modifiedScope', metrics.environmental.modifiedScope)}

### Impact Metrics (Score: ${round(scores.environmental.modifiedImpactScore)})
- Confidentiality Impact (MC): ${mapMetric('modifiedConfidentialityImpact', metrics.environmental.modifiedConfidentialityImpact)}
- Integrity Impact (MI): ${mapMetric('modifiedIntegrityImpact', metrics.environmental.modifiedIntegrityImpact)}
- Availability Impact (MAI): ${mapMetric('modifiedAvailabilityImpact', metrics.environmental.modifiedAvailabilityImpact)}

### Impact Subscore Modifiers (Score: ${round(scores.environmental.modifiedImpactSubScore)})
- Confidentiality Requirement (CR): ${mapMetric('confidentialityRequirement', metrics.environmental.confidentialityRequirement)}
- Integrity Requirement (IR): ${mapMetric('integrityRequirement', metrics.environmental.integrityRequirement)}
- Availability Requirement (AR): ${mapMetric('availabilityRequirement', metrics.environmental.availabilityRequirement)}
__________

# Overall Score: ${round(scores.environmental.environmentalScore)}
`;

    const blob = new Blob([cvssMarkdown], { type: "text/markdown" });
    downloadBlob(blob, "cvss_calculation.md");
  }

  return (
    <Box sx={{ display: "flex", justifyContent: "center", mt: 2.5, mb: 2 }}>
      <ButtonGroup variant="contained" ref={anchorRef} aria-label="split button">
        <Button onClick={handleClick} startIcon={<DownloadIcon />}>
          Export calculation
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
