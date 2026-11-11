# Teste visual automatizado do XTRATO

O teste de navegador está em `tests/e2e_dashboard.py`. Ele autentica uma conta de teste, abre o painel em desktop (1440 px) e celular (390 px), valida os principais blocos do dashboard, captura erros JavaScript/respostas HTTP 5xx e registra uma captura de tela em cada viewport.

## Pré-requisitos

- XTRATO em execução e acessível em `http://127.0.0.1:8000` (ou URL definida em `XTRATO_BASE_URL`).
- Conta de teste já criada no banco. O teste não cria, altera ou apaga usuários e não deve ser executado com dados financeiros reais.
- Python 3.12 e Playwright.

## Windows PowerShell

Na raiz do repositório, com o ambiente virtual ativado:

```powershell
python -m pip install playwright==1.56.0
python -m playwright install chromium

$env:XTRATO_TEST_USERNAME = "usuario-de-teste"
$env:XTRATO_TEST_PASSWORD = "senha-da-conta-de-teste"
$env:XTRATO_BASE_URL = "http://127.0.0.1:8000"
$env:XTRATO_ARTIFACTS_DIR = "artifacts"

python tests/e2e_dashboard.py
```

As imagens `dashboard-desktop.png` e `dashboard-mobile.png` são gravadas na pasta `artifacts`.

## Observações

- O script apenas faz login e lê o painel; não cria compras, cartões, categorias ou despesas.
- A checagem de overflow horizontal é aplicada às viewports desktop e mobile. O teste usa as views reais `#loginView` e `#appView` da aplicação. O teste também registra erros de console do navegador, exceções JavaScript e respostas HTTP 5xx.
- O teste não substitui a revisão manual de contraste, legibilidade, foco por teclado e comportamento em navegadores diferentes.
- Este teste de navegador ainda não está integrado ao workflow do GitHub Actions. Execute-o manualmente em ambiente local; os testes Python e o smoke test Docker/PostgreSQL do CI não substituem a inspeção visual em navegador.
