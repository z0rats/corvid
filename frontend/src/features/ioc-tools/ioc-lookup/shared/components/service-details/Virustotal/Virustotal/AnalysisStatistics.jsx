import React from "react";
import { PieChart, Pie, ResponsiveContainer } from "recharts";

import AccessTimeIcon from "@mui/icons-material/AccessTime";
import CalendarMonthOutlinedIcon from "@mui/icons-material/CalendarMonthOutlined";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import DataUsageIcon from "@mui/icons-material/DataUsage";
import HighlightOffIcon from "@mui/icons-material/HighlightOff";
import PeopleIcon from "@mui/icons-material/People";
import PollOutlinedIcon from "@mui/icons-material/PollOutlined";
import ReportProblemIcon from "@mui/icons-material/ReportProblem";
import ThumbDownOutlinedIcon from "@mui/icons-material/ThumbDownOutlined";
import ThumbUpOutlinedIcon from "@mui/icons-material/ThumbUpOutlined";
import QuestionMarkIcon from "@mui/icons-material/QuestionMark";

import Avatar from "@mui/material/Avatar";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Divider from "@mui/material/Divider";
import Grid from "@mui/material/Grid2";
import LinearProgress, {
  linearProgressClasses,
} from "@mui/material/LinearProgress";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemAvatar from "@mui/material/ListItemAvatar";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import { styled, useTheme } from "@mui/material/styles";
import Typography from '@mui/material/Typography';

const BorderLinearProgress = styled(LinearProgress)(({ theme }) => ({
  height: 10,
  borderRadius: 5,
  [`&.${linearProgressClasses.colorPrimary}`]: {
    backgroundColor: theme.palette.success.main,
  },
  [`& .${linearProgressClasses.bar}`]: {
    borderRadius: 5,
    backgroundColor: theme.palette.error.main,
  },
}));

export default function AnalysisStatistics(props) {
  const theme = useTheme();
  const attributes = props.result?.data?.attributes || {};
  const totalVotes = attributes.total_votes || { malicious: 0, harmless: 0 };

  const textColor =
    props.malCount > 0
      ? "error.main"
      : (props.stats.suspicious || 0) > 0
      ? "warning.main"
      : "success.main";

  return (
    <Card
      key={"statistics_card"}
      sx={{
        mb: 1,
        p: 2,
        borderRadius: 1,
        boxShadow: 0,
        width: "calc(50% - 10px)",
      }}
    >
      <Grid container spacing={2}>
        <Grid size={6}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DataUsageIcon />
            <Typography variant="h6" component="h2">Analysis Statistics</Typography>
          </Box>
          <List>
            <ListItem disablePadding>
              <ListItemAvatar>
                <Avatar sx={{ backgroundColor: 'success.main' }}>
                  <CheckCircleOutlineIcon />
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary="Harmless"
                secondary={
                  props.stats.harmless || 0
                }
              />
            </ListItem>
            <ListItem disablePadding>
              <ListItemAvatar>
                <Avatar sx={{ backgroundColor: "red" }}>
                  <HighlightOffIcon />
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary="Malicious"
                secondary={
                  props.stats.malicious || 0
                }
              />
            </ListItem>
            <ListItem disablePadding>
              <ListItemAvatar>
                <Avatar sx={{ backgroundColor: 'warning.main' }}>
                  <ReportProblemIcon />
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary="Suspicious"
                secondary={
                  props.stats.suspicious || 0
                }
              />
            </ListItem>
            <ListItem disablePadding>
              <ListItemAvatar>
                <Avatar>
                  <QuestionMarkIcon />
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary="Undetected"
                secondary={
                  props.stats.undetected || 0
                }
              />
            </ListItem>
            <ListItem disablePadding>
              <ListItemAvatar>
                <Avatar>
                  <AccessTimeIcon />
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary="Timeout"
                secondary={
                  props.stats.timeout || 0
                }
              />
            </ListItem>
          </List>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }} sx={{ display: "flex", alignItems: "center" }}>
          <ResponsiveContainer width="80%" height="80%">
            <PieChart width={250} height={250}>
              <Pie
                data={[
                  { name: "malcount", value: props.malCount },
                  {
                    name: "suspicious",
                    value: props.stats.suspicious || 0,
                    fill: theme.palette.warning.main,
                  },
                  {
                    name: "harmless",
                    value: props.stats.harmless || 0,
                    fill: theme.palette.success.main,
                  },
                  {
                    name: "undetected",
                    value: props.stats.undetected || 0,
                    fill: "grey",
                  },
                  {
                    name: "timeout",
                    value: props.stats.timeout || 0,
                    fill: "grey",
                  },
                  {
                    name: "Remaining",
                    value:
                      props.totalEngines -
                      (props.malCount +
                        (props.stats.harmless || 0) +
                        (props.stats.suspicious || 0) +
                        (props.stats.undetected || 0) +
                        (props.stats.timeout || 0)),
                    fill: theme.palette.chart.inactive,
                  },
                ]}
                dataKey="value"
                startAngle={90}
                endAngle={-270}
                innerRadius="80%"
                outerRadius="100%"
                minAngle={1}
                domain={[0, props.totalEngines]}
                stroke="none"
                strokeWidth={0}
                fill="red"
              />
              <foreignObject
                width="100%"
                height="100%"
                style={{ textAlign: "center" }}
              >
                <Box
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "center",
                    alignItems: "center",
                    height: "100%",
                    width: "100%",
                  }}
                >
                  <Typography variant="h3" color={textColor} align="center">
                    {props.malCount}
                  </Typography>
                  <Typography variant="h5" color="text.secondary" align="center">
                    / {props.totalEngines}
                  </Typography>
                </Box>
              </foreignObject>
            </PieChart>
          </ResponsiveContainer>
        </Grid>
      </Grid>

      <Divider>
        <Box
          sx={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
          }}
        >
          <PeopleIcon />
          <Typography variant="body1" sx={{ ml: 1 }}>
            Community
          </Typography>
        </Box>
      </Divider>
      <Grid container spacing={2}>
        <Grid size={6}>
          <List>
            <ListItem alignItems="flex-start">
              <ListItemIcon>
                <PollOutlinedIcon color="action" />
              </ListItemIcon>
              <ListItemText
                primary="Reputation"
                secondary={attributes.reputation ?? 'N/A'}
              />
            </ListItem>
            <ListItem alignItems="flex-start">
              <ListItemIcon>
                <ThumbDownOutlinedIcon htmlColor="red" />
              </ListItemIcon>
              <ListItemText
                primary="Voted malicious"
                secondary={totalVotes.malicious}
              />
            </ListItem>
          </List>
        </Grid>

        <Grid size={6}>
          <List>
            <ListItem alignItems="flex-start">
              <ListItemIcon>
                <CalendarMonthOutlinedIcon color="action" />
              </ListItemIcon>
              <ListItemText
                primary="Last modification"
                secondary={attributes.last_modification_date
                  ? `${new Date(attributes.last_modification_date * 1000).toLocaleDateString()} ${new Date(attributes.last_modification_date * 1000).toLocaleTimeString()}`
                  : 'N/A'}
              />
            </ListItem>
            <ListItem alignItems="flex-start">
              <ListItemIcon>
                <ThumbUpOutlinedIcon htmlColor={theme.palette.success.main} />
              </ListItemIcon>
              <ListItemText
                primary="Voted harmless"
                secondary={totalVotes.harmless}
              />
            </ListItem>
          </List>
        </Grid>
      </Grid>
      {totalVotes.malicious === 0 && totalVotes.harmless === 0 ? null : (
        <Box sx={{ display: "flex", alignItems: "center" }}>
          <Box sx={{ width: "100%", m: 1 }}>
            <BorderLinearProgress
              variant="determinate"
              value={
                (totalVotes.malicious /
                  (totalVotes.harmless + totalVotes.malicious)) *
                100
              }
            />
          </Box>
        </Box>
      )}
    </Card>
  );
}
