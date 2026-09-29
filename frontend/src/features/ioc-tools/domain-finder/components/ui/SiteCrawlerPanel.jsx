import React from "react";
import { useTranslation } from 'react-i18next';
import { useSiteCrawler } from "../../hooks/api/useSiteCrawler";

import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import LinearProgress from '@mui/material/LinearProgress';
import Link from '@mui/material/Link';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import TravelExploreIcon from '@mui/icons-material/TravelExplore';

const DEFAULT_MAX_PAGES = 15;
const DEFAULT_MAX_DEPTH = 2;

const IOC_CATEGORY_KEYS = [
  'domains', 'ips', 'urls', 'emails', 'md5', 'sha1', 'sha256', 'cves', 'secrets', 'js_endpoints'
];

function isSearchPattern(domain) {
  return domain.includes('*') || domain.includes('?');
}

function statusColor(statusCode) {
  if (statusCode >= 200 && statusCode < 300) return 'success';
  if (statusCode >= 300 && statusCode < 400) return 'info';
  return 'warning';
}

export default function SiteCrawlerPanel({ domain }) {
  const { t } = useTranslation('iocTools');
  const { data, loading, error, crawl } = useSiteCrawler(domain);

  if (!domain || isSearchPattern(domain)) return null;

  const nonEmptyCategories = data
    ? IOC_CATEGORY_KEYS.filter((key) => (data.iocs?.[key] || []).length > 0)
    : [];

  return (
    <Card sx={{ mb: 2, p: 1, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {t('domainFinder.siteCrawler.title')}
        </Typography>

        <Alert severity="info" variant="outlined" sx={{ mb: 2, borderRadius: 1 }}>
          {t('domainFinder.siteCrawler.description', {
            maxPages: DEFAULT_MAX_PAGES,
            maxDepth: DEFAULT_MAX_DEPTH
          })}
        </Alert>

        {!data && !loading && (
          <Button variant="outlined" startIcon={<TravelExploreIcon />} onClick={crawl}>
            {t('domainFinder.siteCrawler.startButton')}
          </Button>
        )}

        {loading && <LinearProgress sx={{ mb: 2 }} />}

        {error && (
          <Alert severity="warning" variant="outlined" sx={{ borderRadius: 1, mb: 2 }}>
            {t('domainFinder.siteCrawler.errorPrefix')} {error}
          </Alert>
        )}

        {data && (
          <Stack spacing={1.5}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
              <Chip
                size="small"
                color="primary"
                label={t('domainFinder.siteCrawler.summary', {
                  pages: data.total_pages_crawled,
                  iocs: data.iocs?.statistics?.total_unique_iocs || 0
                })}
              />
              {data.errors?.length > 0 && (
                <Chip
                  size="small"
                  color="warning"
                  variant="outlined"
                  label={t('domainFinder.siteCrawler.errorsSummary', { count: data.errors.length })}
                />
              )}
            </Stack>

            <Divider />

            <Typography variant="subtitle2">
              {t('domainFinder.siteCrawler.pagesTitle')}
            </Typography>
            <List dense sx={{ maxHeight: 240, overflowY: 'auto' }}>
              {data.pages.map((page) => (
                <ListItem key={page.url} disableGutters>
                  <Chip
                    size="small"
                    color={statusColor(page.status_code)}
                    label={page.status_code}
                    sx={{ mr: 1, minWidth: 48 }}
                  />
                  <ListItemText
                    primary={
                      <Link href={page.url} target="_blank" rel="noopener noreferrer">
                        {page.url}
                      </Link>
                    }
                    secondary={page.title || undefined}
                  />
                </ListItem>
              ))}
            </List>

            <Typography variant="subtitle2">
              {t('domainFinder.siteCrawler.iocsTitle')}
            </Typography>
            {nonEmptyCategories.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                {t('domainFinder.siteCrawler.noIocs')}
              </Typography>
            ) : (
              nonEmptyCategories.map((key) => {
                const values = data.iocs[key];
                return (
                  <Accordion key={key} disableGutters elevation={0} sx={{ border: 1, borderColor: 'divider' }}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="body2">
                        {t(`domainFinder.siteCrawler.iocCategories.${key}`)} ({values.length})
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails sx={{ maxHeight: 200, overflowY: 'auto' }}>
                      <Stack spacing={0.5}>
                        {values.map((value) => (
                          <Typography key={value} variant="body2" sx={{ fontFamily: 'monospace' }}>
                            {value}
                          </Typography>
                        ))}
                      </Stack>
                    </AccordionDetails>
                  </Accordion>
                );
              })
            )}

            <Box>
              <Button size="small" onClick={crawl}>
                {t('domainFinder.siteCrawler.recrawlButton')}
              </Button>
            </Box>
          </Stack>
        )}
      </CardContent>
    </Card>
  );
}
