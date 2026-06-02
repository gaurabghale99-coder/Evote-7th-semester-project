-- Migration: add password_hash column to voters
-- Run after adding email column.

ALTER TABLE voters ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
