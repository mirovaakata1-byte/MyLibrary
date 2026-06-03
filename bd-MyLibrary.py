import sqlite3
DB_NAME="Каталог_книг_(физическая библиотека).db"

with sqlite3.connect(DB_NAME) as conn:
    conn.execute("PRAGMA foreign_keys = ON")
    cur=conn.cursor()

    cur.executescript("""DROP TABLE IF EXISTS history;
                      DROP TABLE IF EXISTS book_authors;
                      DROP TABLE IF EXISTS book_genres;
                      DROP TABLE IF EXISTS books;
                      DROP TABLE IF EXISTS users;
                      DROP TABLE IF EXISTS locations;
                      DROP TABLE IF EXISTS publishers;
                      DROP TABLE IF EXISTS genres;
                      DROP TABLE IF EXISTS authors""")
#Таблица авторов
    cur.executescript("""CREATE TABLE authors
                      (id_authors INTEGER PRIMARY KEY,
                      name_authors TEXT NOT NULL,
                      sort_name TEXT)""")
#Таблица жанров   
    cur.executescript("""CREATE TABLE genres
                      (id_genre INTEGER PRIMARY KEY,
                      name_genre TEXT NOT NULL)""")
#Таблица издателей   
    cur.executescript("""CREATE TABLE publishers
                      (id_publisher INTEGER PRIMARY KEY,
                      name_publishers TEXT NOT NULL)""")
#Таблица мест расположения    
    cur.executescript("""CREATE TABLE locations
                      (id_location INTEGER PRIMARY KEY,
                      location_room TEXT, 
                      location_wardrobe INTEGER NOT NULL,
                      location_shelf INTEGER NOT NULL,
                      description TEXT)""")
#Таблица пользователей
    cur.executescript("""CREATE TABLE users 
                      (id_user INTEGER PRIMARY KEY,
                      username TEXT NOT NULL,
                      email TEXT NOT NULL UNIQUE,
                      phone TEXT,
                      password_hash TEXT NOT NULL)""")
    
    cur.executescript("""CREATE TABLE books
                      (id_book INTEGER PRIMARY KEY,
                      book_title TEXT NOT NULL,
                      isbn TEXT UNIQUE,
                      udk TEXT,
                      publication_year INTEGER CHECK (publication_year > 0 AND publication_year <= CAST(strftime('%%Y', 'now') AS INTEGER) + 1),
                      page_count INTEGER CHECK (page_count > 0),
                      description TEXT,
                      cover_image_path TEXT,
                      status TEXT NOT NULL DEFAULT 'в наличии' CHECK (status IN ('в наличии', 'выдана', 'утрачена')), 
                      added_date TEXT DEFAULT CURRENT_TIMESTAMP,
                      modified_date DEFAULT CURRENT_TIMESTAMP,
                      publisher_id INTEGER,
                      location_id INTEGER,
                      user_id INTEGER NOT NULL,
                      FOREIGN KEY (publisher_id) REFERENCES publishers (id_publisher),
                      FOREIGN KEY (location_id) REFERENCES locations (id_location),
                      FOREIGN KEY (user_id) REFERENCES users (id_user))""")
    
    cur.executescript("""CREATE TABLE book_genres
                      (book_id INTEGER NOT NULL,
                      genre_id INTEGER NOT NULL,
                      FOREIGN KEY (book_id) REFERENCES books (id_book),
                      FOREIGN KEY (genre_id) REFERENCES genres (id_genre))""")
    
    cur.executescript("""CREATE TABLE book_authors
                      (book_id INTEGER NOT NULL,
                      author_id INTEGER NOT NULL,
                      FOREIGN KEY (book_id) REFERENCES books (id_book),
                      FOREIGN KEY (author_id) REFERENCES authors (id_authors))""")
    
    cur.executescript("""CREATE TABLE history
                      (id_history INTEGER PRIMARY KEY,
                      user_id INTEGER NOT NULL,
                      book_id INTEGER NOT NULL,
                      action TEXT NOT NULL DEFAULT 'добавление' CHECK (action IN ('добавление', 'удаление', 'редактирование', 'выдача', 'возврат')),
                      action_timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (user_id) REFERENCES users (id_user),
                      FOREIGN KEY (book_id) REFERENCES books (id_book))""")
        
print ("ВСЕ ТАБЛИЦЫ СОЗДАНЫ!!!")