-- 添加 version_id 列到 dialog_histories 表
ALTER TABLE dialog_histories 
ADD COLUMN IF NOT EXISTS version_id INTEGER;

-- 添加外键约束
ALTER TABLE dialog_histories 
ADD CONSTRAINT fk_dialog_histories_version_id 
FOREIGN KEY (version_id) 
REFERENCES analysis_session_versions(id) 
ON DELETE SET NULL;

-- 验证
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'dialog_histories';
