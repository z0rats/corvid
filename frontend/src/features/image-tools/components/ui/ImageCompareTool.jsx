import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import { useImageCompare } from '../../hooks/api/useImageCompare';

const STATUS_COLOR = { match: 'success', differ: 'warning', only_left: 'default', only_right: 'default' };

function FilePicker({ label, file, onChange }) {
  return (
    <Button component="label" variant="outlined" startIcon={<UploadFileIcon />} sx={{ flex: 1, justifyContent: 'flex-start' }}>
      <Typography variant="body2" noWrap>{file ? file.name : label}</Typography>
      <input type="file" accept="image/*" hidden onChange={(e) => onChange(e.target.files?.[0] || null)} />
    </Button>
  );
}

export default function ImageCompareTool() {
  const { t } = useTranslation('imageTools');
  const [fileLeft, setFileLeft] = useState(null);
  const [fileRight, setFileRight] = useState(null);
  const { result, loading, error, compareImages } = useImageCompare();

  return (
    <Accordion sx={{ mb: 2 }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box
          sx={{
            display: "flex",
            alignItems: "center"
          }}>
          <CompareArrowsIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="subtitle1" fontWeight="medium">{t('compare.title')}</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
          <FilePicker label={t('compare.chooseFirst')} file={fileLeft} onChange={setFileLeft} />
          <FilePicker label={t('compare.chooseSecond')} file={fileRight} onChange={setFileRight} />
        </Box>
        <Button
          variant="contained"
          disableElevation
          disabled={!fileLeft || !fileRight || loading}
          onClick={() => compareImages(fileLeft, fileRight)}
        >
          {t('compare.compareButton')}
        </Button>

        {loading && <LinearProgress sx={{ mt: 2 }} />}
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}

        {result && (
          <Box sx={{ mt: 2 }}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
              <Chip size="small" color="success" label={t('compare.matchCount', { count: result.summary.match_count })} />
              <Chip size="small" color="warning" label={t('compare.differCount', { count: result.summary.differ_count })} />
              <Chip size="small" variant="outlined" label={t('compare.onlyLeftCount', { count: result.summary.only_left_count })} />
              <Chip size="small" variant="outlined" label={t('compare.onlyRightCount', { count: result.summary.only_right_count })} />
              <Chip
                size="small"
                color={result.pixels_likely_match ? 'success' : 'default'}
                label={t(result.pixels_likely_match ? 'compare.pixelsMatch' : 'compare.pixelsDiffer', { value: result.phash_distance })}
              />
            </Box>

            <Box sx={{ overflowX: 'auto' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>{t('compare.field')}</TableCell>
                    <TableCell sx={{ wordBreak: 'break-all' }}>{result.left.filename}</TableCell>
                    <TableCell sx={{ wordBreak: 'break-all' }}>{result.right.filename}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {result.field_diffs.map((diff) => (
                    <TableRow key={diff.field}>
                      <TableCell sx={{ whiteSpace: 'nowrap' }}>
                        <Chip size="small" color={STATUS_COLOR[diff.status]} label={diff.field} variant="outlined" />
                      </TableCell>
                      <TableCell sx={{ wordBreak: 'break-all' }}>{diff.left_value ?? '—'}</TableCell>
                      <TableCell sx={{ wordBreak: 'break-all' }}>{diff.right_value ?? '—'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          </Box>
        )}
      </AccordionDetails>
    </Accordion>
  );
}
