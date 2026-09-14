// Vercel Serverless Function: /api/watchlist
const WATCHLIST = [
  { id: 'WL-01', plate: 'GJ01ER4492', vehicle_type: 'Hyundai Creta', vehicle_color: 'White', reason: 'Arms Act Section 25 / Highway Robbery', priority: 'CRITICAL', status: 'ACTIVE', timestamp: '2026-09-14 18:30:00', fir_number: 'FIR/2026/AHM-8821' },
  { id: 'WL-02', plate: 'GJ05JK9901', vehicle_type: 'Mahindra Scorpio', vehicle_color: 'Black', reason: 'Narcotics NDPS Interception Warrant', priority: 'CRITICAL', status: 'ACTIVE', timestamp: '2026-09-14 17:15:00', fir_number: 'FIR/2026/GNR-4410' },
  { id: 'WL-03', plate: 'HR26BR9044', vehicle_type: 'Toyota Fortuner', vehicle_color: 'Silver', reason: 'Interstate Gold Smuggling Flight Risk', priority: 'HIGH', status: 'ACTIVE', timestamp: '2026-09-14 16:45:00', fir_number: 'FIR/2026/RJK-1102' },
  { id: 'WL-04', plate: 'MH02CD4492', vehicle_type: 'Maruti Brezza', vehicle_color: 'Red', reason: 'Vehicle Theft FIR #4412 Navsari', priority: 'HIGH', status: 'ACTIVE', timestamp: '2026-09-14 15:20:00', fir_number: 'FIR/2026/NAV-3391' },
  { id: 'WL-05', plate: 'GJ01RU8892', vehicle_type: 'Honda City', vehicle_color: 'Grey', reason: 'Hit-and-Run Sanand Road Inquiry', priority: 'MEDIUM', status: 'ACTIVE', timestamp: '2026-09-14 14:10:00', fir_number: 'FIR/2026/SAN-0914' }
];

module.exports = (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.status(200).json({
    status: 'SUCCESS',
    count: WATCHLIST.length,
    watchlist: WATCHLIST
  });
};
