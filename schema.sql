-- Create table to store user info
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    place TEXT NOT NULL,
    password_hash TEXT NOT NULL
);

-- ALTER TABLE users RENAME COLUMN password TO password_hash;

-- ideally you'd also do a data migration - here we'd hash all passwords