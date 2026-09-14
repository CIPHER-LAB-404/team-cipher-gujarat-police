/**
 * SENTINEL — Gujarat Police Command & Intelligence Platform
 * Tactical UI/UX Asset & Dynamic Placeholder Engine
 * 
 * Provides high-performance, responsive SVG Data-URI placeholders
 * with HUD targeting reticles, Indian MoRTH license plate graphics,
 * vehicle class silhouettes, and camera feed telemetry overlays.
 */

(function (window) {
  'use strict';

  const TacticalPlaceholders = {
    /**
     * Generates a tactical CCTV feed standby graphic with HUD scanlines & reticle
     */
    cctvStandby(camName = 'CCTV SENSOR FEED', camId = 'CAM-01', width = 640, height = 360) {
      const escapedName = (camName || 'CCTV SENSOR').replace(/"/g, '&quot;');
      const escapedId = (camId || 'CAM-01').replace(/"/g, '&quot;');
      const now = new Date().toLocaleTimeString('en-IN', { hour12: false });

      const svg = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
  <defs>
    <linearGradient id="bg-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#050914" />
      <stop offset="50%" stop-color="#0a1224" />
      <stop offset="100%" stop-color="#03060d" />
    </linearGradient>
    <pattern id="tactical-grid" width="30" height="30" patternUnits="userSpaceOnUse">
      <path d="M 30 0 L 0 0 0 30" fill="none" stroke="rgba(56, 189, 248, 0.05)" stroke-width="1"/>
    </pattern>
    <linearGradient id="laser-glow" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="rgba(0, 242, 255, 0)" />
      <stop offset="50%" stop-color="rgba(0, 242, 255, 0.8)" />
      <stop offset="100%" stop-color="rgba(0, 242, 255, 0)" />
    </linearGradient>
  </defs>

  <!-- Dark Tactical Canvas -->
  <rect width="100%" height="100%" fill="url(#bg-grad)" />
  <rect width="100%" height="100%" fill="url(#tactical-grid)" />

  <!-- Corner Brackets -->
  <path d="M 20 50 L 20 20 L 50 20" fill="none" stroke="#38BDF8" stroke-width="2.5" stroke-linecap="round" />
  <path d="M ${width - 50} 20 L ${width - 20} 20 L ${width - 20} 50" fill="none" stroke="#38BDF8" stroke-width="2.5" stroke-linecap="round" />
  <path d="M 20 ${height - 50} L 20 ${height - 20} L 50 ${height - 20}" fill="none" stroke="#38BDF8" stroke-width="2.5" stroke-linecap="round" />
  <path d="M ${width - 50} ${height - 20} L ${width - 20} ${height - 20} L ${width - 20} ${height - 50}" fill="none" stroke="#38BDF8" stroke-width="2.5" stroke-linecap="round" />

  <!-- Center Crosshair & Reticle -->
  <circle cx="${width / 2}" cy="${height / 2}" r="50" fill="none" stroke="rgba(56, 189, 248, 0.25)" stroke-width="1.5" stroke-dasharray="6,4" />
  <circle cx="${width / 2}" cy="${height / 2}" r="4" fill="#00F2FF" />
  <line x1="${width / 2 - 70}" y1="${height / 2}" x2="${width / 2 - 15}" y2="${height / 2}" stroke="#00F2FF" stroke-width="1.5" />
  <line x1="${width / 2 + 15}" y1="${height / 2}" x2="${width / 2 + 70}" y2="${height / 2}" stroke="#00F2FF" stroke-width="1.5" />
  <line x1="${width / 2}" y1="${height / 2 - 70}" x2="${width / 2}" y2="${height / 2 - 15}" stroke="#00F2FF" stroke-width="1.5" />
  <line x1="${width / 2}" y1="${height / 2 + 15}" x2="${width / 2}" y2="${height / 2 + 70}" stroke="#00F2FF" stroke-width="1.5" />

  <!-- Top Telemetry Bar -->
  <rect x="25" y="25" width="110" height="24" rx="4" fill="rgba(16, 185, 129, 0.15)" stroke="rgba(16, 185, 129, 0.4)" stroke-width="1" />
  <circle cx="37" cy="37" r="4" fill="#10B981" />
  <text x="48" y="41" fill="#10B981" font-family="'JetBrains Mono', monospace" font-size="11" font-weight="700" letter-spacing="1">LIVE ONVIF</text>

  <rect x="${width - 145}" y="25" width="120" height="24" rx="4" fill="rgba(15, 23, 42, 0.7)" stroke="rgba(56, 189, 248, 0.25)" stroke-width="1" />
  <text x="${width - 135}" y="41" fill="#94A3B8" font-family="'JetBrains Mono', monospace" font-size="10" font-weight="600">${now} IST</text>

  <!-- Central Camera Designation -->
  <text x="${width / 2}" y="${height / 2 + 75}" fill="#E2E8F0" font-family="'Inter', sans-serif" font-size="14" font-weight="700" text-anchor="middle" letter-spacing="0.5">${escapedName}</text>
  <text x="${width / 2}" y="${height / 2 + 95}" fill="#38BDF8" font-family="'JetBrains Mono', monospace" font-size="11" font-weight="600" text-anchor="middle" letter-spacing="1.5">ID: ${escapedId} • 1 FPS ANPR ACTIVE</text>

  <!-- Bottom HUD Status -->
  <rect x="25" y="${height - 45}" width="${width - 50}" height="24" rx="3" fill="rgba(15, 23, 42, 0.85)" stroke="rgba(255, 255, 255, 0.08)" />
  <text x="35" y="${height - 29}" fill="#64748B" font-family="'JetBrains Mono', monospace" font-size="10">RESOLUTION: 4K UHD</text>
  <text x="${width / 2}" y="${height - 29}" fill="#38BDF8" font-family="'JetBrains Mono', monospace" font-size="10" text-anchor="middle">STREAM HEALTH: OPTIMAL (12ms)</text>
  <text x="${width - 35}" y="${height - 29}" fill="#10B981" font-family="'JetBrains Mono', monospace" font-size="10" text-anchor="end">SENTRY LINKED</text>
</svg>`.trim();

      return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
    },

    /**
     * Generates a high-contrast Indian MoRTH License Plate Graphic Placeholder
     */
    licensePlate(plateNumber = 'GJ01AB1234', width = 280, height = 75) {
      const cleanPlate = (plateNumber || 'GJ01AB1234').toUpperCase().replace(/[^A-Z0-9]/g, '');
      const stateCode = cleanPlate.slice(0, 2) || 'GJ';
      const rto = cleanPlate.slice(2, 4) || '01';
      const series = cleanPlate.slice(4, -4) || 'AB';
      const num = cleanPlate.slice(-4) || '1234';
      const formatted = `${stateCode} ${rto} ${series} ${num}`.trim();

      const svg = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
  <defs>
    <linearGradient id="plate-bg" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF" />
      <stop offset="100%" stop-color="#F1F5F9" />
    </linearGradient>
    <filter id="plate-shadow" x="-5%" y="-10%" width="110%" height="130%">
      <feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="rgba(0,0,0,0.6)"/>
    </filter>
  </defs>

  <!-- Plate Base with Border & Shadow -->
  <rect x="4" y="4" width="${width - 8}" height="${height - 8}" rx="8" fill="url(#plate-bg)" stroke="#0F172A" stroke-width="3" filter="url(#plate-shadow)"/>
  <rect x="7" y="7" width="${width - 14}" height="${height - 14}" rx="6" fill="none" stroke="#64748B" stroke-width="0.8"/>

  <!-- Left Blue Stripe for IND -->
  <path d="M 7 13 C 7 9.7 9.7 7 13 7 L 38 7 L 38 ${height - 7} L 13 ${height - 7} C 9.7 ${height - 7} 7 ${height - 9.7} 7 ${height - 13} Z" fill="#0038A8" />
  
  <!-- Ashoka Chakra (Stylized Circle with Spokes) -->
  <circle cx="22" cy="${height / 2 - 10}" r="8" fill="none" stroke="#FFFFFF" stroke-width="1.2" />
  <circle cx="22" cy="${height / 2 - 10}" r="2" fill="#FFFFFF" />
  
  <!-- IND Text -->
  <text x="22" y="${height / 2 + 15}" fill="#FFFFFF" font-family="'Inter', sans-serif" font-size="11" font-weight="900" text-anchor="middle" letter-spacing="1">IND</text>

  <!-- Hologram Stamp Badge (Top Left Corner of Plate) -->
  <rect x="44" y="10" width="10" height="10" rx="1.5" fill="#94A3B8" stroke="#475569" stroke-width="0.5" opacity="0.6"/>

  <!-- License Plate Registration Characters (FE-Schrift / Bold Mono) -->
  <text x="${(width + 38) / 2}" y="${height / 2 + 10}" fill="#0F172A" font-family="'JetBrains Mono', 'Segoe UI', monospace" font-size="25" font-weight="900" text-anchor="middle" letter-spacing="3.5">${formatted}</text>
</svg>`.trim();

      return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
    },

    /**
     * Generates a tactical vehicle silhouette & detection crop placeholder
     */
    vehicleCard(vehicleType = 'Car', colorName = 'White', width = 320, height = 200) {
      const type = (vehicleType || 'Car').toLowerCase();
      const color = colorName || 'Tactical Dark';

      // SVG vehicle path silhouettes
      let silhouettePath = '';
      if (type.includes('motorcycle') || type.includes('bike') || type.includes('2w')) {
        silhouettePath = 'M 60 140 A 20 20 0 1 0 100 140 A 20 20 0 1 0 60 140 M 220 140 A 20 20 0 1 0 260 140 A 20 20 0 1 0 220 140 M 80 140 L 120 110 L 160 110 L 200 140 M 140 110 L 170 80 L 190 80 M 170 80 L 240 140';
      } else if (type.includes('truck') || type.includes('hcv') || type.includes('bus')) {
        silhouettePath = 'M 50 140 L 50 60 L 210 60 L 210 90 L 260 90 L 270 120 L 270 140 L 250 140 A 15 15 0 0 1 220 140 L 120 140 A 15 15 0 0 1 90 140 Z M 215 70 L 250 95 L 215 95 Z';
      } else if (type.includes('auto') || type.includes('rickshaw') || type.includes('3w')) {
        silhouettePath = 'M 70 140 L 80 80 L 180 80 L 220 110 L 220 140 L 190 140 A 15 15 0 0 1 160 140 L 110 140 A 15 15 0 0 1 80 140 Z M 95 90 L 140 90 L 140 115 L 95 115 Z';
      } else {
        // Default Car / Sedan / SUV
        silhouettePath = 'M 40 130 L 65 95 L 110 80 L 200 80 L 240 95 L 280 110 L 280 135 L 255 135 A 18 18 0 0 1 220 135 L 115 135 A 18 18 0 0 1 80 135 Z M 75 100 L 115 86 L 155 86 L 155 105 L 75 105 Z M 165 86 L 195 86 L 225 100 L 165 105 Z';
      }

      const svg = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
  <defs>
    <linearGradient id="v-bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#09101f" />
      <stop offset="100%" stop-color="#040711" />
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="100%" height="100%" fill="url(#v-bg)" />

  <!-- Bounding Box Target Reticle -->
  <rect x="20" y="20" width="${width - 40}" height="${height - 40}" rx="6" fill="none" stroke="rgba(56, 189, 248, 0.25)" stroke-dasharray="6,4" stroke-width="1.5" />
  
  <!-- Corner Aim Brackets -->
  <path d="M 18 35 L 18 18 L 35 18" fill="none" stroke="#00F2FF" stroke-width="2.5" />
  <path d="M ${width - 35} 18 L ${width - 18} 18 L ${width - 18} 35" fill="none" stroke="#00F2FF" stroke-width="2.5" />
  <path d="M 18 ${height - 35} L 18 ${height - 18} L 35 ${height - 18}" fill="none" stroke="#00F2FF" stroke-width="2.5" />
  <path d="M ${width - 35} ${height - 18} L ${width - 18} ${height - 18} L ${width - 18} ${height - 35}" fill="none" stroke="#00F2FF" stroke-width="2.5" />

  <!-- Vehicle Silhouette Outline -->
  <g transform="translate(10, 5) scale(0.95)">
    <path d="${silhouettePath}" fill="rgba(56, 189, 248, 0.12)" stroke="#38BDF8" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
  </g>

  <!-- Top Badge -->
  <rect x="30" y="28" width="95" height="20" rx="3" fill="rgba(0, 242, 255, 0.15)" stroke="rgba(0, 242, 255, 0.4)" stroke-width="0.8" />
  <text x="77" y="42" fill="#00F2FF" font-family="'JetBrains Mono', monospace" font-size="10" font-weight="700" text-anchor="middle">${vehicleType.toUpperCase()}</text>

  <!-- Confidence & Color Badge -->
  <text x="${width - 30}" y="42" fill="#94A3B8" font-family="'JetBrains Mono', monospace" font-size="10" font-weight="600" text-anchor="end">COLOR: ${color.toUpperCase()}</text>

  <!-- Bottom Details Bar -->
  <rect x="25" y="${height - 36}" width="${width - 50}" height="20" rx="3" fill="rgba(15, 23, 42, 0.9)" />
  <text x="35" y="${height - 23}" fill="#34D399" font-family="'JetBrains Mono', monospace" font-size="9" font-weight="700">OPTICAL CROP VERIFIED</text>
  <text x="${width - 35}" y="${height - 23}" fill="#64748B" font-family="'JetBrains Mono', monospace" font-size="9" text-anchor="end">YOLOv8 DETECT</text>
</svg>`.trim();

      return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
    },

    /**
     * Police Officer Cyber Insignia Badge
     */
    officerBadge(width = 80, height = 80) {
      const svg = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
  <defs>
    <linearGradient id="badge-glow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38BDF8" />
      <stop offset="100%" stop-color="#1D4ED8" />
    </linearGradient>
  </defs>
  <polygon points="40,8 70,22 70,55 40,74 10,55 10,22" fill="url(#badge-glow)" stroke="#60A5FA" stroke-width="2" />
  <polygon points="40,14 64,26 64,52 40,68 16,52 16,26" fill="#0B132B" stroke="rgba(255,255,255,0.15)" stroke-width="1" />
  <circle cx="40" cy="35" r="10" fill="#FBBF24" />
  <path d="M 28 55 C 28 46 52 46 52 55" fill="none" stroke="#FBBF24" stroke-width="2" />
</svg>`.trim();
      return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
    },

    /**
     * Automatically hooks into all img tags across the page
     * and provides tactical fallbacks without ever leaving an image broken
     */
    attachImageErrorFallbacks() {
      document.addEventListener('error', (event) => {
        const target = event.target;
        if (target && target.tagName === 'IMG' && !target.dataset.fallbackApplied) {
          target.dataset.fallbackApplied = 'true';
          const src = target.getAttribute('src') || '';

          if (src.includes('plate') || target.classList.contains('plate-img') || target.classList.contains('plate-crop')) {
            target.src = '/test_indian_plate.jpg';
          } else if (src.includes('vehicle') || target.classList.contains('vehicle-img') || target.classList.contains('car-crop')) {
            target.src = '/test_indian_car.jpg';
          } else if (src.includes('snapshot') || src.includes('stream') || target.classList.contains('feed-live-mjpeg')) {
            target.src = '/sample_cam04_snapshot.jpg';
          } else {
            target.src = '/logo.png';
          }
        }
      }, true);
    }
  };

  // Expose globally
  window.TacticalPlaceholders = TacticalPlaceholders;

  // Initialize automatic fallback listener immediately
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => TacticalPlaceholders.attachImageErrorFallbacks());
  } else {
    TacticalPlaceholders.attachImageErrorFallbacks();
  }

})(typeof window !== 'undefined' ? window : this);
