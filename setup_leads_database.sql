-- =====================================================
-- SISTEMA DE LEADS - CONSCÓRCIO TRIÂNGULO
-- Script Completo para Execução Única
-- =====================================================

-- Configurações iniciais
SET client_min_messages = WARNING;
SET default_transaction_isolation = 'read committed';

-- Pré-requisitos
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

BEGIN;

-- =====================================================
-- 1. FUNÇÕES AUXILIARES
-- =====================================================

-- Função para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Função para atualizar last_interaction_at automaticamente
CREATE OR REPLACE FUNCTION update_lead_last_interaction()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE leads 
    SET last_interaction_at = NEW.created_at 
    WHERE id = NEW.lead_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 2. TABELAS
-- =====================================================

-- Tabela principal de leads
DROP TABLE IF EXISTS leads CASCADE;
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome VARCHAR(255) NOT NULL,
    documento VARCHAR(20),
    email VARCHAR(255),
    telefone VARCHAR(20),
    origem VARCHAR(100) NOT NULL DEFAULT 'manual',
    etapa VARCHAR(50) DEFAULT 'novo' 
        CHECK (etapa IN ('novo', 'qualificado', 'proposta', 'fechado', 'perdido')),
    score INTEGER DEFAULT 0 
        CHECK (score >= 0 AND score <= 100),
    classificacao VARCHAR(20) DEFAULT 'frio' 
        CHECK (classificacao IN ('quente', 'morno', 'frio')),
    status VARCHAR(20) DEFAULT 'ativo' 
        CHECK (status IN ('ativo', 'inativo', 'convertido')),
    observacoes TEXT,
    dados_extras JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_interaction_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT uq_leads_documento UNIQUE (documento)
);

-- Interações com leads
DROP TABLE IF EXISTS lead_interactions CASCADE;
CREATE TABLE lead_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL,
    canal VARCHAR(50) NOT NULL DEFAULT 'manual',
    tipo VARCHAR(50) NOT NULL DEFAULT 'contato',
    conteudo TEXT,
    direcao VARCHAR(10) DEFAULT 'entrada' 
        CHECK (direcao IN ('entrada', 'saida')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_interactions_lead FOREIGN KEY (lead_id) 
        REFERENCES leads(id) ON DELETE CASCADE
);

-- Campanhas de nutrição
DROP TABLE IF EXISTS campanhas CASCADE;
CREATE TABLE campanhas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome VARCHAR(255) NOT NULL,
    tipo VARCHAR(50) NOT NULL DEFAULT 'email',
    status VARCHAR(20) DEFAULT 'ativa' 
        CHECK (status IN ('ativa', 'pausada', 'finalizada')),
    segmento VARCHAR(100),
    template_conteudo TEXT,
    agendamento JSONB DEFAULT '{}',
    metricas JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT uq_campanhas_nome UNIQUE (nome)
);

-- Participação em campanhas
DROP TABLE IF EXISTS campanha_participantes CASCADE;
CREATE TABLE campanha_participantes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campanha_id UUID NOT NULL,
    lead_id UUID NOT NULL,
    status VARCHAR(20) DEFAULT 'enviado' 
        CHECK (status IN ('enviado', 'entregue', 'aberto', 'clicado', 'convertido', 'erro')),
    enviado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    aberto_em TIMESTAMP WITH TIME ZONE,
    clicado_em TIMESTAMP WITH TIME ZONE,
    convertido_em TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT fk_participantes_campanha FOREIGN KEY (campanha_id) 
        REFERENCES campanhas(id) ON DELETE CASCADE,
    CONSTRAINT fk_participantes_lead FOREIGN KEY (lead_id) 
        REFERENCES leads(id) ON DELETE CASCADE,
    CONSTRAINT uq_campanha_lead UNIQUE(campanha_id, lead_id)
);

-- Propostas e contratos
DROP TABLE IF EXISTS propostas CASCADE;
CREATE TABLE propostas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL,
    numero_contrato INTEGER,
    codigo_grupo INTEGER,
    codigo_bem INTEGER,
    prazo INTEGER,
    valor_total DECIMAL(15,2),
    status VARCHAR(50) DEFAULT 'rascunho' 
        CHECK (status IN ('rascunho', 'enviada', 'assinada', 'cancelada')),
    dados_proposta JSONB DEFAULT '{}',
    pdf_base64 TEXT,
    envelope_docusign_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_propostas_lead FOREIGN KEY (lead_id) 
        REFERENCES leads(id) ON DELETE RESTRICT,
    CONSTRAINT uq_numero_contrato UNIQUE (numero_contrato)
);

-- Feedback e satisfação
DROP TABLE IF EXISTS feedbacks CASCADE;
CREATE TABLE feedbacks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID,
    proposta_id UUID,
    tipo VARCHAR(50) NOT NULL DEFAULT 'satisfacao',
    conteudo TEXT NOT NULL,
    sentimento VARCHAR(20) 
        CHECK (sentimento IN ('positivo', 'neutro', 'negativo')),
    score_sentimento DECIMAL(3,2) 
        CHECK (score_sentimento >= 0.00 AND score_sentimento <= 1.00),
    canal VARCHAR(50) DEFAULT 'manual',
    status VARCHAR(20) DEFAULT 'novo' 
        CHECK (status IN ('novo', 'processado', 'respondido', 'fechado')),
    resposta TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processado_em TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT fk_feedbacks_lead FOREIGN KEY (lead_id) 
        REFERENCES leads(id) ON DELETE SET NULL,
    CONSTRAINT fk_feedbacks_proposta FOREIGN KEY (proposta_id) 
        REFERENCES propostas(id) ON DELETE SET NULL
);

-- Métricas diárias
DROP TABLE IF EXISTS metricas_leads CASCADE;
CREATE TABLE metricas_leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    data DATE NOT NULL,
    total_leads INTEGER DEFAULT 0,
    leads_quentes INTEGER DEFAULT 0,
    leads_mornos INTEGER DEFAULT 0,
    leads_frios INTEGER DEFAULT 0,
    conversoes INTEGER DEFAULT 0,
    taxa_conversao DECIMAL(5,2) DEFAULT 0.00,
    engajamento_medio DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT uq_metricas_data UNIQUE (data)
);

-- =====================================================
-- 3. ÍNDICES
-- =====================================================

-- Leads
CREATE INDEX idx_leads_classificacao ON leads(classificacao);
CREATE INDEX idx_leads_origem ON leads(origem);
CREATE INDEX idx_leads_etapa ON leads(etapa);
CREATE INDEX idx_leads_score ON leads(score);
CREATE INDEX idx_leads_created_at ON leads(created_at);
CREATE INDEX idx_leads_last_interaction ON leads(last_interaction_at);
CREATE INDEX idx_leads_email ON leads(email) WHERE email IS NOT NULL;
CREATE INDEX idx_leads_status ON leads(status);

-- Interações
CREATE INDEX idx_interactions_lead_id ON lead_interactions(lead_id);
CREATE INDEX idx_interactions_canal ON lead_interactions(canal);
CREATE INDEX idx_interactions_tipo ON lead_interactions(tipo);
CREATE INDEX idx_interactions_created_at ON lead_interactions(created_at);

-- Campanhas
CREATE INDEX idx_campanha_participantes_campanha ON campanha_participantes(campanha_id);
CREATE INDEX idx_campanha_participantes_lead ON campanha_participantes(lead_id);
CREATE INDEX idx_campanha_participantes_status ON campanha_participantes(status);

-- Propostas
CREATE INDEX idx_propostas_lead_id ON propostas(lead_id);
CREATE INDEX idx_propostas_status ON propostas(status);

-- Feedbacks
CREATE INDEX idx_feedbacks_lead_id ON feedbacks(lead_id);
CREATE INDEX idx_feedbacks_sentimento ON feedbacks(sentimento);
CREATE INDEX idx_feedbacks_status ON feedbacks(status);

-- =====================================================
-- 4. TRIGGERS
-- =====================================================

-- Triggers para updated_at
CREATE TRIGGER update_leads_updated_at 
    BEFORE UPDATE ON leads 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campanhas_updated_at 
    BEFORE UPDATE ON campanhas 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_propostas_updated_at 
    BEFORE UPDATE ON propostas 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger para atualizar last_interaction_at
CREATE TRIGGER update_lead_interaction_time 
    AFTER INSERT ON lead_interactions 
    FOR EACH ROW EXECUTE FUNCTION update_lead_last_interaction();

-- =====================================================
-- 5. FUNÇÕES DE NEGÓCIO
-- =====================================================

-- Função para calcular score automático
CREATE OR REPLACE FUNCTION calcular_score_lead(lead_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
    score_calculado INTEGER := 0;
    total_interacoes INTEGER;
    dias_ultima_interacao INTEGER;
    total_propostas INTEGER;
    propostas_assinadas INTEGER;
BEGIN
    -- Contar interações (cada uma vale 10 pontos)
    SELECT COUNT(*) INTO total_interacoes 
    FROM lead_interactions 
    WHERE lead_id = lead_uuid;
    
    score_calculado := score_calculado + (total_interacoes * 10);
    
    -- Verificar última interação
    SELECT (CURRENT_DATE - last_interaction_at::DATE) INTO dias_ultima_interacao
    FROM leads 
    WHERE id = lead_uuid;
    
    -- Pontuação por recência
    CASE 
        WHEN dias_ultima_interacao <= 1 THEN
            score_calculado := score_calculado + 30;
        WHEN dias_ultima_interacao <= 7 THEN
            score_calculado := score_calculado + 20;
        WHEN dias_ultima_interacao <= 30 THEN
            score_calculado := score_calculado + 10;
        ELSE
            score_calculado := score_calculado - 5;
    END CASE;
    
    -- Contar propostas (cada uma vale 25 pontos)
    SELECT COUNT(*) INTO total_propostas 
    FROM propostas 
    WHERE lead_id = lead_uuid;
    
    score_calculado := score_calculado + (total_propostas * 25);
    
    -- Bonus por propostas assinadas (vale 50 pontos cada)
    SELECT COUNT(*) INTO propostas_assinadas 
    FROM propostas 
    WHERE lead_id = lead_uuid AND status = 'assinada';
    
    score_calculado := score_calculado + (propostas_assinadas * 50);
    
    -- Limitar entre 0 e 100
    score_calculado := GREATEST(0, LEAST(100, score_calculado));
    
    RETURN score_calculado;
END;
$$ LANGUAGE plpgsql;

-- Função para classificar lead automaticamente
CREATE OR REPLACE FUNCTION classificar_lead(score_value INTEGER)
RETURNS VARCHAR(20) AS $$
BEGIN
    RETURN CASE 
        WHEN score_value >= 80 THEN 'quente'
        WHEN score_value >= 50 THEN 'morno'
        ELSE 'frio'
    END;
END;
$$ LANGUAGE plpgsql;

-- Função para atualizar score e classificação
CREATE OR REPLACE FUNCTION atualizar_lead_score(lead_uuid UUID)
RETURNS VOID AS $$
DECLARE
    novo_score INTEGER;
    nova_classificacao VARCHAR(20);
BEGIN
    novo_score := calcular_score_lead(lead_uuid);
    nova_classificacao := classificar_lead(novo_score);
    
    UPDATE leads 
    SET score = novo_score, 
        classificacao = nova_classificacao
    WHERE id = lead_uuid;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 6. VIEWS
-- =====================================================

-- View para dashboard de leads
CREATE OR REPLACE VIEW vw_dashboard_leads AS
SELECT 
    DATE(created_at) AS data,
    COUNT(*) AS total_leads,
    COUNT(*) FILTER (WHERE classificacao = 'quente') AS leads_quentes,
    COUNT(*) FILTER (WHERE classificacao = 'morno') AS leads_mornos,
    COUNT(*) FILTER (WHERE classificacao = 'frio') AS leads_frios,
    COUNT(*) FILTER (WHERE etapa = 'fechado') AS conversoes,
    ROUND(AVG(score), 2) AS score_medio,
    COUNT(DISTINCT origem) AS origens_distintas
FROM leads 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY data DESC;

-- View para performance de campanhas
CREATE OR REPLACE VIEW vw_performance_campanhas AS
SELECT 
    c.nome AS campanha,
    c.tipo,
    c.status,
    COUNT(cp.id) AS total_enviados,
    COUNT(*) FILTER (WHERE cp.status = 'aberto') AS abertos,
    COUNT(*) FILTER (WHERE cp.status = 'clicado') AS clicados,
    COUNT(*) FILTER (WHERE cp.status = 'convertido') AS convertidos,
    COALESCE(
        ROUND(COUNT(*) FILTER (WHERE cp.status = 'aberto') * 100.0 / NULLIF(COUNT(cp.id), 0), 2), 
        0
    ) AS taxa_abertura,
    COALESCE(
        ROUND(COUNT(*) FILTER (WHERE cp.status = 'clicado') * 100.0 / NULLIF(COUNT(cp.id), 0), 2), 
        0
    ) AS taxa_clique,
    COALESCE(
        ROUND(COUNT(*) FILTER (WHERE cp.status = 'convertido') * 100.0 / NULLIF(COUNT(cp.id), 0), 2), 
        0
    ) AS taxa_conversao
FROM campanhas c
LEFT JOIN campanha_participantes cp ON c.id = cp.campanha_id
GROUP BY c.id, c.nome, c.tipo, c.status;

-- View para leads ativos com resumo
CREATE OR REPLACE VIEW vw_leads_ativos AS
SELECT 
    l.*,
    COUNT(li.id) AS total_interacoes,
    MAX(li.created_at) AS ultima_interacao_completa,
    COUNT(p.id) AS total_propostas,
    COUNT(*) FILTER (WHERE p.status = 'assinada') AS propostas_assinadas,
    COALESCE(SUM(p.valor_total) FILTER (WHERE p.status = 'assinada'), 0) AS valor_total_assinado
FROM leads l
LEFT JOIN lead_interactions li ON l.id = li.lead_id
LEFT JOIN propostas p ON l.id = p.lead_id
WHERE l.status = 'ativo'
GROUP BY l.id;

-- =====================================================
-- 7. DADOS INICIAIS (SEEDS)
-- =====================================================

-- Inserir campanhas padrão
INSERT INTO campanhas (nome, tipo, status, template_conteudo) VALUES
('Boas-vindas', 'email', 'ativa', 'Bem-vindo ao Consórcio Triângulo! Conheça nossos produtos.'),
('Nutrição - Produtos', 'email', 'ativa', 'Descubra as vantagens do consórcio para você.'),
('Follow-up Manual', 'manual', 'ativa', 'Contato telefônico de follow-up.'),
('Reativação', 'email', 'ativa', 'Não perca esta oportunidade única!'),
('Onboarding Novos Leads', 'email', 'ativa', 'Sequência de boas-vindas para novos interessados.');

-- Inserir leads de exemplo
INSERT INTO leads (nome, documento, email, telefone, origem, classificacao, score, observacoes) VALUES
('João Silva Santos', '12345678901', 'joao.silva@email.com', '(11) 99999-9999', 'site', 'quente', 85, 'Interessado em consórcio de carro popular. Tem entrada guardada.'),
('Maria Oliveira Costa', '98765432100', 'maria.oliveira@email.com', '(11) 98888-8888', 'indicacao', 'morno', 60, 'Consultou sobre consórcio imobiliário. Primeira casa própria.'),
('Pedro Henrique Souza', '11122233344', 'pedro.souza@email.com', '(11) 97777-7777', 'whatsapp', 'frio', 25, 'Primeiro contato via WhatsApp. Ainda pesquisando.'),
('Ana Clara Ferreira', '55566677788', 'ana.ferreira@email.com', '(11) 96666-6666', 'forms', 'morno', 55, 'Preencheu formulário no site. Interessada em moto.'),
('Carlos Eduardo Lima', '99988877766', 'carlos.lima@email.com', '(11) 95555-5555', 'manual', 'quente', 90, 'Cliente antigo retornando. Já teve consórcio conosco.');

-- Inserir interações para os leads
INSERT INTO lead_interactions (lead_id, canal, tipo, conteudo, direcao) 
SELECT 
    l.id,
    CASE l.origem 
        WHEN 'site' THEN 'web'
        WHEN 'whatsapp' THEN 'whatsapp'
        WHEN 'forms' THEN 'web'
        ELSE 'telefone'
    END,
    'contato_inicial',
    'Primeiro contato realizado com ' || l.nome || '. Origem: ' || l.origem,
    'entrada'
FROM leads l;

-- Inserir algumas interações de follow-up
INSERT INTO lead_interactions (lead_id, canal, tipo, conteudo, direcao) 
SELECT 
    l.id,
    'telefone',
    'follow_up',
    'Follow-up telefônico realizado. Lead ' || l.classificacao,
    'saida'
FROM leads l 
WHERE l.classificacao IN ('quente', 'morno')
LIMIT 3;

-- Inserir propostas de exemplo
INSERT INTO propostas (lead_id, numero_contrato, codigo_grupo, codigo_bem, prazo, valor_total, status, dados_proposta)
SELECT 
    l.id,
    ROW_NUMBER() OVER () + 1000,
    ROW_NUMBER() OVER () + 100,
    CASE l.nome 
        WHEN 'João Silva Santos' THEN 1001
        WHEN 'Carlos Eduardo Lima' THEN 2001
        ELSE 1501
    END,
    CASE l.classificacao 
        WHEN 'quente' THEN 60
        ELSE 80
    END,
    CASE l.nome 
        WHEN 'João Silva Santos' THEN 25000.00
        WHEN 'Carlos Eduardo Lima' THEN 45000.00
        ELSE 35000.00
    END,
    CASE l.classificacao 
        WHEN 'quente' THEN 'enviada'
        ELSE 'rascunho'
    END,
    json_build_object(
        'tipo_bem', CASE l.nome WHEN 'João Silva Santos' THEN 'Carro Popular' ELSE 'Imóvel' END,
        'parcela_mensal', CASE l.nome WHEN 'João Silva Santos' THEN 416.67 ELSE 437.50 END
    )::jsonb
FROM leads l 
WHERE l.classificacao IN ('quente', 'morno')
LIMIT 3;

-- =====================================================
-- 8. COMENTÁRIOS PARA DOCUMENTAÇÃO
-- =====================================================

COMMENT ON TABLE leads IS 'Tabela principal de leads com classificação automática e scoring inteligente';
COMMENT ON TABLE lead_interactions IS 'Histórico completo de interações com leads (omnichannel)';
COMMENT ON TABLE campanhas IS 'Campanhas de nutrição, marketing e automação';
COMMENT ON TABLE campanha_participantes IS 'Participação e métricas de leads em campanhas';
COMMENT ON TABLE propostas IS 'Propostas comerciais e contratos gerados';
COMMENT ON TABLE feedbacks IS 'Feedback dos clientes com análise de sentimento';
COMMENT ON TABLE metricas_leads IS 'Métricas agregadas para dashboards e relatórios';

COMMENT ON COLUMN leads.score IS 'Score automático 0-100: interações (10pts), recência (30pts), propostas (25pts), assinadas (50pts)';
COMMENT ON COLUMN leads.classificacao IS 'Classificação automática: quente (80+), morno (50-79), frio (0-49)';
COMMENT ON COLUMN leads.origem IS 'Canal de origem: manual, site, whatsapp, forms, indicacao, crm';
COMMENT ON COLUMN leads.dados_extras IS 'Dados específicos do canal de origem e informações extras';

COMMIT;

-- =====================================================
-- 9. VERIFICAÇÃO E RELATÓRIO FINAL
-- =====================================================

-- Função para gerar relatório de instalação
DO $
DECLARE
    tabelas_count INTEGER;
    indices_count INTEGER;
    funcoes_count INTEGER;
    views_count INTEGER;
    leads_count INTEGER;
BEGIN
    -- Contar objetos criados
    SELECT COUNT(*) INTO tabelas_count
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
      AND table_name IN ('leads','lead_interactions','campanhas','campanha_participantes','propostas','feedbacks','metricas_leads');
    
    SELECT COUNT(*) INTO indices_count
    FROM pg_indexes 
    WHERE schemaname = 'public' 
      AND indexname LIKE 'idx_%';
    
    SELECT COUNT(*) INTO funcoes_count
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public' 
      AND p.proname IN ('calcular_score_lead', 'classificar_lead', 'atualizar_lead_score');
    
    SELECT COUNT(*) INTO views_count
    FROM information_schema.views
    WHERE table_schema = 'public'
      AND table_name LIKE 'vw_%';
      
    SELECT COUNT(*) INTO leads_count FROM leads;
    
    -- Exibir relatório
    RAISE NOTICE '';
    RAISE NOTICE '======================================================';
    RAISE NOTICE '✅ SISTEMA DE LEADS INSTALADO COM SUCESSO!';
    RAISE NOTICE '======================================================';
    RAISE NOTICE 'Tabelas criadas: %/7', tabelas_count;
    RAISE NOTICE 'Índices criados: %', indices_count;
    RAISE NOTICE 'Funções criadas: %/3', funcoes_count;
    RAISE NOTICE 'Views criadas: %/3', views_count;
    RAISE NOTICE 'Leads inseridos: %', leads_count;
    RAISE NOTICE '';
    
    IF tabelas_count = 7 AND funcoes_count = 3 AND views_count = 3 AND leads_count > 0 THEN
        RAISE NOTICE '🚀 Sistema 100%% funcional e pronto para uso!';
    ELSE
        RAISE NOTICE '⚠️  Verifique se todos os objetos foram criados corretamente.';
    END IF;
    
    RAISE NOTICE '';
    RAISE NOTICE 'PRÓXIMOS PASSOS:';
    RAISE NOTICE '1. Teste as views: SELECT * FROM vw_dashboard_leads;';
    RAISE NOTICE '2. Teste o scoring: SELECT calcular_score_lead(id) FROM leads LIMIT 1;';
    RAISE NOTICE '3. Configure sua aplicação para usar as tabelas';
    RAISE NOTICE '4. Implemente integração com APIs externas conforme necessário';
END $;

-- Consulta para verificar objetos criados (pode ser executada manualmente)
SELECT 
    'Tabelas' as tipo_objeto,
    COUNT(*) as quantidade,
    '7 esperadas' as observacao
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('leads','lead_interactions','campanhas','campanha_participantes','propostas','feedbacks','metricas_leads')

UNION ALL

SELECT 
    'Índices' as tipo_objeto,
    COUNT(*) as quantidade,
    'Performance otimizada' as observacao
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND indexname LIKE 'idx_%'

UNION ALL

SELECT 
    'Funções' as tipo_objeto,
    COUNT(*) as quantidade,
    '3 esperadas' as observacao
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public' 
  AND p.proname IN ('calcular_score_lead', 'classificar_lead', 'atualizar_lead_score')

UNION ALL

SELECT 
    'Views' as tipo_objeto,
    COUNT(*) as quantidade,
    '3 esperadas' as observacao
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name LIKE 'vw_%'

UNION ALL

SELECT 
    'Leads de exemplo' as tipo_objeto,
    COUNT(*) as quantidade,
    'Dados para testes' as observacao
FROM leads;

-- Resumo dos leads criados por classificação
SELECT 
    '=== RESUMO DOS LEADS CRIADOS ===' as relatorio,
    NULL::VARCHAR as classificacao,
    NULL::BIGINT as quantidade,
    NULL::NUMERIC as score_medio
WHERE FALSE

UNION ALL

SELECT 
    NULL as relatorio,
    classificacao,
    COUNT(*) as quantidade,
    ROUND(AVG(score), 1) as score_medio
FROM leads 
GROUP BY classificacao
ORDER BY 
    CASE classificacao 
        WHEN 'quente' THEN 1 
        WHEN 'morno' THEN 2 
        WHEN 'frio' THEN 3
        ELSE 4
    END;