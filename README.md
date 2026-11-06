# XTRATO — controle pessoal de cartões

Aplicação web pessoal para centralizar compras de vários cartões, acompanhar parcelas por mês de fatura e controlar um orçamento mensal global.

## O que esta base já implementa

- Login privado, sem cadastro público.
- PostgreSQL para persistência em servidor; SQLite pode ser usado nos testes locais.
- Cadastro e arquivamento de cartões, com banco, bandeira, últimos quatro dígitos, fechamento e vencimento.
- Categorias pessoais.
- Compras à vista, parceladas e despesas fixas mensais.
- Compra parcelada em andamento: informar total ou valor da parcela, parcela atual e mês da fatura atual.
- Cada parcela fica armazenada como um lançamento separado, associado a `YYYY-MM` da fatura.
- Parcelas anteriores de uma compra em andamento são preservadas como histórico e não são lançadas novamente no mês atual.
- Rateio de centavos sem perda: eventual diferença de arredondamento fica na última parcela.
- Limite mensal global entre todos os cartões, independente do limite de crédito bancário. O último limite configurado continua valendo nos meses seguintes até você criar uma nova alteração.
- Visão geral, extrato unificado, categorias, evolução mensal e lista de despesas fixas.
- Cancelamento preserva parcelas históricas e cancela lançamentos a partir do mês atual.
- Migrações com Alembic e execução com Docker Compose.
- Fuso horário configurável (`APP_TIMEZONE`), por padrão `America/Sao_Paulo`, para decisões de virada do mês.
- Valores monetários em centavos inteiros com colunas de 64 bits para evitar estouro em parcelamentos maiores.

## Rodar localmente

Pré-requisitos: Docker e Docker Compose.

1. Copie `.env.example` para `.env`.
2. Gere a senha do banco com `openssl rand -hex 24` e use o resultado em `POSTGRES_PASSWORD`. O formato hexadecimal evita problemas de caracteres especiais na URL de conexão.
3. Altere `INITIAL_ADMIN_USERNAME`, `INITIAL_ADMIN_PASSWORD` e `APP_SECRET_KEY`. Gere a chave com `openssl rand -hex 32`. Não use os valores de exemplo.
4. Mantenha `APP_ENV=development` e `COOKIE_SECURE=false` para o acesso local por HTTP. O fuso padrão é `America/Sao_Paulo` (`APP_TIMEZONE`).
5. Execute:

```bash
docker compose up -d --build
```

6. Abra `http://localhost:8000` e entre com o usuário e senha definidos no `.env`.

O usuário inicial e as categorias padrão são criados automaticamente na primeira inicialização. Não existe rota de cadastro público.

Para acompanhar a inicialização:

```bash
docker compose logs -f app
```

## Publicar em um servidor com HTTPS

A aplicação já inclui um perfil opcional com Caddy para terminar TLS automaticamente. Para publicar:

1. Aponte um domínio/subdomínio para o IP do servidor (registros DNS A/AAAA).
2. No `.env`, defina `DOMAIN=seu-dominio.com`, `APP_ENV=production`, `COOKIE_SECURE=true` e `APP_TIMEZONE=America/Sao_Paulo`. A aplicação se recusará a iniciar em produção se o cookie seguro não estiver habilitado.
3. Gere um segredo longo para `APP_SECRET_KEY` (`openssl rand -hex 32`) e senhas fortes e únicas para o PostgreSQL e para o usuário. Para `POSTGRES_PASSWORD`, mantenha o formato hexadecimal gerado com `openssl rand -hex 24`.
4. Libere as portas TCP 80 e 443 (e UDP 443, opcional para HTTP/3) no firewall do servidor.
5. Execute:

```bash
docker compose --profile proxy up -d --build
```

6. Acesse `https://seu-dominio.com`.

Não publique o app sem HTTPS. Em produção, mantenha o acesso à porta interna da aplicação restrito e use o Caddy ou outro proxy HTTPS.

## Banco de dados e backup

Os dados do PostgreSQL ficam no volume Docker `xtrato_pgdata`. Um backup lógico pode ser feito com:

```bash
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup-xtrato.sql
```

E restaurado em uma instância vazia com:

```bash
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"' < backup-xtrato.sql
```

Guarde os backups fora do servidor e teste a restauração periodicamente. O volume sozinho não substitui backup.

## Regras importantes do produto

- O orçamento é calculado pelo mês da fatura, não pelo mês da compra.
- O limite configurado é global e continua valendo nos meses seguintes; uma nova configuração cria uma alteração a partir daquele mês.
- O limite mensal acompanha o mês em que a fatura será paga, e não apenas o mês em que a compra foi feita.
- O fechamento e o vencimento do cartão são usados juntos para sugerir o mês de pagamento: compras após o fechamento entram no ciclo seguinte; o dia de vencimento define se o ciclo é pago no mesmo mês do fechamento ou no mês seguinte.
- A sugestão pode ser alterada manualmente para refletir a fatura real da instituição, inclusive quando a administradora usa regras específicas.
- Uma compra parcelada gera uma linha por parcela. O valor total é dividido em centavos e a soma das parcelas sempre fecha com o total informado.
- Para compra antiga em andamento, o mês informado é o da parcela atual. O sistema deduz o mês inicial conforme o número da parcela e marca as anteriores como históricas.
- Despesas fixas geram lançamentos mensais de forma idempotente, sem duplicar a mesma recorrência no mesmo mês.
- O limite mede o comprometimento líquido na fatura. Um pagamento da fatura não deve ser lançado como compra.

## Desenvolvimento sem Docker (opcional)

Crie um ambiente virtual, instale `requirements-dev.txt`, configure `DATABASE_URL=sqlite:///./xtrato.db`, `APP_SECRET_KEY`, `INITIAL_ADMIN_USERNAME` e `INITIAL_ADMIN_PASSWORD`, então execute `alembic upgrade head` e `uvicorn app.main:app --reload`. Em um banco vazio, a primeira inicialização cria a conta e as categorias padrão. Para validar a lógica, execute `python -m pytest -q`.

## Endpoints principais

- `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`
- `GET/POST/PUT/DELETE /api/cards`
- `GET/POST/PUT/DELETE /api/categories`
- `POST /api/purchases`, `POST /api/purchases/{id}/cancel`
- `GET /api/entries?month=YYYY-MM`
- `GET /api/dashboard?month=YYYY-MM`
- `GET /api/recurrences`
- `PUT /api/budgets`
- `GET /healthz`
