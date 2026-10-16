import { useCallback } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import LinearProgress from '@mui/material/LinearProgress';
import Button from '@mui/material/Button';
import CancelIcon from '@mui/icons-material/Cancel';

import ScanForm from './ScanForm';
import ResultsView from './ResultsView';
import ReportExportButtons from './ReportExportButtons';
import { useRuBusinessCheck } from '../hooks/useRuBusinessCheck';
import { usePrefillFromQuery } from '../../../core/hooks/usePrefillFromQuery';
import PageHeader from '../../../core/components/ui/PageHeader';

// Russian-only by design, like the rest of this feature's UI (see docs/adr/0014-ru-business-check-source-semantics-and-storage.md).
const PAGE_DESCRIPTION = [
  'Проверка контрагента по ИНН или названию: выписка ЕГРЮЛ/ЕГРИП + сверка директора с реестром',
  'дисквалифицированных лиц и перечнем терроризм/ОМУ (ФедСФМ) + арбитражные дела + проверка на',
  'активное банкротство (Федресурс) + признаки массовой регистрации/руководителя (Прозрачный',
  'бизнес) + реестр недобросовестных поставщиков (РНП) + опционально, при указании сайта —',
  'сверка возраста домена с датой регистрации компании. ФССП автоматически не проверяется',
  '(капча на каждом запросе) — доступна только ручная проверка по ссылке.',
].join(' ');

export default function NewSearch() {
  const { result, loading, error, scan, cancelScan } = useRuBusinessCheck();

  // Hand-off from a command-palette pivot (e.g. "7712345678 business check") — see crossFeatureNav.ts.
  const prefillValue = usePrefillFromQuery(useCallback((value) => scan({ query: value, force_refresh: false }), [scan]));

  return (
    <Box>
      <PageHeader
        title="RU Business Check"
        description={PAGE_DESCRIPTION}
      />

      <ScanForm onScan={scan} disabled={loading} initialQuery={prefillValue} />

      {loading && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress sx={{ mb: 0.5 }} />
          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button size="small" color="error" startIcon={<CancelIcon />} onClick={cancelScan}>
              Отменить
            </Button>
          </Box>
        </Box>
      )}
      {error && <Typography color="error" sx={{ mb: 2 }}>{error}</Typography>}

      {result?.status === 'completed' && <ReportExportButtons searchId={result.id} />}

      <ResultsView result={result} />
    </Box>
  );
}
