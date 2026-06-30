import React from "react";
import { useTranslation } from 'react-i18next';

import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Stack from "@mui/material/Stack";
import Typography from '@mui/material/Typography';

export default function CrowdsourcedContext(props) {
  const { t } = useTranslation('iocTools');
  return (
    <Card
      key="crowdsourced_context_card"
      sx={{ m: 1, p: 2, borderRadius: 1, boxShadow: 0 }}
    >
      <Typography variant="h5" component="h2" gutterBottom>
        {t('providers.virustotal.crowdsourcedContext')}
      </Typography>
      {props.result["data"]["attributes"]["crowdsourced_context"].length > 0 ? (
        props.result["data"]["attributes"]["crowdsourced_context"].map(
          (cc, index) => {
            return (
              <Box key={index + "_box"} sx={{ mb: 2 }}>
                <Stack spacing={0.5}>
                  <Typography variant="body2">
                    <Typography component="span" fontWeight="bold">{t('providers.virustotal.title')} </Typography>
                    {cc.title}
                  </Typography>
                  <Typography variant="body2">
                    <Typography component="span" fontWeight="bold">{t('providers.nistnvd.source')} </Typography>
                    {cc.source}
                  </Typography>
                  <Typography variant="body2">
                    <Typography component="span" fontWeight="bold">{t('providers.virustotal.timestamp')} </Typography>
                    {cc.timestamp}
                  </Typography>
                  <Typography variant="body2">
                    <Typography component="span" fontWeight="bold">{t('providers.virustotal.detail')} </Typography>
                    {cc.detail}
                  </Typography>
                  <Typography variant="body2">
                    <Typography component="span" fontWeight="bold">{t('providers.virustotal.severity')} </Typography>
                    {cc.severity}
                  </Typography>
                </Stack>
              </Box>
            );
          }
        )
      ) : (
        <Typography>{t('providers.virustotal.none')}</Typography>
      )}
    </Card>
  );
}
