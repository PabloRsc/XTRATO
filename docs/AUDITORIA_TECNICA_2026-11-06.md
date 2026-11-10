# Relatório de auditoria técnica — XTRATO

**Data:** 06/11/2026  
**Base revisada:** branch `main` no commit `4852ae16ce14dfec68c4706e6af4330659f65374`  
**Escopo:** API FastAPI, autenticação, sessão, regras financeiras, banco/migrações, backup/restauração, interface web, Docker e CI.

## Resultado executivo

A base tem uma cobertura automatizada útil e passou no CI da `main` imediatamente antes desta auditoria, incluindo suíte Python, migrações SQLite, verificação sintática JavaScript, build Docker e smoke test integrado com PostgreSQL.

A auditoria não equivale a pentest externo nem a uma validação de produção com provedor real. Não há ambiente hospedado, DNS, TLS gerenciado ou credenciais de produção configurados nesta etapa.

## Áreas revisadas

- **Autenticação e sessões:** cookies assinados, `SameSite=Strict`, expiração, versão de sessão, troca de senha, hash Argon2 e limitação de tentativas.
- **Autorização e isolamento:** consultas de cartões, categorias, compras, faturas, orçamento, dashboard e backup sempre vinculadas ao usuário autenticado; tentativas cruzadas cobertas por testes.
- **Proteção HTTP:** cabeçalho anti-CSRF para mutações, validação de Origin quando fornecido, respostas privadas sem cache, cabeçalhos de segurança e limite de 10 MB para upload de backup.
- **Dados financeiros:** valores inteiros em centavos, divisão exata de parcelas, créditos assinados, limite progressivo, ciclos de fatura, recorrências idempotentes e cancelamento preservando histórico.
- **Backup/restauração:** exclusão de credenciais, validação de estrutura e vínculos, remapeamento de IDs, transação única, conta de destino vazia e serialização de restaurações por linha de usuário no PostgreSQL.
- **Interface:** escape de valores dinâmicos inseridos no HTML, ausência de armazenamento local para dados financeiros e breakpoints responsivos até telas estreitas.
- **Entrega:** Docker, PostgreSQL, Alembic, probes `/healthz` e `/readyz`, variáveis de ambiente e pipeline CI.

## Correções desta auditoria

1. **Categorias após restauração:** a inicialização não deve semear categorias padrão em contas já existentes. Isso alterava a coleção restaurada após um reinício. A criação das categorias padrão permanece na criação da primeira conta.
2. **Cabeçalhos de proxy:** o comando do servidor não deve confiar em `X-Forwarded-For` de qualquer origem. O valor curinga foi substituído por `FORWARDED_ALLOW_IPS`; o Compose define uma faixa bridge privada de exemplo e a documentação exige configurar a faixa real do proxy em plataformas externas.
3. **Regressão de inicialização:** foi adicionado teste que executa o lifespan com uma conta existente e confirma que a lista exata de categorias permanece inalterada.

## Limitações e itens obrigatórios antes da publicação

- O limitador de login é mantido em memória por processo. Com múltiplas réplicas, não compartilha contadores e reinicia junto com o processo. Para implantação multi-instância, mover o controle para Redis ou mecanismo compartilhado.
- O limitador por IP depende de `FORWARDED_ALLOW_IPS` configurado corretamente. Nunca usar `*` em produção; usar somente CIDRs/IPs efetivos do proxy do provedor.
- `SELECT FOR UPDATE` serializa restaurações concorrentes no PostgreSQL. SQLite não oferece o mesmo bloqueio por linha; não usar SQLite como banco de produção multiusuário.
- A política de backup automático, retenção, restauração de desastre e monitoramento precisa ser fornecida pelo provedor ou configurada separadamente. O backup JSON do usuário não substitui backup nativo do PostgreSQL.
- Não foi executado teste de carga, análise SAST/DAST externa, varredura de dependências com banco de vulnerabilidades em tempo real, nem teste manual em dispositivos físicos.
- O CI comprova a execução em ambiente de teste, não garante disponibilidade ou gratuidade permanente de um provedor de hospedagem.

## Critérios de aceite para lançamento

- PR desta auditoria integrada e CI verde no commit de produção.
- Escolher provedor com PostgreSQL persistente, política de backup e limites gratuitos conhecidos.
- Definir segredos fortes fora do GitHub; remover variáveis de bootstrap após criar a primeira conta.
- Configurar HTTPS, cookies seguros, domínio e CIDR confiável do proxy.
- Fazer backup inicial, restaurar em ambiente isolado e conferir totais e histórico.
- Validar fluxo de login, compra, parcelamento, estorno, cancelamento, backup e restauração no ambiente hospedado.
- Somente então considerar a publicação pronta para uso com dados financeiros reais.

## Conclusão

A revisão de código e os testes automatizados cobrem os fluxos centrais da aplicação e não indicam bloqueador funcional conhecido além das correções listadas nesta PR e das configurações operacionais ainda pendentes. O projeto pode avançar para a preparação de publicação após a integração e validação desta PR, mas não deve ser declarado pronto para produção antes de concluir os critérios de aceite acima.


## Atualização de revisão — 10/11/2026

**Branch revisada:** `feat/xtrato-dashboard-mockup-rebuild`  
**Pull Request:** #51  
**Última correção financeira verificada:** compromissos de cartão filtrados por compras ativas, parcelas abertas e mês de fatura igual ou posterior ao mês selecionado.

### Validações adicionais

- Testes específicos de dashboard para previsão de 12 meses, parcelas futuras e isolamento entre contas.
- Teste de regressão para impedir que faturas antigas ainda marcadas como abertas reduzam o limite disponível atual.
- CI do commit `cdd26cba8e14e9671eb8e2345c6cf4163c02faf7` concluído com sucesso, incluindo testes Python, migrações SQLite, sintaxe JavaScript, build Docker e smoke test PostgreSQL.
- Verificação estática dos identificadores HTML sem duplicações e confirmação de breakpoints responsivos no CSS.

### Pendências que continuam bloqueando o aceite de produção

- Inspeção visual real em navegador desktop e celular, incluindo modais, estados vazios, telas estreitas e contraste nos temas.
- Integração do PR após revisão visual e CI verde no commit final.
- Configuração e validação do provedor de hospedagem, PostgreSQL persistente, backups, HTTPS, variáveis de ambiente e política de retenção.
- Teste de fumaça autenticado no ambiente hospedado, sem utilizar dados financeiros reais antes de confirmar backup e restauração.

**Status:** aprovado em CI; ainda não aprovado para produção. Não afirmar que a aplicação foi publicada ou que a hospedagem foi validada até concluir os itens acima.
