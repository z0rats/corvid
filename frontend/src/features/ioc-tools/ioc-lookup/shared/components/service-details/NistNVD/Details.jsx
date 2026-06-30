import React from "react";
import { useTranslation } from 'react-i18next';

import CalendarMonthIcon from "@mui/icons-material/CalendarMonth";
import Card from "@mui/material/Card";
import DescriptionIcon from "@mui/icons-material/Description";
import EventIcon from "@mui/icons-material/Event";
import Grid from "@mui/material/Grid";
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import ModelTrainingIcon from "@mui/icons-material/ModelTraining";
import ReactMarkdown from "react-markdown";
import SourceIcon from "@mui/icons-material/Source";
import Typography from "@mui/material/Typography";

export default function Details(props) {
  const { t } = useTranslation('iocTools');
  return (
    <Card
      variant="outlined"
      key="details_card"
      sx={{ m: 1, p: 2, borderRadius: 5, boxShadow: 0 }}
    >
      <Typography variant="h5" gutterBottom component="div">
        {t('providers.nistnvd.details')}
      </Typography>
      {props.details ? (
        <>
          <List>
            <Grid container spacing={2}>
              <Grid size={6}>
                <ListItem>
                  <ListItemIcon>
                    <SourceIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('providers.nistnvd.sourceIdentifier')}
                    secondary={props.details.sourceIdentifier}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CalendarMonthIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('providers.crowdstrike.published')}
                    secondary={props.details.published}
                  />
                </ListItem>
              </Grid>
              <Grid size={6}>
                <ListItem>
                  <ListItemIcon>
                    <EventIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('providers.nistnvd.lastModified')}
                    secondary={props.details.lastModified}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <ModelTrainingIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('providers.nistnvd.vulnerabilityStatus')}
                    secondary={props.details.vulnStatus}
                  />
                </ListItem>
              </Grid>
            </Grid>
            <ListItem>
              <ListItemIcon>
                <DescriptionIcon />
              </ListItemIcon>
              <ListItemText
                primary={t('providers.nistnvd.description')}
                secondary={
                    <ReactMarkdown>{props.details.descriptions[0].value}</ReactMarkdown>
                }
              />
            </ListItem>
          </List>
        </>
      ) : null}
    </Card>
  );
}
