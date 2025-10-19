const axios = require('axios');

const BASE_URL = 'http://localhost:3000/api/tasks';

// Test data
const testTasks = [
  {
    title: 'Complete Assignment 6',
    description: 'Finish the MongoDB task management API assignment',
    status: 'in-progress',
    priority: 'high',
    dueDate: new Date('2024-12-31'),
    category: 'Work'
  },
  {
    title: 'Buy groceries',
    description: 'Get milk, bread, and vegetables',
    status: 'pending',
    priority: 'medium',
    dueDate: new Date('2024-12-20'),
    category: 'Shopping'
  },
  {
    title: 'Doctor appointment',
    description: 'Annual checkup',
    status: 'pending',
    priority: 'high',
    dueDate: new Date('2024-12-25'),
    category: 'Health'
  }
];

async function testAPI() {
  console.log('🚀 Starting API Tests...\n');

  try {
    // Test 1: Create tasks (POST)
    console.log('1. Testing POST /api/tasks - Create tasks');
    const createdTasks = [];
    
    for (const task of testTasks) {
      try {
        const response = await axios.post(BASE_URL, task);
        console.log(`✅ Created task: ${response.data.title} (ID: ${response.data._id})`);
        createdTasks.push(response.data);
      } catch (error) {
        console.log(`❌ Failed to create task: ${task.title}`);
        console.log(`   Error: ${error.response?.data?.message || error.message}`);
      }
    }

    console.log('\n2. Testing GET /api/tasks - Get all tasks');
    const getAllResponse = await axios.get(BASE_URL);
    console.log(`✅ Retrieved ${getAllResponse.data.length} tasks`);
    console.log('Tasks:', getAllResponse.data.map(t => ({ id: t._id, title: t.title, status: t.status })));

    if (createdTasks.length > 0) {
      const taskId = createdTasks[0]._id;
      
      console.log('\n3. Testing GET /api/tasks/:id - Get single task');
      const getSingleResponse = await axios.get(`${BASE_URL}/${taskId}`);
      console.log(`✅ Retrieved task: ${getSingleResponse.data.title}`);

      console.log('\n4. Testing PUT /api/tasks/:id - Update task');
      const updateData = {
        title: 'Complete Assignment 6 - UPDATED',
        status: 'completed',
        priority: 'low'
      };
      const updateResponse = await axios.put(`${BASE_URL}/${taskId}`, updateData);
      console.log(`✅ Updated task: ${updateResponse.data.title} (Status: ${updateResponse.data.status})`);

      console.log('\n5. Testing DELETE /api/tasks/:id - Delete task');
      const deleteResponse = await axios.delete(`${BASE_URL}/${taskId}`);
      console.log(`✅ Deleted task: ${deleteResponse.data.message}`);

      console.log('\n6. Testing GET /api/tasks - Verify deletion');
      const finalGetResponse = await axios.get(BASE_URL);
      console.log(`✅ Remaining tasks: ${finalGetResponse.data.length}`);
    }

    console.log('\n🎉 All tests completed successfully!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    if (error.response) {
      console.error('Response data:', error.response.data);
    }
  }
}

// Test validation errors
async function testValidation() {
  console.log('\n🔍 Testing validation errors...\n');

  try {
    // Test missing required fields
    console.log('Testing missing required fields:');
    await axios.post(BASE_URL, { description: 'No title provided' });
  } catch (error) {
    console.log(`✅ Validation error caught: ${error.response?.data?.message}`);
  }

  try {
    // Test invalid enum values
    console.log('Testing invalid enum values:');
    await axios.post(BASE_URL, {
      title: 'Test Task',
      status: 'invalid-status',
      priority: 'invalid-priority',
      dueDate: new Date('2024-12-31'),
      category: 'InvalidCategory'
    });
  } catch (error) {
    console.log(`✅ Validation error caught: ${error.response?.data?.message}`);
  }

  try {
    // Test title length limit
    console.log('Testing title length limit:');
    await axios.post(BASE_URL, {
      title: 'A'.repeat(101), // 101 characters
      dueDate: new Date('2024-12-31'),
      category: 'Work'
    });
  } catch (error) {
    console.log(`✅ Validation error caught: ${error.response?.data?.message}`);
  }
}

// Run tests
if (require.main === module) {
  testAPI().then(() => {
    return testValidation();
  }).catch(console.error);
}

module.exports = { testAPI, testValidation };
