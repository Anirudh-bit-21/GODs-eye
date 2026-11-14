import { SarRouteEngine } from './router.js';

// DOM Elements
const screenPicker = document.getElementById('screen-picker');
const screenNav = document.getElementById('screen-navigation');
const btnGps = document.getElementById('btn-gps');
const townButtons = document.querySelectorAll('.btn-town');
const btnNextStep = document.getElementById('btn-next-step');
const btnPrevStep = document.getElementById('btn-prev-step');
const btnChangeLocation = document.getElementById('btn-change-location');

// Navigation Display Elements
const destHavenName = document.getElementById('dest-haven-name');
const destHavenClearance = document.getElementById('dest-haven-clearance');
const etaChildElder = document.getElementById('eta-child-elder');
const etaStandard = document.getElementById('eta-standard');
const routeDistance = document.getElementById('route-distance');
const navStepCount = document.getElementById('nav-step-count');
const navSymbol = document.getElementById('nav-symbol');
const navInstructionMain = document.getElementById('nav-instruction-main');
const navInstructionSub = document.getElementById('nav-instruction-sub');
const whySafeText = document.getElementById('why-safe-text');
const offlineStatus = document.getElementById('offline-status');
const offlineText = document.getElementById('offline-text');
const sarTimeLabel = document.getElementById('sar-time-label');

// State
const router = new SarRouteEngine();
let currentRoute = null;
let currentStepIndex = 0;

// Audio context for sound chime
let audioCtx = null;
function playChime(freq = 587.33) {
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
    gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.35);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.35);
  } catch (e) {
    // Audio not allowed yet or disabled
  }
}

function triggerHaptic(duration = 60) {
  if (navigator.vibrate) {
    navigator.vibrate(duration);
  }
}

// Online / Offline monitor
function updateNetworkStatus() {
  if (navigator.onLine) {
    offlineText.textContent = 'OFFLINE READY';
    offlineStatus.style.borderColor = '#00e676';
  } else {
    offlineText.textContent = 'OFFLINE MODE (ACTIVE)';
    offlineStatus.style.borderColor = '#ffd600';
    offlineStatus.style.background = '#332b00';
  }
}
window.addEventListener('online', updateNetworkStatus);
window.addEventListener('offline', updateNetworkStatus);
updateNetworkStatus();

// Initialize Router
async function initApp() {
  const loaded = await router.load('./data');
  if (!loaded) {
    console.warn('Network fetch failed; attempting relative fallback...');
    await router.load('data');
  }
}
initApp();

// Location Handling
btnGps.addEventListener('click', () => {
  btnGps.disabled = true;
  btnGps.innerHTML = '<span>⏳</span><span>GETTING SATELLITE FIX...</span>';

  if (!navigator.geolocation) {
    alert('Geolocation not supported on this browser. Please select your town below.');
    resetGpsBtn();
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      resetGpsBtn();
      calculateRoute(pos.coords.latitude, pos.coords.longitude, 'Your GPS Position');
    },
    (err) => {
      console.warn('GPS error:', err);
      // Fallback to closest default town
      resetGpsBtn();
      alert('Could not get GPS fix. Using Syabru Besi Market demo location.');
      calculateRoute(28.1610, 85.3420, 'Syabru Besi');
    },
    { timeout: 7000, enableHighAccuracy: true }
  );
});

function resetGpsBtn() {
  btnGps.disabled = false;
  btnGps.innerHTML = '<span style="font-size: 32px;">🧭</span><span>USE MY GPS LOCATION</span>';
}

townButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    const lat = parseFloat(btn.dataset.lat);
    const lon = parseFloat(btn.dataset.lon);
    const townName = btn.querySelector('.town-name').textContent;
    triggerHaptic(50);
    playChime(523.25);
    calculateRoute(lat, lon, townName);
  });
});

function calculateRoute(lat, lon, label) {
  if (!router.isLoaded) {
    alert('Map data is still loading. Please wait a second.');
    return;
  }

  const result = router.findSafeHavenRoute(lat, lon);
  if (!result || !result.success) {
    alert(result?.message || 'Could not compute dry route from this location. Road may be completely submerged.');
    return;
  }

  currentRoute = result;
  currentStepIndex = 0;

  // Populate Destination Overview
  destHavenName.textContent = result.safeHaven.name;
  destHavenClearance.textContent = `+${result.safeHaven.elevationMarginM}m DRY`;
  etaChildElder.textContent = `~${result.metrics.childElderEtaMinutes} min`;
  etaStandard.textContent = `~${result.metrics.standardEtaMinutes} min`;
  routeDistance.textContent = `${result.metrics.totalDistanceKm} km (${result.metrics.totalDistanceMeters}m)`;
  whySafeText.textContent = result.safeHaven.whySafe ||
    `Verified dry ground above flood line. Staged supplies: ${result.safeHaven.stagedSupplies.join(', ')}.`;

  if (result.timestampUtc) {
    sarTimeLabel.textContent = result.timestampUtc;
  }

  // Switch Screens
  screenPicker.style.display = 'none';
  screenNav.style.display = 'block';
  window.scrollTo({ top: 0, behavior: 'smooth' });

  renderCurrentStep();
  playChime(659.25);
}

function renderCurrentStep() {
  if (!currentRoute || !currentRoute.steps) return;
  const steps = currentRoute.steps;
  const step = steps[currentStepIndex];

  navStepCount.textContent = `STEP ${currentStepIndex + 1} OF ${steps.length}`;
  navSymbol.textContent = step.symbol;
  navInstructionMain.textContent = step.instruction;
  navInstructionSub.textContent = step.subText;

  // Button states
  btnPrevStep.disabled = currentStepIndex === 0;

  if (currentStepIndex === steps.length - 1) {
    btnNextStep.innerHTML = '<span>YOU ARE SAFE! 🛡️</span>';
    btnNextStep.style.backgroundColor = '#00e676';
  } else {
    btnNextStep.innerHTML = '<span>NEXT STEP ❯</span>';
    btnNextStep.style.backgroundColor = '';
  }
}

// Navigation Step Controls
btnNextStep.addEventListener('click', () => {
  if (!currentRoute) return;
  if (currentStepIndex < currentRoute.steps.length - 1) {
    currentStepIndex++;
    triggerHaptic(50);
    playChime(659.25);
    renderCurrentStep();
  } else {
    // Already at destination
    triggerHaptic([100, 50, 100]);
    playChime(880.0);
    alert(`You have reached ${currentRoute.safeHaven.name}!\n\nThis safe-haven is verified dry by Copernicus Sentinel-1 SAR microwave radar.`);
  }
});

btnPrevStep.addEventListener('click', () => {
  if (!currentRoute) return;
  if (currentStepIndex > 0) {
    currentStepIndex--;
    triggerHaptic(30);
    playChime(440.0);
    renderCurrentStep();
  }
});

btnChangeLocation.addEventListener('click', () => {
  triggerHaptic(40);
  screenNav.style.display = 'none';
  screenPicker.style.display = 'block';
  currentRoute = null;
  currentStepIndex = 0;
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Service Worker Registration for Offline Cache
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').then(
      (reg) => console.log('Civilian PWA ServiceWorker registered:', reg.scope),
      (err) => console.warn('ServiceWorker registration failed:', err)
    );
  });
}

