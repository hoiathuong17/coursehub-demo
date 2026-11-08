BEGIN;

-- Bổ sung cột note VARCHAR(200) cho bảng enrollment_events
ALTER TABLE enrollment_events
ADD COLUMN note VARCHAR(200);

-- Ghi nhận phiên bản migration 002 vào bảng theo dõi schema_migrations
INSERT INTO schema_migrations (version, description)
VALUES ('002', 'Add note column to enrollment_events');

COMMIT;

