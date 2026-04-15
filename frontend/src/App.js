import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
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
      <HealthCheck>
        <AppRoutes />
      </HealthCheck>
    </ThemeProvider>
  );
}

export default App;
