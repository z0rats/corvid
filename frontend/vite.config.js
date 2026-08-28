import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    strictPort: true,
  },
  build: {
    outDir: 'build',
    assetsDir: 'static',
    sourcemap: false,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/setupTests.js'],
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      reportsDirectory: './coverage',
      // `all` + `include` make every src file count toward the denominator,
      // not just ones some test happens to import - without this, a file no
      // test ever touches (directly or transitively) is invisible to the
      // report rather than showing up as 0%, which quietly inflates the
      // percentage as untested surface grows.
      all: true,
      include: ['src/**/*.{js,jsx,ts,tsx}'],
    },
  },
});
