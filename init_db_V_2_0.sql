-- ============================================================
-- Создание таблиц базы данных "Каталог книг (физическая библиотека)"
-- PostgreSQL 18.3
-- Пользователи — только владельцы библиотек (администраторы).
-- Читатели хранятся как атрибуты книги (borrower_*).
-- ============================================================

DROP TABLE IF EXISTS book_authors CASCADE;
DROP TABLE IF EXISTS book_genres CASCADE;
DROP TABLE IF EXISTS history CASCADE;
DROP TABLE IF EXISTS books CASCADE;
DROP TABLE IF EXISTS authors CASCADE;
DROP TABLE IF EXISTS genres CASCADE;
DROP TABLE IF EXISTS publishers CASCADE;
DROP TABLE IF EXISTS locations CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Таблица авторов
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sort_name VARCHAR(255)
);

-- Таблица жанров
CREATE TABLE genres (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- Таблица издателей
CREATE TABLE publishers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

-- Таблица мест расположения
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT
);

-- Таблица пользователей (только владельцы библиотек)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(30),
    password_hash VARCHAR(255) NOT NULL
);

-- Таблица книг
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    isbn VARCHAR(20) UNIQUE,
    udk VARCHAR(20),
    publication_year INTEGER CHECK (publication_year > 0 AND publication_year <= CAST(strftime('%Y', 'now') AS INTEGER) + 1),
    page_count INTEGER CHECK (page_count > 0),
    description TEXT,
    cover_image_path TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'в наличии' CHECK (status IN ('в наличии', 'выдана', 'утрачена')),
    -- данные читателя (заполняются при статусе 'выдана')
    borrower_name VARCHAR(255),
    borrower_address TEXT,
    borrower_phone VARCHAR(30),
    added_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    location_id INTEGER REFERENCES locations(id) ON DELETE SET NULL,
    publisher_id INTEGER REFERENCES publishers(id) ON DELETE SET NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
);

-- Функция автообновления modified_date
CREATE OR REPLACE FUNCTION update_modified_date()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_date = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_books_modified
    BEFORE UPDATE ON books
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_date();

-- Связь книги-авторы
CREATE TABLE book_authors (
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, author_id)
);

-- Связь книги-жанры
CREATE TABLE book_genres (
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    genre_id INTEGER NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, genre_id)
);

-- Таблица истории (все действия выполняются владельцами)
CREATE TABLE history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL CHECK (action IN ('добавление', 'удаление', 'редактирование', 'выдача', 'возврат')),
    action_timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы
CREATE INDEX idx_books_title ON books(title);
CREATE INDEX idx_books_isbn ON books(isbn);
CREATE INDEX idx_books_status ON books(status);
CREATE INDEX idx_books_location_id ON books(location_id);
CREATE INDEX idx_books_publisher_id ON books(publisher_id);
CREATE INDEX idx_books_user_id ON books(user_id);
CREATE INDEX idx_book_authors_book_id ON book_authors(book_id);
CREATE INDEX idx_book_authors_author_id ON book_authors(author_id);
CREATE INDEX idx_book_genres_book_id ON book_genres(book_id);
CREATE INDEX idx_book_genres_genre_id ON book_genres(genre_id);
CREATE INDEX idx_history_user_id ON history(user_id);
CREATE INDEX idx_history_book_id ON history(book_id);
CREATE INDEX idx_history_timestamp ON history(action_timestamp);

-- ============================================================
-- Тестовые данные
-- ============================================================

-- Авторы
INSERT INTO authors (name, sort_name) VALUES
('Лев Николаевич Толстой', 'Толстой, Л.Н.'),
('Фёдор Михайлович Достоевский', 'Достоевский, Ф.М.'),
('Джордж Оруэлл', 'Оруэлл, Дж.'),
('Михаил Булгаков', 'Булгаков, М.А.'),
('Джоан Роулинг', 'Роулинг, Дж.К.');

-- Жанры
INSERT INTO genres (name) VALUES
('Роман'),
('Философия'),
('Классика'),
('Антиутопия'),
('Фэнтези'),
('Сатира');

-- Издатели
INSERT INTO publishers (name) VALUES
('Эксмо'),
('АСТ'),
('Азбука-Аттикус');

-- Места расположения
INSERT INTO locations (name, description) VALUES
('Шкаф 1, полка 2', 'В гостиной, слева от окна'),
('Стеллаж Б, ряд 3', 'В кабинете'),
('Шкаф 2, полка 1', 'В спальне');

-- Пользователи (владельцы библиотек)
INSERT INTO users (username, email, phone, password_hash) VALUES
('admin', 'admin@library.local', '+7(000)000-00-00', 'hash_admin');
-- При необходимости можно добавить других владельцев, например:
-- ('maria', 'maria@library.local', '+7(111)222-33-44', 'hash_maria');

-- Книги (все принадлежат admin, user_id=1)
INSERT INTO books (title, isbn, udk, publication_year, page_count, description, cover_image_path, status, location_id, publisher_id, borrower_name, borrower_address, borrower_phone, user_id) VALUES
('Война и мир', '978-5-17-118343-5', '821.161.1', 1869, 1300, 'Всемирно известный роман-эпопея Л.Н. Толстого.', NULL, 'в наличии', 1, 1, NULL, NULL, NULL, 1),
('Преступление и наказание', '978-5-04-089636-7', '821.161.1', 1866, 672, 'Социально-психологический роман Достоевского.', NULL, 'в наличии', 1, 2, NULL, NULL, NULL, 1),
('1984', '978-5-389-08268-4', '821.111', 1949, 328, 'Классическая антиутопия Джорджа Оруэлла.', NULL, 'в наличии', 2, 3, NULL, NULL, NULL, 1),
('Скотный двор', '978-5-04-092121-2', '821.111', 1945, 112, 'Сатирическая повесть-притча.', NULL, 'в наличии', 2, 2, NULL, NULL, NULL, 1),
('Мастер и Маргарита', '978-5-17-109238-6', '821.161.1', 1967, 416, 'Мистический роман о дьяволе в Москве.', NULL, 'в наличии', 3, 1, NULL, NULL, NULL, 1),
('Гарри Поттер и философский камень', '978-5-389-08255-4', '821.111', 1997, 432, 'Первая книга о юном волшебнике.', NULL, 'в наличии', 2, 3, NULL, NULL, NULL, 1),
('Идиот', '978-5-04-096976-4', '821.161.1', 1869, 640, 'Роман о "положительно прекрасном человеке".', NULL, 'в наличии', 1, 2, NULL, NULL, NULL, 1),
('Анна Каренина', '978-5-04-089637-4', '821.161.1', 1877, 864, 'Трагедия любви в высшем обществе.', NULL, 'в наличии', 1, 1, NULL, NULL, NULL, 1),
('Гарри Поттер и Тайная комната', '978-5-389-08256-1', '821.111', 1998, 480, 'Вторая книга серии о Гарри Поттере.', NULL, 'выдана', 2, 3, 'Иванов Иван', 'ул. Пушкина, д.10', '+7(999)123-45-67', 1),
('Собачье сердце', '978-5-04-091812-0', '821.161.1', 1925, 160, 'Острая сатира на строительство нового общества.', NULL, 'в наличии', 3, 2, NULL, NULL, NULL, 1);

-- Связи книг с авторами
INSERT INTO book_authors (book_id, author_id) VALUES
(1, 1),   -- Война и мир -> Толстой
(2, 2),   -- Преступление и наказание -> Достоевский
(3, 3),   -- 1984 -> Оруэлл
(4, 3),   -- Скотный двор -> Оруэлл
(5, 4),   -- Мастер и Маргарита -> Булгаков
(6, 5),   -- Гарри Поттер 1 -> Роулинг
(7, 2),   -- Идиот -> Достоевский
(8, 1),   -- Анна Каренина -> Толстой
(9, 5),   -- Гарри Поттер 2 -> Роулинг
(10, 4);  -- Собачье сердце -> Булгаков

-- Связи книг с жанрами
INSERT INTO book_genres (book_id, genre_id) VALUES
(1, 1), (1, 3),               -- Война и мир: Роман, Классика
(2, 1), (2, 2), (2, 3),       -- Преступление и наказание: Роман, Философия, Классика
(3, 4), (3, 3),               -- 1984: Антиутопия, Классика
(4, 4), (4, 6),               -- Скотный двор: Антиутопия, Сатира
(5, 1), (5, 6), (5, 3),       -- Мастер и Маргарита: Роман, Сатира, Классика
(6, 5),                       -- Гарри Поттер: Фэнтези
(7, 1), (7, 2), (7, 3),       -- Идиот: Роман, Философия, Классика
(8, 1), (8, 3),               -- Анна Каренина: Роман, Классика
(9, 5),                       -- Гарри Поттер 2: Фэнтези
(10, 6), (10, 3);             -- Собачье сердце: Сатира, Классика

-- История действий (все действия выполняет admin, user_id=1)
INSERT INTO history (user_id, book_id, action, action_timestamp) VALUES
(1, 1, 'добавление', CURRENT_TIMESTAMP - INTERVAL '30 days'),
(1, 2, 'добавление', CURRENT_TIMESTAMP - INTERVAL '28 days'),
(1, 6, 'добавление', CURRENT_TIMESTAMP - INTERVAL '25 days'),
(1, 9, 'выдача', CURRENT_TIMESTAMP - INTERVAL '10 days'),
(1, 3, 'добавление', CURRENT_TIMESTAMP - INTERVAL '20 days'),
(1, 9, 'возврат', CURRENT_TIMESTAMP - INTERVAL '1 day');