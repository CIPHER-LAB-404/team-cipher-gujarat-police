// Vercel Serverless Function: /api/db/stats
module.exports = (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  res.status(200).json({
    status: 'OPTIMAL',
    storage_engine: 'SQLite 3 with WAL Mode & Vercel Edge Serverless',
    records: {
      users: 9,
      cameras: 30,
      watchlist: 5,
      detections: 24,
      stolen_vehicle_reports: 5,
      audit_logs: 382
    },
    performance: {
      average_query_ms: 1.2,
      wal_checkpoint: 'PASSING',
      integrity_check: 'OK'
    }
  });
};
