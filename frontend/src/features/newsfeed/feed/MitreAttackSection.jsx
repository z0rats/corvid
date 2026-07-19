import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Collapse from "@mui/material/Collapse";
import Link from "@mui/material/Link";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import ExpandMoreIcon from "@mui/icons-material/ExpandMoreOutlined";
import ShieldIcon from "@mui/icons-material/ShieldOutlined";
import { createLogger } from "../../../core/utils/logger";

const logger = createLogger("MitreAttackSection");

function parseMitreData(raw) {
  try {
    if (typeof raw === "string") return JSON.parse(raw);
    if (typeof raw === "object") return raw;
    return null;
  } catch (error) {
    logger.error("Error parsing threat intel:", error);
    return null;
  }
}

function MitreLink({ id, url, children }) {
  const content = children || id;
  if (!url) return <>{content}</>;
  return (
    <Link href={url} target="_blank" rel="noopener noreferrer" underline="hover" color="primary.main" sx={{ fontWeight: "inherit" }}>
      {content}
    </Link>
  );
}

function SectionLabel({ children }) {
  return (
    <Box
      sx={{
        writingMode: "vertical-lr",
        transform: "rotate(180deg)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: 40,
        pr: 0.25,
      }}
    >
      <Typography
        variant="caption"
        color="text.disabled"
        sx={{
          fontWeight: 600,
          letterSpacing: 1.2,
          textTransform: "uppercase",
          fontSize: "0.65rem",
          whiteSpace: "nowrap",
          userSelect: "none",
        }}
      >
        {children}
      </Typography>
    </Box>
  );
}

function Section({ label, children }) {
  return (
    <Box sx={{ display: "flex", gap: 2 }}>
      <Box sx={{ borderRight: 2, borderColor: "divider", flexShrink: 0, display: "flex" }}>
        <SectionLabel>{label}</SectionLabel>
      </Box>
      <Box sx={{ flex: 1, minWidth: 0, py: 1 }}>
        {children}
      </Box>
    </Box>
  );
}

function ChipList({ items }) {
  return (
    <Stack direction="row" flexWrap="wrap" gap={0.75}>
      {items.map((item) => (
        <Chip
          key={item.key}
          label={item.suffix ? `${item.name} (${item.suffix})` : item.name}
          size="small"
          variant="outlined"
          color={item.color || "default"}
          component={item.url ? Link : "div"}
          href={item.url || undefined}
          target={item.url ? "_blank" : undefined}
          rel={item.url ? "noopener noreferrer" : undefined}
          clickable={!!item.url}
        />
      ))}
    </Stack>
  );
}

function TTPItem({ ttp, isLast }) {
  const { t } = useTranslation('newsfeed');
  const [open, setOpen] = useState(false);
  const hasDetails = ttp.procedure_example || ttp.detection_opportunities?.length > 0;

  const techniquePath = [
    { name: ttp.technique.name, id: ttp.technique.id, url: ttp.technique.url },
    ttp.sub_technique ? { name: ttp.sub_technique.name, id: ttp.sub_technique.id, url: ttp.sub_technique.url } : null,
  ].filter(Boolean);

  return (
    <Box
      sx={{
        py: 1.5,
        borderBottom: isLast ? "none" : 1,
        borderColor: "divider",
        cursor: hasDetails ? "pointer" : "default",
        transition: "background-color 150ms",
        "&:hover": hasDetails ? { bgcolor: "action.hover" } : {},
        px: 1.5,
        mx: -1.5,
        borderRadius: 1,
      }}
      onClick={hasDetails ? () => setOpen(!open) : undefined}
    >
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={1}>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography variant="body2" sx={{ fontWeight: 600, lineHeight: 1.5 }}>
            {techniquePath.map((t, i) => (
              <React.Fragment key={t.id}>
                {i > 0 && (
                  <Typography component="span" sx={{ fontWeight: 400, color: "text.disabled", mx: 0.5 }}>/</Typography>
                )}
                <MitreLink id={t.id} url={t.url}>{t.name}</MitreLink>
              </React.Fragment>
            ))}
          </Typography>
          <Typography variant="caption" color="text.disabled" sx={{ lineHeight: 1.4 }}>
            {ttp.tactic.name}
            {" "}
            <Typography component="span" variant="caption" sx={{ fontFamily: "monospace", fontSize: "0.7rem" }}>
              {techniquePath.map((t) => t.id).join(" / ")}
            </Typography>
            {ttp.affected_platforms?.length > 0 && (
              <> &middot; {ttp.affected_platforms.join(", ")}</>
            )}
          </Typography>
        </Box>
        {hasDetails && (
          <ExpandMoreIcon
            fontSize="small"
            sx={{
              color: "text.disabled",
              transform: open ? "rotate(180deg)" : "rotate(0deg)",
              transition: "transform 200ms ease",
              mt: 0.5,
              flexShrink: 0,
            }}
          />
        )}
      </Stack>

      {ttp.behavior && (
        <Box sx={{ mt: 1.5 }}>
          <Typography
            variant="caption"
            color="text.disabled"
            sx={{ fontWeight: 600, letterSpacing: 0.8, textTransform: "uppercase", display: "block", mb: 0.5 }}
          >
            {t('feed.mitre.observedBehavior')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6, fontSize: "0.85rem" }}>
            {ttp.behavior}
          </Typography>
        </Box>
      )}

      <Collapse in={open} timeout={250}>
        <Stack spacing={2} sx={{ mt: 2, mb: 0.5 }}>
          {ttp.procedure_example && (
            <Box>
              <Typography
                variant="caption"
                color="text.disabled"
                sx={{ fontWeight: 600, letterSpacing: 0.8, textTransform: "uppercase", display: "block", mb: 0.5 }}
              >
                {t('feed.mitre.procedureExample')}
              </Typography>
              <Box
                sx={{
                  fontFamily: "monospace",
                  fontSize: "0.75rem",
                  color: "text.secondary",
                  bgcolor: "action.hover",
                  px: 2,
                  py: 1.5,
                  borderRadius: 1.5,
                  overflowX: "auto",
                  lineHeight: 1.7,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                }}
              >
                {ttp.procedure_example}
              </Box>
            </Box>
          )}
          {ttp.detection_opportunities?.length > 0 && (
            <Box>
              <Typography
                variant="caption"
                color="text.disabled"
                sx={{ fontWeight: 600, letterSpacing: 0.8, textTransform: "uppercase", display: "block", mb: 0.75 }}
              >
                {t('feed.mitre.detectionOpportunities')}
              </Typography>
              <Stack spacing={0.75}>
                {ttp.detection_opportunities.map((d, i) => (
                  <Box key={i} sx={{ display: "flex", gap: 1.5, alignItems: "flex-start" }}>
                    <Box sx={{ width: 4, height: 4, borderRadius: "50%", bgcolor: "text.disabled", mt: 1, flexShrink: 0 }} />
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: "0.82rem", lineHeight: 1.6 }}>
                      {d}
                    </Typography>
                  </Box>
                ))}
              </Stack>
            </Box>
          )}
        </Stack>
      </Collapse>
    </Box>
  );
}

export default function MitreAttackSection({ item }) {
  const { t } = useTranslation('newsfeed');
  const data = parseMitreData(item.mitre_attack);

  if (!data || !data.has_mitre_data) return null;

  const hasActors = data.threat_actors?.length > 0;
  const hasSoftware = data.software?.length > 0;
  const hasTargets = data.targeted_sectors?.length > 0 || data.targeted_regions?.length > 0;
  const hasTTPs = data.ttps?.length > 0;

  if (!hasActors && !hasSoftware && !hasTargets && !hasTTPs) return null;

  const actorItems = (data.threat_actors || []).map((a) => ({
    key: a.name, name: a.name, url: a.mitre_url, bold: true,
  }));

  const softwareItems = (data.software || []).map((sw) => ({
    key: sw.name, name: sw.name, url: sw.mitre_url,
    suffix: sw.type === "malware" ? "malware" : null,
    color: sw.type === "malware" ? "error" : "default",
  }));

  const targetItems = [
    ...(data.targeted_sectors || []),
    ...(data.targeted_regions || []),
  ].map((t) => ({ key: t, name: t }));

  return (
    <Accordion variant="secondary" elevation={0} sx={{ borderRadius: 1, boxShadow: "none !important" }}>
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{
          "& .MuiAccordionSummary-content": { margin: 0 },
          flexDirection: "row-reverse",
        }}
      >
        <Stack direction="row" alignItems="center" spacing={1}>
          <ShieldIcon />
          <Typography variant="body2" sx={{ fontWeight: "bold" }}>
            {t('feed.mitre.title')}
          </Typography>
        </Stack>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 3, py: 2.5 }}>
        <Stack spacing={2.5} divider={<Box sx={{ display: "flex", justifyContent: "center" }}><Box sx={{ height: "1px", width: "85%", background: (theme) => `linear-gradient(to right, transparent, ${theme.palette.divider} 15%, ${theme.palette.divider} 85%, transparent)` }} /></Box>}>
          {hasActors && (
            <Section label={t('feed.mitre.actors')}>
              <ChipList items={actorItems} />
            </Section>
          )}
          {hasSoftware && (
            <Section label={t('feed.mitre.software')}>
              <ChipList items={softwareItems} />
            </Section>
          )}
          {hasTargets && (
            <Section label={t('feed.mitre.targets')}>
              <ChipList items={targetItems} />
            </Section>
          )}
          {hasTTPs && (
            <Section label={t('feed.mitre.techniques')}>
              <Stack spacing={0.5}>
                {[...data.ttps]
                  .sort((a, b) => a.tactic.id.localeCompare(b.tactic.id) || a.technique.id.localeCompare(b.technique.id))
                  .map((ttp, idx, sorted) => (
                    <TTPItem key={`${ttp.technique.id}-${idx}`} ttp={ttp} isLast={idx === sorted.length - 1} />
                  ))}
              </Stack>
            </Section>
          )}
        </Stack>
      </AccordionDetails>
    </Accordion>
  );
}
