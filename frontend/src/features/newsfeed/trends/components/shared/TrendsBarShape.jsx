import React from "react";
import Tooltip from '@mui/material/Tooltip';

export default function TrendsBarShape({ x, y, width, height, payload, onSelect, onBlacklist, blacklistTitle }) {
  const cx = x + width / 2;
  const cy = y + height + 12;

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        rx={4}
        ry={4}
        fill={payload.color}
        style={{ cursor: onSelect ? 'pointer' : 'default' }}
        onClick={onSelect}
      />
      {onBlacklist && (
        <Tooltip title={blacklistTitle} arrow placement="bottom">
          <g
            transform={`translate(${cx}, ${cy})`}
            onClick={(e) => { e.stopPropagation(); onBlacklist(); }}
            style={{ cursor: 'pointer' }}
          >
            <circle r={8} fill="transparent" />
            <text textAnchor="middle" dominantBaseline="central" fontSize={12} fill="currentColor" opacity={0.4}>
              ✕
            </text>
          </g>
        </Tooltip>
      )}
    </g>
  );
}
