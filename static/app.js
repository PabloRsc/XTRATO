(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const money = cents => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format((Number(cents) || 0) / 100);
  const moneyInputToCents = value => Math.round(Number(String(value).replace(',', '.')) * 100);
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
    state.cards = await api('/api/cards');
    state.categories = await api('/api/categories');
    await refreshDashboard();
    renderCardOptions();
    renderCategoryOptions();
    renderCards();
    renderCategories();
    refreshStaticIcons();
  }
  async function refreshDashboard() {
    const dashboard = await api(`/api/dashboard?month=${encodeURIComponent(state.month)}`);
    state.dashboard = dashboard;
    state.entries = dashboard.recent_entries || [];
    renderDashboard();
    if (state.activePage === 'statement') await loadStatement();
    if (state.activePage === 'recurrences') await loadRecurrences();
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
    $('#cardTotals').innerHTML = d.cards.length ? d.cards.map(c => `<div class="card-total-line"><span>${escapeHtml(c.name)}${c.active ? '' : ' · arquivado'}</span><b>${money(c.total_cents)}</b></div>`).join('') : '<div class="muted-dark">Cadastre seu primeiro cartão para começar.</div>';
    renderCategoryChart(d.categories || []);
    renderTrend(d.trend || []);
    renderEntries($('#recentEntries'), d.recent_entries || [], true);
    $('#monthPicker').value = state.month;
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
      const label = row.label.slice(0, 3);
      return `<div class="trend-column ${current}"><span class="trend-value">${row.total_cents > 0 ? money(row.total_cents).replace(',00', '') : ''}</span><div class="trend-bar-area"><div class="trend-bar" style="height:${height}%"></div></div><small>${escapeHtml(label)}</small></div>`;
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
    const options = state.cards.map(c => `<option value="${c.id}">${escapeHtml(c.name)}${c.last_four ? ` ···· ${c.last_four}` : ''}</option>`).join('');
    $('#purchaseCard').innerHTML = `<option value="">${state.cards.length ? 'Selecione um cartão' : 'Cadastre um cartão'}</option>${options}`;
    $('#statementCardFilter').innerHTML = `<option value="">Todos os cartões</option>${options}`;
  }
  function renderCategoryOptions() {
    $('#purchaseCategory').innerHTML = `<option value="">Selecione uma categoria</option>${state.categories.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('')}`;
  }
  function renderCards() {
    const target = $('#cardsList');
    if (!state.cards.length) { target.innerHTML = '<div class="empty-inline">Nenhum cartão cadastrado. Adicione seu primeiro cartão ao lado.</div>'; return; }
    target.innerHTML = state.cards.map(c => `<div class="managed-item"><div class="managed-color" style="background:${escapeHtml(c.color)}">${icon('card')}</div><div class="managed-copy"><b>${escapeHtml(c.name)}${c.last_four ? ` ···· ${c.last_four}` : ''}</b><small>${escapeHtml(c.issuer || c.brand || 'Cartão')} · Fecha dia ${c.closing_day} · Vence dia ${c.due_day} · ${Number(c.due_month_offset) === 0 ? 'mesmo mês' : 'mês seguinte'}</small></div><div class="managed-actions"><button type="button" data-edit-card="${c.id}">Editar</button><button type="button" data-archive-card="${c.id}">Arquivar</button></div></div>`).join('');
    target.querySelectorAll('[data-edit-card]').forEach(b => b.addEventListener('click', () => startEditCard(Number(b.dataset.editCard))));
    target.querySelectorAll('[data-archive-card]').forEach(b => b.addEventListener('click', () => archiveResource('cards', Number(b.dataset.archiveCard), 'cartão')));
  }
  function renderCategories() {
    const target = $('#categoriesList');
    if (!state.categories.length) { target.innerHTML = '<div class="empty-inline">Nenhuma categoria cadastrada.</div>'; return; }
    target.innerHTML = state.categories.map(c => `<div class="managed-item"><div class="managed-color" style="background:${escapeHtml(c.color)}">${icon(c.icon || categoryIcon(c.name))}</div><div class="managed-copy"><b>${escapeHtml(c.name)}</b><small>Categoria de gastos</small></div><div class="managed-actions"><button type="button" data-edit-category="${c.id}">Editar</button><button type="button" data-archive-category="${c.id}">Arquivar</button></div></div>`).join('');
    target.querySelectorAll('[data-edit-category]').forEach(b => b.addEventListener('click', () => startEditCategory(Number(b.dataset.editCategory))));
    target.querySelectorAll('[data-archive-category]').forEach(b => b.addEventListener('click', () => archiveResource('categories', Number(b.dataset.archiveCategory), 'categoria')));
  }
  async function archiveResource(resource, id, label) {
    if (!window.confirm(`Arquivar este ${label}? Os lançamentos existentes serão preservados.`)) return;
    try {
      await api(`/api/${resource}/${id}`, { method: 'DELETE' });
      state[resource] = await api(`/api/${resource}`);
      if (resource === 'cards') { renderCards(); renderCardOptions(); }
      else { renderCategories(); renderCategoryOptions(); }
      await refreshDashboard();
      toast(`${label[0].toUpperCase()}${label.slice(1)} arquivado.`);
    } catch (error) { toast(error.message); }
  }

  async function loadRecurrences() {
    const rows = await api('/api/recurrences');
    const target = $('#recurrencesList');
    if (!rows.length) { target.innerHTML = '<div class="empty-inline">Nenhuma despesa fixa cadastrada. Use “Nova compra” e escolha “Fixo mensal”.</div>'; return; }
    target.innerHTML = rows.map(row => `<div class="entry-row"><div class="merchant"><div class="merchant-symbol">${icon('repeat')}</div><div class="merchant-copy"><b>${escapeHtml(row.description)}</b><small>${escapeHtml(row.category_name)} · Início ${formatMonth(row.first_invoice_month)}</small></div></div><div class="entry-card">${escapeHtml(row.card_name)}</div><div class="entry-type"><span>Fixo mensal</span></div><div class="entry-amount">${money(row.amount_cents)}<small>${row.active ? 'Ativa' : 'Arquivada'}</small></div><div class="entry-actions">${row.active ? `<button class="mini-action" data-edit-purchase="${row.id}" data-description="${escapeHtml(row.description)}" data-notes="${escapeHtml(row.notes || '')}">Editar</button><button class="mini-action" data-cancel="${row.id}">Encerrar</button>` : ''}</div></div>`).join('');
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
    const amountCents = moneyInputToCents(data.get('amount'));
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

  function startEditCard(id) {
    const card = state.cards.find(item => item.id === id);
    if (!card) return;
    state.editingCardId = id;
    const form = $('#cardForm');
    for (const key of ['name', 'issuer', 'brand', 'last_four', 'closing_day', 'due_day', 'due_month_offset', 'color']) {
      form.elements[key].value = card[key] ?? '';
    }
    $('#cardFormTitle').textContent = 'Editar cartão';
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
    form.elements.closing_day.value = 25;
    form.elements.due_day.value = 5;
    form.elements.due_month_offset.value = 1;
    form.elements.color.value = '#247a57';
    $('#cardFormTitle').textContent = 'Adicionar cartão';
    $('#cardFormSubmit').textContent = 'Salvar cartão';
    $('#cancelCardEdit').classList.add('hidden');
    $('#cardFormMessage').textContent = '';
  }
  async function submitCard(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const fd = new FormData(form);
    const payload = { name: fd.get('name').trim(), issuer: fd.get('issuer').trim(), brand: fd.get('brand'), last_four: fd.get('last_four') || null, closing_day: Number(fd.get('closing_day')), due_day: Number(fd.get('due_day')), due_month_offset: Number(fd.get('due_month_offset')), color: fd.get('color') };
    try {
      const editing = state.editingCardId;
      await api(editing ? `/api/cards/${editing}` : '/api/cards', { method: editing ? 'PUT' : 'POST', body: JSON.stringify(payload) });
      resetCardEditor();
      state.cards = await api('/api/cards');
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
      state.categories = await api('/api/categories');
      renderCategories(); renderCategoryOptions();
      await refreshDashboard();
      toast(editing ? 'Categoria atualizada.' : 'Categoria cadastrada.');
    } catch (error) { $('#categoryFormMessage').textContent = error.message; }
  }

  function wireEvents() {
    $$('.nav-item').forEach(button => button.addEventListener('click', () => setPage(button.dataset.page)));
    $$('[data-go]').forEach(button => button.addEventListener('click', () => setPage(button.dataset.go)));
    $('#monthPicker').addEventListener('change', async event => {
      if (!event.target.value) return;
      state.month = event.target.value;
      await refreshDashboard();
    });
    $('#newPurchase').addEventListener('click', () => openPurchase());
    $('#newPurchaseStatement').addEventListener('click', () => openPurchase());
    $('#newRecurring').addEventListener('click', () => openPurchase('recorrente'));
    $('#editBudget').addEventListener('click', () => {
      $('#budgetMonthLabel').textContent = formatMonth(state.month);
      $('#budgetForm').elements.amount.value = state.dashboard?.limit_cents != null ? (state.dashboard.limit_cents / 100).toFixed(2) : '';
      $('#budgetError').textContent = '';
      openModal('budgetModal');
    });
    $$('[data-close]').forEach(button => button.addEventListener('click', () => closeModal(button.dataset.close)));
    $$('.modal-backdrop').forEach(backdrop => backdrop.addEventListener('click', event => { if (event.target === backdrop) closeModal(backdrop.id); }));
    document.addEventListener('keydown', event => { if (event.key === 'Escape') $$('.modal-backdrop:not(.hidden)').forEach(m => closeModal(m.id)); });
    $$('.type-switch button').forEach(button => button.addEventListener('click', () => setKind(button.dataset.kind)));
    $('#ongoingCheck').addEventListener('change', updateOngoingFields);
    $('#valueMode').addEventListener('change', updateOngoingFields);
    $('#purchaseForm').elements.amount.addEventListener('input', updateCalculation);
    $('#purchaseForm').elements.installment_count.addEventListener('input', updateCalculation);
    $('#purchaseForm').elements.current_installment.addEventListener('input', updateCalculation);
    $('#purchaseForm').elements.direction.addEventListener('change', updateDirectionOptions);
    $('#firstInvoiceMonth').addEventListener('change', () => { state.invoiceMonthTouched = true; });
    $('#purchaseDate').addEventListener('change', () => { state.invoiceMonthTouched = false; suggestInvoiceMonth(); });
    $('#purchaseCard').addEventListener('change', suggestInvoiceMonth);
    $('#purchaseForm').addEventListener('submit', submitPurchase);
    $('#budgetForm').addEventListener('submit', submitBudget);
    $('#cardForm').addEventListener('submit', submitCard);
    $('#categoryForm').addEventListener('submit', submitCategory);
    $('#cancelCardEdit').addEventListener('click', resetCardEditor);
    $('#cancelCategoryEdit').addEventListener('click', resetCategoryEditor);
    $('#purchaseEditForm').addEventListener('submit', submitPurchaseEdit);
    $('#statementSearch').addEventListener('input', () => { clearTimeout(loadStatement.timer); loadStatement.timer = setTimeout(loadStatement, 180); });
    $('#statementCardFilter').addEventListener('change', loadStatement);
    $('#logoutButton').addEventListener('click', logout);
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
  async function logout() {
    try { await api('/api/auth/logout', { method: 'POST', body: '{}' }); } catch (_) { /* local logout anyway */ }
    state.user = null;
    showLogin();
  }

  async function init() {
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
