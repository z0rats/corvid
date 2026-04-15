export function createChartTheme(theme) {
  return {
    axis: {
      ticks: {
        text: {
          fill: theme.palette.text.primary,
          fontSize: 14,
          fontWeight: 500,
        },
        line: {
          stroke: theme.palette.divider,
        },
      },
      legend: {
        text: {
          fill: theme.palette.text.primary,
          fontSize: 16,
          fontWeight: 600,
        },
      },
    },
    grid: {
      line: {
        stroke: theme.palette.divider,
        strokeOpacity: 0.2,
      },
    },
    tooltip: {
      container: {
        background: theme.palette.background.paper,
        color: theme.palette.text.primary,
        fontSize: '14px',
        borderRadius: theme.shape.borderRadius,
        boxShadow: theme.shadows[1],
        border: `1px solid ${theme.palette.divider}`,
      },
    },
    labels: {
      text: {
        fill: theme.palette.text.primary,
        fontSize: 12,
      },
    },
    legends: {
      text: {
        fill: theme.palette.text.secondary,
      },
    },
  };
}
