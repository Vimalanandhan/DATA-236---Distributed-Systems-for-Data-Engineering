import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './components/Home/Home';
import CreateBook from './components/Create/CreateBook';
import UpdateBook from './components/Update/UpdateBook';
import DeleteBook from './components/Delete/DeleteBook';

const App = () => {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchBooks();
  }, []);

  const fetchBooks = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:3000/api/books');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setBooks(data);
    } catch (error) {
      setError('Failed to fetch books. Please ensure the server is running.');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading books...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Home books={books} onError={setError} />} />
          <Route path="/create" element={<CreateBook onAddBook={setBooks} />} />
          <Route 
            path="/update/:id" 
            element={<UpdateBook books={books} setBooks={setBooks} />} 
          />
          <Route 
            path="/delete/:id" 
            element={<DeleteBook books={books} setBooks={setBooks} />} 
          />
        </Routes>
      </div>
    </Router>
  );
};

export default App;