-- ============================================================
-- 中级经济师备考助手 · Supabase 初始化 SQL（幂等可重复执行）
-- 用途：在 Supabase SQL Editor 粘贴整段执行，无论跑几遍都不会报错。
-- 对应代码中的 cloudPush / cloudPull：表 app_data，按 user_id upsert。
-- ============================================================

-- 1) 建表（IF NOT EXISTS，已存在则跳过）
CREATE TABLE IF NOT EXISTS app_data (
  user_id    text        PRIMARY KEY,                       -- 对应代码 currentUser
  payload    jsonb       NOT NULL DEFAULT '{}'::jsonb,       -- 对应云端同步的学习数据
  updated_at timestamptz NOT NULL DEFAULT now()              -- upsert 时由代码写入
);

-- 2) 开启行级安全（重复执行无害）
ALTER TABLE app_data ENABLE ROW LEVEL SECURITY;

-- 3) 访问策略：先删后建，保证幂等（解决 42710 "policy already exists"）
DROP POLICY IF EXISTS "Allow all for anon" ON app_data;
CREATE POLICY "Allow all for anon" ON app_data
  FOR ALL
  TO anon
  USING (true)
  WITH CHECK (true);

-- ============================================================
-- 可选：若希望不同用户严格隔离（anon 也能只读写自己的 user_id 行），
-- 可改用下面这条策略替换上面的 CREATE POLICY（同样 DROP + CREATE 幂等）。
-- 注意：anon 角色没有登录身份，user_id 由客户端传入，此策略仅做行级过滤，
-- 并不能真正防止他人用别的 user_id 读写——如需更强隔离需改用 authenticated 角色。
-- ============================================================
-- DROP POLICY IF EXISTS "Allow all for anon" ON app_data;
-- CREATE POLICY "Allow all for anon" ON app_data
--   FOR ALL
--   TO anon
--   USING (user_id = current_setting('request.jwt.claims', true)::json->>'sub')
--   WITH CHECK (user_id = current_setting('request.jwt.claims', true)::json->>'sub');
