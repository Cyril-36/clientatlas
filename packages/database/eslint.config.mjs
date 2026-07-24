import { defineConfig, globalIgnores } from "eslint/config";
import typescriptEslint from "typescript-eslint";

export default defineConfig([
  ...typescriptEslint.configs.recommended,
  globalIgnores([
    "node_modules/**",
    "coverage/**",
    "migrations/generated/**"
  ])
]);

