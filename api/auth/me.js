// Vercel Serverless Function: /api/auth/me
module.exports = (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  res.status(200).json({
    username: 'admin',
    role: 'SUPER_ADMIN',
    name: 'Officer CIPHER',
    badge_number: 'GP-7749',
    department: 'Gujarat Police Headquarters',
    station: 'Gandhinagar Cyber Command',
    clearance: 'TOP_SECRET_LEVEL_4'
  });
};
