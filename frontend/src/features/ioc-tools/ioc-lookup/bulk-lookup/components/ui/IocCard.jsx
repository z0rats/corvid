import React, { useState, useMemo, memo } from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { styled } from '@mui/material/styles';
import { useTheme } from '@mui/material/styles';
import ServiceRow from './ServiceRow';
import { TLP_COLORS } from '../../../shared/utils/tlpUtils';
import { SERVICE_DEFINITIONS } from '../../../shared/config/serviceConfig';

const StyledHeaderCell = styled(TableCell)(({ theme }) => ({
  backgroundColor: theme.palette.background.tablecell,
  fontWeight: 'bold',
}));

const StyledExpandMoreIcon = styled(ExpandMoreIcon, {
  shouldForwardProp: (prop) => prop !== 'isExpanded',
})(({ theme, isExpanded }) => ({
  transform: !isExpanded ? 'rotate(0deg)' : 'rotate(180deg)',
  marginLeft: 'auto',
  transition: theme.transitions.create('transform', {
    duration: theme.transitions.duration.shortest,
  }),
}));

function IocCard({ ioc, onToggleExpand }) {
  const theme = useTheme();
  const [expanded, setExpanded] = useState(ioc.isCardExpanded || false);

  const handleExpandClick = () => {
    setExpanded(!expanded);
  };
  
  const tlpColor = TLP_COLORS[ioc.overallTlp] || TLP_COLORS.WHITE;

  const cellStyle = useMemo(() => ({
    padding: "12px 16px",
    verticalAlign: "middle",
  }), []);

  const avatarStyle = useMemo(() => ({
    width: 30,
    height: 30,
    border: "1px solid",
    borderColor: theme.palette.background.tableborder,
  }), [theme.palette.background.tableborder]);

  return (
    <Card sx={{ 
        mb: 1, 
        width: '100%', 
        borderLeft: `10px solid ${tlpColor}`,
        borderRadius: 1,
      }}>
      <CardHeader
        action={
          <IconButton onClick={handleExpandClick} aria-expanded={expanded} aria-label="show more">
            <StyledExpandMoreIcon isExpanded={expanded}/>
          </IconButton>
        }
        title={
            <Typography variant="h6" component="div" sx={{ wordBreak: 'break-all' }}>
                {ioc.value}
            </Typography>
        }
        sx={{ '& .MuiCardHeader-content': { overflow: 'hidden' } }}
      />
      <Collapse in={expanded} timeout="auto" unmountOnExit>
        <CardContent sx={{ pt: 0 }}>
          {Object.keys(ioc.services).length > 0 ? (
            <TableContainer component={Paper} sx={{ boxShadow: 0 }}>
              <Table aria-label="service results">
                <TableHead>
                  <TableRow>
                    <StyledHeaderCell sx={{ width: '40px' }} />
                    <StyledHeaderCell>Service</StyledHeaderCell>
                    <StyledHeaderCell>Result</StyledHeaderCell>
                    <StyledHeaderCell sx={{ width: '40px' }} />
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(ioc.services)
                    .filter(([serviceName]) => SERVICE_DEFINITIONS[serviceName])
                    .map(([serviceName, serviceData]) => (
                      <ServiceRow
                        key={serviceName}
                        serviceName={serviceName}
                        serviceData={serviceData}
                        iocValue={ioc.value}
                        iocType={ioc.type}
                        avatarStyle={avatarStyle}
                        cellStyle={cellStyle}
                      />
                    ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No services configured or results available for this IOC type.
            </Typography>
          )}
        </CardContent>
      </Collapse>
    </Card>
  );
}

export default memo(IocCard);
