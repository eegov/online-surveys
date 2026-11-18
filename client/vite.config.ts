import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  server: {
    // В разработке клиент на 5173, сервер на 8080: /api проксируется,
    // поэтому клиент и сервер для браузера на одном адресе, как за Nginx в эксплуатации.
    proxy: {
      '/api': 'http://localhost:8080',
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    reporters: ['default', 'junit'],
    outputFile: { junit: './reports/junit.xml' },
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/main.tsx', 'src/test/**', 'src/**/*.test.{ts,tsx}'],
      reporter: ['text', 'json-summary', 'html', 'lcov'],
      reportsDirectory: './coverage',
    },
  },
});
