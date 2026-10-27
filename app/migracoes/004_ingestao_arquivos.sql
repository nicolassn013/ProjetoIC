-- 004_ingestao_arquivos.sql
-- Diário da aquisição de arquivos da estação (FTP ou pasta local). Serve para:
--  * não processar duas vezes o mesmo arquivo (mesmo nome e mesmo conteúdo);
--  * saber o que deu erro e por quê, sem perder o arquivo (a cópia bruta fica em dados/brutos/maws55/);
--  * auditar de onde veio cada dado (nome do arquivo e sha256).
-- Um arquivo reenviado com o mesmo nome e conteúdo diferente gera uma nova linha.

CREATE TABLE IF NOT EXISTS ingestao_arquivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origem TEXT NOT NULL,
    nome_arquivo TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    processado_em DATETIME NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ok', 'erro')),
    linhas_lidas INTEGER,
    linhas_gravadas INTEGER,
    primeiro_registro DATETIME,
    ultimo_registro DATETIME,
    mensagem TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ingestao_nome_sha_status
    ON ingestao_arquivos (nome_arquivo, sha256, status);
