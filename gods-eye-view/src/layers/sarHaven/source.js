import { readResponseJsonCapped } from '../../sources/httpBody.js';

export function createSarHavenSource({
  fetchImpl = (...args) => globalThis.fetch(...args),
} = {}) {
  async function fetchJson(endpoint, signal) {
    const res = await fetchImpl(endpoint, { signal });
    if (!res.ok) {
      throw new Error(`SAR Haven endpoint ${endpoint} failed (${res.status})`);
    }
    return readResponseJsonCapped(res, 2 * 1024 * 1024, signal);
  }

  return {
    label: 'Copernicus Sentinel-1 SAR + DEM + OSM',
    async getSnapshot({ signal } = {}) {
      const [metadata, floodExtent, safeZones, dryMicrozones, safeCorridors] = await Promise.all([
        fetchJson('/api/sar-haven/metadata', signal).catch(() => ({})),
        fetchJson('/api/sar-haven/flood-extent', signal),
        fetchJson('/api/sar-haven/safe-zones', signal),
        fetchJson('/api/sar-haven/dry-microzones', signal),
        fetchJson('/api/sar-haven/safe-corridors', signal),
      ]);

      return {
        metadata,
        floodExtent,
        safeZones,
        dryMicrozones,
        safeCorridors,
        timestamp: metadata.sar_latest_pass_utc || '2026-08-27T00:15:32Z',
      };
    },
  };
}

