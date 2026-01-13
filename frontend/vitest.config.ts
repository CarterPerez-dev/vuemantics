// ===================
// © AngelaMos | 2025
// vitest.config.ts
// ===================

import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      globals: true,
      environment: 'jsdom',
      css: true,
    },
  })
)
