
const express = require('express');
const router = express.Router();
const MonitoringAlert = require('../models/MonitoringAlert');
const auth = require('../middleware/auth');

// @route   GET /api/alerts
// @desc    Get all alerts for the authenticated user
// @access  Private
router.get('/', auth, async (req, res) => {
  try {
    const alerts = await MonitoringAlert.find({ employee: req.user.id }).sort({ timestamp: -1 });
    res.json(alerts);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
});

module.exports = router;
