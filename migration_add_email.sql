-- Migration: add email column to voters and backfill placeholder emails
-- Run this script after the DB is created.

-- Add email column (unique, not null after backfill)
ALTER TABLE voters ADD COLUMN IF NOT EXISTS email VARCHAR(255);

-- Backfill placeholder emails using voter_id
DO $$
DECLARE r RECORD;
BEGIN
  FOR r IN SELECT voter_id FROM voters WHERE email IS NULL LOOP
    UPDATE voters SET email = format('voter%d@example.com', r.voter_id)
    WHERE voter_id = r.voter_id;
  END LOOP;
END $$;

-- Add unique constraint after backfill
ALTER TABLE voters ADD CONSTRAINT voters_email_key UNIQUE (email);
