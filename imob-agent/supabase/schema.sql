-- ============================================================
-- BLOCO 1 — Executar no Supabase Dashboard
-- URL: https://supabase.com/dashboard/project/romukfrgzzhnxntessft
-- Seção: SQL Editor
-- ============================================================

-- Habilitar extensão pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabela de base de conhecimento (RAG)
CREATE TABLE IF NOT EXISTS knowledge_base (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    content     TEXT        NOT NULL,
    embedding   vector(768),
    category    TEXT,
    metadata    JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Função de busca semântica por similaridade coseno
CREATE OR REPLACE FUNCTION match_knowledge(
    query_embedding  vector(768),
    match_threshold  float   DEFAULT 0.75,
    match_count      int     DEFAULT 3
)
RETURNS TABLE (
    id          UUID,
    content     TEXT,
    category    TEXT,
    similarity  float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        kb.id,
        kb.content,
        kb.category,
        1 - (kb.embedding <=> query_embedding) AS similarity
    FROM knowledge_base kb
    WHERE 1 - (kb.embedding <=> query_embedding) >= match_threshold
    ORDER BY kb.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Índice IVFFLAT para busca vetorial aproximada (ANN)
CREATE INDEX IF NOT EXISTS knowledge_base_embedding_idx
    ON knowledge_base
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);


-- ============================================================
-- BLOCO 2 — Executar no PostgreSQL do Dokploy
-- Conexão: postgresql://imobiliaria:****@agente-imobilirio-postgresai-x6dyqc:5432/postgress_memory
-- ============================================================

-- Tabela de conversas
CREATE TABLE IF NOT EXISTS conversations (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    phone       TEXT        NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    status      TEXT        DEFAULT 'active'
);

-- Tabela de mensagens por conversa
CREATE TABLE IF NOT EXISTS messages (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    phone       TEXT        NOT NULL,
    role        TEXT        NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT        NOT NULL,
    intent      TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para performance em consultas por número e ordenação temporal
CREATE INDEX IF NOT EXISTS messages_phone_idx
    ON messages (phone);

CREATE INDEX IF NOT EXISTS messages_created_at_idx
    ON messages (created_at DESC);
