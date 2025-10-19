const mongoose = require('mongoose');

const episodeSchema = new mongoose.Schema({
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
  fact: {
    type: String,
    required: true,
    maxlength: 500
  },
  importance: {
    type: Number,
    required: true,
    min: 0,
    max: 1
  },
  embedding: {
    type: [Number],
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

episodeSchema.index({ user_id: 1, created_at: -1 });
episodeSchema.index({ user_id: 1, session_id: 1, created_at: -1 });

module.exports = mongoose.model('Episode', episodeSchema);
