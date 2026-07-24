import { readdir, readFile } from "node:fs/promises";
import { join, relative } from "node:path";

const root = process.cwd();
const ignored = new Set([".git", ".next", ".venv", "node_modules"]);
const patterns = [
  /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/,
  /\bAIza[0-9A-Za-z_-]{35}\b/,
  /\bgh[pousr]_[0-9A-Za-z]{36,255}\b/,
  /\bsk-(?:live|proj)-[0-9A-Za-z_-]{20,}\b/,
  /\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b/
];
const violations = [];

async function walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (ignored.has(entry.name)) continue;
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      await walk(path);
      continue;
    }
    if (entry.name.endsWith(".lock") || entry.name === "package-lock.json") continue;
    let source;
    try {
      source = await readFile(path, "utf8");
    } catch {
      continue;
    }
    for (const pattern of patterns) {
      if (pattern.test(source)) {
        violations.push(`${relative(root, path)}: possible committed secret`);
      }
    }
  }
}

await walk(root);
if (violations.length) {
  process.stderr.write(`${violations.join("\n")}\n`);
  process.exitCode = 1;
} else {
  process.stdout.write("Secret patterns not detected.\n");
}
