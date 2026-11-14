import * as Cesium from 'cesium';
import { msg, t } from '../../i18n/index.js';
import { useSarHavenPanelStore } from '../../ui/stores/sarHavenPanel.js';

export const SAR_HAVEN_LAYER_ID = 'sar-haven';

const FLOOD_FILL = Cesium.Color.fromCssColorString('#d88934').withAlpha(0.55);
const FLOOD_OUTLINE = Cesium.Color.fromCssColorString('#ffad55');
const SAFE_ZONE_FILL = Cesium.Color.fromCssColorString('#2ea043').withAlpha(0.50);
const SAFE_ZONE_OUTLINE = Cesium.Color.fromCssColorString('#3fb950');
const MICROZONE_FILL = Cesium.Color.fromCssColorString('#f0883e').withAlpha(0.60);
const MICROZONE_OUTLINE = Cesium.Color.fromCssColorString('#ffa657');
const CORRIDOR_COLOR = Cesium.Color.fromCssColorString('#20e7f2');

export function createSarHavenLayer({
  source,
} = {}) {
  let _viewer = null;
  let _enabled = false;
  let _dataSource = null;
  let _snapshot = null;
  let _lastUpdate = null;
  let _panelStore = null;

  let _params = {
    showFlood: true,
    showSafeZones: true,
    showMicrozones: true,
    showCorridors: true,
  };

  const getPanelStore = () => {
    if (!_panelStore) {
      _panelStore = useSarHavenPanelStore();
    }
    return _panelStore;
  };

  function ringToCartesians(ring) {
    const cartesians = [];
    for (const [lon, lat] of ring) {
      cartesians.push(Cesium.Cartesian3.fromDegrees(lon, lat));
    }
    return cartesians;
  }

  function clearVisuals() {
    if (_dataSource) {
      _dataSource.entities.removeAll();
    }
  }

  function renderVisuals() {
    if (!_dataSource || !_snapshot) return;
    clearVisuals();

    const { floodExtent, safeZones, dryMicrozones, safeCorridors, timestamp } = _snapshot;

    // 1. SAR Flood Extent Polygons
    if (_params.showFlood && floodExtent?.features) {
      for (const feat of floodExtent.features) {
        const coords = feat.geometry?.coordinates;
        if (!coords || !coords[0]) continue;
        const hierarchy = new Cesium.PolygonHierarchy(ringToCartesians(coords[0]));
        _dataSource.entities.add({
          name: `Flood Extent (${feat.properties?.severity || 'Active'})`,
          polygon: {
            hierarchy,
            material: FLOOD_FILL,
            outline: true,
            outlineColor: FLOOD_OUTLINE,
            outlineWidth: 2,
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          },
          properties: feat.properties,
        });
      }
    }

    // 2. Safe Evacuation Corridors
    if (_params.showCorridors && safeCorridors?.features) {
      for (const feat of safeCorridors.features) {
        const coords = feat.geometry?.coordinates;
        if (!coords || coords.length < 2) continue;
        const positions = coords.map(([lon, lat]) => Cesium.Cartesian3.fromDegrees(lon, lat));
        _dataSource.entities.add({
          name: feat.properties?.name || 'Safe Dry Corridor',
          polyline: {
            positions,
            width: 4,
            material: CORRIDOR_COLOR,
            clampToGround: true,
          },
          properties: feat.properties,
        });
      }
    }

    // 3. Safe Zones
    if (_params.showSafeZones && safeZones?.features) {
      for (const feat of safeZones.features) {
        const props = feat.properties || {};
        const coords = feat.geometry?.coordinates;
        if (!coords || !coords[0]) continue;

        const hierarchy = new Cesium.PolygonHierarchy(ringToCartesians(coords[0]));
        // Label anchor near first coordinate
        const anchor = coords[0][0];
        const position = Cesium.Cartesian3.fromDegrees(anchor[0], anchor[1], (props.elevation_m || 1000) + 15);

        _dataSource.entities.add({
          id: `safe-zone-${props.safe_zone_id}`,
          name: props.name,
          polygon: {
            hierarchy,
            material: SAFE_ZONE_FILL,
            outline: true,
            outlineColor: SAFE_ZONE_OUTLINE,
            outlineWidth: 2,
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          },
          position,
          point: {
            pixelSize: 10,
            color: SAFE_ZONE_OUTLINE,
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2,
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          },
          label: {
            text: `#${props.rank} SAFE: ${props.name}\n+${props.height_above_flood_m}m above flood (${props.capacity_people} ppl)`,
            font: 'bold 11px "JetBrains Mono", monospace',
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 3,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new Cesium.Cartesian2(0, -12),
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
          properties: props,
        });
      }
    }

    // 4. Guaranteed Dry Microzones (Staging)
    if (_params.showMicrozones && dryMicrozones?.features) {
      for (const feat of dryMicrozones.features) {
        const props = feat.properties || {};
        const coords = feat.geometry?.coordinates;
        if (!coords || !coords[0]) continue;

        const hierarchy = new Cesium.PolygonHierarchy(ringToCartesians(coords[0]));
        const anchor = coords[0][0];
        const position = Cesium.Cartesian3.fromDegrees(anchor[0], anchor[1], (props.elevation_m || 1000) + 10);

        _dataSource.entities.add({
          id: `microzone-${props.microzone_id}`,
          name: props.name,
          polygon: {
            hierarchy,
            material: MICROZONE_FILL,
            outline: true,
            outlineColor: MICROZONE_OUTLINE,
            outlineWidth: 2,
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          },
          position,
          label: {
            text: `⛺ RELIEF STAGING: ${props.name}\nWater · Food · Power · Med`,
            font: 'bold 10px "JetBrains Mono", monospace',
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            fillColor: Cesium.Color.YELLOW,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 3,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new Cesium.Cartesian2(0, -10),
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
          properties: props,
        });
      }
    }

    if (_viewer?.scene) {
      _viewer.scene.requestRender();
    }
  }

  function publishPanelState() {
    const store = getPanelStore();
    if (!store) return;

    if (!_enabled || !_snapshot) {
      store.publish(null);
      store.connect(null);
      return;
    }

    const { metadata, safeZones, dryMicrozones, timestamp } = _snapshot;

    store.publish({
      active: true,
      sarPassUtc: timestamp,
      honestyLabel: `Latest SAR pass: ${timestamp} (Sentinel-1 GRD IW)`,
      metadata,
      sublayers: { ..._params },
      safeZones: safeZones?.features?.map((f) => f.properties) || [],
      microzones: dryMicrozones?.features?.map((f) => f.properties) || [],
    });

    store.connect({
      toggleSublayer: (key) => {
        _params[key] = !_params[key];
        renderVisuals();
        publishPanelState();
      },
      flyToSafeZone: (szId) => {
        if (!_viewer || !_snapshot?.safeZones?.features) return;
        const target = _snapshot.safeZones.features.find((f) => f.properties?.safe_zone_id === szId);
        if (!target) return;
        const coords = target.geometry.coordinates[0][0];
        _viewer.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(coords[0], coords[1], 4500),
          orientation: {
            heading: Cesium.Math.toRadians(0),
            pitch: Cesium.Math.toRadians(-45),
            roll: 0.0,
          },
          duration: 2.0,
        });
      },
      flyToCorridor: () => {
        if (!_viewer) return;
        _viewer.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(85.26, 28.05, 32000),
          orientation: {
            heading: Cesium.Math.toRadians(12),
            pitch: Cesium.Math.toRadians(-50),
            roll: 0.0,
          },
          duration: 2.5,
        });
      },
    });
  }

  return {
    id: SAR_HAVEN_LAYER_ID,
    name: 'SAR Flood Safe-Haven',
    icon: 'water_drop',
    source: 'Copernicus Sentinel-1 SAR + DEM + OSM',

    async init(viewer) {
      _viewer = viewer;
      _dataSource = new Cesium.CustomDataSource('sar-haven-data');
      await _viewer.dataSources.add(_dataSource);
      return true;
    },

    async enable() {
      _enabled = true;
      if (_dataSource) _dataSource.show = true;
      try {
        _snapshot = await source.getSnapshot();
        _lastUpdate = Date.now();
        renderVisuals();
        publishPanelState();
        return true;
      } catch (err) {
        console.error('Failed to load SAR Haven snapshot:', err);
        return false;
      }
    },

    async disable() {
      _enabled = false;
      if (_dataSource) _dataSource.show = false;
      publishPanelState();
      return true;
    },

    async update() {
      if (!_enabled) return true;
      try {
        _snapshot = await source.getSnapshot();
        _lastUpdate = Date.now();
        renderVisuals();
        publishPanelState();
        return true;
      } catch {
        return false;
      }
    },

    destroy() {
      if (_viewer && _dataSource) {
        _viewer.dataSources.remove(_dataSource, true);
        _dataSource = null;
      }
      _viewer = null;
      publishPanelState();
    },

    setParams(next = {}) {
      _params = { ..._params, ...next };
      renderVisuals();
      publishPanelState();
      return true;
    },

    getParams() {
      return { ..._params };
    },

    getStats() {
      const szCount = _snapshot?.safeZones?.features?.length || 8;
      const passTime = _snapshot?.timestamp || '2026-08-27T00:15:32Z';
      return {
        count: szCount,
        countLabel: `${szCount} havens · SAR ${passTime.slice(11, 16)}Z`,
        lastUpdate: _lastUpdate,
      };
    },
  };
}

