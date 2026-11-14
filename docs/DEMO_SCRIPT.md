# 3-Minute Hackathon Demo Script: "Dancing with the SARs"
## Inverted SAR Dual-Perspective Flood Safe-Haven Platform
**Target Audience:** NASA Space Apps Challenge Judges  
**Time Limit:** 3 Minutes (180 Seconds)  
**Presenter Roles:** Presenter 1 (Story & Agency Mode) & Presenter 2 (Civilian Mode & Tech)

---

### Phase 1: The Problem & The Inverted SAR Breakthrough (0:00 – 0:45)
**Visual:** Slide 1 or GOD's EYE VIEW 3D globe centered over the Himalayas.

> **Presenter 1:**  
> "When catastrophic floods strike, optical satellites like Landsat or Sentinel-2 are completely blind. They can't see through monsoon clouds, rainstorms, or nighttime darkness.
> 
> "Tragically, statistical post-disaster audits show that **children aged 9 to 14 and older adults suffer the highest mortality rates**. Why? Because every disaster map shows destruction in red, but **nobody shows where it is dry and how to get there**.
> 
> "Our project, **Dancing with the SARs**, inverts this paradigm. Instead of using Synthetic Aperture Radar just to show what drowned, we **invert Sentinel-1 C-band SAR backscatter** and combine it with **Copernicus GLO-30 DEM** to discover **guaranteed dry, accessible Safe Havens** and route vulnerable families to safety."

---

### Phase 2: Agency Mode — 3D Globe Tactical Command (0:45 – 1:45)
**Visual:** Browser at `http://localhost:8080`, Nepal incident scene active. Open the **"SAR SAFE-HAVEN"** panel on the right rail.

> **Presenter 1:**  
> "Here is **Agency Mode**, built directly into God's Eye View for disaster responders, the military, and municipal incident commanders:
> 
> 1. **Verified SAR Flood Extent (Blue overlay):** Delineated from Sentinel-1 GRD IW VV specular reflection through heavy cloud cover. Note our **Honesty Protocol**: every layer explicitly displays `Latest SAR pass: 2026-08-26 12:45 UTC`. We never claim SAR is real-time video.
> 2. **Inverted Safe Havens (Green markers):** 8 multi-criteria ranked safe havens. Each haven is evaluated for **Height Above Nearest Drainage (HAND)**, slope stability (< 16° to prevent landslide traps), and direct road proximity.
> 3. **Relief Staging Micro-Zones (Amber shields):** Guaranteed dry zones identified from 5-year flood recurrence baselines, allowing agencies to pre-stage clean drinking water, high-calorie food, power banks, and medical trauma kits *before* roads are cut off.
> 4. **Safe Corridors (Cyan vs Red paths):** Responders can immediately see where floodwaters have severed 7 critical road segments in the Bhote Koshi / Trishuli gorge, and which high-ridge arteries remain open."

---

### Phase 3: Civilian Mode — Child & Elderly Evacuation PWA (1:45 – 2:30)
**Visual:** Switch to Mobile View / Smartphone screen showing `http://localhost:8080/civilian/` (or `civilian-app/index.html`).

> **Presenter 2:**  
> "Civilians fleeing rising waters cannot interpret complex GIS software on a fragile connection. So we built **Civilian Mode**—a standalone, offline-first Progressive Web App designed specifically for children and older adults:
> 
> 1. **Ultra-Accessible UI:** Meets **WCAG AAA standards**. Giant 72-pixel buttons, high-contrast amber, green, and black, and dual iconography with large text. No confusing menus.
> 2. **One Tap Location:** Tap **'USE MY GPS'** or select your town—like **Syabru Besi Market**.
> 3. **Dual Walking ETA:** We calculate both a standard adult walking speed (4.2 km/h) and a **Child & Elderly walking speed (2.8 km/h)**, taking into account mud, incline, and fear.
> 4. **One Instruction Per Screen:** As you walk, a giant 100-pixel directional arrow guides you step-by-step: *'Step 1: Walk 450 meters uphill away from the river bank.'*
> 5. **'Why is this safe?' transparency:** It clearly explains that the haven is +38 meters above the water line with pre-staged water supplies.
> 6. **100% Offline Resilience:** *(Turn off Wi-Fi in DevTools)* Even with zero cell tower connectivity, the cached road graph and in-browser Dijkstra engine compute safe routes completely offline."

---

### Phase 4: Data Engine & Summary (2:30 – 3:00)
**Visual:** Quick terminal snippet showing `sar-pipeline/route_engine.py` or `sar-pipeline/detect_safe_zones.py`.

> **Presenter 1:**  
> "Under the hood, our pipeline combines:
> - **Copernicus Sentinel-1 SAR** (ESA) with Lee speckle filtering and Otsu thresholding.
> - **JRC Global Surface Water** to mask permanent rivers.
> - **Copernicus GLO-30 DEM** to eliminate radar shadow and compute HAND elevation margins.
> - **OpenStreetMap road graphs** dynamically penalized when severed by flood polygons.
> - **Google Earth Engine live updater** (`sar-pipeline/gee_sar_update.py`) with zero cloud key hardcoding.
> 
> "By dancing with the SARs, we transform radar from a tool of post-mortem damage assessment into a live beacon of hope—saving the most vulnerable lives before the water reaches them. Thank you."

---

### Quick Cheat-Sheet for Q&A:
- **Q: How does SAR see water?**  
  *A:* Water acts as a specular mirror, reflecting microwave pulses away from the radar sensor, causing a dramatic drop in backscatter (<-16 dB in VV).
- **Q: Why slope masking?**  
  *A:* Mountainous terrain produces radar shadow and layover artifacts, and steep slopes (>16°) in the Himalayas are prone to post-flood mudslides.
- **Q: Does this need an internet connection during a flood?**  
  *A:* No! The civilian app and routing engine are fully cached in a Service Worker. All graph nodes and safe haven polygons run client-side.

