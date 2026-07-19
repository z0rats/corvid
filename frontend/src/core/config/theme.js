import { createTheme } from "@mui/material/styles";
import { alpha } from "@mui/material/styles";

const colors = {
  primary: {
    50: '#F0F9F7',
    100: '#DAF1EA',
    200: '#B5E3D6',
    300: '#89D2BD',
    400: '#5EC2A6',
    500: '#42AE8F',
    600: '#38947A',
    700: '#2F7C66',
    800: '#266452',
    900: '#1B463A',
  },

  secondary: {
    50: '#FDF9F2',
    100: '#F8EEDD',
    200: '#F1DCB6',
    300: '#E9C78B',
    400: '#E1B363',
    500: '#DAA13E',
    600: '#C78C26',
    700: '#A5741F',
    800: '#815A18',
    900: '#5E4212',
  },

  error: {
    50: '#FBF0EE',
    100: '#F5D9D6',
    300: '#E4948B',
    400: '#DA6E62',
    500: '#D35345',
    600: '#C23C2E',
    700: '#A53327',
  },

  success: {
    50: '#EFF6FA',
    100: '#D7E8F4',
    300: '#81B5DA',
    400: '#539ACD',
    500: '#3683BA',
    600: '#2E6F9E',
    700: '#265D84',
  },

  neutral: {
    50: '#FAFAFA',
    100: '#F1F3F3',
    200: '#DFE2E1',
    300: '#C4CAC9',
    400: '#98A4A1',
    500: '#6E7C79',
    600: '#515C59',
    700: '#3A413F',
    800: '#242927',
    900: '#161818',
    950: '#0D0F0E',
  }
};

const lightPalette = {
  mode: "light",
  primary: {
    main: colors.primary[700],
    light: colors.primary[500],
    dark: colors.primary[900],
    contrastText: "#ffffff",
  },
  secondary: {
    main: colors.secondary[700],
    light: colors.secondary[500],
    dark: colors.secondary[900],
    contrastText: "#ffffff",
  },
  error: {
    main: colors.error[500],
    light: colors.error[300],
    dark: colors.error[700],
  },
  warning: {
    main: colors.secondary[700],
    light: colors.secondary[500],
    dark: colors.secondary[900],
  },
  info: {
    main: colors.success[500],
    light: colors.success[300],
    dark: colors.success[700],
  },
  success: {
    main: colors.success[500],
    light: colors.success[300],
    dark: colors.success[700],
  },
  background: {
    default: colors.neutral[200],
    paper: colors.neutral[100],
    card: colors.neutral[50],
    detailArea: colors.neutral[300],
    textfieldlarge: colors.neutral[200],
    tablecell: colors.neutral[100],
    tableborder: colors.neutral[200],
    cvssCircle: colors.neutral[200],
  },
  chart: {
    low: colors.success[500],
    medium: colors.secondary[500],
    high: colors.error[500],
    inactive: colors.neutral[300],
  },
  text: {
    primary: colors.neutral[900],
    secondary: colors.neutral[600],
    disabled: colors.neutral[400],
  },
  divider: alpha(colors.neutral[900], 0.08),
  action: {
    active: colors.neutral[600],
    hover: alpha(colors.neutral[900], 0.04),
    selected: alpha(colors.primary[500], 0.08),
    disabled: colors.neutral[300],
    disabledBackground: colors.neutral[100],
  },
};

const darkPalette = {
  mode: "dark",
  primary: {
    main: colors.primary[400],
    light: colors.primary[300],
    dark: colors.primary[600],
    contrastText: colors.neutral[900],
  },
  secondary: {
    main: colors.secondary[400],
    light: colors.secondary[300],
    dark: colors.secondary[600],
    contrastText: colors.neutral[900],
  },
  error: {
    main: colors.error[400],
    light: colors.error[300],
    dark: colors.error[600],
  },
  warning: {
    main: colors.secondary[400],
    light: colors.secondary[300],
    dark: colors.secondary[600],
  },
  info: {
    main: colors.success[400],
    light: colors.success[300],
    dark: colors.success[600],
  },
  success: {
    main: colors.success[400],
    light: colors.success[300],
    dark: colors.success[600],
  },
  background: {
    default: colors.neutral[950],
    paper: colors.neutral[900],
    card: colors.neutral[800],
    detailArea: colors.neutral[700],
    textfieldlarge: colors.neutral[800],
    tablecell: colors.neutral[900],
    tableborder: 'rgba(250, 250, 250, 0.12)',
    cvssCircle: colors.neutral[800],
  },
  chart: {
    low: colors.success[400],
    medium: colors.secondary[400],
    high: colors.error[400],
    inactive: colors.neutral[700],
  },
  text: {
    primary: colors.neutral[50],
    secondary: colors.neutral[400],
    disabled: colors.neutral[600],
  },
  divider: alpha(colors.neutral[50], 0.12),
  action: {
    active: colors.neutral[300],
    hover: alpha(colors.neutral[50], 0.04),
    selected: alpha(colors.primary[400], 0.12),
    disabled: colors.neutral[700],
    disabledBackground: colors.neutral[800],
  },
};

const typography = {
  fontFamily: '"Archivo", "Helvetica", "Arial", sans-serif',
  h1: {
    fontWeight: 700,
    fontSize: "2.5rem",
    lineHeight: 1.2,
    letterSpacing: "-0.02em",
  },
  h2: {
    fontWeight: 700,
    fontSize: "2rem",
    lineHeight: 1.3,
    letterSpacing: "-0.01em",
  },
  h3: {
    fontWeight: 700,
    fontSize: "1.75rem",
    lineHeight: 1.4,
    letterSpacing: "-0.01em",
  },
  h4: {
    fontWeight: 700,
    fontSize: "1.5rem",
    lineHeight: 1.4,
  },
  h5: {
    fontWeight: 700,
    fontSize: "1.25rem",
    lineHeight: 1.5,
  },
  h6: {
    fontWeight: 700,
    fontSize: "1.125rem",
    lineHeight: 1.5,
  },
  body1: {
    fontSize: "1rem",
    lineHeight: 1.6,
    letterSpacing: "0.01em",
  },
  body2: {
    fontSize: "0.875rem",
    lineHeight: 1.6,
    letterSpacing: "0.01em",
  },
  button: {
    textTransform: "none",
    fontWeight: 500,
    letterSpacing: "0.02em",
  },
  caption: {
    fontSize: "0.75rem",
    lineHeight: 1.4,
    letterSpacing: "0.02em",
  },
};

const shape = {
  borderRadius: 8,
};

const createFilledAlertStyle = (bgColor) => ({ theme }) => ({
  ...(theme.palette.mode === "dark" && {
    backgroundColor: bgColor,
    color: colors.neutral[900],
    "& .MuiAlert-icon": {
      color: colors.neutral[900],
    },
    "& .MuiAlert-action": {
      color: colors.neutral[900],
      "& .MuiIconButton-root": {
        color: colors.neutral[900],
        "&:hover": {
          backgroundColor: alpha(colors.neutral[900], 0.1),
        },
      },
    },
  }),
});

const reducedMotion = {
  "@media (prefers-reduced-motion: reduce)": {
    transition: "none",
  },
};

const components = {
  MuiButton: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        textTransform: "none",
        fontWeight: 500,
        padding: "10px 24px",
        transition: "background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease",
        ...reducedMotion,
      },
      containedPrimary: ({ theme }) => ({
        backgroundColor: theme.palette.primary.main,
        boxShadow: "none",
        "&:hover": {
          backgroundColor: theme.palette.mode === "dark" ? colors.primary[300] : colors.primary[800],
          boxShadow: "none",
        },
      }),
      containedSecondary: ({ theme }) => ({
        backgroundColor: theme.palette.secondary.main,
        boxShadow: "none",
        "&:hover": {
          backgroundColor: theme.palette.mode === "dark" ? colors.secondary[300] : colors.secondary[800],
          boxShadow: "none",
        },
      }),
      outlined: ({ theme }) => ({
        borderWidth: 2,
        ...(theme.palette.mode === "dark" && {
          borderColor: colors.neutral[600],
          color: colors.neutral[200],
        }),
        "&:hover": {
          borderWidth: 2,
          ...(theme.palette.mode === "dark"
            ? {
                backgroundColor: alpha(colors.primary[400], 0.08),
                borderColor: colors.primary[400],
              }
            : {
                backgroundColor: alpha(colors.primary[500], 0.08),
              }),
        },
      }),
    },
  },
  MuiCard: {
    styleOverrides: {
      root: ({ theme }) => ({
        borderRadius: 8,
        border: theme.palette.mode === "dark"
          ? `1px solid ${colors.neutral[800]}`
          : `1px solid ${colors.neutral[200]}`,
        boxShadow: "none",
        backgroundColor: theme.palette.mode === "dark" ? colors.neutral[900] : undefined,
      }),
    },
  },
  MuiTextField: {
    styleOverrides: {
      root: ({ theme }) => ({
        "& .MuiOutlinedInput-root": {
          borderRadius: 8,
          backgroundColor: theme.palette.mode === "dark" ? colors.neutral[800] : colors.neutral[100],
          transition: "border-color 0.15s ease, box-shadow 0.15s ease",
          ...reducedMotion,
          "& fieldset": {
            borderColor: theme.palette.mode === "dark" ? colors.neutral[700] : colors.neutral[300],
            borderWidth: 2,
          },
          "&:hover fieldset": {
            borderColor: theme.palette.mode === "dark" ? colors.primary[400] : colors.primary[400],
          },
          "&.Mui-focused fieldset": {
            borderColor: theme.palette.mode === "dark" ? colors.primary[400] : colors.primary[500],
            boxShadow: theme.palette.mode === "dark"
              ? `0 0 0 3px ${alpha(colors.primary[400], 0.15)}`
              : `0 0 0 3px ${alpha(colors.primary[500], 0.1)}`,
          },
        },
      }),
    },
  },
  MuiChip: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        fontWeight: 500,
      },
      colorPrimary: ({ theme }) => ({
        backgroundColor: theme.palette.mode === "dark"
          ? alpha(colors.primary[400], 0.15)
          : colors.primary[100],
        color: theme.palette.mode === "dark" ? colors.primary[300] : colors.primary[800],
        "&:hover": {
          backgroundColor: theme.palette.mode === "dark"
            ? alpha(colors.primary[400], 0.25)
            : colors.primary[200],
        },
      }),
    },
  },
  MuiAccordion: {
    styleOverrides: {
      root: ({ theme }) => ({
        borderRadius: 8,
        marginBottom: 8,
        backgroundColor: theme.palette.mode === "dark" ? colors.neutral[900] : colors.neutral[100],
        border: theme.palette.mode === "dark"
          ? `1px solid ${colors.neutral[800]}`
          : `1px solid ${colors.neutral[200]}`,
        boxShadow: "none",
        "&:before": {
          display: "none",
        },
        "&.Mui-expanded": {
          margin: "0 0 8px 0",
        },
      }),
    },
  },
  MuiAppBar: {
    styleOverrides: {
      root: ({ theme }) => ({
        backgroundColor: theme.palette.background.paper,
        color: theme.palette.text.primary,
        borderBottom: `1px solid ${theme.palette.divider}`,
        boxShadow: "none",
      }),
    },
  },
  MuiTabs: {
    styleOverrides: {
      indicator: ({ theme }) => ({
        height: 3,
        borderRadius: 3,
        backgroundColor: theme.palette.primary.main,
      }),
    },
  },
  MuiTab: {
    styleOverrides: {
      root: ({ theme }) => ({
        textTransform: "none",
        fontWeight: 600,
        fontSize: "0.95rem",
        borderRadius: 8,
        margin: "0 4px",
        minHeight: 48,
        ...(theme.palette.mode === "dark" && {
          color: colors.neutral[400],
        }),
        "&:hover": {
          backgroundColor: theme.palette.mode === "dark"
            ? alpha(colors.primary[400], 0.08)
            : alpha(colors.primary[500], 0.04),
          ...(theme.palette.mode === "dark" && {
            color: colors.neutral[200],
          }),
        },
        "&.Mui-selected": {
          color: theme.palette.mode === "dark" ? colors.primary[400] : colors.primary[700],
        },
      }),
    },
  },
  MuiListItemButton: {
    styleOverrides: {
      root: ({ theme }) => ({
        borderRadius: 8,
        margin: "2px 8px",
        "&.Mui-selected": {
          backgroundColor: theme.palette.mode === "dark"
            ? alpha(colors.primary[400], 0.15)
            : alpha(colors.primary[700], 0.08),
          color: theme.palette.mode === "dark" ? colors.primary[300] : colors.primary[800],
          "&:hover": {
            backgroundColor: theme.palette.mode === "dark"
              ? alpha(colors.primary[400], 0.2)
              : alpha(colors.primary[700], 0.12),
          },
        },
        "&:hover": {
          backgroundColor: theme.palette.mode === "dark"
            ? alpha(colors.neutral[50], 0.04)
            : alpha(colors.neutral[500], 0.04),
        },
      }),
    },
  },
  MuiIconButton: {
    styleOverrides: {
      root: ({ theme }) => ({
        borderRadius: 10,
        transition: "background-color 0.15s ease, color 0.15s ease",
        ...reducedMotion,
        ...(theme.palette.mode === "dark" && {
          color: colors.neutral[400],
        }),
        "&:hover": {
          backgroundColor: theme.palette.mode === "dark"
            ? alpha(colors.neutral[50], 0.08)
            : alpha(colors.neutral[500], 0.08),
          ...(theme.palette.mode === "dark" && {
            color: colors.neutral[200],
          }),
        },
      }),
    },
  },
  MuiSwitch: {
    styleOverrides: {
      root: ({ theme }) => ({
        width: 42,
        height: 26,
        padding: 0,
        "& .MuiSwitch-switchBase": {
          padding: 1,
          "&.Mui-checked": {
            transform: "translateX(16px)",
            color: "#fff",
            "& + .MuiSwitch-track": {
              backgroundColor: colors.primary[500],
              opacity: 1,
            },
          },
        },
        "& .MuiSwitch-thumb": {
          boxSizing: "border-box",
          width: 24,
          height: 24,
          ...(theme.palette.mode === "dark"
            ? {
                backgroundColor: colors.neutral[100],
                boxShadow: "0 2px 4px 0 rgba(0,0,0,0.4)",
              }
            : {
                boxShadow: "0 2px 4px 0 rgba(0,35,11,0.2)",
              }),
        },
        "& .MuiSwitch-track": {
          borderRadius: 13,
          backgroundColor: theme.palette.mode === "dark" ? colors.neutral[600] : colors.neutral[300],
          opacity: 1,
        },
      }),
    },
  },
  MuiTable: {
    styleOverrides: {
      root: ({ theme }) => ({
        ...(theme.palette.mode === "dark" && {
          borderCollapse: "separate",
        }),
      }),
    },
  },
  MuiTableHead: {
    styleOverrides: {
      root: {
        backgroundColor: 'inherit',
      },
    },
  },
  MuiTableRow: {
    styleOverrides: {
      root: ({ theme }) => ({
        ...(theme.palette.mode === "dark" && {
          backgroundColor: colors.neutral[900],
          "&:nth-of-type(odd)": {
            backgroundColor: alpha(colors.neutral[800], 0.5),
          },
        }),
      }),
    },
  },
  MuiTableCell: {
    styleOverrides: {
      root: ({ theme }) => ({
        ...(theme.palette.mode === "dark" && {
          borderBottom: `1px solid ${colors.neutral[800]}`,
        }),
      }),
      head: ({ theme }) => ({
        ...(theme.palette.mode === "dark" && {
          fontWeight: 600,
          color: colors.primary[300],
        }),
      }),
      body: ({ theme }) => ({
        ...(theme.palette.mode === "dark" && {
          color: colors.neutral[300],
        }),
      }),
    },
  },
  MuiSkeleton: {
    styleOverrides: {
      root: ({ theme }) => ({
        backgroundColor: theme.palette.mode === "dark"
          ? alpha(colors.neutral[50], 0.08)
          : alpha(colors.neutral[900], 0.08),
        "&::after": {
          background: theme.palette.mode === "dark"
            ? `linear-gradient(90deg, transparent, ${alpha(colors.neutral[50], 0.04)}, transparent)`
            : `linear-gradient(90deg, transparent, ${alpha(colors.neutral[900], 0.04)}, transparent)`,
        },
      }),
    },
  },
  MuiAlert: {
    styleOverrides: {
      root: {
        borderRadius: 8,
      },
      filledSuccess: createFilledAlertStyle(colors.success[600]),
      filledError: createFilledAlertStyle(colors.error[600]),
      filledWarning: createFilledAlertStyle(colors.secondary[600]),
      filledInfo: createFilledAlertStyle(colors.success[600]),
    },
  },
};

const lightShadows = [
  "none",
  "0px 1px 2px rgba(0, 0, 0, 0.05)",
  "0px 1px 3px rgba(0, 0, 0, 0.1), 0px 1px 2px rgba(0, 0, 0, 0.06)",
  "0px 4px 6px -1px rgba(0, 0, 0, 0.1), 0px 2px 4px -1px rgba(0, 0, 0, 0.06)",
  "0px 10px 15px -3px rgba(0, 0, 0, 0.1), 0px 4px 6px -2px rgba(0, 0, 0, 0.05)",
  "0px 20px 25px -5px rgba(0, 0, 0, 0.1), 0px 10px 10px -5px rgba(0, 0, 0, 0.04)",
  "0px 25px 50px -12px rgba(0, 0, 0, 0.25)",
  ...Array(18).fill("none"),
];

const darkShadows = [
  "none",
  "0px 1px 2px rgba(0, 0, 0, 0.3)",
  "0px 1px 3px rgba(0, 0, 0, 0.4), 0px 1px 2px rgba(0, 0, 0, 0.3)",
  "0px 4px 6px -1px rgba(0, 0, 0, 0.4), 0px 2px 4px -1px rgba(0, 0, 0, 0.3)",
  "0px 10px 15px -3px rgba(0, 0, 0, 0.4), 0px 4px 6px -2px rgba(0, 0, 0, 0.3)",
  "0px 20px 25px -5px rgba(0, 0, 0, 0.4), 0px 10px 10px -5px rgba(0, 0, 0, 0.2)",
  "0px 25px 50px -12px rgba(0, 0, 0, 0.6)",
  ...Array(18).fill("none"),
];

const baseThemeOptions = {
  typography,
  shape,
  components,
};

export const lightTheme = createTheme({
  ...baseThemeOptions,
  palette: lightPalette,
  shadows: lightShadows,
});

export const darkTheme = createTheme({
  ...baseThemeOptions,
  palette: darkPalette,
  shadows: darkShadows,
});

export { colors };
