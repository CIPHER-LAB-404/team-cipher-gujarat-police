// Vercel Serverless Function: /api/detections/recent
const DETECTIONS = [
  { id: 'DET-2026-901', camera_id: 'cam01', plate: 'HR 26 BR 9044', confidence: 0.948, vehicle_type: 'SUV / Fortuner', vehicle_color: 'Silver', timestamp: '2026-09-14 20:15:32', is_watchlist_hit: true, speed_kmh: 62 },
  { id: 'DET-2026-902', camera_id: 'cam05', plate: 'GJ 01 ER 4492', confidence: 0.932, vehicle_type: 'Sedan / Creta', vehicle_color: 'White', timestamp: '2026-09-14 20:14:18', is_watchlist_hit: true, speed_kmh: 58 },
  { id: 'DET-2026-903', camera_id: 'cam12', plate: 'GJ 05 JK 9901', confidence: 0.915, vehicle_type: 'Commercial / Scorpio', vehicle_color: 'Black', timestamp: '2026-09-14 20:12:05', is_watchlist_hit: true, speed_kmh: 74 },
  { id: 'DET-2026-904', camera_id: 'cam17', plate: 'MH 02 CD 4492', confidence: 0.961, vehicle_type: 'Hatchback / Brezza', vehicle_color: 'Red', timestamp: '2026-09-14 20:09:44', is_watchlist_hit: true, speed_kmh: 45 },
  { id: 'DET-2026-905', camera_id: 'cam03', plate: 'GJ 01 RU 8892', confidence: 0.927, vehicle_type: 'Sedan / City', vehicle_color: 'Grey', timestamp: '2026-09-14 20:06:12', is_watchlist_hit: false, speed_kmh: 51 },
  { id: 'DET-2026-906', camera_id: 'cam04', plate: 'GJ 27 AB 1234', confidence: 0.954, vehicle_type: 'Motorcycle', vehicle_color: 'Black', timestamp: '2026-09-14 20:03:59', is_watchlist_hit: false, speed_kmh: 38 }
];

module.exports = (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.status(200).json({
    status: 'SUCCESS',
    count: DETECTIONS.length,
    detections: DETECTIONS
  });
};
