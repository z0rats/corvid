import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import AccessGate from "./core/components/ui/AccessGate";
import HealthCheck from "./core/components/ui/HealthCheck";
import { AppRoutes } from "./core/config/routes";
import { useAppSettings } from "./core/hooks/api/useAppSettings";
import { useThemeManager } from "./core/hooks/ui/useThemeManager";

function App() {
  useAppSettings();

  const { theme } = useThemeManager();

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AccessGate>
        <HealthCheck>
          <AppRoutes />
        </HealthCheck>
      </AccessGate>
    </ThemeProvider>
  );
}

export default App;
