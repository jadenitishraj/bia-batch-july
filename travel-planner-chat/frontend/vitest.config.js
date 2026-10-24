import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.test.js'],
    restoreMocks: true,
    coverage: {
      provider: 'v8',
      include: ['src/**/*.js'],
      exclude: [],
      reporter: ['text', 'json-summary'],
      thresholds: { statements: 90, branches: 90, functions: 90, lines: 90 },
    },
  },
});
