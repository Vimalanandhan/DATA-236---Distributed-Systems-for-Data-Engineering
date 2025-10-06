from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List
import models
import schemas
from database import get_db
import math

router = APIRouter(prefix="/library", tags=["library"])

@router.post("/authors", response_model=schemas.Author, status_code=201)
def create_author(author: schemas.AuthorCreate, db: Session = Depends(get_db)):
    try:
        db_author = models.Author(
            first_name=author.first_name,
            last_name=author.last_name,
            email=author.email
        )
        db.add(db_author)
        db.commit()
        db.refresh(db_author)
        return db_author
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")

@router.get("/authors", response_model=schemas.PaginatedAuthors)
def get_authors(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * per_page
    
    total = db.query(models.Author).count()
    
    authors = db.query(models.Author).offset(offset).limit(per_page).all()
    
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    
    return schemas.PaginatedAuthors(
        authors=authors,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@router.get("/authors/{author_id}", response_model=schemas.Author)
def get_author(author_id: int, db: Session = Depends(get_db)):
    author = db.query(models.Author).filter(models.Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author

@router.put("/authors/{author_id}", response_model=schemas.Author)
def update_author(author_id: int, author_update: schemas.AuthorUpdate, db: Session = Depends(get_db)):
    author = db.query(models.Author).filter(models.Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    try:
        update_data = author_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(author, field, value)
        
        db.commit()
        db.refresh(author)
        return author
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")

@router.delete("/authors/{author_id}", status_code=204)
def delete_author(author_id: int, db: Session = Depends(get_db)):
    author = db.query(models.Author).filter(models.Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    books_count = db.query(models.Book).filter(models.Book.author_id == author_id).count()
    if books_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete author. They have {books_count} associated book(s). Please delete the books first."
        )
    
    db.delete(author)
    db.commit()
    return None

@router.post("/books", response_model=schemas.BookWithAuthor, status_code=201)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    author = db.query(models.Author).filter(models.Author.id == book.author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    try:
        db_book = models.Book(
            title=book.title,
            isbn=book.isbn,
            publication_year=book.publication_year,
            available_copies=book.available_copies,
            author_id=book.author_id
        )
        db.add(db_book)
        db.commit()
        db.refresh(db_book)
        
        db_book = db.query(models.Book).options(joinedload(models.Book.author)).filter(models.Book.id == db_book.id).first()
        return db_book
    except IntegrityError as e:
        db.rollback()
        if "isbn" in str(e):
            raise HTTPException(status_code=400, detail="ISBN already exists")
        raise HTTPException(status_code=400, detail="Database constraint violation")

@router.get("/books", response_model=schemas.PaginatedBooks)
def get_books(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * per_page
    
    total = db.query(models.Book).count()
    
    books = db.query(models.Book).options(joinedload(models.Book.author)).offset(offset).limit(per_page).all()
    
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    
    return schemas.PaginatedBooks(
        books=books,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@router.get("/books/{book_id}", response_model=schemas.BookWithAuthor)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).options(joinedload(models.Book.author)).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.put("/books/{book_id}", response_model=schemas.BookWithAuthor)
def update_book(book_id: int, book_update: schemas.BookUpdate, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
   
    if book_update.author_id is not None:
        author = db.query(models.Author).filter(models.Author.id == book_update.author_id).first()
        if not author:
            raise HTTPException(status_code=404, detail="Author not found")
    
    try:
        update_data = book_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(book, field, value)
        
        db.commit()
        db.refresh(book)
        
       
        book = db.query(models.Book).options(joinedload(models.Book.author)).filter(models.Book.id == book_id).first()
        return book
    except IntegrityError as e:
        db.rollback()
        if "isbn" in str(e):
            raise HTTPException(status_code=400, detail="ISBN already exists")
        raise HTTPException(status_code=400, detail="Database constraint violation")

@router.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    db.delete(book)
    db.commit()
    return None

@router.get("/authors/{author_id}/books", response_model=List[schemas.BookWithAuthor])
def get_books_by_author(author_id: int, db: Session = Depends(get_db)):
    author = db.query(models.Author).filter(models.Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    books = db.query(models.Book).options(joinedload(models.Book.author)).filter(models.Book.author_id == author_id).all()
    return books
