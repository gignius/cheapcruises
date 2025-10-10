-- Migration: Add detailed cruise information fields
-- Run this on the production database

ALTER TABLE cruise_deals ADD COLUMN IF NOT EXISTS cabin_details TEXT;
ALTER TABLE cruise_deals ADD COLUMN IF NOT EXISTS itinerary TEXT;
ALTER TABLE cruise_deals ADD COLUMN IF NOT EXISTS ship_details TEXT;
ALTER TABLE cruise_deals ADD COLUMN IF NOT EXISTS inclusions TEXT;
