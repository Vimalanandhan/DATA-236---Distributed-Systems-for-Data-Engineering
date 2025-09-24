import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { deleteBook } from '../../store/bookSlice';
import { getBookById } from '../../services/api';
import './DeleteBook.css';

const DeleteBook = () => {
  const [book, setBook] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { id } = useParams();
  const { loading } = useSelector(state => state.books);

  useEffect(() => {
    const fetchBook = async () => {
      try {
        const bookData = await getBookById(id);
        setBook(bookData);
      } catch (error) {
        setError('Failed to fetch book details');
        console.error('Error:', error);
      }
    };

    fetchBook();
  }, [id]);

  const handleDelete = async () => {
    try {
      await dispatch(deleteBook(id)).unwrap();
      navigate('/');
    } catch (error) {
      setError(error.message);
      console.error('Error:', error);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="error-message">{error}</div>;

  return (
    <div className="delete-book-container">
      <h2>Delete Book</h2>
      {book && (
        <div className="book-details">
          <h3>{book.title}</h3>
          <p>Author: {book.author}</p>
          <p>ISBN: {book.isbn}</p>
          {book.publishedYear && <p>Published Year: {book.publishedYear}</p>}
          <p className="warning-text">Are you sure you want to delete this book?</p>
        </div>
      )}
      <div className="button-group">
        <button 
          onClick={handleDelete} 
          className="delete-button" 
          disabled={loading}
        >
          {loading ? 'Deleting...' : 'Delete Book'}
        </button>
        <button 
          onClick={() => navigate('/')} 
          className="cancel-button"
          disabled={loading}
        >
          Cancel
        </button>
      </div>
    </div>
  );
};

export default DeleteBook;