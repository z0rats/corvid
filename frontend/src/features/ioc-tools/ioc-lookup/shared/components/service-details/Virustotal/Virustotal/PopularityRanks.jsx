import React from "react";
import { useTranslation } from 'react-i18next';

import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Divider from "@mui/material/Divider";
import Grid from "@mui/material/Grid";
import StarHalfIcon from "@mui/icons-material/StarHalfOutlined";
import StarIcon from "@mui/icons-material/StarOutlined";
import Typography from '@mui/material/Typography';

export default function PopularityRanks(props) {
  const { t } = useTranslation('iocTools');
  return (
    <Card
      key="popularity_card"
      sx={{ m: 1, p: 2, borderRadius: 1, boxShadow: 0 }}
    >
      <Grid container alignItems="center">
        <Grid mr={1}>
          <StarHalfIcon />
        </Grid>
        <Grid>
          <Typography variant="h5" component="h2" gutterBottom>
            {t('providers.virustotal.popularityRanks')}
          </Typography>
        </Grid>
      </Grid>
      <Typography variant="subtitle1" color="text.secondary">
        {t('providers.virustotal.popularityRanksHelper')}
      </Typography>
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.625 }}>
        {Object.entries(
          props.result["data"]["attributes"]["popularity_ranks"]
        ).map(([name, data]) => (
          <Box
            key={name + "_div"}
            sx={{ flexBasis: "15%", mb: 0.625 }}
          >
            <Card
              variant="outlined"
              key={name + "_popularity_card"}
              sx={{ m: 1, p: 1.5, borderRadius: 5, boxShadow: 0 }}
            >
              <Typography variant="h6" component="h2" gutterBottom>
                {name}
              </Typography>
              <Divider sx={{ my: 1 }} />
              <Grid container spacing={1} alignItems="center">
                <Grid>
                  <StarIcon color="action" />
                </Grid>
                <Grid>
                  <Typography variant="subtitle1" component="span">
                    {data.rank}
                  </Typography>
                </Grid>
              </Grid>
            </Card>
          </Box>
        ))}
      </Box>
    </Card>
  );
}
