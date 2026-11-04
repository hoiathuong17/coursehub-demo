BEGIN;

-- Xóa cột note khỏi bảng enrollment_events khi rollback
ALTER TABLE enrollment_events
DROP COLUMN IF EXISTS note;

-- Xóa phiên bản migration 002 khỏi schema_migrations
DELETE FROM schema_migrations
WHERE version = '002';

COMMIT;

