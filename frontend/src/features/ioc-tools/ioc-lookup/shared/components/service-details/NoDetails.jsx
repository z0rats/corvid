import React from 'react'
import Card from '@mui/material/Card'
import { styled } from '@mui/material/styles';
import NotInterestedIcon from '@mui/icons-material/NotInterested';
import Divider from '@mui/material/Divider';
import MuiGrid from '@mui/material/Grid2';
import Typography from '@mui/material/Typography';

const StyledGrid = styled(MuiGrid)(({ theme }) => ({
    width: '100%',
    ...theme.typography.body2,
    '& [role="separator"]': {
      margin: theme.spacing(0, 2),
    },
  }));

export default function NoDetails() {
  return (
    <>
        <Card elevation={0} sx={{ maxWidth: 600, m: 2, p: 2, borderRadius: 2 }}>
            <StyledGrid container>
                <StyledGrid size="grow" display="flex" justifyContent="center" alignItems="center">
                    <NotInterestedIcon sx={{ fontSize: 80, color: 'text.disabled'}} />
                </StyledGrid>
                <Divider orientation="vertical" flexItem></Divider>
                <StyledGrid size="grow" sx={{p: 2}}>
                    <Typography variant="h5">No details available</Typography>
                    <Typography>There are no further details availables for this item.</Typography>
                </StyledGrid>
            </StyledGrid>
        </Card>
    </>
  )
}
