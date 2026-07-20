module.exports = (req, res, next) => {
  // Check if user is admin or procurement agent
  if (req.user.role !== "Admin" && req.user.role !== "Procurement Agent") {
    return res.status(403).json({ error: "Access denied. Admin or Procurement Agent only." })
  }

  next()
}