-- Drop existing tables if they exist
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS enrollments CASCADE;

-- Create courses table
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    duration VARCHAR(50),
    summary TEXT,
    image VARCHAR(255),
    price FLOAT,
    description TEXT,
    courseObjectives JSONB,
    curriculum JSONB,
    targetAudience JSONB,
    courseBenefits JSONB,
    courseCompletion JSONB
);