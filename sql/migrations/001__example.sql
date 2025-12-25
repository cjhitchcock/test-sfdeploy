-- Example migration: create a sample table if not exists
CREATE TABLE IF NOT EXISTS sample_table (
  id NUMBER PRIMARY KEY,
  created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP
);
