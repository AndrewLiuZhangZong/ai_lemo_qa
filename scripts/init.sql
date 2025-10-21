-- AI智能客服问答系统 - 数据库初始化脚本

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 知识库表
CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100),
    keywords TEXT[],
    milvus_id BIGINT,  -- 对应Milvus中的向量ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status INTEGER DEFAULT 1 CHECK (status IN (0, 1)),  -- 0:草稿 1:已发布
    source VARCHAR(200),
    CONSTRAINT knowledge_base_question_check CHECK (char_length(question) > 0),
    CONSTRAINT knowledge_base_answer_check CHECK (char_length(answer) > 0)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_base(category);
CREATE INDEX IF NOT EXISTS idx_kb_status ON knowledge_base(status);
CREATE INDEX IF NOT EXISTS idx_kb_created_at ON knowledge_base(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_kb_milvus_id ON knowledge_base(milvus_id);
CREATE INDEX IF NOT EXISTS idx_kb_question_gin ON knowledge_base USING gin(question gin_trgm_ops);

-- 对话历史表
CREATE TABLE IF NOT EXISTS conversation_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(100),
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    intent VARCHAR(100),
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    knowledge_id INTEGER REFERENCES knowledge_base(id),
    feedback INTEGER CHECK (feedback IN (-1, 0, 1)),  -- -1:不满意 0:未评价 1:满意
    response_time INTEGER,  -- 响应时间(毫秒)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_ch_session_id ON conversation_history(session_id);
CREATE INDEX IF NOT EXISTS idx_ch_user_id ON conversation_history(user_id);
CREATE INDEX IF NOT EXISTS idx_ch_created_at ON conversation_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ch_intent ON conversation_history(intent);
CREATE INDEX IF NOT EXISTS idx_ch_feedback ON conversation_history(feedback);

-- 用户反馈表
CREATE TABLE IF NOT EXISTS user_feedback (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversation_history(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_uf_conversation_id ON user_feedback(conversation_id);
CREATE INDEX IF NOT EXISTS idx_uf_rating ON user_feedback(rating);
CREATE INDEX IF NOT EXISTS idx_uf_created_at ON user_feedback(created_at DESC);

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认配置
INSERT INTO system_config (config_key, config_value, description) VALUES
    ('confidence_threshold', '0.7', '答案匹配置信度阈值'),
    ('max_context_turns', '5', '最大上下文轮数'),
    ('session_timeout', '1800', '会话超时时间(秒)'),
    ('enable_sensitive_filter', 'true', '是否启用敏感词过滤'),
    ('similar_questions_count', '3', '推荐相似问题数量')
ON CONFLICT (config_key) DO NOTHING;

-- 敏感词表
CREATE TABLE IF NOT EXISTS sensitive_words (
    id SERIAL PRIMARY KEY,
    word VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_sw_word ON sensitive_words(word);
CREATE INDEX IF NOT EXISTS idx_sw_category ON sensitive_words(category);

-- 统计报表视图
CREATE OR REPLACE VIEW v_daily_stats AS
SELECT 
    DATE(created_at) as stat_date,
    COUNT(*) as total_conversations,
    COUNT(DISTINCT session_id) as unique_sessions,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(confidence) as avg_confidence,
    AVG(response_time) as avg_response_time,
    SUM(CASE WHEN feedback = 1 THEN 1 ELSE 0 END) as positive_feedback,
    SUM(CASE WHEN feedback = -1 THEN 1 ELSE 0 END) as negative_feedback,
    SUM(CASE WHEN feedback = 0 THEN 1 ELSE 0 END) as no_feedback
FROM conversation_history
GROUP BY DATE(created_at)
ORDER BY stat_date DESC;

-- 热门问题视图
CREATE OR REPLACE VIEW v_hot_questions AS
SELECT 
    kb.id,
    kb.question,
    kb.category,
    COUNT(ch.id) as ask_count,
    AVG(ch.confidence) as avg_confidence,
    SUM(CASE WHEN ch.feedback = 1 THEN 1 ELSE 0 END) as positive_count
FROM knowledge_base kb
LEFT JOIN conversation_history ch ON kb.id = ch.knowledge_id
WHERE kb.status = 1
GROUP BY kb.id, kb.question, kb.category
ORDER BY ask_count DESC
LIMIT 100;

-- 更新时间戳触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为knowledge_base表添加触发器
DROP TRIGGER IF EXISTS update_kb_updated_at ON knowledge_base;
CREATE TRIGGER update_kb_updated_at
    BEFORE UPDATE ON knowledge_base
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 为system_config表添加触发器
DROP TRIGGER IF EXISTS update_sc_updated_at ON system_config;
CREATE TRIGGER update_sc_updated_at
    BEFORE UPDATE ON system_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入示例数据（用于测试）
INSERT INTO knowledge_base (question, answer, category, keywords) VALUES
    ('如何退货？', '您可以在订单页面点击"申请退货"，选择退货原因并提交。我们会在1-2个工作日内处理您的退货申请。退货商品需保持原包装完好，未使用。', '售后服务', ARRAY['退货', '售后', '退款']),
    ('退货需要多久？', '退货申请提交后，我们会在1-2个工作日内审核。审核通过后，请您寄回商品。我们收到商品后3-5个工作日内完成退款，款项将原路返回。', '售后服务', ARRAY['退货', '时间', '退款']),
    ('支持哪些支付方式？', '我们支持多种支付方式：微信支付、支付宝、银行卡、花呗、信用卡等。您可以在结算页面选择合适的支付方式。', '支付问题', ARRAY['支付', '付款', '方式']),
    ('配送时间是多久？', '一般情况下，订单在24小时内发货。普通快递3-5天到达，偏远地区可能需要5-7天。您可以在订单详情页查看物流信息。', '物流配送', ARRAY['配送', '物流', '快递', '时间']),
    ('如何修改订单？', '订单提交后30分钟内可以自助修改。进入"我的订单"，选择需要修改的订单，点击"修改订单"即可。超过30分钟请联系客服协助处理。', '订单问题', ARRAY['订单', '修改', '更改']),
    ('忘记密码怎么办？', '点击登录页面的"忘记密码"，输入注册手机号，通过短信验证码即可重置密码。如手机号已停用，请联系客服处理。', '账号问题', ARRAY['密码', '重置', '找回', '账号']),
    ('如何申请发票？', '您可以在订单完成后的"订单详情"页面申请发票。支持电子发票和纸质发票，电子发票即时开具，纸质发票会随商品一起寄出。', '发票问题', ARRAY['发票', '开票', '报销']),
    ('商品可以换货吗？', '可以的。如果收到的商品有质量问题或尺寸不合适，可以在签收后7天内申请换货。换货商品需保持吊牌完整、未洗涤。', '售后服务', ARRAY['换货', '更换', '售后']),
    ('会员有什么权益？', '会员享有：积分返现、生日礼券、专属折扣、优先客服、免费退换货、新品试用等多项权益。会员等级越高，权益越丰富。', '会员相关', ARRAY['会员', '权益', 'VIP', '特权']),
    ('如何联系客服？', '您可以通过以下方式联系我们：1) 在线客服（网站右下角）；2) 客服电话：400-123-4567（工作日9:00-18:00）；3) 官方微信公众号留言。', '客服咨询', ARRAY['客服', '联系', '咨询', '电话'])
ON CONFLICT DO NOTHING;

-- 创建数据库用户权限（如需要）
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO lemo_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO lemo_user;

-- 输出初始化完成信息
DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'AI智能客服问答系统数据库初始化完成！';
    RAISE NOTICE '===========================================';
    RAISE NOTICE '数据库名称: ai_lemo_qa';
    RAISE NOTICE '已创建表:';
    RAISE NOTICE '  - knowledge_base (知识库)';
    RAISE NOTICE '  - conversation_history (对话历史)';
    RAISE NOTICE '  - user_feedback (用户反馈)';
    RAISE NOTICE '  - system_config (系统配置)';
    RAISE NOTICE '  - sensitive_words (敏感词)';
    RAISE NOTICE '已创建视图:';
    RAISE NOTICE '  - v_daily_stats (每日统计)';
    RAISE NOTICE '  - v_hot_questions (热门问题)';
    RAISE NOTICE '示例数据: 已插入10条知识库数据';
    RAISE NOTICE '===========================================';
END $$;

