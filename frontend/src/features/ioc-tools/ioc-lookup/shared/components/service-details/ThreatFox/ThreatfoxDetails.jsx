import React from 'react';
import { useTranslation } from 'react-i18next';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import Grid from '@mui/material/Grid';
import Link from '@mui/material/Link';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import MalwareIcon from '@mui/icons-material/BugReport';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutlined';
import InfoIcon from '@mui/icons-material/InfoOutlined';
import TagIcon from '@mui/icons-material/Label';
import IocValueIcon from '@mui/icons-material/Language';
import LinkIcon from '@mui/icons-material/Link';
import PersonIcon from '@mui/icons-material/Person';
import ReportProblemIcon from '@mui/icons-material/ReportProblemOutlined';
import TimeIcon from '@mui/icons-material/Schedule';
import SecurityIcon from '@mui/icons-material/Security';

import NoDetails from '../NoDetails';

const RenderSection = ({ icon, title, content, dense = true, yes, no }) => {
  if (!content && typeof content !== 'boolean') return null;

  const secondaryContent = React.isValidElement(content) ? content :
    (typeof content === 'boolean' ? (content ? yes : no) : String(content));

  return (
    <ListItem dense={dense} sx={{py: 0.5, alignItems: React.isValidElement(content) ? 'flex-start' : 'center'}}>
      <ListItemIcon sx={{minWidth: 36}}>
        {icon || <InfoIcon color="action" />}
      </ListItemIcon>
      <ListItemText
        primary={title}
        secondary={secondaryContent}
        primaryTypographyProps={{ variant: 'caption', fontWeight: 'medium', color: 'text.secondary' }}
        secondaryTypographyProps={{ variant: 'body2', component: React.isValidElement(content) ? 'div' : 'span', sx:{wordBreak: 'break-all'} }}
      />
    </ListItem>
  );
};


export default function ThreatfoxDetails({ result, ioc }) {
  const { t } = useTranslation('iocTools');
  const notAvailable = t('providers.common.notAvailable');
  const yes = t('providers.common.yes');
  const no = t('providers.common.no');

  if (!result) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.threatfox.loading')} />
      </Box>
    );
  }

  if (result.error) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.threatfox.errorFetching', { error: result.message || result.error })} />
      </Box>
    );
  }

  // query_status: "ok", "no_result", "illegal_search_term", "illegal_ioc_format"
  if (result.query_status !== "ok") {
    let message = t('providers.threatfox.queryStatus', { status: result.query_status?.replace(/_/g, ' ') || t('providers.threatfox.unknownError') });
    if (result.query_status === "no_result") {
      message = t('providers.threatfox.notFound', { ioc });
      return (
        <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection:'column', minHeight: 100, textAlign:'center' }}>
            <CheckCircleOutlineIcon color="success" sx={{fontSize: 40, mb:1}}/>
            <Typography variant="h6">{message}</Typography>
        </Box>
      );
    }
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection:'column', minHeight: 100, textAlign:'center' }}>
        <ReportProblemIcon color="warning" sx={{fontSize: 40, mb:1}}/>
        <Typography variant="h6">{message}</Typography>
      </Box>
    );
  }

  if (!Array.isArray(result.data) || result.data.length === 0) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection:'column', minHeight: 100, textAlign:'center' }}>
         <CheckCircleOutlineIcon color="success" sx={{fontSize: 40, mb:1}}/>
        <Typography variant="h6">{t('providers.threatfox.foundNoEntries')}</Typography>
        <Typography variant="body2" color="text.secondary">{t('providers.threatfox.foundNoEntriesHint')}</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ margin: 1, mt:0 }}>
        <Grid container spacing={1} alignItems="center" mb={1}>
            <SecurityIcon color="action"/>
            <Typography variant="h6" component="div" sx={{ ml: 1 }}>
              {t('providers.threatfox.intelligenceFor')} <Typography component="span" sx={{wordBreak: 'break-all'}}>{ioc}</Typography>
            </Typography>
        </Grid>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }} mb={2}>
            {t('providers.threatfox.displayingRecords', { count: result.data.length })}
        </Typography>
        {result.data.map((entry, index) => (
        <Card key={entry.id || index} elevation={0} sx={{ mb: 2, borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
            <CardContent sx={{p:2}}>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    {t('providers.threatfox.entryIdConfidence', { id: entry.id, confidence: entry.confidence_level })}
                </Typography>
                <Divider sx={{mb:1}}/>
                <List disablePadding dense>
                    <RenderSection
                        icon={<IocValueIcon />}
                        title={t('providers.threatfox.iocValue')}
                        content={entry.ioc_value}
                        yes={yes} no={no}
                    />
                    <RenderSection
                        icon={<InfoIcon />}
                        title={t('providers.threatfox.iocType')}
                        content={<>{entry.ioc_type} <Typography variant="caption" color="text.disabled">({entry.ioc_type_desc})</Typography></>}
                        yes={yes} no={no}
                    />
                    <RenderSection
                        icon={<SecurityIcon />}
                        title={t('providers.threatfox.threatType')}
                        content={<>{entry.threat_type} <Typography variant="caption" color="text.disabled">({entry.threat_type_desc})</Typography></>}
                        yes={yes} no={no}
                    />
                    <RenderSection
                        icon={<MalwareIcon />}
                        title={t('providers.threatfox.malware')}
                        yes={yes} no={no}
                        content={
                            <Box>
                                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                {entry.malware_printable} ({entry.malware === 'unknown' ? t('providers.threatfox.genericUnknown') : entry.malware})
                                </Typography>
                                {entry.malware_alias && <Typography variant="caption" color="text.secondary">{t('providers.threatfox.alias')} {entry.malware_alias}</Typography>}
                                <br/>
                                {entry.malware_malpedia && (
                                <Link
                                    href={entry.malware_malpedia}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5, typography: 'caption' }}
                                >
                                    <LinkIcon sx={{ fontSize: 'inherit' }} /> {t('providers.threatfox.malpediaEntry')}
                                </Link>
                                )}
                            </Box>
                        }
                    />
                    <RenderSection
                        icon={<TimeIcon />}
                        title={t('providers.threatfox.timeline')}
                        yes={yes} no={no}
                        content={
                            <Box>
                                <Typography variant="caption">{t('providers.threatfox.firstSeen')} {entry.first_seen_utc ? new Date(entry.first_seen_utc).toLocaleString() : notAvailable}</Typography><br/>
                                <Typography variant="caption">{t('providers.threatfox.lastSeen')} {entry.last_seen_utc ? new Date(entry.last_seen_utc).toLocaleString() : notAvailable}</Typography>
                            </Box>
                        }
                    />
                    <RenderSection
                        icon={<PersonIcon />}
                        title={t('providers.threatfox.reporter')}
                        content={entry.reporter}
                        yes={yes} no={no}
                    />
                    {entry.reference && (
                        <RenderSection
                            icon={<LinkIcon />}
                            title={t('providers.threatfox.reference')}
                            yes={yes} no={no}
                            content={
                                <Link href={entry.reference} target="_blank" rel="noopener noreferrer" sx={{typography:'body2'}}>
                                    {entry.reference}
                                </Link>
                            }
                        />
                    )}
                    {entry.tags?.length > 0 && <RenderSection
                        icon={<TagIcon />}
                        title={t('providers.threatfox.tags')}
                        yes={yes} no={no}
                        content={
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.2 }}>
                            {entry.tags.map((tag) => (
                            <Chip key={tag} label={tag} size="small" variant="outlined" sx={{ borderRadius: 1 }}/>
                            ))}
                        </Box>
                        }
                    />}
                </List>
            </CardContent>
        </Card>
        ))}
    </Box>
  );
}
