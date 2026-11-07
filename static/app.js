(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const money = cents => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format((Number(cents) || 0) / 100);
  const moneyInputToCents = value => Math.round(Number(String(value).replace(',', '.')) * 100);
  const purchaseInputToCents = value => { const digits = String(value ?? '').replace(/\D/g, ''); return digits ? Number(digits) : 0; };
  const saoPauloDate = () => {
    const parts = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'America/Sao_Paulo',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).formatToParts(new Date());
    return Object.fromEntries(parts
      .filter(part => ['year', 'month', 'day'].includes(part.type))
      .map(part => [part.type, part.value]));
  };
  const monthNow = () => {
    const { year, month } = saoPauloDate();
    return `${year}-${month}`;
  };
  const todayISO = () => {
    const { year, month, day } = saoPauloDate();
    return `${year}-${month}-${day}`;
  };
  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
  const formatDate = value => {
    if (!value) return '';
    const [y, m, d] = value.split('-').map(Number);
    return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short' }).format(new Date(y, m - 1, d)).replace('.', '');
  };
  const formatMonth = value => {
    if (!value) return '';
    const [y, m] = value.split('-').map(Number);
    return new Intl.DateTimeFormat('pt-BR', { month: 'long', year: 'numeric' }).format(new Date(y, m - 1, 1));
  };
  const addMonth = (value, amount) => {
    const [y, m] = value.split('-').map(Number);
    const d = new Date(y, m - 1 + amount, 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
  };

  const paths = {
    grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    receipt: '<path d="M5 3h14v18l-3-2-4 2-4-2-3 2z"/><path d="M8 8h8M8 12h8M8 16h4"/>',
    card: '<rect x="2.5" y="5" width="19" height="14" rx="2.5"/><path d="M3 9.5h18M7 15h3"/>',
    tag: '<path d="M20.5 13 13 20.5a2 2 0 0 1-2.8 0L3.5 13.8a2 2 0 0 1-.5-1.3V5a2 2 0 0 1 2-2h7.5a2 2 0 0 1 1.4.6l6.6 6.6a2 2 0 0 1 0 2.8Z"/><circle cx="8" cy="8" r="1"/>',
    repeat: '<path d="m17 2 4 4-4 4"/><path d="M3 11V9a3 3 0 0 1 3-3h15M7 22l-4-4 4-4"/><path d="M21 13v2a3 3 0 0 1-3 3H3"/>',
    shield: '<path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z"/><path d="m9 12 2 2 4-4"/>',
    logout: '<path d="M10 17l5-5-5-5M15 12H3"/><path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6"/>',
    calendar: '<rect x="3" y="4.5" width="18" height="17" rx="2"/><path d="M7 2.5v4M17 2.5v4M3 9h18"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    gauge: '<path d="M4.5 19a9 9 0 1 1 15 0"/><path d="m12 13 4-4M7 18h10"/>',
    search: '<circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 5 5"/>',
    utensils: '<path d="M7 2v8M4 2v5a3 3 0 0 0 6 0V2M7 10v12M17 2v20M17 2c3 2 4 5 4 8h-4"/>',
    'shopping-basket': '<path d="m3 10 2 10h14l2-10zM8 10l4-7 4 7M8 14v3M12 14v3M16 14v3"/>',
    'car-front': '<path d="m5 17-1 3M19 17l1 3M3 14l2-7h14l2 7v3H3z"/><path d="M5 14h14M7 17h.01M17 17h.01"/>',
    'heart-pulse': '<path d="M20.8 8.8c0 5.4-8.8 11-8.8 11s-8.8-5.6-8.8-11A4.8 4.8 0 0 1 12 6.4a4.8 4.8 0 0 1 8.8 2.4Z"/><path d="M3.5 12h4l2-3 3 6 2-3h5"/>',
    ticket: '<path d="M3 7a2 2 0 0 0 0 4v2a2 2 0 0 0 0 4h18a2 2 0 0 0 0-4v-2a2 2 0 0 0 0-4z"/><path d="M13 7v2M13 13v2M13 19v.01"/>',
    'shopping-bag': '<path d="M5 8h14l1 13H4L5 8Z"/><path d="M9 8a3 3 0 0 1 6 0"/>',
    dots: '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
    laptop: '<rect x="4" y="4" width="16" height="12" rx="1.5"/><path d="M2 20h20l-2-4H4z"/>',
    play: '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="m10 8 5 4-5 4z"/>',
    coffee: '<path d="M4 9h13v7a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4zM17 11h2a2 2 0 0 1 0 4h-2M8 3v3M12 3v3"/>',
    home: '<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-6v-7h-4v7H4a1 1 0 0 1-1-1z"/>',
    book: '<path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v18H6.5A2.5 2.5 0 0 0 4 22z"/><path d="M4 4.5v17.5M8 6h8"/>',
    download: '<path d="M12 3v12m0 0 4-4m-4 4-4-4"/><path d="M4 17v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>',
    upload: '<path d="M12 16V4m0 0L8 8m4-4 4 4"/><path d="M4 17v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>',
    moon: '<path d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5 8.5 8.5 0 1 0 20.5 14.2Z"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"/>'
  };
  const icon = (name, cls = '') => `<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true">${paths[name] || paths.tag}</svg>`;
  const categoryIcon = name => ({ 'Alimentação':'utensils', 'Mercado':'shopping-basket', 'Transporte':'car-front', 'Saúde':'heart-pulse', 'Assinaturas':'repeat', 'Lazer':'ticket', 'Compras':'shopping-bag', 'Outros':'tag' }[name] || 'tag');

  const state = { user: null, month: monthNow(), dashboard: null, cards: [], categories: [], entries: [], activePage: 'dashboard', invoiceMonthTouched: false, editingCardId: null, editingCategoryId: null, editingPurchaseId: null };

  async function api(path, options = {}) {
    const method = (options.method || 'GET').toUpperCase();
    const headers = { ...(options.headers || {}) };
    if (options.body !== undefined) headers['Content-Type'] = 'application/json';
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) headers['X-Xtrato-Request'] = '1';
    const response = await fetch(path, { ...options, method, headers, credentials: 'same-origin' });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(payload.detail || 'Não foi possível concluir a operação.');
      error.status = response.status;
      if (response.status === 401 && path !== '/api/auth/login' && path !== '/api/auth/me') showLogin();
      throw error;
    }
    return payload;
  }

  function showLogin() {
    $('#appView').classList.add('hidden');
    $('#loginView').classList.remove('hidden');
    $('#loginError').textContent = '';
  }
  function showApp(user) {
    state.user = user;
    $('#loginView').classList.add('hidden');
    $('#appView').classList.remove('hidden');
    $('#profileName').textContent = user.username;
    $('#avatarInitial').textContent = user.username.slice(0, 1).toUpperCase();
  }
  function toast(message) {
    const node = $('#toast');
    node.textContent = message;
    node.classList.add('show');
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => node.classList.remove('show'), 2700);
  }
  function openModal(id) { $(`#${id}`).classList.remove('hidden'); }
  function closeModal(id) { $(`#${id}`).classList.add('hidden'); }
  function applyTheme(theme) {
    const selected = theme === 'dark' ? 'dark' : 'light';
    document.documentElement.dataset.theme = selected;
    document.documentElement.style.colorScheme = selected;
    const button = $('#themeToggle');
    if (button) {
      const next = selected === 'dark' ? 'light' : 'dark';
      button.innerHTML = icon(next === 'dark' ? 'moon' : 'sun');
      button.setAttribute('aria-label', next === 'dark' ? 'Ativar tema escuro' : 'Ativar tema claro');
      button.title = next === 'dark' ? 'Ativar tema escuro' : 'Ativar tema claro';
    }
    const meta = $('meta[name="theme-color"]');
    if (meta) meta.content = selected === 'dark' ? '#0b1110' : '#f5f7f4';
  }

  function toggleTheme() {
    const current = document.documentElement.dataset.theme || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('xtrato-theme', next); } catch (_) { /* storage may be unavailable */ }
    applyTheme(next);
  }

  function initializeTheme() {
    let saved = 'light';
    try { saved = localStorage.getItem('xtrato-theme') || 'light'; } catch (_) { /* use default */ }
    applyTheme(saved);
  }

  function refreshStaticIcons() {
    $$('[data-icon]').forEach(node => {
      const name = node.dataset.icon;
      node.innerHTML = icon(name);
    });
  }
  function setPage(page) {
    state.activePage = page;
    $$('.page-view').forEach(node => node.classList.toggle('hidden', node.id !== `page-${page}`));
    $$('.nav-item').forEach(node => node.classList.toggle('active', node.dataset.page === page));
    const names = { dashboard: 'Visão geral', statement: 'Extrato', cards: 'Cartões', categories: 'Categorias', recurrences: 'Despesas fixas' };
    $('#breadcrumbPage').textContent = names[page] || 'Visão geral';
    if (page === 'statement') loadStatement();
    if (page === 'recurrences') loadRecurrences();
  }

  async function loadInitialData() {
    state.cards = await api('/api/cards?include_archived=true');
    state.categories = await api('/api/categories?include_archived=true');
    await refreshDashboard();
    renderCardOptions();
    renderCategoryOptions();
    renderCards();
    renderCategories();
    refreshStaticIcons();
  }
  async function changeSelectedMonth(offset) {
    const [year, month] = state.month.split('-').map(Number);
    const date = new Date(year, month - 1 + offset, 1);
    state.month = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    $('#monthPicker').value = state.month;
    await refreshDashboard();
  }

  async function refreshDashboard() {
    const dashboard = await api(`/api/dashboard?month=${encodeURIComponent(state.month)}`);
    state.dashboard = dashboard;
    state.entries = dashboard.recent_entries || [];
    renderDashboard();
    await loadStatement();
    await loadRecurrences();
  }

  function renderDashboard() {
    const d = state.dashboard;
    if (!d) return;
    const hasBudget = d.limit_cents !== null && d.limit_cents !== undefined;
    $('#budgetSpent').textContent = money(d.spent_cents);
    $('#budgetOf').textContent = hasBudget ? `de ${money(d.limit_cents)}` : 'sem limite definido';
    $('#budgetPercent').textContent = hasBudget ? `${d.percentage}%` : '—';
    $('#budgetProgress').style.width = `${hasBudget ? Math.min(Math.max(d.percentage, 0), 100) : 0}%`;
    $('#budgetProgress').style.background = hasBudget && d.percentage >= 100 ? 'linear-gradient(90deg,#c66a63,#df9188)' : '';
    $('#budgetCommitted').textContent = money(d.spent_cents);
    $('#budgetAvailable').textContent = hasBudget ? money(d.available_cents) : '—';
    $('#budgetCredits').textContent = money(d.credits_cents);
    $('#budgetAvailable').classList.toggle('positive', hasBudget && d.available_cents >= 0);
    $('#budgetAvailable').style.color = hasBudget && d.available_cents < 0 ? 'var(--red)' : '';
    let warning = '';
    if (!hasBudget) warning = 'Defina um limite mensal para acompanhar quanto ainda pode comprometer.';
    else if (d.percentage >= 100) warning = 'Você atingiu ou ultrapassou o limite mensal definido.';
    else if (d.percentage >= 85) warning = 'Atenção: você está próximo do limite mensal.';
    else if (d.percentage >= 70) warning = 'Atenção: mais de 70% do orçamento já está comprometido.';
    $('#budgetWarning').textContent = warning;
    $('#cardCount').textContent = `${d.cards.length} ${d.cards.length === 1 ? 'cartão' : 'cartões'}`;
    $('#cardTotal').textContent = money(d.spent_cents);
    renderWalletCards(d.cards || []);
    renderCategoryChart(d.categories || []);
    renderTrend(d.trend || []);
    renderForecast(d.forecast || []);
    $('#monthPicker').value = state.month;
  }

  function renderWalletCards(totals) {
    const target = $('#walletCards');
    if (!target) return;
    const active = state.cards.filter(card => card.active !== false);
    $('#cardCount').textContent = `${active.length} ${active.length === 1 ? 'cartão' : 'cartões'}`;
    $('#cardTotal').textContent = money((totals || []).reduce((sum, card) => sum + (Number(card.total_cents) || 0), 0));
    if (!active.length) {
      target.innerHTML = '<div class="empty-inline">Adicione seu primeiro cartão para começar.</div>';
      return;
    }
    target.innerHTML = active.map(card => {
      const theme = bankTheme(card.issuer);
      const total = (totals || []).find(row => Number(row.id) === Number(card.id));
      return `<button type="button" class="xtrato-wallet-card" data-wallet-card="${card.id}" style="--wallet-bank:${theme.color};--wallet-ink:${theme.ink}">
        <span class="xtrato-wallet-card-top"><span class="xtrato-wallet-bank-mark">${brandLogoMarkup(card.issuer)}</span><span class="xtrato-wallet-chevron">↗</span></span>
        <span class="xtrato-wallet-card-name">${escapeHtml(card.name || card.issuer)}</span>
        <span class="xtrato-wallet-card-bottom"><b>${money(total?.total_cents || 0)}</b><small>Fecha dia ${card.closing_day} · vence dia ${card.due_day}</small></span>
      </button>`;
    }).join('');
    target.querySelectorAll('[data-wallet-card]').forEach(button => button.addEventListener('click', () => {
      $('#statementCardFilter').value = button.dataset.walletCard;
      loadStatement();
      $('#statementSearch').focus();
    }));
  }

  function renderCategoryChart(categories) {
    const target = $('#categoryChart');
    const positives = categories.filter(c => c.total_cents > 0);
    if (!positives.length) {
      target.innerHTML = '<div class="empty-inline">Seus gastos por categoria aparecerão aqui.</div>';
      return;
    }
    const max = Math.max(...positives.map(c => c.total_cents));
    target.innerHTML = positives.slice(0, 6).map(c => `<div class="category-bar-row"><div class="category-symbol" style="color:${escapeHtml(c.color)};background:${escapeHtml(c.color)}18">${icon(c.icon || categoryIcon(c.name))}</div><div class="category-name">${escapeHtml(c.name)}</div><div class="category-track"><span style="width:${Math.max(3, c.total_cents / max * 100)}%;background:${escapeHtml(c.color)}"></span></div><div class="category-value">${money(c.total_cents)}</div></div>`).join('');
  }
  function renderTrend(trend) {
    const target = $('#trendChart');
    if (!trend.length || trend.every(x => x.total_cents === 0)) {
      target.innerHTML = '<div class="empty-inline">Seus gastos aparecerão aqui conforme você registrar compras.</div>';
      return;
    }
    const max = Math.max(1, ...trend.map(x => Math.max(0, x.total_cents)));
    target.innerHTML = trend.map(row => {
      const height = Math.max(3, Math.max(0, row.total_cents) / max * 100);
      const current = row.month === state.month ? 'current' : '';
      return '<div class="trend-column ' + current + '"><span class="trend-value">' + (row.total_cents > 0 ? money(row.total_cents).replace(',00', '') : '') + '</span><div class="trend-bar-area"><div class="trend-bar" style="height:' + height + '%"></div></div><small>' + escapeHtml(row.label.slice(0,3)) + '</small></div>';
    }).join('');
  }

  function renderForecast(rows) {
    const target = $('#forecastChart');
    const summary = $('#forecastSummary');
    if (!rows || !rows.length || rows.every(row => row.total_cents <= 0)) {
      summary.innerHTML = '';
      target.innerHTML = '<div class="empty-inline">Ainda não há parcelas ou despesas recorrentes suficientes para projetar os próximos meses.</div>';
      return;
    }
    const max = Math.max(1, ...rows.map(row => Math.max(0, row.total_cents)));
    const next = rows.slice(0, 3).reduce((sum, row) => sum + Math.max(0, row.total_cents), 0);
    summary.innerHTML = '<div><small>Compromissos nos próximos 3 meses</small><b>' + money(next) + '</b></div><div><small>Maior previsão mensal</small><b>' + money(Math.max(...rows.map(row => row.total_cents))) + '</b></div>';
    target.innerHTML = rows.map((row, index) => {
      const height = Math.max(row.total_cents > 0 ? 5 : 0, Math.max(0, row.total_cents) / max * 100);
      const current = index === 0 ? 'is-current' : '';
      return '<div class="forecast-column ' + current + '" title="' + escapeHtml(row.label) + ': ' + money(row.total_cents) + '"><div class="forecast-bar-wrap"><span class="forecast-value">' + (row.total_cents > 0 ? money(row.total_cents) : '—') + '</span><div class="forecast-bar" style="height:' + height + '%"></div></div><small>' + escapeHtml(row.label) + '</small></div>';
    }).join('');
  }

  function renderEntries(target, rows, allowCancel = false) {
    if (!rows.length) {
      target.innerHTML = '<div class="empty-inline">Nenhum lançamento encontrado neste mês.</div>';
      return;
    }
    target.innerHTML = rows.map(row => {
      const credit = row.direction === 'credit';
      const kind = row.kind === 'parcelado' ? `${row.installment_number}/${row.installment_count}` : row.kind === 'recorrente' ? 'Fixo mensal' : 'À vista';
      const status = row.entry_status === 'historical' ? '<span class="status-pill historical">Parcela anterior</span>' : credit ? '<span class="status-pill credit">Estorno</span>' : '';
      const amount = `${credit ? '− ' : ''}${money(row.amount_cents)}`;
      const date = formatDate(row.purchase_date);
      const edit = allowCancel && row.purchase_active ? `<button class="mini-action" data-edit-purchase="${row.purchase_id}" data-description="${escapeHtml(row.description)}" data-notes="${escapeHtml(row.notes || '')}" title="Editar descrição e observações">Editar</button>` : '';
      const cancel = allowCancel && row.purchase_active && row.entry_status !== 'historical' ? `<button class="mini-action" data-cancel="${row.purchase_id}" title="Cancelar esta compra">Cancelar</button>` : '';
      return `<div class="entry-row"><div class="merchant"><div class="merchant-symbol" style="color:${escapeHtml(row.category_color)};background:${escapeHtml(row.category_color)}18">${icon(row.category_icon || categoryIcon(row.category_name))}</div><div class="merchant-copy"><b>${escapeHtml(row.description)}</b><small>${date} · ${escapeHtml(row.category_name)} ${status}</small></div></div><div class="entry-card">${escapeHtml(row.card_name)}</div><div class="entry-type"><span>${escapeHtml(kind)}</span></div><div class="entry-amount" style="${credit ? 'color:var(--green)' : ''}">${amount}<small>${credit ? 'Crédito na fatura' : row.kind === 'parcelado' ? 'Parcela da fatura' : row.kind === 'recorrente' ? 'Cobrança mensal' : 'Compra única'}</small></div><div class="entry-actions">${edit}${cancel}</div></div>`;
    }).join('');
    target.querySelectorAll('[data-edit-purchase]').forEach(button => button.addEventListener('click', () => openPurchaseEdit(Number(button.dataset.editPurchase), button.dataset.description, button.dataset.notes)));
    target.querySelectorAll('[data-cancel]').forEach(button => button.addEventListener('click', () => cancelPurchase(Number(button.dataset.cancel))));
  }

  async function loadStatement() {
    const q = $('#statementSearch').value.trim();
    const card = $('#statementCardFilter').value;
    const params = new URLSearchParams({ month: state.month });
    if (q) params.set('q', q);
    if (card) params.set('card_id', card);
    const rows = await api(`/api/entries?${params.toString()}`);
    state.entries = rows;
    $('#statementCount').textContent = `${rows.length} ${rows.length === 1 ? 'lançamento' : 'lançamentos'}`;
    const total = rows.reduce((sum, r) => sum + (r.direction === 'credit' ? -r.amount_cents : r.amount_cents), 0);
    $('#statementTotal').textContent = money(total);
    renderEntries($('#statementEntries'), rows, true);
  }

  async function cancelPurchase(id) {
    if (!window.confirm('Cancelar esta compra e suas parcelas atuais/futuras? As parcelas anteriores serão preservadas no histórico.')) return;
    try {
      const result = await api(`/api/purchases/${id}/cancel`, { method: 'POST', body: '{}' });
      toast(result.message || 'Compra cancelada.');
      await refreshDashboard();
    } catch (error) { toast(error.message); }
  }

  function renderCardOptions() {
    const activeCards = state.cards.filter(card => card.active !== false);
    const purchaseOptions = activeCards.map(card => `<option value="${card.id}">${escapeHtml(card.name)}</option>`).join('');
    const filterOptions = state.cards.map(card => `<option value="${card.id}">${escapeHtml(card.name)}${card.active === false ? ' · arquivado' : ''}</option>`).join('');
    $('#purchaseCard').innerHTML = `<option value="">${activeCards.length ? 'Selecione um cartão' : 'Cadastre um cartão ativo'}</option>${purchaseOptions}`;
    $('#statementCardFilter').innerHTML = `<option value="">Todos os cartões</option>${filterOptions}`;
  }
  function renderCategoryOptions() {
    const activeCategories = state.categories.filter(category => category.active !== false);
    $('#purchaseCategory').innerHTML = `<option value="">Selecione uma categoria</option>${activeCategories.map(category => `<option value="${category.id}">${escapeHtml(category.name)}</option>`).join('')}`;
  }
  const BANK_THEMES = {
    'Nubank': { mark: 'nu', color: '#820AD1', ink: '#fff' },
    'Itaú': { mark: 'itaú', color: '#EC7000', ink: '#fff' },
    'Bradesco': { mark: 'bradesco', color: '#CC092F', ink: '#fff' },
    'Banco do Brasil': { mark: 'BB', color: '#F7D117', ink: '#173B78' },
    'Caixa Econômica Federal': { mark: 'CAIXA', color: '#0066A1', ink: '#fff' },
    'Santander': { mark: 'Santander', color: '#EC0000', ink: '#fff' },
    'Inter': { mark: 'inter', color: '#FF7A00', ink: '#fff' },
    'C6 Bank': { mark: 'C6', color: '#171717', ink: '#fff' },
    'BTG Pactual': { mark: 'BTG', color: '#153D5B', ink: '#fff' },
    'Banco PAN': { mark: 'PAN', color: '#00AEEF', ink: '#08334A' },
    'Mercado Pago': { mark: 'MP', color: '#009EE3', ink: '#fff' },
    'PicPay': { mark: 'PicPay', color: '#21C25E', ink: '#083B20' },
    'PagBank': { mark: 'PagBank', color: '#00A868', ink: '#fff' },
    'Sicredi': { mark: 'sicredi', color: '#3FAE29', ink: '#fff' },
    'Sicoob': { mark: 'sicoob', color: '#003641', ink: '#fff' },
    'Banrisul': { mark: 'banrisul', color: '#005CA9', ink: '#fff' },
    'Banco Original': { mark: 'original', color: '#00A859', ink: '#fff' },
    'Neon': { mark: 'neon', color: '#0075FF', ink: '#fff' },
    'XP': { mark: 'XP', color: '#111827', ink: '#fff' },
    'Digio': { mark: 'digio', color: '#6639B7', ink: '#fff' },
    'Will Bank': { mark: 'will', color: '#FFDF00', ink: '#171717' },
    'BV': { mark: 'bv', color: '#00A5B5', ink: '#fff' },
    'Porto Bank': { mark: 'porto', color: '#003B70', ink: '#fff' },
    'Sofisa Direto': { mark: 'sofisa', color: '#164B3B', ink: '#fff' },
    'Unicred': { mark: 'unicred', color: '#008B67', ink: '#fff' },
    'Cresol': { mark: 'cresol', color: '#006B3C', ink: '#fff' },
    'Amazon': { mark: 'amazon', color: '#232F3E', ink: '#fff' },
    'Mercado Livre': { mark: 'ML', color: '#FFE600', ink: '#263238' },
    'Magalu': { mark: 'magalu', color: '#0086FF', ink: '#fff' },
    'Carrefour': { mark: 'Carrefour', color: '#004E9B', ink: '#fff' },
    'Renner': { mark: 'Renner', color: '#C8102E', ink: '#fff' },
    'Riachuelo': { mark: 'riachuelo', color: '#171717', ink: '#fff' },
    'Atacadão': { mark: 'Atacadão', color: '#E6B800', ink: '#173B78' },
    'Credicard': { mark: 'credicard', color: '#111827', ink: '#fff' },
    'Bradescard': { mark: 'bradescard', color: '#C8102E', ink: '#fff' },
    'DM': { mark: 'DM', color: '#E31837', ink: '#fff' },
    'Outro': { mark: '•••', color: '#247a57', ink: '#fff' },
  };
  const BRAND_PATHS = {
    'Nubank': 'M7.2795 5.4336c-1.1815 0-2.1846.4628-2.9432 1.252h-.002c-.0541-.0022-.1074-.002-.162-.002-1.5436 0-2.9925.8835-3.699 2.2559-.3088.5996-.4234 1.2442-.459 1.9003-.0321.589 0 1.1863 0 1.7696v5.6523H3.184s.0022-2.784 0-5.1777c-.0014-1.6112-.0118-3.0471 0-3.3418.056-1.3937.4372-2.3053 1.1484-3.0508 2.3585.0018 3.8852 1.6091 3.9705 4.168.0196.5874.0254 3.7304.0254 3.7304v3.672h3.1678v-4.965c0-1.5007.0127-2.8006-.0918-3.6952-.292-2.5-1.821-4.168-4.1248-4.168zm8.3903.3008l-3.166.0039v4.9648c0 1.5009-.0127 2.8007.0919 3.6953.2921 2.5001 1.821 4.168 4.1248 4.168 1.1815 0 2.1846-.4628 2.9432-1.252.0003-.0003.0016.0004.002 0 .0542.0023.1093.002.164.002 1.5435 0 2.9905-.8835 3.6971-2.2558.3088-.5997.4233-1.2442.459-1.9004.032-.5889 0-1.1862 0-1.7695V5.7383H20.816s-.0022 2.784 0 5.1777c.0015 1.6113.0119 3.047 0 3.3418-.056 1.3935-.4372 2.3053-1.1483 3.0508-2.3586-.0018-3.8853-1.6091-3.9706-4.168-.0196-.5874-.0273-2.0437-.0273-3.7324Z',
    'Neon': 'M24 0V24l-9.365-8.045V24H0V0ZM2.942 21.087h8.751V9.563l9.365 8.204V2.919L2.942 2.914Z',
    'PicPay': 'M16.463 1.587v7.537H24V1.587zm1.256 1.256h5.025v5.025h-5.025zm1.256 1.256v2.513h2.513V4.099zM3.77 5.355V8.53h3.376c2.142 0 3.358 1.04 3.358 2.939 0 1.947-1.216 3.011-3.358 3.011H3.769V8.53H0v13.884h3.769v-4.76h3.57c4.333 0 6.815-2.352 6.815-6.32 0-3.771-2.482-5.978-6.814-5.978Z'
  };
  function brandLogoMarkup(issuer) {
    const theme = bankTheme(issuer);
    if (BRAND_PATHS[issuer]) return '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="' + BRAND_PATHS[issuer] + '"/></svg>';
    if (issuer === 'Mercado Pago') return '<svg class="mercado-pago-logo" viewBox="0 0 150 48" role="img" aria-label="Mercado Pago"><g fill="none" stroke="currentColor" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 23 22 10c5-4 11-4 16 0l8 7 8-7c5-4 11-4 16 0l14 13-13 13-13-9-8 6-8-6-13 9Z"/><path d="m38 19 13 12c3 3 8-1 5-4l-7-7m-12 5 10 9c3 3 8-1 5-4m-12 1 6 6c3 3 8-1 5-4"/></g><text x="91" y="30" fill="currentColor" font-size="15" font-weight="800" letter-spacing="-1">mercado</text><text x="91" y="43" fill="currentColor" font-size="12" font-weight="700" letter-spacing="-.3">pago</text></svg>';
    if (issuer === 'Santander') return '<svg viewBox="0 0 150 42" role="img" aria-label="Santander"><path d="M16 4c-1 8 8 10 8 17 0 5-4 8-9 8-4 0-7-2-8-6 0 9 6 14 15 14 10 0 17-7 17-16 0-10-9-14-13-21 0 7-4 9-6 12-2-3-3-5-4-8Z" fill="currentColor"/><text x="45" y="28" fill="currentColor" font-size="23" font-weight="700" letter-spacing="-1">Santander</text></svg>';
    if (issuer === 'Itaú') return '<svg viewBox="0 0 90 42" role="img" aria-label="Itaú"><rect x="1" y="1" width="40" height="40" rx="8" fill="#003399"/><text x="21" y="28" text-anchor="middle" fill="#fff" font-size="20" font-weight="800">itaú</text><text x="48" y="27" fill="currentColor" font-size="18" font-weight="700">Itaú</text></svg>';
    if (issuer === 'Amazon') return '<svg class="amazon-wordmark" viewBox="0 0 120 42" role="img" aria-label="Amazon"><text x="3" y="25">amazon</text><path d="M18 31 Q59 47 101 29" /></svg>';
    const wordmarks = { 'Banco do Brasil':'Banco do Brasil', 'Caixa Econômica Federal':'CAIXA', 'C6 Bank':'C6 Bank', 'BTG Pactual':'BTG Pactual', 'Banco PAN':'Banco PAN', 'Mercado Livre':'mercado livre', 'Will Bank':'will bank', 'Porto Bank':'porto', 'PicPay':'PicPay', 'Nubank':'nu', 'Inter':'inter', 'Bradesco':'bradesco', 'Neon':'neon', 'XP':'XP' };
    return '<span class="brand-wordmark">' + escapeHtml(wordmarks[issuer] || issuer || theme.mark) + '</span>';
  }
  function bankTheme(issuer) { return BANK_THEMES[issuer] || BANK_THEMES.Outro; }
  function applyBankChoiceBrand(mark, issuer) {
    const theme = bankTheme(issuer);
    mark.innerHTML = brandLogoMarkup(issuer);
    mark.style.setProperty('--bank-tile', theme.color);
    mark.style.setProperty('--bank-tile-ink', theme.ink);
    mark.setAttribute('aria-label', issuer);
  }
  function renderCards() {
    const target = $('#cardsList');
    const activeCards = state.cards.filter(card => card.active !== false);
    const archivedCards = state.cards.filter(card => card.active === false);
    const totalLimit = activeCards.reduce((sum, card) => sum + (Number(card.limit_cents) || 0), 0);
    $('#cardsActiveCount').textContent = String(activeCards.length);
    $('#cardsArchivedCount').textContent = String(archivedCards.length);
    $('#cardsTotalLimit').textContent = money(totalLimit);
    if (!state.cards.length) { target.innerHTML = '<div class="empty-inline">Nenhum cartão cadastrado. Adicione seu primeiro cartão.</div>'; return; }
    target.innerHTML = state.cards.map(card => {
      const theme = bankTheme(card.issuer);
      const archived = card.active === false;
      return '<article class="bank-card-entry ' + (archived ? 'is-archived' : '') + '">' +
        '<div class="bank-card-face wallet-card-face" data-issuer="' + escapeHtml(card.issuer || 'Outro') + '" style="--bank-color:' + theme.color + ';--bank-ink:' + theme.ink + '">' +
          '<span class="wallet-card-glass" aria-hidden="true"></span>' +
          '<div class="bank-card-top"><span class="bank-logo-mark">' + brandLogoMarkup(card.issuer) + '</span></div>' +
          '<div class="wallet-card-bottom"><span class="wallet-card-label">' + escapeHtml(card.name && card.name !== card.issuer ? card.name : 'Crédito') + '</span><span class="wallet-card-orbit" aria-hidden="true"></span></div>' +
        '</div><div class="bank-card-details"><div><small>Limite total</small><strong>' + money(card.limit_cents || 0) + '</strong></div><div class="bank-card-actions">' +
          (archived ? '<span class="status-pill historical">Arquivado</span><button type="button" data-reactivate-card="' + card.id + '">Reativar</button>' : '<button type="button" data-edit-card="' + card.id + '">Editar</button><button type="button" data-archive-card="' + card.id + '">Arquivar</button>') +
        '</div></div></article>';
    }).join('');
    target.querySelectorAll('[data-edit-card]').forEach(button => button.addEventListener('click', () => startEditCard(button.dataset.editCard)));
    target.querySelectorAll('[data-archive-card]').forEach(button => button.addEventListener('click', () => archiveResource('cards', Number(button.dataset.archiveCard), 'cartão')));
    target.querySelectorAll('[data-reactivate-card]').forEach(button => button.addEventListener('click', () => reactivateResource('cards', Number(button.dataset.reactivateCard), 'cartão')));
  }
  function renderCategories() {
    const target = $('#categoriesList');
    const activeCategories = state.categories.filter(category => category.active !== false);
    const archivedCategories = state.categories.filter(category => category.active === false);
    $('#categoriesActiveCount').textContent = String(activeCategories.length);
    $('#categoriesArchivedCount').textContent = String(archivedCategories.length);
    if (!state.categories.length) { target.innerHTML = '<div class="empty-inline">Nenhuma categoria cadastrada.</div>'; return; }
    target.innerHTML = state.categories.map(category => `<div class="managed-item"><div class="managed-color" style="background:${escapeHtml(category.color)}">${icon(category.icon || categoryIcon(category.name))}</div><div class="managed-copy"><b>${escapeHtml(category.name)} ${category.active === false ? '<span class="status-pill historical">Arquivada</span>' : ''}</b><small>Categoria de gastos</small></div><div class="managed-actions">${category.active === false ? `<button type="button" data-reactivate-category="${category.id}">Reativar</button>` : `<button type="button" data-edit-category="${category.id}">Editar</button><button type="button" data-archive-category="${category.id}">Arquivar</button>`}</div></div>`).join('');
    target.querySelectorAll('[data-edit-category]').forEach(button => button.addEventListener('click', () => startEditCategory(Number(button.dataset.editCategory))));
    target.querySelectorAll('[data-archive-category]').forEach(button => button.addEventListener('click', () => archiveResource('categories', Number(button.dataset.archiveCategory), 'categoria')));
    target.querySelectorAll('[data-reactivate-category]').forEach(button => button.addEventListener('click', () => reactivateResource('categories', Number(button.dataset.reactivateCategory), 'categoria')));
  }
  async function archiveResource(resource, id, label) {
    if (!window.confirm(`Arquivar este ${label}? Os lançamentos existentes serão preservados.`)) return;
    try {
      await api(`/api/${resource}/${id}`, { method: 'DELETE' });
      state[resource] = await api(`/api/${resource}?include_archived=true`);
      if (resource === 'cards') { renderCards(); renderCardOptions(); }
      else { renderCategories(); renderCategoryOptions(); }
      await refreshDashboard();
      toast(`${label[0].toUpperCase()}${label.slice(1)} arquivado.`);
    } catch (error) { toast(error.message); }
  }

  async function reactivateResource(resource, id, label) {
    try {
      await api(`/api/${resource}/${id}/reactivate`, { method: 'POST' });
      state[resource] = await api(`/api/${resource}?include_archived=true`);
      if (resource === 'cards') { renderCards(); renderCardOptions(); }
      else { renderCategories(); renderCategoryOptions(); }
      await refreshDashboard();
      toast(`${label[0].toUpperCase()}${label.slice(1)} reativado.`);
    } catch (error) {
      toast(error.message);
    }
  }

  async function loadRecurrences() {
    const rows = await api('/api/recurrences');
    const target = $('#recurrencesList');
    const activeRows = rows.filter(row => row.active);
    const archivedRows = rows.filter(row => !row.active);
    const monthlyTotal = activeRows.reduce((sum, row) => sum + (Number(row.amount_cents) || 0), 0);
    $('#recurrencesActiveCount').textContent = String(activeRows.length);
    $('#recurrencesArchivedCount').textContent = String(archivedRows.length);
    $('#recurrencesMonthlyTotal').textContent = money(monthlyTotal);
    if (!rows.length) { target.innerHTML = '<div class="empty-inline">Nenhuma despesa fixa cadastrada. Use “Nova compra” e escolha “Fixo mensal”.</div>'; return; }
    target.innerHTML = rows.map(row => `<article class="recurrence-entry ${row.active ? 'is-active' : 'is-archived'}"><div class="merchant"><div class="merchant-symbol">${icon('repeat')}</div><div class="merchant-copy"><b>${escapeHtml(row.description)}</b><small>${escapeHtml(row.category_name)} · Início ${formatMonth(row.first_invoice_month)}</small></div></div><div class="entry-card">${escapeHtml(row.card_name)}</div><div class="entry-type"><span>Fixo mensal</span></div><div class="entry-amount">${money(row.amount_cents)}<small>${row.active ? 'Ativa' : 'Arquivada'}</small></div><div class="entry-actions">${row.active ? `<button class="mini-action" data-edit-purchase="${row.id}" data-description="${escapeHtml(row.description)}" data-notes="${escapeHtml(row.notes || '')}">Editar</button><button class="mini-action" data-cancel="${row.id}">Encerrar</button>` : ''}</div></article>`).join('');
    target.querySelectorAll('[data-edit-purchase]').forEach(b => b.addEventListener('click', () => openPurchaseEdit(Number(b.dataset.editPurchase), b.dataset.description, b.dataset.notes)));
    target.querySelectorAll('[data-cancel]').forEach(b => b.addEventListener('click', () => cancelPurchase(Number(b.dataset.cancel))));
  }

  function suggestInvoiceMonth() {
    const dateValue = $('#purchaseDate').value;
    const card = state.cards.find(c => String(c.id) === $('#purchaseCard').value);
    if (!dateValue || !card || state.invoiceMonthTouched) return;
    const d = new Date(`${dateValue}T12:00:00`);
    const month = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    const statementOffset = d.getDate() > card.closing_day ? 1 : 0;
    const paymentOffset = Number(card.due_month_offset ?? 1);
    $('#firstInvoiceMonth').value = addMonth(month, statementOffset + paymentOffset);
  }
  function setKind(kind) {
    const form = $('#purchaseForm');
    form.elements.kind.value = kind;
    $$('.type-switch button').forEach(b => b.classList.toggle('selected', b.dataset.kind === kind));
    if (kind !== 'parcelado') $('#ongoingCheck').checked = false;
    $('#installmentFields').classList.toggle('hidden', kind !== 'parcelado');
    $('#recurrenceEndField').classList.toggle('hidden', kind !== 'recorrente');
    $('#invoiceMonthField').classList.toggle('hidden', kind === 'parcelado' && $('#ongoingCheck').checked);
    $('#invoiceMonthLabel').querySelector('span').textContent = kind === 'recorrente' ? 'Mês de pagamento inicial' : 'Mês de pagamento da primeira parcela';
    updateOngoingFields();
    updateCalculation();
  }
  function updateDirectionOptions() {
    const credit = $('#purchaseForm').elements.direction.value === 'credit';
    const recurringButton = $('.type-switch button[data-kind="recorrente"]');
    recurringButton.disabled = credit;
    recurringButton.title = credit ? 'Estornos e créditos são lançamentos eventuais.' : '';
    $('#ongoingCheck').disabled = credit;
    if (credit) {
      $('#ongoingCheck').checked = false;
      if ($('#purchaseForm').elements.kind.value === 'recorrente') setKind('avista');
    }
    updateOngoingFields();
  }

  function updateOngoingFields() {
    const active = $('#ongoingCheck').checked;
    const installment = $('#purchaseForm').elements.kind.value === 'parcelado';
    $('#ongoingFields').classList.toggle('hidden', !active);
    $('#invoiceMonthField').classList.toggle('hidden', active);
    $('#firstInvoiceMonth').required = !active;
    if (!active || !installment) $('#valueMode').value = 'total';
    $('#valueMode').disabled = !active || !installment;
    const label = $('#amountLabel').querySelector('span');
    const direction = $('#purchaseForm').elements.direction.value;
    label.textContent = direction === 'credit' ? 'Valor do estorno (R$)' : (active && $('#valueMode').value === 'installment' ? 'Valor de cada parcela (R$)' : 'Valor da compra (R$)');
    updateCalculation();
  }
  function updateCalculation() {
    const kind = $('#purchaseForm').elements.kind.value;
    const amount = moneyInputToCents($('#purchaseForm').elements.amount.value || '0');
    const count = Math.max(1, Number($('#purchaseForm').elements.installment_count.value || 1));
    const ongoing = $('#ongoingCheck').checked && kind === 'parcelado';
    const mode = $('#valueMode').value;
    if (kind === 'avista') { $('#calculationPreview').classList.add('hidden'); return; }
    $('#calculationPreview').classList.remove('hidden');
    let per = amount;
    let detail = 'Cobrança mensal prevista';
    let label = 'Valor mensal';
    if (kind === 'parcelado') {
      if (ongoing && mode === 'installment') {
        per = amount;
        const current = $('#purchaseForm').elements.current_installment.value || 1;
        detail = `Parcela atual ${current}/${count} · valor informado por parcela`;
        label = 'Valor de cada parcela';
      } else {
        const base = Math.floor(amount / count);
        const remainder = amount % count;
        per = base;
        detail = remainder
          ? `${count - 1} parcelas de ${money(base)} e última de ${money(base + remainder)}`
          : `${count} parcelas de ${money(base)}`;
        label = 'Valor da primeira parcela';
      }
    }
    $('#calculationLabel').textContent = label;
    $('#calculationAmount').textContent = money(per);
    $('#calculationDetail').textContent = detail;
  }
  function resetPurchaseForm() {
    const form = $('#purchaseForm');
    form.reset();
    form.elements.kind.value = 'avista';
    form.elements.purchase_date.value = todayISO();
    form.elements.installment_count.value = 3;
    form.elements.current_installment.value = 2;
    form.elements.value_mode.value = 'total';
    form.elements.current_invoice_month.value = state.month;
    $('#firstInvoiceMonth').value = state.month;
    $('#ongoingCheck').checked = false;
    $('#firstInvoiceMonth').required = true;
    state.invoiceMonthTouched = false;
    setKind('avista');
    updateOngoingFields();
    $('#purchaseError').textContent = '';
    suggestInvoiceMonth();
  }
  function openPurchase(kind = 'avista') {
    resetPurchaseForm();
    if (kind === 'recorrente') setKind('recorrente');
    if (!state.cards.length || !state.categories.length) {
      toast('Antes de lançar, cadastre ao menos um cartão e uma categoria.');
      if (!state.cards.length) setPage('cards'); else setPage('categories');
      return;
    }
    renderCardOptions();
    renderCategoryOptions();
    openModal('purchaseModal');
  }

  async function submitPurchase(event) {
    event.preventDefault();
    const form = $('#purchaseForm');
    const data = new FormData(form);
    const kind = data.get('kind');
    const amountCents = purchaseInputToCents(data.get('amount'));
    const payload = {
      description: data.get('description').trim(),
      kind,
      direction: data.get('direction') || 'expense',
      purchase_date: data.get('purchase_date'),
      card_id: Number(data.get('card_id')),
      category_id: Number(data.get('category_id')),
      amount_cents: amountCents,
      value_mode: data.get('value_mode') || 'total',
      installment_count: kind === 'parcelado' ? Number(data.get('installment_count')) : 1,
      ongoing: kind === 'parcelado' && $('#ongoingCheck').checked,
      current_installment: kind === 'parcelado' ? Number(data.get('current_installment') || 1) : 1,
      first_invoice_month: kind === 'parcelado' && $('#ongoingCheck').checked ? null : data.get('first_invoice_month'),
      current_invoice_month: kind === 'parcelado' && $('#ongoingCheck').checked ? data.get('current_invoice_month') : null,
      end_invoice_month: kind === 'recorrente' ? (data.get('end_invoice_month') || null) : null,
      notes: data.get('notes') || '',
    };
    if (!payload.amount_cents || payload.amount_cents < 1) { $('#purchaseError').textContent = 'Informe um valor válido.'; return; }
    $('#purchaseError').textContent = '';
    try {
      await api('/api/purchases', { method: 'POST', body: JSON.stringify(payload) });
      closeModal('purchaseModal');
      // Open the invoice month where the new purchase was recorded so it is immediately visible.
      if (payload.first_invoice_month) {
        state.month = payload.first_invoice_month;
        $('#monthPicker').value = state.month;
      }
      await refreshDashboard();
      if (state.activePage === 'statement') await loadStatement();
      if (state.activePage === 'recurrences') await loadRecurrences();
      toast(kind === 'recorrente' ? 'Despesa fixa cadastrada.' : 'Compra registrada com sucesso.');
    } catch (error) { $('#purchaseError').textContent = error.message; }
  }

  function openPurchaseEdit(id, description, notes) {
    state.editingPurchaseId = id;
    $('#purchaseEditForm').elements.description.value = description || '';
    $('#purchaseEditForm').elements.notes.value = notes || '';
    $('#purchaseEditError').textContent = '';
    openModal('purchaseEditModal');
  }
  async function submitPurchaseEdit(event) {
    event.preventDefault();
    if (!state.editingPurchaseId) return;
    const form = $('#purchaseEditForm');
    const payload = {
      description: form.elements.description.value.trim(),
      notes: form.elements.notes.value.trim(),
    };
    try {
      await api(`/api/purchases/${state.editingPurchaseId}`, { method: 'PATCH', body: JSON.stringify(payload) });
      state.editingPurchaseId = null;
      closeModal('purchaseEditModal');
      await refreshDashboard();
      toast('Descrição e observações atualizadas.');
    } catch (error) { $('#purchaseEditError').textContent = error.message; }
  }

  async function submitBudget(event) {
    event.preventDefault();
    const amount = moneyInputToCents($('#budgetForm').elements.amount.value);
    if (!Number.isFinite(amount) || amount < 0) { $('#budgetError').textContent = 'Informe um limite válido.'; return; }
    try {
      await api('/api/budgets', { method: 'PUT', body: JSON.stringify({ month: state.month, limit_cents: amount }) });
      closeModal('budgetModal');
      await refreshDashboard();
      toast('Limite mensal atualizado.');
    } catch (error) { $('#budgetError').textContent = error.message; }
  }

  function parseMoneyInput(value) {
    const raw = String(value ?? '').trim().replace(/R\$/gi, '').replace(/\s/g, '');
    if (!raw) return 0;
    const normalized = raw.includes(',') ? raw.replace(/\./g, '').replace(',', '.') : raw;
    const amount = Number(normalized);
    return Number.isFinite(amount) && amount >= 0 ? amount : NaN;
  }
  function formatMoneyInput(value) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value || 0));
  }
  function setSelectedBank(issuer) {
    const input = $('#cardIssuer');
    const picker = $('#bankPicker');
    let choice = [...picker.querySelectorAll('[data-bank]')].find(item => item.dataset.bank === issuer);
    if (!choice && issuer) {
      choice = document.createElement('button');
      choice.type = 'button';
      choice.className = 'bank-choice';
      choice.dataset.bank = issuer;
      choice.innerHTML = '<span class="bank-choice-mark"></span><b></b>';
      applyBankChoiceBrand(choice.querySelector('.bank-choice-mark'), issuer);
      choice.querySelector('b').textContent = issuer;
      picker.insertBefore(choice, picker.lastElementChild);
      choice.addEventListener('click', () => { setSelectedBank(issuer); updateCardPreview(); });
    }
    input.value = issuer || '';
    picker.querySelectorAll('[data-bank]').forEach(item => {
      const selected = item.dataset.bank === issuer;
      item.classList.toggle('is-selected', selected);
      item.setAttribute('aria-pressed', selected ? 'true' : 'false');
    });
    picker.querySelectorAll('.bank-choice-mark').forEach(mark => { const item = mark.closest('[data-bank]'); applyBankChoiceBrand(mark, item.dataset.bank); });
    updateCardPreview();
  }
  function filterBankCatalog() {
    const query = ($('#bankSearch')?.value || '').trim().toLocaleLowerCase('pt-BR');
    const picker = $('#bankPicker');
    let visible = 0;
    picker.querySelectorAll('[data-bank]').forEach(item => {
      const show = item.dataset.bank.toLocaleLowerCase('pt-BR').includes(query);
      item.classList.toggle('hidden', !show);
      if (show) visible++;
    });
    picker.querySelectorAll('[data-bank-heading]').forEach(heading => {
      const next = heading.nextElementSibling;
      let hasVisible = false;
      let node = next;
      while (node && !node.hasAttribute('data-bank-heading')) { if (node.matches('[data-bank]') && !node.classList.contains('hidden')) hasVisible = true; node = node.nextElementSibling; }
      heading.classList.toggle('hidden', !hasVisible);
    });
    $('#bankSearchEmpty').classList.toggle('hidden', visible > 0);
  }
  function updateCardPreview() {
    const form = $('#cardForm');
    if (!form) return;
    const issuer = form.elements.issuer.value || 'Nubank';
    const theme = bankTheme(issuer);
    const amount = parseMoneyInput(form.elements.limit.value);
    const nickname = form.elements.name.value.trim() || 'Crédito';
    $('#previewCardFace').style.setProperty('--preview-color', theme.color);
    $('#previewCardFace').style.setProperty('--preview-ink', theme.ink);
    $('#previewBankMark').innerHTML = brandLogoMarkup(issuer);
    $('#previewCardFace').dataset.issuer = issuer;
    $('#previewBankName').textContent = '';
    $('#previewCardName').textContent = nickname;
    $('#previewCardLimit').textContent = Number.isFinite(amount) ? formatMoneyInput(amount) : '—';
    $('#previewLimitFact').textContent = Number.isFinite(amount) ? formatMoneyInput(amount) : '—';
    $('#previewClosingDay').textContent = form.elements.closing_day.value || '—';
    $('#previewDueDay').textContent = form.elements.due_day.value || '—';
  }
  function startEditCard(id) {
    const card = state.cards.find(item => item.id === id);
    if (!card) return;
    state.editingCardId = id;
    const form = $('#cardForm');
    form.elements.name.value = card.name === card.issuer ? '' : (card.name || '');
    form.elements.limit.value = ((card.limit_cents || 0) / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2 });
    form.elements.closing_day.value = card.closing_day ?? 3;
    form.elements.due_day.value = card.due_day ?? 10;
    setSelectedBank(card.issuer || 'Outro');
    $('#cardFormTitle').textContent = 'Editar instituição';
    $('#cardFormSubmit').textContent = 'Salvar alterações';
    $('#cancelCardEdit').classList.remove('hidden');
    $('#cardFormMessage').textContent = 'Alterar fechamento ou vencimento afeta apenas sugestões de novas compras.';
    setPage('cards');
    form.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
  function resetCardEditor() {
    state.editingCardId = null;
    const form = $('#cardForm');
    form.reset();
    form.elements.closing_day.value = 3;
    form.elements.due_day.value = 10;
    setSelectedBank('Nubank');
    $('#cardFormTitle').textContent = 'Instituição';
    $('#cardFormSubmit').textContent = '✓　Salvar cartão';
    $('#cancelCardEdit').classList.add('hidden');
    $('#cardFormMessage').textContent = '';
    updateCardPreview();
  }
  async function submitCard(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const fd = new FormData(form);
    const issuer = String(fd.get('issuer') || '').trim();
    const limit = parseMoneyInput(fd.get('limit'));
    if (!issuer) { $('#cardFormMessage').textContent = 'Escolha o banco do cartão.'; return; }
    if (!Number.isFinite(limit)) { $('#cardFormMessage').textContent = 'Informe um limite válido.'; return; }
    const theme = bankTheme(issuer);
    const payload = { name: String(fd.get('name') || '').trim(), issuer, limit_cents: Math.round(limit * 100), brand: '', last_four: null, closing_day: Number(fd.get('closing_day')), due_day: Number(fd.get('due_day')), color: theme.color };
    try {
      const editing = state.editingCardId;
      await api(editing ? `/api/cards/${editing}` : '/api/cards', { method: editing ? 'PUT' : 'POST', body: JSON.stringify(payload) });
      resetCardEditor();
      state.cards = await api('/api/cards?include_archived=true');
      renderCards(); renderCardOptions();
      await refreshDashboard();
      toast(editing ? 'Cartão atualizado.' : 'Cartão cadastrado.');
    } catch (error) { $('#cardFormMessage').textContent = error.message; }
  }
  function startEditCategory(id) {
    const category = state.categories.find(item => item.id === id);
    if (!category) return;
    state.editingCategoryId = id;
    const form = $('#categoryForm');
    for (const key of ['name', 'color', 'icon']) form.elements[key].value = category[key] ?? '';
    $('#categoryFormTitle').textContent = 'Editar categoria';
    $('#categoryFormSubmit').textContent = 'Salvar alterações';
    $('#cancelCategoryEdit').classList.remove('hidden');
    $('#categoryFormMessage').textContent = 'Os lançamentos existentes manterão os valores financeiros originais.';
    setPage('categories');
    form.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
  function resetCategoryEditor() {
    state.editingCategoryId = null;
    const form = $('#categoryForm');
    form.reset();
    form.elements.color.value = '#78a88b';
    $('#categoryFormTitle').textContent = 'Nova categoria';
    $('#categoryFormSubmit').textContent = 'Salvar categoria';
    $('#cancelCategoryEdit').classList.add('hidden');
    $('#categoryFormMessage').textContent = '';
  }
  async function submitCategory(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const fd = new FormData(form);
    const payload = { name: fd.get('name').trim(), color: fd.get('color'), icon: fd.get('icon') };
    try {
      const editing = state.editingCategoryId;
      await api(editing ? `/api/categories/${editing}` : '/api/categories', { method: editing ? 'PUT' : 'POST', body: JSON.stringify(payload) });
      resetCategoryEditor();
      state.categories = await api('/api/categories?include_archived=true');
      renderCategories(); renderCategoryOptions();
      await refreshDashboard();
      toast(editing ? 'Categoria atualizada.' : 'Categoria cadastrada.');
    } catch (error) { $('#categoryFormMessage').textContent = error.message; }
  }

  function wireEvents() {
    $('#themeToggle').addEventListener('click', toggleTheme);
    $$('.nav-item').forEach(button => button.addEventListener('click', () => setPage(button.dataset.page)));
    $$('[data-go]').forEach(button => button.addEventListener('click', () => setPage(button.dataset.go)));
    $('#monthPicker').addEventListener('change', async event => {
      if (!event.target.value) return;
      state.month = event.target.value;
      await refreshDashboard();
    });
    $('#newPurchase').addEventListener('click', () => openPurchase());
    $('#manageResources').addEventListener('click', () => openModal('managementModal'));
    $('#manageCardsShortcut').addEventListener('click', () => openModal('managementModal'));
    $('[data-management-tab]').forEach(button => button.addEventListener('click', () => {
      const cards = button.dataset.managementTab === 'cards';
      $('[data-management-tab]').forEach(item => item.classList.toggle('active', item === button));
      $('#managementCards').classList.toggle('hidden', !cards);
      $('#managementCategories').classList.toggle('hidden', cards);
    }));
    $('#monthPrevious').addEventListener('click', async () => changeSelectedMonth(-1));
    $('#monthNext').addEventListener('click', async () => changeSelectedMonth(1));
    $('#editBudget').addEventListener('click', () => {
      $('#budgetMonthLabel').textContent = formatMonth(state.month);
      $('#budgetForm').elements.amount.value = state.dashboard?.limit_cents != null ? (state.dashboard.limit_cents / 100).toFixed(2) : '';
      $('#budgetError').textContent = '';
      openModal('budgetModal');
    });
    $$('[data-close]').forEach(button => button.addEventListener('click', () => closeModal(button.dataset.close)));
    // Preserve form data: backdrop clicks do not dismiss open modals.
    document.addEventListener('keydown', event => { if (event.key === 'Escape') $$('.modal-backdrop:not(.hidden)').forEach(m => closeModal(m.id)); });
    $$('.type-switch button').forEach(button => button.addEventListener('click', () => setKind(button.dataset.kind)));
    $('#ongoingCheck').addEventListener('change', updateOngoingFields);
    $('#valueMode').addEventListener('change', updateOngoingFields);
    const purchaseAmountInput = $('#purchaseForm').elements.amount;
    purchaseAmountInput.addEventListener('input', () => {
      const digits = purchaseAmountInput.value.replace(/\D/g, '');
      purchaseAmountInput.value = digits
        ? (Number(digits) / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
        : '';
      updateCalculation();
    });
    $('#purchaseForm').elements.installment_count.addEventListener('input', updateCalculation);
    $('#purchaseForm').elements.current_installment.addEventListener('input', updateCalculation);
    $('#purchaseForm').elements.direction.addEventListener('change', updateDirectionOptions);
    $('#firstInvoiceMonth').addEventListener('change', () => { state.invoiceMonthTouched = true; });
    $('#purchaseDate').addEventListener('change', () => { state.invoiceMonthTouched = false; suggestInvoiceMonth(); });
    $('#purchaseCard').addEventListener('change', suggestInvoiceMonth);
    $('#purchaseForm').addEventListener('submit', submitPurchase);
    $('#budgetForm').addEventListener('submit', submitBudget);
    $('#cardForm').addEventListener('submit', submitCard);
    $('#bankPicker').querySelectorAll('[data-bank]').forEach(button => button.addEventListener('click', () => setSelectedBank(button.dataset.bank)));
    $('#bankSearch').addEventListener('input', filterBankCatalog);
    $('#bankPicker').querySelectorAll('.bank-choice-mark').forEach(mark => { const item = mark.closest('[data-bank]'); applyBankChoiceBrand(mark, item.dataset.bank); });
    filterBankCatalog();
    ['name', 'limit', 'closing_day', 'due_day'].forEach(key => $('#cardForm').elements[key].addEventListener('input', updateCardPreview));
    setSelectedBank('Nubank');
    $('#categoryForm').addEventListener('submit', submitCategory);
    $('#cancelCardEdit').addEventListener('click', resetCardEditor);
    $('#cancelCategoryEdit').addEventListener('click', resetCategoryEditor);
    $('#purchaseEditForm').addEventListener('submit', submitPurchaseEdit);
    $('#statementSearch').addEventListener('input', () => { clearTimeout(loadStatement.timer); loadStatement.timer = setTimeout(loadStatement, 180); });
    $('#statementCardFilter').addEventListener('change', loadStatement);
    $('#logoutButton').addEventListener('click', logout);
    $('#passwordChangeButton').addEventListener('click', () => {
      $('#passwordChangeForm').reset();
      $('#passwordChangeError').textContent = '';
      openModal('passwordModal');
    });
    $('#passwordChangeForm').addEventListener('submit', submitPasswordChange);
    $('#mobileLogout').addEventListener('click', logout);
    $('#backupButton').addEventListener('click', () => window.location.assign('/api/backup'));
    $('#restoreButton').addEventListener('click', () => $('#backupRestoreFile').click());
    $('#backupRestoreFile').addEventListener('change', restoreBackupFromFile);
    $('#loginForm').addEventListener('submit', login);
  }

  async function restoreBackupFromFile(event) {
    const file = event.currentTarget.files?.[0];
    event.currentTarget.value = '';
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      toast('O arquivo excede o limite de 10 MB.');
      return;
    }

    let backup;
    try {
      backup = JSON.parse(await file.text());
    } catch {
      toast('Não foi possível ler o arquivo. Selecione um backup JSON válido.');
      return;
    }
    if (!backup || backup.format !== 'xtrato-backup' || backup.version !== 1) {
      toast('Formato de backup não reconhecido ou versão incompatível.');
      return;
    }

    const confirmation = window.prompt(
      'A restauração só funciona em uma conta sem cartões, compras ou limites. Digite RESTAURAR para continuar.'
    );
    if (confirmation !== 'RESTAURAR') {
      toast('Restauração cancelada.');
      return;
    }

    try {
      const result = await api('/api/backup/restore', {
        method: 'POST',
        body: JSON.stringify({ ...backup, confirmation: 'RESTAURAR' }),
      });
      await loadInitialData();
      toast(`Backup restaurado: ${result.restored.purchases} compras e ${result.restored.cards} cartões.`);
    } catch (error) {
      toast(error.message);
    }
  }

  async function login(event) {
    event.preventDefault();
    const fd = new FormData(event.currentTarget);
    $('#loginError').textContent = '';
    try {
      const user = await api('/api/auth/login', { method: 'POST', body: JSON.stringify({ username: fd.get('username'), password: fd.get('password') }) });
      showApp(user);
      await loadInitialData();
    } catch (error) { $('#loginError').textContent = error.message; }
  }
  async function submitPasswordChange(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const currentPassword = form.elements.current_password.value;
    const newPassword = form.elements.new_password.value;
    const confirmPassword = form.elements.confirm_password.value;
    $('#passwordChangeError').textContent = '';

    if (newPassword !== confirmPassword) {
      $('#passwordChangeError').textContent = 'A confirmação não corresponde à nova senha.';
      return;
    }
    if (newPassword.length < 12) {
      $('#passwordChangeError').textContent = 'A nova senha precisa ter pelo menos 12 caracteres.';
      return;
    }

    try {
      await api('/api/auth/password', {
        method: 'POST',
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      closeModal('passwordModal');
      form.reset();
      state.user = null;
      showLogin();
      toast('Senha alterada. Entre novamente com a nova senha.');
    } catch (error) {
      $('#passwordChangeError').textContent = error.message;
    }
  }

  async function logout() {
    try { await api('/api/auth/logout', { method: 'POST', body: '{}' }); } catch (_) { /* local logout anyway */ }
    state.user = null;
    showLogin();
  }

  async function init() {
    initializeTheme();
    refreshStaticIcons();
    state.month = monthNow();
    $('#monthPicker').value = state.month;
    $('#purchaseDate').value = todayISO();
    $('#firstInvoiceMonth').value = state.month;
    wireEvents();
    updateDirectionOptions();
    try {
      const user = await api('/api/auth/me');
      showApp(user);
      await loadInitialData();
    } catch (_) {
      showLogin();
    }
  }
  document.addEventListener('DOMContentLoaded', init);
})();
