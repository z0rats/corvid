import React from 'react';
import { useTheme } from '@mui/material/styles';
import { modeValue } from '../../../../core/utils/themeUtils';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import LaunchIcon from '@mui/icons-material/Launch';

const titleTruncateSx = {
  display: '-webkit-box',
  WebkitLineClamp: 2,
  WebkitBoxOrient: 'vertical',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  lineHeight: '1.4em',
  maxHeight: '2.8em',
};

const ArticleTable = ({ selectedArticleIds, selectedTitle, articleDetails, articleLoading }) => {
  const theme = useTheme();

  if (!selectedTitle || selectedArticleIds.length === 0) {
    return null;
  }

  return (
    <Card sx={{ mt: 2 }}>
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          <Typography variant="h6" color="text.primary">
            Articles containing
          </Typography>
          <Chip
            label={selectedTitle}
            sx={{
              ml: 1,
              mr: 1,
              bgcolor: modeValue(theme, theme.palette.primary.dark, theme.palette.primary.light),
              color: modeValue(theme, theme.palette.primary.contrastText, theme.palette.primary.dark),
              fontWeight: 'medium'
            }}
          />
          <Typography variant="body1" color="text.secondary">
            ({selectedArticleIds.length} occurrences)
          </Typography>
        </Box>

        <TableContainer>
          <Table size="medium">
            <TableHead>
              <TableRow>
                <TableCell>Source</TableCell>
                <TableCell>Title</TableCell>
                <TableCell>Date</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {selectedArticleIds.map((articleId) => {
                const article = articleDetails[articleId];
                const isLoading = articleLoading[articleId];

                if (isLoading) {
                  return (
                    <TableRow key={articleId}>
                      <TableCell colSpan={4}>
                        <Box display="flex" alignItems="center" gap={1}>
                          <CircularProgress size={20} />
                          <Typography variant="body2">Loading article details...</Typography>
                        </Box>
                      </TableCell>
                    </TableRow>
                  );
                }

                if (article?.error) {
                  return (
                    <TableRow key={articleId}>
                      <TableCell colSpan={4}>
                        <Alert severity="error" size="small">
                          Error loading article {articleId}: {article.error}
                        </Alert>
                      </TableCell>
                    </TableRow>
                  );
                }

                if (!article) {
                  return (
                    <TableRow key={articleId}>
                      <TableCell colSpan={4}>
                        <Typography variant="body2" color="text.secondary">
                          Article details not available.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  );
                }

                return (
                  <TableRow key={articleId} hover>
                    <TableCell>
                      <Chip
                        label={article.feedname}
                        size="small"
                        sx={{
                          bgcolor: modeValue(theme, theme.palette.secondary.dark, theme.palette.secondary.light),
                          color: modeValue(theme, theme.palette.secondary.contrastText, theme.palette.secondary.dark),
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="body2"
                        color="text.primary"
                        sx={titleTruncateSx}
                      >
                        {article.title}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {new Date(article.date).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {article.link && (
                        <Tooltip title="Open article">
                          <IconButton
                            size="small"
                            href={article.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            aria-label="Open article"
                            sx={{
                              color: modeValue(theme, theme.palette.secondary.light, theme.palette.secondary.dark)
                            }}
                          >
                            <LaunchIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
};

export default ArticleTable;