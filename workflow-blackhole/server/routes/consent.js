
const express = require('express');
const router = express.Router();
const User = require('../models/User');
const auth = require('../middleware/auth');

// @route   POST /api/consent/
// @desc    Update user consent for monitoring
// @access  Private
router.post('/', auth, async (req, res) => {
  try {
    const { consent } = req.body;

    if (typeof consent !== 'boolean') {
      return res.status(400).json({ msg: 'Consent value must be a boolean' });
    }

    const user = await User.findById(req.user.id);

    if (!user) {
      return res.status(404).json({ msg: 'User not found' });
    }

    user.monitoringPaused = !consent;
    user.lastConsentDate = new Date();

    await user.save();

    res.json({
      msg: `Monitoring ${user.monitoringPaused ? 'paused' : 'resumed'} successfully`,
      monitoringPaused: user.monitoringPaused,
    });
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
});

module.exports = router;
