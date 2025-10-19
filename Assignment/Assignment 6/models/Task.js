const mongoose = require('mongoose');

const taskSchema = new mongoose.Schema({
  title: {
    type: String,
    required: [true, 'Title is required'],
    maxlength: [100, 'Title cannot exceed 100 characters'],
    trim: true
  },
  description: {
    type: String,
    trim: true
  },
  status: {
    type: String,
    enum: {
      values: ['pending', 'in-progress', 'completed'],
      message: 'Status must be one of: pending, in-progress, completed'
    },
    default: 'pending'
  },
  priority: {
    type: String,
    enum: {
      values: ['low', 'medium', 'high'],
      message: 'Priority must be one of: low, medium, high'
    },
    default: 'medium'
  },
  dueDate: {
    type: Date,
    required: [true, 'Due date is required']
  },
  category: {
    type: String,
    enum: {
      values: ['Work', 'Personal', 'Shopping', 'Health', 'Other'],
      message: 'Category must be one of: Work, Personal, Shopping, Health, Other'
    }
  }
}, {
  timestamps: true 
});

module.exports = mongoose.model('Task', taskSchema);