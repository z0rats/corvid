import React from "react";

import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Divider from "@mui/material/Divider";
import Grid from "@mui/material/Grid";
import StarHalfIcon from "@mui/icons-material/StarHalf";
import StarIcon from "@mui/icons-material/Star";
import Typography from '@mui/material/Typography';

export default function PopularityRanks(props) {
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
            Popularity ranks
          </Typography>
        </Grid>
      </Grid>
      <Typography variant="subtitle1" color="text.secondary">
        Domain's position in popularity ranks such as Alexa, Quantcast, Statvoo,
        etc.
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
