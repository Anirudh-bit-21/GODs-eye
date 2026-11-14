import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url));
const dataDir = path.join(root, 'data', 'nepal');

function readJsonFile(filename) {
  const p = path.join(dataDir, filename);
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

export function sarHavenProxy() {
  return {
    name: 'sar-haven-provider',
    configureServer(server) {
      server.middlewares.use('/api/sar-haven', (req, res, next) => {
        const url = new URL(req.url, 'http://localhost');
        const pathname = url.pathname.replace(/^\//, '');

        if (pathname === 'metadata' || pathname === '') {
          const data = readJsonFile('metadata.json');
          if (!data) {
            res.statusCode = 404;
            return res.end(JSON.stringify({ error: 'Metadata not found' }));
          }
          res.setHeader('Content-Type', 'application/json');
          return res.end(JSON.stringify(data));
        }

        if (pathname === 'flood-extent') {
          const data = readJsonFile('flood_extent.geojson');
          if (!data) {
            res.statusCode = 404;
            return res.end(JSON.stringify({ error: 'Flood extent not found' }));
          }
          res.setHeader('Content-Type', 'application/json');
          return res.end(JSON.stringify(data));
        }

        if (pathname === 'safe-zones') {
          const data = readJsonFile('safe_zones.geojson');
          if (!data) {
            res.statusCode = 404;
            return res.end(JSON.stringify({ error: 'Safe zones not found' }));
          }
          res.setHeader('Content-Type', 'application/json');
          return res.end(JSON.stringify(data));
        }

        if (pathname === 'dry-microzones') {
          const data = readJsonFile('dry_microzones.geojson');
          if (!data) {
            res.statusCode = 404;
            return res.end(JSON.stringify({ error: 'Dry microzones not found' }));
          }
          res.setHeader('Content-Type', 'application/json');
          return res.end(JSON.stringify(data));
        }

        if (pathname === 'safe-corridors') {
          const data = readJsonFile('safe_corridors.geojson');
          if (!data) {
            res.statusCode = 404;
            return res.end(JSON.stringify({ error: 'Safe corridors not found' }));
          }
          res.setHeader('Content-Type', 'application/json');
          return res.end(JSON.stringify(data));
        }

        if (pathname === 'road-graph') {
          const data = readJsonFile('road_graph.json');
          if (!data) {
            res.statusCode = 404;
            return res.end(JSON.stringify({ error: 'Road graph not found' }));
          }
          res.setHeader('Content-Type', 'application/json');
          return res.end(JSON.stringify(data));
        }

        if (pathname === 'dem-corridor') {
          const data = readJsonFile('dem_corridor.json');
          if (!data) {
            res.statusCode = 404;
            return res.end(JSON.stringify({ error: 'DEM corridor not found' }));
          }
          res.setHeader('Content-Type', 'application/json');
          return res.end(JSON.stringify(data));
        }

        next();
      });
    },
  };
}

