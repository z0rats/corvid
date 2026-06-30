import React from "react";
import { useTranslation } from 'react-i18next';

import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import Grid from "@mui/material/Grid";
import Typography from '@mui/material/Typography';

import LocalOfferIcon from "@mui/icons-material/LocalOffer";

export default function TypeTags(props) {
  const { t } = useTranslation('iocTools');
  return (
    <Card
      key="tags_card"
      sx={{ m: 1, p: 2, borderRadius: 1, boxShadow: 0 }}
    >
      <Grid container alignItems="center">
        <Grid mr={1}>
          <LocalOfferIcon />
        </Grid>
        <Grid>
          <Typography variant="h5" component="h2" gutterBottom>
            {t('providers.virustotal.typeTags')}
          </Typography>
        </Grid>
      </Grid>
      {props.result["data"]["attributes"]["type_tags"].length > 0 ? (
        <>
          {props.result["data"]["attributes"]["type_tags"].map((tag, index) => (
            <React.Fragment key={index}>
              <Chip label={tag} sx={{ m: 0.5 }} />
              {index !==
                props.result["data"]["attributes"]["type_tags"].length - 1}
            </React.Fragment>
          ))}
        </>
      ) : (
        <Typography>{t('providers.virustotal.none')}</Typography>
      )}
    </Card>
  );
}
