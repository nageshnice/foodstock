import * as esbuild from "esbuild";
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const dist = join(__dirname, "dist");

mkdirSync(join(dist, "assets"), { recursive: true });

await esbuild.build({
  entryPoints: [join(__dirname, "src", "main.tsx")],
  outfile: join(dist, "assets", "app.js"),
  bundle: true,
  format: "esm",
  platform: "browser",
  jsx: "automatic",
  loader: {
    ".ts": "ts",
    ".tsx": "tsx",
  },
  external: [],
  sourcemap: false,
  minify: true,
  treeShaking: true,
});

let html = readFileSync(join(__dirname, "index.html"), "utf-8");
html = html.replace(
  '<script type="module" src="/src/main.tsx"></script>',
  '<script type="module" src="/admin/assets/app.js"></script>',
);
writeFileSync(join(dist, "index.html"), html);

console.log("Build complete: admin/dist/");
