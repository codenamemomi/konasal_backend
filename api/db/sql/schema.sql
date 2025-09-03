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

CREATE TABLE enrollments (
    user_id UUID NOT NULL,
    course_id INTEGER NOT NULL,  -- Note: This should match courses.id type
    progress FLOAT,
    id UUID NOT NULL,
    time_created TIME WITH TIME ZONE,
    time_updated TIME WITH TIME ZONE,
    date_created DATE,
    date_updated DATE,
    PRIMARY KEY (user_id, course_id, id),
    FOREIGN KEY(course_id) REFERENCES courses(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);