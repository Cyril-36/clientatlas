import { readdir, readFile } from "node:fs/promises";
import { extname, join, relative } from "node:path";

const root = process.cwd();
const ignored = new Set([".git", ".next", ".venv", "node_modules"]);
const violations = [];

async function walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (ignored.has(entry.name)) continue;
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      await walk(path);
      continue;
    }
    const projectPath = relative(root, path);
    if (
      /(^|\/)(page|layout)\.(tsx|jsx)$/.test(projectPath) ||
      extname(path) === ".css"
    ) {
      violations.push(`${projectPath}: frontend file is forbidden`);
    }
    if (
      /apps\/product-api\/(app|src)\//.test(projectPath) &&
      [".ts", ".tsx"].includes(extname(path))
    ) {
      const source = await readFile(path, "utf8");
      if (/service[_-]?role|MIGRATION_DATABASE_URL/i.test(source)) {
        violations.push(`${projectPath}: privileged credential reference`);
      }
    }
  }
}

await walk(root);
if (violations.length) {
  process.stderr.write(`${violations.join("\n")}\n`);
  process.exitCode = 1;
} else {
  process.stdout.write("Architecture invariants passed.\n");
}
