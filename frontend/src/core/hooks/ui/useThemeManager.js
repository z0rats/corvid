import { useCallback, useMemo } from 'react';
import { useAtom } from 'jotai';
import { themeModeAtom } from '../../state/atoms';
import { lightTheme, darkTheme } from '../../config/theme';

export function useThemeManager() {
  const [mode, setMode] = useAtom(themeModeAtom);

  const toggleColorMode = useCallback(() => {
    setMode((prevMode) => prevMode === 'light' ? 'dark' : 'light');
  }, [setMode]);

  const theme = useMemo(() => (mode === 'light' ? lightTheme : darkTheme), [mode]);

  return { mode, theme, toggleColorMode };
}
