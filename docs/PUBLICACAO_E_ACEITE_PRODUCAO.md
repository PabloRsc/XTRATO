# Publicação e aceite de produção — XTRATO

Atualizado em 10/11/2026. Este guia complementa o README; não representa uma publicação já realizada.

## Estado conhecido

- Código e documentação estão na branch `feat/xtrato-dashboard-mockup-rebuild`.
- Pull Request #51: https://github.com/PabloRsc/XTRATO/pull/51
- A execução de CI mais recente do commit `66cdf5dadff05c01ebc0a124d6746566d919725d` concluiu com sucesso: https://github.com/PabloRsc/XTRATO/actions/runs/42930718601
- **78 testes Python aprovados**; compilação, migração SQLite, sintaxe JavaScript, build Docker e smoke test PostgreSQL via Docker Compose aprovados.
- O smoke test validou autenticação, backup/restauração, arquivamento/reativação de cartão, troca de senha, invalidação de sessão e persistência de sessão após reinício.
- A inspeção visual em navegador e a implantação em provedor ainda não foram realizadas.

## Requisitos mínimos do ambiente

1. Serviço web executando o Dockerfile deste repositório, com HTTPS gerenciado.
2. PostgreSQL externo com armazenamento persistente, backups e política de retenção conhecidos.
3. Variáveis secretas configuradas no painel do provedor, nunca em commits:
   - `APP_ENV=production`
   - `APP_SECRET_KEY`: segredo aleatório único, com pelo menos 32 caracteres.
   - `COOKIE_SECURE=true`
   - `APP_TIMEZONE=America/Sao_Paulo`
   - `DATABASE_URL`: conexão PostgreSQL usando o driver instalado, no formato `postgresql+psycopg://usuario:senha@host:5432/banco`.
   - `FORWARDED_ALLOW_IPS`: somente os IPs/CIDRs confiáveis publicados pelo provedor/proxy; nunca usar `*`.
   - `INITIAL_ADMIN_USERNAME` e `INITIAL_ADMIN_PASSWORD` somente na primeira inicialização de um banco vazio. A senha inicial precisa ter pelo menos 12 caracteres; remover as duas variáveis depois de criar e validar o primeiro acesso.
   - `PORT`: fornecida pelo ambiente de hospedagem; o container usa 8000 como fallback.
4. Não utilizar SQLite, disco efêmero ou banco gratuito com expiração curta para guardar o histórico financeiro. Suspensão, limites e expiração do plano gratuito precisam ser confirmados antes da escolha.

## Health checks

- `/healthz`: confirma que o processo web responde.
- `/readyz`: consulta o banco e retorna HTTP 503 se ele estiver indisponível. Configurar este endpoint como readiness/health check quando o provedor permitir.

## Sequência segura de publicação

1. Criar PostgreSQL persistente e registrar como será feito o backup e quem tem acesso.
2. Configurar as variáveis secretas no provedor e conferir o formato de `DATABASE_URL`.
3. Implantar a branch de validação em ambiente privado/staging, não diretamente como produção.
4. Confirmar migrações Alembic, `/healthz` e `/readyz`.
5. Criar a conta inicial, entrar e confirmar HTTPS/cookie seguro.
6. Criar um cartão e uma compra de teste, conferir o mês da fatura e o saldo disponível, e apagar os dados de teste.
7. Baixar o backup JSON autenticado; fazer backup nativo do PostgreSQL e provar que a restauração é possível em uma instância separada.
8. Realizar inspeção visual em navegador desktop e celular: dashboard, seletor de mês, gráficos, modais, estados vazios, formulários e tema claro/escuro.
9. Só depois de todos os itens anteriores, marcar o PR #51 como pronto, revisar e integrar à `main`.
10. Após o deploy de produção, repetir smoke test sem dados financeiros reais e confirmar que os dados persistem após reinício/novo deploy.

## Bloqueios atuais

- O PR #51 continua em rascunho até concluir a inspeção visual.
- Não há provedor de hospedagem do XTRATO conectado nesta sessão. A conexão Vercel disponível está associada a outro repositório e não deve ser usada para publicar este projeto.
- Nenhum banco de produção foi provisionado ou verificado nesta etapa.
- Não declarar o XTRATO publicado ou finalizado até executar os passos acima.

## Proteção de dados

Nunca solicitar nem registrar no GitHub senhas, `APP_SECRET_KEY`, URLs completas com credenciais, backups financeiros ou tokens do provedor. Fazer backup antes de qualquer migração em produção. Não substituir um banco existente por um banco vazio para “facilitar” a publicação.
