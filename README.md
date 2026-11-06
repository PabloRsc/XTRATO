# XTRATO — controle pessoal de cartões

Aplicação web pessoal para centralizar compras de vários cartões, organizar parcelas pelo mês em que a fatura será paga e controlar um orçamento mensal global.

## O que esta base já implementa

- Login privado, sem cadastro público.
- PostgreSQL para persistência em servidor; SQLite pode ser usado nos testes locais.
- Cadastro, edição e arquivamento de cartões, com banco, bandeira, últimos quatro dígitos, fechamento, vencimento e escolha do mês de pagamento (mesmo mês ou mês seguinte).
- Cartões e categorias arquivados permanecem visíveis na área de cadastros e podem ser reativados; não aparecem nos seletores de novas compras enquanto arquivados.
- Categorias pessoais com cadastro, edição e arquivamento.
- Edição segura de descrição e observações de compras/despesas fixas; valores, parcelas e meses de pagamento permanecem preservados.
- Compras à vista, parceladas e despesas fixas mensais.
- Compra parcelada em andamento: informar total ou valor da parcela, parcela atual e mês da fatura atual.
- Cada parcela fica armazenada como um lançamento separado, associado a `YYYY-MM` da fatura.
- Parcelas anteriores de uma compra em andamento são preservadas como histórico e não são lançadas novamente no mês atual.
- Rateio de centavos sem perda: eventual diferença de arredondamento fica na última parcela.
- Limite mensal global entre todos os cartões, independente do limite de crédito bancário. O último limite configurado continua valendo nos meses seguintes até você criar uma nova alteração.
- Visão geral, extrato unificado, categorias, evolução mensal e lista de despesas fixas.
- Cancelamento preserva parcelas históricas e cancela lançamentos a partir do mês atual.
- Estornos/créditos são lançamentos eventuais; não podem ser cadastrados como despesas fixas ou compras em andamento.
- Valores de estorno reduzem o total líquido da fatura nos indicadores gerais, por cartão, por categoria e na evolução mensal.
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
Depois que a primeira conta for criada e você confirmar o acesso, `INITIAL_ADMIN_USERNAME` e `INITIAL_ADMIN_PASSWORD` podem ser removidos das variáveis do servidor. Eles só são necessários quando o banco ainda não contém nenhum usuário; sem eles, uma instalação vazia não inicia, mas um banco já inicializado continua funcionando. A senha da conta deve ser administrada pela opção **Alterar senha** no próprio XTRATO.

Para acompanhar a inicialização:

```bash
docker compose logs -f app
```

## Publicar em um servidor com HTTPS

A aplicação já inclui um perfil opcional com Caddy para terminar TLS automaticamente. Para publicar:

1. Aponte um domínio/subdomínio para o IP do servidor (registros DNS A/AAAA).
2. No `.env`, defina `DOMAIN=seu-dominio.com`, `APP_ENV=production`, `COOKIE_SECURE=true` e `APP_TIMEZONE=America/Sao_Paulo`. A aplicação se recusará a iniciar em produção sem HTTPS/cookie seguro, sem um segredo de sessão único com pelo menos 32 caracteres ou com uma senha inicial fraca.
3. Gere um segredo longo para `APP_SECRET_KEY` (`openssl rand -hex 32`) e senhas fortes e únicas para o PostgreSQL e para o usuário. Para `POSTGRES_PASSWORD`, mantenha o formato hexadecimal gerado com `openssl rand -hex 24`.
4. Libere as portas TCP 80 e 443 (e UDP 443, opcional para HTTP/3) no firewall do servidor.
5. Execute:

```bash
docker compose --profile proxy up -d --build
```

6. Acesse `https://seu-dominio.com`.

Não publique o app sem HTTPS. Em produção, mantenha o acesso à porta interna da aplicação restrito e use o Caddy ou outro proxy HTTPS.

## Hospedagem em plataforma gratuita

A imagem Docker aceita a variável `PORT` definida pela plataforma de hospedagem (com fallback para 8000). Para publicar em qualquer plataforma compatível, ela precisa oferecer:

- Execução de uma imagem Docker ou do `Dockerfile` deste repositório.
- Variáveis de ambiente secretas para as credenciais e configurações.
- Conexão de rede persistente com PostgreSQL externo.
- HTTPS gerenciado pela plataforma ou por proxy reverso.
- Um PostgreSQL com armazenamento persistente e política de retenção conhecida.

Não use SQLite nem armazenamento local efêmero para produção. Em camadas gratuitas, confirme antes os limites de suspensão, memória, horas de execução, armazenamento, backups, limites de conexão e eventual expiração do banco. Uma aplicação que “hospeda grátis” mas apaga o banco ou o disco não é adequada para guardar seu histórico financeiro.

A implantação é independente do provedor: o serviço web recebe `DATABASE_URL`, `APP_SECRET_KEY`, `APP_ENV=production`, `COOKIE_SECURE=true`, `APP_TIMEZONE=America/Sao_Paulo`, `INITIAL_ADMIN_USERNAME`, `INITIAL_ADMIN_PASSWORD` e a variável `PORT` fornecida pelo ambiente. Use HTTPS na plataforma e não coloque segredos no GitHub.

## Backup pessoal

A conta autenticada pode baixar uma cópia portátil dos dados em `GET /api/backup`, também disponível pelo botão **Baixar backup dos dados** na interface. O arquivo JSON inclui cartões (inclusive arquivados), categorias, limites mensais, compras e parcelas, preservando os vínculos entre registros. Na restauração, os IDs são remapeados para evitar colisões com dados de outras contas no servidor de destino. Senhas, hashes e sessões nunca são incluídos.

A restauração fica disponível pelo botão **Restaurar backup**. Selecione um arquivo JSON XTRATO v1 e digite `RESTAURAR` para confirmar. Por segurança, a restauração só é permitida em uma conta sem cartões, compras ou limites cadastrados; categorias padrão ou personalizadas sem vínculos financeiros serão substituídas. A operação valida vínculos, datas com fuso horário e valores exatos de todas as parcelas, e é executada em uma única transação: se qualquer registro falhar, nada é importado.

A restauração não altera o usuário, a senha nem as sessões da conta de destino. Depois de restaurar, confira os cartões, o limite e algumas faturas com os extratos originais.

Guarde uma cópia fora do servidor, de preferência em um local privado com proteção de acesso. O backup JSON é uma cópia de segurança lógica; ele não substitui os backups nativos do PostgreSQL nem um procedimento de restauração testado.

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

## Segurança da conta

Na barra lateral, a opção **Alterar senha** solicita a senha atual e uma nova senha de pelo menos 12 caracteres. As tentativas incorretas são limitadas por conta. Após a troca, o sistema incrementa a versão de sessão do usuário, encerra o acesso atual e rejeita cookies assinados anteriormente em qualquer navegador. É necessário entrar novamente com a nova senha.

## Regras importantes do produto

- O limite mensal global é calculado pelo mês em que a fatura será paga, não pelo mês em que a compra foi realizada.
- O limite configurado continua valendo nos meses seguintes; uma nova configuração cria uma alteração a partir daquele mês.
- Cada cartão define explicitamente se a fatura é paga no mesmo mês do fechamento ou no mês seguinte. Compras após o fechamento entram no ciclo seguinte; o usuário pode ajustar o mês de pagamento de cada compra.
- A sugestão pode ser alterada manualmente para refletir a fatura real da instituição, inclusive quando a administradora usa regras específicas.
- Uma compra parcelada gera uma linha por parcela. O valor total é dividido em centavos e a soma das parcelas sempre fecha com o total informado; eventuais centavos restantes ficam na última parcela e são exibidos no formulário.
- Para compra antiga em andamento, o mês informado é o da parcela atual. O sistema deduz o mês inicial conforme o número da parcela e marca as anteriores como históricas.
- Despesas fixas geram lançamentos mensais de forma idempotente, sem duplicar a mesma recorrência no mesmo mês.
- O limite mede o comprometimento líquido na fatura. Um pagamento da fatura não deve ser lançado como compra.

## Desenvolvimento sem Docker (opcional)

Crie um ambiente virtual, instale `requirements-dev.txt`, configure `DATABASE_URL=sqlite:///./xtrato.db`, `APP_SECRET_KEY`, `INITIAL_ADMIN_USERNAME` e `INITIAL_ADMIN_PASSWORD`, então execute `alembic upgrade head` e `uvicorn app.main:app --reload`. Em um banco vazio, a primeira inicialização cria a conta e as categorias padrão. Para validar a lógica, execute `python -m pytest -q`.

## Endpoints principais

- `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`, `POST /api/auth/password`
- `GET/POST/PUT/DELETE /api/cards`
- `GET/POST/PUT/DELETE /api/categories`
- `POST /api/purchases`, `PATCH /api/purchases/{id}` (descrição/observações), `POST /api/purchases/{id}/cancel`
- `GET /api/entries?month=YYYY-MM`
- `GET /api/dashboard?month=YYYY-MM`
- `GET /api/recurrences`
- `PUT /api/budgets`
- `GET /api/backup`, `POST /api/backup/restore` (restauração em conta vazia)
- `GET /api/cards?include_archived=true`, `POST /api/cards/{id}/reactivate`
- `GET /api/categories?include_archived=true`, `POST /api/categories/{id}/reactivate`
- `GET /healthz`
