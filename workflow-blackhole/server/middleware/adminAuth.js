module.exports = (req, res, next) => {
    // Check if user exists and is admin or manager
    if (!req.user || (req.user.role !== "Admin" && req.user.role !== "Manager")) {
      return res.status(403).json({ error: "Access denied. Admin or Manager only." })
    }

    next()
  }
  