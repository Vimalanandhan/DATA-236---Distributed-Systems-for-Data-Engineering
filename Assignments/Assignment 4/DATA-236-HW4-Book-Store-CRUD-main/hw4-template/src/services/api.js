import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:3000/api'
});

// Request interceptor for error handling
api.interceptors.request.use(
  config => {
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  response => response,
  error => {
    const message = error.response?.data?.message || 'An error occurred';
    return Promise.reject(message);
  }
);

// Get all books
export const getBooks = async () => {
  const response = await api.get('/books');
  return response.data;
};

// Get book by ID
export const getBookById = async (id) => {
  const response = await api.get(`/books/${id}`);
  return response.data;
};

// Create new book
export const createBook = async (bookData) => {
  const response = await api.post('/books', bookData);
  return response.data;
};

// Update existing book
export const updateBook = async (id, bookData) => {
  const response = await api.put(`/books/${id}`, bookData);
  return response.data;
};

// Delete book
export const deleteBook = async (id) => {
  const response = await api.delete(`/books/${id}`);
  return response.data;
};

export default api;