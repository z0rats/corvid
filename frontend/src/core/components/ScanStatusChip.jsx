import React from 'react';
import Chip from '@mui/material/Chip';

const SCAN_STATUS_COLORS = { running: 'info', completed: 'success', cancelled: 'warning', failed: 'error' };

// A scan run's status (backend `ScanRun`: running/completed/cancelled/failed) as a
// coloured chip, shared by every scan feature's history list and detail header. The
// label stays the caller's, since each feature translates it in its own namespace.
export default function ScanStatusChip({ status, label }) {
  return <Chip size="small" label={label} color={SCAN_STATUS_COLORS[status] || 'default'} />;
}
