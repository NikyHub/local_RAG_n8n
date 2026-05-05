-- Factory RAG System - Database Schema
-- This runs on first PostgreSQL startup

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('worker', 'leader', 'manager')),
    team_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    manager_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Query logs
CREATE TABLE IF NOT EXISTS query_logs (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(36) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT,
    sources JSONB,
    confidence FLOAT,
    session_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Experience reports
CREATE TABLE IF NOT EXISTS experience_reports (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(36) NOT NULL,
    title VARCHAR(200) NOT NULL,
    fault_description TEXT NOT NULL,
    solution TEXT NOT NULL,
    photos JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('draft', 'pending', 'approved', 'rejected')),
    reviewer_id VARCHAR(36),
    review_comment TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    doc_type VARCHAR(20) NOT NULL CHECK (doc_type IN ('manual', 'experience', 'guide')),
    file_path TEXT,
    uploaded_by VARCHAR(36),
    chunk_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'processing' CHECK (status IN ('processing', 'ready', 'error')),
    machine_type VARCHAR(100),
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Knowledge chunks (maps to Qdrant vectors)
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id VARCHAR(36) NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    qdrant_point_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_query_logs_user ON query_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_created ON query_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_experience_status ON experience_reports(status);
CREATE INDEX IF NOT EXISTS idx_experience_user ON experience_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
