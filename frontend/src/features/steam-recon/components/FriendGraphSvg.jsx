import { useTranslation } from 'react-i18next';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';

import { MAX_GRAPH_NODES, layoutFriendGraph } from '../utils/friendGraphLayout';

export default function FriendGraphSvg({ closeFriends, targetLabel }) {
  const { t } = useTranslation('steamRecon');
  const theme = useTheme();
  const layout = layoutFriendGraph(closeFriends, targetLabel);

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="h6" component="h2">
        {t('friendGraph.title')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('friendGraph.subtitle', { count: MAX_GRAPH_NODES })}
      </Typography>

      {layout.nodes.length === 0 ? (
        <Typography color="text.secondary">{t('friendGraph.empty')}</Typography>
      ) : (
        <svg
          viewBox={`0 0 ${layout.viewBoxSize} ${layout.viewBoxSize}`}
          role="img"
          aria-label={t('friendGraph.title')}
          style={{ width: '100%', maxWidth: 480, display: 'block', margin: '0 auto' }}
        >
          {layout.edges.map((edge) => (
            <line
              key={edge.id}
              x1={edge.x1}
              y1={edge.y1}
              x2={edge.x2}
              y2={edge.y2}
              stroke={theme.palette.text.secondary}
              strokeOpacity={0.25 + edge.weightRatio * 0.5}
              strokeWidth={1 + edge.weightRatio * 2}
            />
          ))}

          <circle
            cx={layout.target.x}
            cy={layout.target.y}
            r={layout.target.radius}
            fill={theme.palette.primary.main}
          >
            <title>{layout.target.label}</title>
          </circle>
          <text
            x={layout.target.x}
            y={layout.target.y}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={10}
            fill={theme.palette.primary.contrastText}
          >
            {(layout.target.label || '').slice(0, 8)}
          </text>

          {layout.nodes.map((node) => (
            <g key={node.id}>
              <a href={`https://steamcommunity.com/profiles/${node.id}`} target="_blank" rel="noopener noreferrer">
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={node.radius}
                  fill={node.banned ? theme.palette.error.main : theme.palette.secondary.main}
                >
                  <title>
                    {node.label} ({node.mutualCount})
                  </title>
                </circle>
                <text
                  x={node.labelX}
                  y={node.labelY}
                  textAnchor={node.labelAnchor}
                  dominantBaseline="middle"
                  fontSize={11}
                  fill={theme.palette.text.primary}
                >
                  {node.label}
                </text>
              </a>
            </g>
          ))}
        </svg>
      )}
    </Paper>
  );
}
