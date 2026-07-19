import React from "react";
import { useTranslation } from 'react-i18next';

import BarChartIcon from "@mui/icons-material/BarChartOutlined";
import Card from "@mui/material/Card";
import CategoryIcon from "@mui/icons-material/CategoryOutlined";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import Grid from "@mui/material/Grid";
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import PolylineIcon from "@mui/icons-material/PolylineOutlined";
import SourceIcon from "@mui/icons-material/SourceOutlined";
import Typography from "@mui/material/Typography";

import Circle from "./Circle";

export default function CvssMetrics(props) {
  const { t } = useTranslation('iocTools');
  return (
    <Card
      variant="outlined"
      key="cvssMetrics_card"
      sx={{ m: 1, p: 2, borderRadius: 5, boxShadow: 0 }}
    >
      <Typography variant="h5" gutterBottom component="div">
        {t('providers.nistnvd.cvssMetrics')}
      </Typography>
      <>
        <List>
          <Grid container spacing={2}>
            <Grid size={4}>
              <ListItem>
                <ListItemIcon>
                  <PolylineIcon />
                </ListItemIcon>
                <ListItemText
                  primary={t('providers.nistnvd.vectorString')}
                  secondary={props.metrics.cvssData.vectorString}
                />
              </ListItem>
            </Grid>
            <Grid size={4}>
              <ListItem>
                <ListItemIcon>
                  <SourceIcon />
                </ListItemIcon>
                <ListItemText
                  primary={t('providers.nistnvd.source')}
                  secondary={props.metrics.source}
                />
              </ListItem>
            </Grid>
            <Grid size={4}>
              <ListItem>
                <ListItemIcon>
                  <CategoryIcon />
                </ListItemIcon>
                <ListItemText primary={t('providers.common.type')} secondary={props.metrics.type} />
              </ListItem>
            </Grid>
          </Grid>
        </List>
        <Divider>
          <Chip
            icon={<BarChartIcon />}
            label={t('providers.nistnvd.baseScore')}
            sx={{
              fontSize: "20px",
              p: 1.25,
              height: "40px",
            }}
          />
        </Divider>
        <Grid container spacing={2} mt={2} p={1}>
          <Grid size={4}>
            <Typography variant="h6" gutterBottom component="div">
              {t('providers.nistnvd.exploitabilityScore', { score: props.metrics.exploitabilityScore })}
            </Typography>
            <List>
              <ListItem>
                <ListItemText
                  primary={t('providers.nistnvd.attackVector')}
                  secondary={props.metrics.cvssData.attackVector}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary={t('providers.nistnvd.attackComplexity')}
                  secondary={props.metrics.cvssData.attackComplexity}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary={t('providers.nistnvd.privilegesRequired')}
                  secondary={props.metrics.cvssData.privilegesRequired}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary={t('providers.nistnvd.userInteraction')}
                  secondary={props.metrics.cvssData.userInteraction}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary={t('providers.nistnvd.scope')}
                  secondary={props.metrics.cvssData.scope}
                />
              </ListItem>
            </List>
          </Grid>
          <Grid size={4}>
            <Typography variant="h6" gutterBottom component="div">
              {t('providers.nistnvd.impactScore', { score: props.metrics.impactScore })}
            </Typography>
            <List>
              <ListItem>
                <ListItemText
                  primary={t('providers.nistnvd.confidentialityImpact')}
                  secondary={props.metrics.cvssData.confidentialityImpact}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary={t('providers.nistnvd.integrityImpact')}
                  secondary={props.metrics.cvssData.integrityImpact}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary={t('providers.nistnvd.availabilityImpact')}
                  secondary={props.metrics.cvssData.availabilityImpact}
                />
              </ListItem>
            </List>
          </Grid>
          <Grid size={4}>
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                alignItems: "center",
                height: "100%",
              }}
            >
              <Circle value={props.metrics.cvssData.baseScore} />
              <Typography
                variant="h6"
                fontWeight={
                  props.metrics.cvssData.baseScore >= 9.0 ? "bold" : "normal"
                }
                color={
                  props.metrics.cvssData.baseScore >= 7.0
                    ? "red"
                    : props.metrics.cvssData.baseScore >= 4.0
                    ? "orange"
                    : "green"
                }
                align="center"
                gutterBottom
                sx={{ display: "block", marginBottom: 1 }}
              >
                {props.metrics.cvssData.baseSeverity}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </>
    </Card>
  );
}
