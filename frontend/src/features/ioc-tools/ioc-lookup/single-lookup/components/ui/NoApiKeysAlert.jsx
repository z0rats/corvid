import React from 'react'

import Box from '@mui/material/Box';
import Card from '@mui/material/Card'
import Divider from '@mui/material/Divider';
import Grow from '@mui/material/Grow';
import KeyIcon from '@mui/icons-material/Key';
import MuiGrid from '@mui/material/Grid2';
import Typography from '@mui/material/Typography';
import { styled } from '@mui/material/styles';

const StyledGrid = styled(MuiGrid)(({ theme }) => ({
  width: '100%',
  ...theme.typography.body2,
  '& [role="separator"]': {
    margin: theme.spacing(0, 2),
  },
}));

export default function NoApikeys() {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
        <Grow in={true}>
            <Card variant="outlined" elevation={0} sx={{ maxWidth: 800, m: 2, p: 2, borderRadius: 5 }}>
                <StyledGrid container>
                    <StyledGrid size="grow" display="flex" justifyContent="center" alignItems="center">
                        <KeyIcon sx={{ fontSize: 100, color: 'text.disabled'}} />
                    </StyledGrid>
                    <Divider orientation="vertical" flexItem></Divider>
                    <StyledGrid size="grow" sx={{p: 2}}>
                        <Typography variant="h5">No API keys available for this action</Typography>
                        <Typography>You need to add API keys in the settings tab, to use this function.</Typography>
                    </StyledGrid>
                </StyledGrid>
            </Card>
        </Grow>
    </Box>
  )
}
