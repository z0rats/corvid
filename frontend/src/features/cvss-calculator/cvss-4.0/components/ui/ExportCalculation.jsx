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
import { downloadBlob } from "../../../shared/utils/fileUtils";
import { METRIC_MAPS } from "../../constants/exportMaps";

const mapMetric = (category, value) => METRIC_MAPS[category]?.[value] || "Unknown";

export default function ExportCalculation({ metrics, scores, vectorString }) {
  const options = ["Export as markdown", "Export as JSON"];
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
      baseSeverity: scores?.base_severity || "None",
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
    const cvssMarkdown = `# CVSS 4.0 Score
Vector String: ${vectorString}
__________
## Base Score: ${scores?.base_score || 0} (${scores?.base_severity || "None"})

The Base metric group represents the intrinsic characteristics of a vulnerability that are constant over time and across user environments. It is composed of the Exploitability metrics and the Impact metrics.

### Exploitability Metrics
- **Attack Vector (AV)**: ${mapMetric("attack_vector", metrics.attack_vector)}
- **Attack Complexity (AC)**: ${mapMetric("attack_complexity", metrics.attack_complexity)}
- **Attack Requirements (AT)**: ${mapMetric("attack_requirements", metrics.attack_requirements)}
- **Privileges Required (PR)**: ${mapMetric("privileges_required", metrics.privileges_required)}
- **User Interaction (UI)**: ${mapMetric("user_interaction", metrics.user_interaction)}

### Vulnerable System Impact
- **Confidentiality (VC)**: ${mapMetric("vulnerable_system_confidentiality", metrics.vulnerable_system_confidentiality)}
- **Integrity (VI)**: ${mapMetric("vulnerable_system_integrity", metrics.vulnerable_system_integrity)}
- **Availability (VA)**: ${mapMetric("vulnerable_system_availability", metrics.vulnerable_system_availability)}

### Subsequent System Impact
- **Confidentiality (SC)**: ${mapMetric("subsequent_system_confidentiality", metrics.subsequent_system_confidentiality)}
- **Integrity (SI)**: ${mapMetric("subsequent_system_integrity", metrics.subsequent_system_integrity)}
- **Availability (SA)**: ${mapMetric("subsequent_system_availability", metrics.subsequent_system_availability)}

__________

## Threat Metrics
The Threat metrics measure the current state of exploit techniques or code availability.

- **Exploit Maturity (E)**: ${mapMetric("exploit_maturity", metrics.exploit_maturity)}

__________

# Overall Score: ${scores?.base_score || 0} (${scores?.base_severity || "None"})
`;

    const blob = new Blob([cvssMarkdown], { type: "text/markdown" });
    downloadBlob(blob, "cvss_4.0_calculation.md");
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
