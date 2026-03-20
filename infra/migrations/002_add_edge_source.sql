-- Migration 002: add source field to edges table
ALTER TABLE edges ADD COLUMN IF NOT EXISTS source VARCHAR(50) NOT NULL DEFAULT 'auto';
