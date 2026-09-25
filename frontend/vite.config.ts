import { defineConfig } from "vite";
import type { Plugin } from "vite";
import react from "@vitejs/plugin-react";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const maplibreDist = fileURLToPath(
  new URL("./node_modules/maplibre-gl/dist/", import.meta.url),
);
const maplibreWorkerFiles = [
  "maplibre-gl-worker.mjs",
  "maplibre-gl-shared.mjs",
] as const;

function maplibreWorkerAssets(): Plugin {
  return {
    name: "maplibre-worker-assets",
    configureServer(server) {
      server.middlewares.use((request, response, next) => {
        const requestedFile = maplibreWorkerFiles.find(
          (file) => request.url?.split("?", 1)[0] === `/assets/${file}`,
        );
        if (!requestedFile) return next();
        response.statusCode = 200;
        response.setHeader("Content-Type", "application/javascript");
        response.end(readFileSync(join(maplibreDist, requestedFile)));
      });
    },
    generateBundle() {
      for (const file of maplibreWorkerFiles) {
        this.emitFile({
          type: "asset",
          fileName: `assets/${file}`,
          source: readFileSync(join(maplibreDist, file)),
        });
      }
    },
  };
}

export default defineConfig({ plugins: [react(), maplibreWorkerAssets()] });
