import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import AccessGate from "./core/components/ui/AccessGate";
import HealthCheck from "./core/components/ui/HealthCheck";
import { AppRoutes } from "./core/config/routes";
import { useAppSettings } from "./core/hooks/api/useAppSettings";
import { useThemeManager } from "./core/hooks/ui/useThemeManager";

// Rendered inside AccessGate, not in App itself: fetched before a token exists, these requests
// all come back 401, and the backend files every 401 as a "Failed access-token attempts"
// security alert - so a fresh install's first screen would open on a false alarm.
function AppSettingsLoader() {
  useAppSettings();
  return null;
}

function App() {
  const { theme } = useThemeManager();

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AccessGate>
        <AppSettingsLoader />
        <HealthCheck>
          <AppRoutes />
        </HealthCheck>
      </AccessGate>
    </ThemeProvider>
  );
}

export default App;
