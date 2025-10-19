const mongoose = require('mongoose');

const messageSchema = new mongoose.Schema({
  user_id: {
    type: String,
    required: true,
    index: true
  },
  session_id: {
    type: String,
    required: true,
    index: true
  },
  role: {
    type: String,
    enum: ['user', 'assistant'],
    required: true
  },
  content: {
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

messageSchema.index({ user_id: 1, session_id: 1, created_at: -1 });
messageSchema.index({ user_id: 1, created_at: -1 });

module.exports = mongoose.model('Message', messageSchema);
