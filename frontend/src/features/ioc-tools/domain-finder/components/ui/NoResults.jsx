import React from "react";

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Divider from "@mui/material/Divider";
import Grow from "@mui/material/Grow";
import SearchOffIcon from "@mui/icons-material/SearchOff";
import MuiGrid from "@mui/material/Grid2";
import { styled } from "@mui/material/styles";
import Typography from "@mui/material/Typography";

const StyledGrid = styled(MuiGrid)(({ theme }) => ({
  width: "100%",
  ...theme.typography.body2,
  '& [role="separator"]': {
    margin: theme.spacing(0, 2),
  },
}));

export default function NoApikeys(props) {
  return (
    <Box sx={{ display: "flex", justifyContent: "center" }}>
      <Grow in={true}>
        <Card
          variant="outlined"
          elevation={0}
          sx={{ maxWidth: "80%", m: 2, p: 2, borderRadius: 1 }}
        >
          <StyledGrid container>
            <StyledGrid
              size="grow"
              display="flex"
              justifyContent="center"
              alignItems="center"
            >
              <SearchOffIcon sx={{ fontSize: 100, color: "text.disabled" }} />
            </StyledGrid>
            <Divider orientation="vertical" flexItem></Divider>
            <StyledGrid size="grow" sx={{ p: 2 }}>
              <Typography variant="h5">No results</Typography>
              <Typography variant="body1">
                There are no results for your search: "{props.searchterm}"
              </Typography>
            </StyledGrid>
          </StyledGrid>
        </Card>
      </Grow>
    </Box>
  );
}
