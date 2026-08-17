import { useState } from 'react';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import SearchIcon from '@mui/icons-material/Search';

export default function ScanForm({ onScan, disabled, initialQuery }) {
  // `initialQuery` comes from usePrefillFromQuery via NewSearch, which yields `null`
  // (not `undefined`) when absent — a default parameter wouldn't catch that.
  const [query, setQuery] = useState(initialQuery || '');
  const [website, setWebsite] = useState('');
  const [forceRefresh, setForceRefresh] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    onScan({ query: trimmed, force_refresh: forceRefresh, website: website.trim() || null });
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mb: 2 }}>
      <Box sx={{ display: 'flex', gap: 2 }}>
        <TextField
          fullWidth
          size="small"
          label="ИНН или название компании/ИП"
          placeholder="Например: 7712345678 или ООО «Нитка»"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={disabled}
        />
        <Button
          type="submit"
          variant="contained"
          startIcon={<SearchIcon />}
          disabled={disabled || !query.trim()}
          sx={{ whiteSpace: 'nowrap' }}
        >
          Проверить
        </Button>
      </Box>

      <TextField
        fullWidth
        size="small"
        label="Сайт компании (опционально)"
        placeholder="Например: example.ru — для сверки возраста домена с датой регистрации"
        value={website}
        onChange={(e) => setWebsite(e.target.value)}
        disabled={disabled}
        sx={{ mt: 1.5 }}
      />

      <FormControlLabel
        sx={{ mt: 1 }}
        control={<Switch checked={forceRefresh} onChange={(e) => setForceRefresh(e.target.checked)} disabled={disabled} />}
        label="Проверить заново, игнорируя кэш"
      />
    </Box>
  );
}
