const mongoose = require("mongoose");

const ActionEventSchema = new mongoose.Schema({
  userId: { type: String, required: true, index: true },
  sessionId: { type: String, required: true, index: true },

  type: { type: String, required: true },
  category: {
    type: String,
    enum: ["ui", "nav", "system", "agent", "security"],
    required: true
  },

  payload: { type: Object },

  clientTs: { type: Number, required: true },
  serverTs: { type: Number, required: true },

  source: {
    type: String,
    enum: ["client", "agent", "system"],
    required: true
  }
}, { timestamps: true });

module.exports = mongoose.model("ActionEvent", ActionEventSchema);
