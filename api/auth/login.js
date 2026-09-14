// Vercel Serverless Function: /api/auth/login
module.exports = (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Parse body
  let username = 'admin';
  if (req.body) {
    username = req.body.username || req.body.officer_id || username;
  }

  const user = {
    username: username,
    role: 'SUPER_ADMIN',
    name: username === 'admin' ? 'Super Admin (State Command)' : `Officer ${username.toUpperCase()}`,
    badge_number: 'GP-7749',
    department: 'Gujarat Police Headquarters',
    station: 'Gandhinagar Cyber Command',
    clearance: 'TOP_SECRET_LEVEL_4'
  };

  const token = 'CIPHER_SECURE_TOKEN_2026_' + Buffer.from(JSON.stringify(user)).toString('base64');

  res.status(200).json({
    access_token: token,
    token_type: 'bearer',
    user: user
  });
};
