const mongoose = require('mongoose');

const summarySchema = new mongoose.Schema({
  user_id: {
    type: String,
    required: true,
    index: true
  },
  session_id: {
    type: String,
    default: null, 
    index: true
  },
  scope: {
    type: String,
    enum: ['session', 'user'],
    required: true,
    index: true
  },
  text: {
    type: String,
    required: true
  },
  created_at: {
    type: Date,
    default: Date.now,
    index: true
  }
}, {
  timestamps: false 
});

summarySchema.index({ user_id: 1, scope: 1, created_at: -1 });
summarySchema.index({ user_id: 1, session_id: 1, created_at: -1 });

module.exports = mongoose.model('Summary', summarySchema);
