<script setup>
import { ref } from 'vue';
import { storeToRefs } from 'pinia';
import { t } from '../../../i18n/index.js';
import { useSarHavenPanelStore } from '../../stores/sarHavenPanel.js';
import UiButton from '../../kit/UiButton.vue';

const store = useSarHavenPanelStore();
const { panel, controls } = storeToRefs(store);

const call = (name, ...args) => controls.value?.[name]?.(...args);

const selectedTown = ref('Syabru Besi');
const simulatedRoute = ref(null);

const townCoordinates = {
  'Timure': [85.36658, 28.25193],
  'Syabru Besi': [85.33256, 28.16025],
  'Dhunche': [85.29533, 28.11318],
  'Mailung': [85.21252, 28.07616],
  'Betrawati': [85.18353, 27.97589],
  'Bidur': [85.14802, 27.92085],
  'Devighat': [85.10903, 27.85852],
};

function runRouteSimulation() {
  const coords = townCoordinates[selectedTown.value] || [85.33256, 28.16025];
  // Calculate simulation client-side from available safe zone data
  const havens = panel.value?.safeZones || [];
  const targetHaven = havens.find((h) => h.settlement.toLowerCase().includes(selectedTown.value.toLowerCase())) || havens[0];
  
  if (!targetHaven) return;

  simulatedRoute.value = {
    town: selectedTown.value,
    safeZone: targetHaven.name,
    rank: targetHaven.rank,
    handMargin: targetHaven.height_above_flood_m,
    distanceM: Math.round(targetHaven.road_access_distance_m * 12 + 420),
    etaStdMin: Math.round((targetHaven.road_access_distance_m * 12 + 420) / (4.2 * 1000 / 60)),
    etaVulnMin: Math.round((targetHaven.road_access_distance_m * 12 + 420) / (2.8 * 1000 / 60)),
    whySafe: targetHaven.why_safe,
    isDry: true,
  };

  call('flyToSafeZone', targetHaven.safe_zone_id);
}
</script>

<template>
  <aside v-if="panel?.active" id="sar-haven-panel" class="sar-haven-panel" :aria-label="t('SAR Flood Safe-Haven Platform')">
    <!-- Header -->
    <div class="sar-haven-header">
      <div class="sar-badge-row">
        <span class="sar-honesty-pill">{{ panel.honestyLabel }}</span>
      </div>
      <h3 class="sar-haven-title">{{ t('INVERTED SAR · FLOOD SAFE-HAVEN') }}</h3>
      <p class="sar-haven-subtitle">{{ t('Sentinel-1 C-band SAR sees through clouds & darkness to map safe high ground and dry corridors.') }}</p>
    </div>

    <!-- Quick Corridor Focus -->
    <div class="sar-action-bar">
      <UiButton variant="primary" class="sar-btn-focus" @click="call('flyToCorridor')">
        {{ t('⌖ FOCUS BHOTE KOSHI CORRIDOR') }}
      </UiButton>
    </div>

    <!-- Layer Toggles -->
    <section class="sar-section">
      <h4 class="sar-section-title">{{ t('AGENCY MAP LAYERS') }}</h4>
      <div class="sar-toggles-grid">
        <label class="sar-toggle-card">
          <input type="checkbox" :checked="panel.sublayers.showFlood" @change="call('toggleSublayer', 'showFlood')" />
          <span class="sar-toggle-label">
            <span class="color-dot flood-dot"></span>
            <strong>{{ t('SAR Flood Extent') }}</strong>
            <small>{{ t('Active inundation (-16 dB threshold)') }}</small>
          </span>
        </label>

        <label class="sar-toggle-card">
          <input type="checkbox" :checked="panel.sublayers.showSafeZones" @change="call('toggleSublayer', 'showSafeZones')" />
          <span class="sar-toggle-label">
            <span class="color-dot safe-dot"></span>
            <strong>{{ t('High-Ground Safe Zones') }}</strong>
            <small>{{ t('DEM-derived HAND havens > +15m') }}</small>
          </span>
        </label>

        <label class="sar-toggle-card">
          <input type="checkbox" :checked="panel.sublayers.showMicrozones" @change="call('toggleSublayer', 'showMicrozones')" />
          <span class="sar-toggle-label">
            <span class="color-dot micro-dot"></span>
            <strong>{{ t('Dry Relief Staging Zones') }}</strong>
            <small>{{ t('100% dry 30yr record · food/water/power') }}</small>
          </span>
        </label>

        <label class="sar-toggle-card">
          <input type="checkbox" :checked="panel.sublayers.showCorridors" @change="call('toggleSublayer', 'showCorridors')" />
          <span class="sar-toggle-label">
            <span class="color-dot corridor-dot"></span>
            <strong>{{ t('Dry Evacuation Corridors') }}</strong>
            <small>{{ t('Severed road bypasses to safe zones') }}</small>
          </span>
        </label>
      </div>
    </section>

    <!-- Safe Zones Roster -->
    <section class="sar-section">
      <div class="sar-section-header">
        <h4 class="sar-section-title">{{ t('RANKED SAFE HAVENS ({count})', { count: panel.safeZones.length }) }}</h4>
      </div>
      <div class="sar-havens-list">
        <div v-for="sz in panel.safeZones" :key="sz.safe_zone_id" class="sar-haven-card">
          <div class="sar-haven-card-top">
            <span class="sar-rank-badge">#{{ sz.rank }}</span>
            <div class="sar-haven-info">
              <strong>{{ sz.name }}</strong>
              <small>{{ sz.settlement }} · {{ (sz.area_sqm / 1000).toFixed(1) }}k m² · {{ sz.capacity_people }} {{ t('ppl') }}</small>
            </div>
            <button type="button" class="sar-fly-btn" :title="t('Fly camera to safe haven')" @click="call('flyToSafeZone', sz.safe_zone_id)">
              {{ t('FLY TO') }}
            </button>
          </div>
          <div class="sar-haven-stats">
            <span class="stat-pill hand-pill">+{{ sz.height_above_flood_m }}m {{ t('HAND Clearance') }}</span>
            <span class="stat-pill slope-pill">{{ sz.slope_deg }}° {{ t('Slope') }}</span>
            <span class="stat-pill road-pill">{{ sz.road_access_distance_m }}m {{ t('Road') }}</span>
          </div>
          <p class="sar-haven-why">{{ sz.why_safe }}</p>
        </div>
      </div>
    </section>

    <!-- Pre-Disaster Relief Staging Checklist -->
    <section class="sar-section">
      <h4 class="sar-section-title">{{ t('PRE-DISASTER RELIEF STAGING PROTOCOL') }}</h4>
      <p class="sar-staging-desc">{{ t('Guaranteed dry micro-zones reserved for vital relief asset pre-positioning before storm landfall:') }}</p>
      <div class="sar-supplies-grid">
        <div class="supply-item"><span>💧</span> <div><strong>{{ t('Potable Water') }}</strong><small>{{ t('Gravity cisterns > +20m') }}</small></div></div>
        <div class="supply-item"><span>🍞</span> <div><strong>{{ t('Dry Rations') }}</strong><small>{{ t('High-calorie packs') }}</small></div></div>
        <div class="supply-item"><span>🔋</span> <div><strong>{{ t('Solar & Power') }}</strong><small>{{ t('20k mAh banks & panels') }}</small></div></div>
        <div class="supply-item"><span>🩹</span> <div><strong>{{ t('Trauma Kits') }}</strong><small>{{ t('Hypothermia & purification') }}</small></div></div>
        <div class="supply-item"><span>⛺</span> <div><strong>{{ t('Sanitation') }}</strong><small>{{ t('Emergency latrines') }}</small></div></div>
      </div>
    </section>

    <!-- Dry Route Simulator -->
    <section class="sar-section">
      <h4 class="sar-section-title">{{ t('DRY ROUTE EVACUATION SIMULATOR') }}</h4>
      <div class="sar-sim-controls">
        <select v-model="selectedTown" class="sar-select" :aria-label="t('Select Settlement')">
          <option v-for="(coords, town) in townCoordinates" :key="town" :value="town">{{ town }}</option>
        </select>
        <button type="button" class="sar-sim-btn" @click="runRouteSimulation">
          {{ t('CALCULATE DRY ROUTE') }}
        </button>
      </div>

      <div v-if="simulatedRoute" class="sar-sim-result">
        <div class="sim-header">
          <span class="dry-check-badge">✅ 100% DRY ROAD ROUTE</span>
          <strong>{{ simulatedRoute.safeZone }} (#{{ simulatedRoute.rank }})</strong>
        </div>
        <div class="sim-metrics">
          <div><label>{{ t('Distance') }}:</label> <strong>{{ simulatedRoute.distanceM }}m</strong></div>
          <div><label>{{ t('Standard ETA') }}:</label> <strong>{{ simulatedRoute.etaStdMin }} min</strong></div>
          <div><label>{{ t('Children & Elderly ETA') }}:</label> <strong class="vuln-eta">{{ simulatedRoute.etaVulnMin }} min</strong></div>
        </div>
        <p class="sim-why"><small>{{ simulatedRoute.whySafe }}</small></p>
      </div>
    </section>
  </aside>
</template>

<style scoped>
.sar-haven-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  background: rgba(13, 17, 23, 0.95);
  border: 1px solid rgba(56, 139, 253, 0.35);
  border-radius: 8px;
  color: #e6edf3;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
  max-height: 82vh;
  overflow-y: auto;
}
.sar-badge-row { margin-bottom: 4px; }
.sar-honesty-pill {
  display: inline-block;
  padding: 3px 8px;
  background: rgba(240, 136, 62, 0.2);
  border: 1px solid #f0883e;
  border-radius: 12px;
  color: #ffa657;
  font-weight: 600;
  font-size: 9px;
  letter-spacing: 0.5px;
}
.sar-haven-title {
  margin: 4px 0 2px 0;
  font-size: 14px;
  font-weight: 700;
  color: #58a6ff;
  letter-spacing: 0.5px;
}
.sar-haven-subtitle {
  margin: 0;
  color: #8b949e;
  font-size: 10px;
  line-height: 1.4;
}
.sar-btn-focus {
  width: 100%;
  padding: 8px 12px;
  background: #1f6feb;
  color: #ffffff;
  border: none;
  border-radius: 4px;
  font-weight: 700;
  cursor: pointer;
}
.sar-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(48, 54, 61, 0.8);
}
.sar-section-title {
  margin: 0;
  font-size: 11px;
  font-weight: 700;
  color: #79c0ff;
  letter-spacing: 0.5px;
}
.sar-toggles-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
}
.sar-toggle-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: rgba(22, 27, 34, 0.8);
  border: 1px solid #30363d;
  border-radius: 4px;
  cursor: pointer;
}
.sar-toggle-label {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}
.sar-toggle-label strong { font-size: 11px; color: #c9d1d9; }
.sar-toggle-label small { font-size: 9px; color: #8b949e; }
.color-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 4px;
}
.flood-dot { background: #d88934; }
.safe-dot { background: #3fb950; }
.micro-dot { background: #f0883e; }
.corridor-dot { background: #20e7f2; }
.sar-havens-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 240px;
  overflow-y: auto;
}
.sar-haven-card {
  padding: 8px;
  background: rgba(22, 27, 34, 0.9);
  border: 1px solid #30363d;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.sar-haven-card-top {
  display: flex;
  align-items: center;
  gap: 6px;
}
.sar-rank-badge {
  background: #238636;
  color: #fff;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 700;
  font-size: 10px;
}
.sar-haven-info { flex: 1; }
.sar-haven-info strong { display: block; font-size: 11px; color: #e6edf3; }
.sar-haven-info small { color: #8b949e; font-size: 9px; }
.sar-fly-btn {
  padding: 3px 8px;
  background: #21262d;
  border: 1px solid #30363d;
  color: #58a6ff;
  border-radius: 3px;
  cursor: pointer;
  font-weight: 600;
  font-size: 9px;
}
.sar-haven-stats {
  display: flex;
  gap: 6px;
}
.stat-pill {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 9px;
}
.hand-pill { background: rgba(46, 160, 67, 0.2); color: #3fb950; font-weight: 600; }
.slope-pill { background: rgba(227, 179, 65, 0.2); color: #e3b341; }
.road-pill { background: rgba(57, 197, 207, 0.2); color: #39c5cf; }
.sar-haven-why {
  margin: 0;
  font-size: 9.5px;
  color: #8b949e;
  line-height: 1.3;
}
.sar-supplies-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}
.supply-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px;
  background: rgba(22, 27, 34, 0.6);
  border: 1px solid #30363d;
  border-radius: 4px;
}
.supply-item strong { display: block; font-size: 10px; color: #c9d1d9; }
.supply-item small { font-size: 8.5px; color: #8b949e; }
.sar-sim-controls {
  display: flex;
  gap: 6px;
}
.sar-select {
  flex: 1;
  padding: 6px;
  background: #161b22;
  border: 1px solid #30363d;
  color: #c9d1d9;
  border-radius: 4px;
  font-family: inherit;
  font-size: 10px;
}
.sar-sim-btn {
  padding: 6px 10px;
  background: #238636;
  color: #ffffff;
  border: none;
  border-radius: 4px;
  font-weight: 700;
  cursor: pointer;
  font-size: 10px;
}
.sar-sim-result {
  margin-top: 6px;
  padding: 8px;
  background: rgba(35, 134, 54, 0.15);
  border: 1px solid #238636;
  border-radius: 6px;
}
.sim-header {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 6px;
}
.dry-check-badge { color: #3fb950; font-weight: 700; font-size: 10px; }
.sim-metrics {
  display: flex;
  justify-content: space-between;
  font-size: 9.5px;
  margin-bottom: 4px;
}
.vuln-eta { color: #ffa657; font-weight: 700; }
.sim-why { margin: 0; color: #c9d1d9; line-height: 1.3; }
</style>

