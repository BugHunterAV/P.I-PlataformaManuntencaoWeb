// ============================================================
//  NanaSmart — app.js
//  Toda a lógica JS separada do HTML
// ============================================================

var BASE = localStorage.getItem('ns_base') || 'http://localhost:8000';
var TOKEN         = localStorage.getItem('ns_tok') || '';       // access token JWT
var REFRESH_TOKEN = localStorage.getItem('ns_ref') || '';       // refresh token JWT
var CUR = 'dashboard';

var PAGE_TITLES = {
  dashboard: 'Dashboard',
  ativos: 'Ativos Industriais',
  manutencao: 'Ordens de Manutencao',
  historico: 'Historico de Manutencao',
  sensores: 'Sensores IoT',
  telemetria: 'Telemetria',
  alertas: 'Alertas Automaticos',
  localizacao: 'Localizacao Industrial',
  conta: 'Minha Conta'
};

// ── Helpers de API ──────────────────────────────────────────

function api(path) {
  return BASE + '/api' + path;
}

function hdrs() {
  var h = { 'Content-Type': 'application/json' };
  if (TOKEN) h['Authorization'] = 'Bearer ' + TOKEN;  // JWT usa Bearer
  return h;
}

// Tenta renovar o access token usando o refresh token
async function refreshAccessToken() {
  if (!REFRESH_TOKEN) return false;
  try {
    var r = await fetch(BASE + '/api/auth/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: REFRESH_TOKEN })
    });
    if (r.ok) {
      var d = await r.json();
      TOKEN = d.access;
      localStorage.setItem('ns_tok', TOKEN);
      return true;
    }
  } catch(e) {}
  return false;
}

// Wrapper de fetch que renova token automaticamente em caso de 401
async function apiFetch(url, opts) {
  opts = opts || {};
  opts.headers = hdrs();
  var r = await fetch(url, opts);
  if (r.status === 401 && REFRESH_TOKEN) {
    var ok = await refreshAccessToken();
    if (ok) {
      opts.headers = hdrs();
      r = await fetch(url, opts);
    }
  }
  return r;
}

function fmt(d) {
  if (!d) return '--';
  try { return new Date(d).toLocaleString('pt-BR'); } catch(e) { return String(d); }
}

function badge(s) {
  if (!s) return '<span class="badge b-gray">--</span>';
  var map = {
    ativo:'b-green', inativo:'b-gray', em_manutencao:'b-orange',
    aberta:'b-blue', em_andamento:'b-orange', concluida:'b-green', cancelada:'b-gray',
    critica:'b-red', alta:'b-orange', media:'b-blue', baixa:'b-gray',
    preventiva:'b-blue', corretiva:'b-red', preditiva:'b-orange',
    temperatura:'b-orange', vibracao:'b-blue', pressao:'b-green', corrente:'b-red', umidade:'b-blue'
  };
  var cls = map[s] || 'b-gray';
  return '<span class="badge ' + cls + '">' + String(s).replace(/_/g,' ') + '</span>';
}

function showToast(msg, type) {
  var wrap = document.getElementById('toasts');
  var el = document.createElement('div');
  el.className = 'toast';
  var color = type === 'success' ? '#00C853' : (type === 'error' ? '#FF1744' : '#1E88E5');
  el.innerHTML = '<span style="color:' + color + ';font-weight:700;font-size:11px">[' + String(type).toUpperCase() + ']</span><span>' + String(msg) + '</span>';
  wrap.appendChild(el);
  setTimeout(function() { if (el.parentNode) el.parentNode.removeChild(el); }, 4000);
}

function loadingRow(cols) {
  cols = cols || 6;
  return '<tr><td colspan="' + cols + '"><div class="loading"><div class="spin"></div>Carregando...</div></td></tr>';
}

function emptyRow(msg, cols) {
  cols = cols || 6;
  return '<tr><td colspan="' + cols + '"><div class="empty">' + String(msg) + '</div></td></tr>';
}

function getList(data) {
  if (!data) return [];
  return Array.isArray(data) ? data : (data.results || []);
}

// ── Modais ──────────────────────────────────────────────────

function openM(id) {
  document.getElementById(id).classList.add('open');
  if (id === 'm-manut') fillSel('m-ativo', '/ativos/', false);
  if (id === 'm-sensor') fillSel('s-ativo', '/ativos/', false);
  if (id === 'm-leit') {
    fillSel('lt-ativo', '/ativos/', false);
    fillSel('lt-sensor', '/telemetria/sensores/', true);
  }
  if (id === 'm-local') fillSel('loc-ativo', '/ativos/', false);
}

function closeM(id) {
  document.getElementById(id).classList.remove('open');
}

document.querySelectorAll('.overlay').forEach(function(o) {
  o.addEventListener('click', function(e) {
    if (e.target === o) o.classList.remove('open');
  });
});

async function fillSel(selId, path, optional) {
  try {
    var r = await apiFetch(api(path));
    if (!r.ok) return;
    var data = await r.json();
    var items = getList(data);
    var sel = document.getElementById(selId);
    var cur = sel.value;
    var html = optional ? '<option value="">-- Nenhum --</option>' : '';
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      html += '<option value="' + it.id + '">' + (it.nome || it.name || String(it.id)) + '</option>';
    }
    sel.innerHTML = html;
    if (cur) sel.value = cur;
  } catch(e) {}
}

// ── Autenticação ─────────────────────────────────────────────
//  O backend expõe /api/accounts/login/ e /api/accounts/register/
//  Ambos são endpoints DRF com Token auth.

function switchTab(t) {
  document.getElementById('tab-login').style.display = (t === 'login') ? '' : 'none';
  document.getElementById('tab-reg').style.display = (t === 'reg') ? '' : 'none';
  document.getElementById('tab-btn-login').className = 'auth-tab' + ((t === 'login') ? ' active' : '');
  document.getElementById('tab-btn-reg').className = 'auth-tab' + ((t === 'reg') ? ' active' : '');
}

/**
 * Preenche usuário e senha de teste no formulário de login
 * (usado pelo botão "Usar login de teste")
 */
function fillDemo() {
  document.getElementById('l-user').value = 'admin';
  document.getElementById('l-pass').value = 'admin123';
}

async function doLogin() {
  var user = document.getElementById('l-user').value.trim();
  var pass = document.getElementById('l-pass').value;
  var msg  = document.getElementById('l-msg');
  msg.textContent = '';
  msg.style.color = 'var(--dim)';

  if (!user || !pass) { msg.textContent = 'Preencha usuario e senha.'; return; }

  BASE = document.getElementById('api-url').value.replace(/\/$/, '');
  localStorage.setItem('ns_base', BASE);

  msg.textContent = 'Autenticando...';

  try {
    // JWT: POST /api/auth/login/ -> { access, refresh }
    var r = await fetch(BASE + '/api/auth/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: user, password: pass })
    });

    var data;
    try { data = await r.json(); } catch(e) { data = {}; }

    if (r.ok && data.access) {
      TOKEN         = data.access;
      REFRESH_TOKEN = data.refresh || '';
      localStorage.setItem('ns_tok', TOKEN);
      localStorage.setItem('ns_ref', REFRESH_TOKEN);
      document.getElementById('auth-gate').style.display = 'none';
      document.getElementById('sb-user').textContent = user;
      loadDash();
      showToast('Login realizado! Bem-vindo, ' + user, 'success');
    } else {
      var err = data.detail
        || (data.non_field_errors && data.non_field_errors[0])
        || (data.username && data.username[0])
        || JSON.stringify(data)
        || 'Credenciais invalidas.';
      msg.style.color = 'var(--red)';
      msg.textContent = String(err);
    }
  } catch(e) {
    msg.style.color = 'var(--red)';
    msg.textContent = 'Erro de conexao: ' + e.message + '. Verifique se o backend esta rodando em ' + BASE;
  }
}

async function doRegister() {
  var user  = document.getElementById('r-user').value.trim();
  var email = document.getElementById('r-email').value.trim();
  var pass  = document.getElementById('r-pass').value;
  var msg   = document.getElementById('r-msg');
  msg.textContent = '';
  msg.style.color = 'var(--dim)';

  if (!user || !pass) { msg.textContent = 'Preencha usuario e senha.'; return; }
  if (pass.length < 6) { msg.textContent = 'A senha deve ter ao menos 6 caracteres.'; return; }

  // Atualiza BASE com o valor atual da URL bar
  BASE = document.getElementById('api-url').value.replace(/\/$/, '');
  localStorage.setItem('ns_base', BASE);

  msg.textContent = 'Criando conta...';

  try {
    var r = await fetch(BASE + '/api/usuarios/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: user, email: email, password: pass })
    });

    var data;
    try { data = await r.json(); } catch(e) { data = {}; }

    if (r.ok) {
      // Se o registro já retorna token, faz login direto
      if (data.token) {
        TOKEN = data.token;
        localStorage.setItem('ns_tok', TOKEN);
        document.getElementById('auth-gate').style.display = 'none';
        document.getElementById('sb-user').textContent = data.username || user;
        loadDash();
        showToast('Conta criada e login realizado!', 'success');
      } else {
        msg.style.color = 'var(--green)';
        msg.textContent = 'Conta criada com sucesso! Faca login.';
        setTimeout(function() { switchTab('login'); }, 1200);
      }
    } else {
      // Monta mensagem de erro legível
      var errParts = [];
      if (typeof data === 'object') {
        Object.keys(data).forEach(function(k) {
          var v = Array.isArray(data[k]) ? data[k].join(', ') : String(data[k]);
          errParts.push(k + ': ' + v);
        });
      }
      msg.style.color = 'var(--red)';
      msg.textContent = errParts.length ? errParts.join(' | ') : 'Erro ao criar conta.';
    }
  } catch(e) {
    msg.style.color = 'var(--red)';
    msg.textContent = 'Erro de conexao: ' + e.message;
  }
}

async function doLogout() {
  TOKEN = '';
  REFRESH_TOKEN = '';
  localStorage.removeItem('ns_tok');
  localStorage.removeItem('ns_ref');
  location.reload();
}

function copyTok() {
  navigator.clipboard.writeText(TOKEN).then(function() { showToast('Token copiado!', 'success'); });
}

// ── Navegação ────────────────────────────────────────────────

function goto(pg) {
  var pages    = document.querySelectorAll('.page');
  var navItems = document.querySelectorAll('.nav-item');
  for (var i = 0; i < pages.length; i++) pages[i].classList.remove('active');
  for (var j = 0; j < navItems.length; j++) navItems[j].classList.remove('active');
  document.getElementById('page-' + pg).classList.add('active');
  for (var k = 0; k < navItems.length; k++) {
    var oc = navItems[k].getAttribute('onclick');
    if (oc && oc.indexOf("'" + pg + "'") >= 0) navItems[k].classList.add('active');
  }
  document.getElementById('page-title').textContent = PAGE_TITLES[pg] || pg;
  CUR = pg;
  loadPage(pg);
}

function refresh() { loadPage(CUR); }

function loadPage(pg) {
  var fns = {
    dashboard:   loadDash,
    ativos:      loadAtivos,
    manutencao:  loadManut,
    historico:   loadHist,
    sensores:    loadSensores,
    telemetria:  loadTele,
    alertas:     loadAlertas,
    localizacao: loadLocal,
    conta:       loadConta
  };
  if (fns[pg]) fns[pg]();
}

async function testConn() {
  BASE = document.getElementById('api-url').value.replace(/\/$/, '');
  localStorage.setItem('ns_base', BASE);
  var dot = document.getElementById('api-dot');
  try {
    var r = await apiFetch(api('/ativos/'));
    if (r.ok || r.status === 401 || r.status === 403) {
      dot.className = 'api-dot';
      showToast('API conectada! Status: ' + r.status, 'success');
    } else {
      dot.className = 'api-dot off';
      showToast('API retornou status ' + r.status, 'error');
    }
  } catch(e) {
    dot.className = 'api-dot off';
    showToast('Sem conexao: ' + e.message, 'error');
  }
}

// ── Dashboard ────────────────────────────────────────────────

async function loadDash() {
  var results = await Promise.allSettled([
    apiFetch(api('/ativos/')).then(function(r) { return r.json(); }),
    apiFetch(api('/manutencao/')).then(function(r) { return r.json(); }),
    apiFetch(api('/alertas/')).then(function(r) { return r.json(); }),
    apiFetch(api('/telemetria/sensores/')).then(function(r) { return r.json(); }),
    apiFetch(api('/dashboards/kpis/')).then(function(r) { return r.json(); })
  ]);
  var ativos  = (results[0].status === 'fulfilled') ? getList(results[0].value) : [];
  var manut   = (results[1].status === 'fulfilled') ? getList(results[1].value) : [];
  var alertas = (results[2].status === 'fulfilled') ? getList(results[2].value) : [];
  var sens    = (results[3].status === 'fulfilled') ? getList(results[3].value) : [];
  document.getElementById('ds-ativos').textContent  = ativos.length;
  var openManut = 0;
  for (var i = 0; i < manut.length; i++) {
    if (manut[i].status === 'aberta' || manut[i].status === 'em_andamento') openManut++;
  }
  document.getElementById('ds-manut').textContent   = openManut;
  document.getElementById('ds-alertas').textContent = alertas.length;
  document.getElementById('ds-sens').textContent    = sens.length;
  if (results[4].status === 'fulfilled') {
    var k = results[4].value;
    var mtbf = parseFloat(k.mtbf_horas || k.mtbf || 0);
    var mttr = parseFloat(k.mttr_horas || k.mttr || 0);
    var disp = parseFloat(k.disponibilidade || k.disponibilidade_percent || 0);
    document.getElementById('k-mtbf').textContent   = mtbf.toFixed(1);
    document.getElementById('k-mttr').textContent   = mttr.toFixed(1);
    document.getElementById('k-disp').textContent   = disp.toFixed(1);
    document.getElementById('k-mtbf-b').style.width = Math.min(mtbf / 5, 100) + '%';
    document.getElementById('k-mttr-b').style.width = Math.min(mttr / 0.72, 100) + '%';
    document.getElementById('k-disp-b').style.width = Math.min(disp, 100) + '%';
  }
  var tb = document.getElementById('dash-tb');
  if (!ativos.length) { tb.innerHTML = emptyRow('Nenhum ativo cadastrado', 4); return; }
  var rows = '';
  var limit = Math.min(ativos.length, 8);
  for (var j = 0; j < limit; j++) {
    var a = ativos[j];
    rows += '<tr><td><strong>' + (a.nome || '--') + '</strong></td>' +
      '<td><code>' + (a.numero_serie || '--') + '</code></td>' +
      '<td>' + badge(a.status) + '</td>' +
      '<td>' + fmt(a.criado_em || a.created_at) + '</td></tr>';
  }
  tb.innerHTML = rows;
}

// ── Ativos ───────────────────────────────────────────────────

async function loadAtivos() {
  var tb  = document.getElementById('ativos-tb');
  tb.innerHTML = loadingRow(6);
  var url = api('/ativos/?');
  var sEl = document.getElementById('fa-search');
  var stEl = document.getElementById('fa-status');
  if (sEl && sEl.value) url += 'search=' + encodeURIComponent(sEl.value) + '&';
  if (stEl && stEl.value) url += 'status=' + stEl.value + '&';
  try {
    var r = await apiFetch(url);
    if (!r.ok) { tb.innerHTML = emptyRow('Erro ' + r.status, 6); return; }
    var data = await r.json();
    var items = getList(data);
    if (!items.length) { tb.innerHTML = emptyRow('Nenhum ativo encontrado', 6); return; }
    var rows = '';
    for (var i = 0; i < items.length; i++) {
      var a = items[i];
      rows += '<tr><td><strong>' + (a.nome || '--') + '</strong></td>' +
        '<td><code>' + (a.numero_serie || '--') + '</code></td>' +
        '<td>' + (a.modelo || '--') + '</td>' +
        '<td>' + badge(a.status) + '</td>' +
        '<td>' + fmt(a.criado_em || a.created_at) + '</td>' +
        '<td><div class="row-acts">' +
          '<button class="btn btn-outline btn-sm" onclick="editAtivo(' + a.id + ')">Editar</button>' +
          '<button class="btn btn-danger" onclick="delAtivo(' + a.id + ')">Del</button>' +
        '</div></td></tr>';
    }
    tb.innerHTML = rows;
  } catch(e) { tb.innerHTML = emptyRow(e.message, 6); }
}

function resetAtivoForm() {
  ['a-id','a-nome','a-serie','a-modelo','a-fab','a-data','a-desc'].forEach(function(id) {
    document.getElementById(id).value = '';
  });
  document.getElementById('a-status').value = 'ativo';
  document.getElementById('ativo-modal-ttl').textContent = 'Novo Ativo';
}

async function editAtivo(id) {
  try {
    var r = await apiFetch(api('/ativos/' + id + '/'));
    var a = await r.json();
    document.getElementById('a-id').value     = id;
    document.getElementById('a-nome').value   = a.nome || '';
    document.getElementById('a-serie').value  = a.numero_serie || '';
    document.getElementById('a-modelo').value = a.modelo || '';
    document.getElementById('a-fab').value    = a.fabricante || '';
    document.getElementById('a-status').value = a.status || 'ativo';
    document.getElementById('a-data').value   = a.data_aquisicao || '';
    document.getElementById('a-desc').value   = a.descricao || '';
    document.getElementById('ativo-modal-ttl').textContent = 'Editar Ativo';
    openM('m-ativo');
  } catch(e) { showToast('Erro ao carregar ativo', 'error'); }
}

async function saveAtivo() {
  var id    = document.getElementById('a-id').value;
  var nome  = document.getElementById('a-nome').value;
  var serie = document.getElementById('a-serie').value;
  if (!nome || !serie) { showToast('Nome e N Serie sao obrigatorios', 'error'); return; }
  var body = {
    nome: nome,
    numero_serie: serie,
    modelo:     document.getElementById('a-modelo').value,
    fabricante: document.getElementById('a-fab').value,
    status:     document.getElementById('a-status').value,
    data_aquisicao: document.getElementById('a-data').value || null,
    descricao:  document.getElementById('a-desc').value
  };
  try {
    var url = id ? api('/ativos/' + id + '/') : api('/ativos/');
    var r = await apiFetch(url, { method: id ? 'PUT' : 'POST', body: JSON.stringify(body) });
    if (r.ok) {
      showToast(id ? 'Ativo atualizado!' : 'Ativo criado!', 'success');
      closeM('m-ativo');
      loadAtivos();
    } else {
      var e = await r.json();
      showToast('Erro: ' + JSON.stringify(e), 'error');
    }
  } catch(e) { showToast('Erro: ' + e.message, 'error'); }
}

async function delAtivo(id) {
  if (!confirm('Excluir este ativo?')) return;
  try {
    var r = await apiFetch(api('/ativos/' + id + '/'), { method: 'DELETE' });
    if (r.ok || r.status === 204) { showToast('Ativo excluido', 'success'); loadAtivos(); }
    else showToast('Erro ao excluir', 'error');
  } catch(e) { showToast(e.message, 'error'); }
}

// ── Manutencao ───────────────────────────────────────────────

async function loadManut() {
  var tb  = document.getElementById('manut-tb');
  tb.innerHTML = loadingRow(7);
  var url = api('/manutencao/?');
  var sEl  = document.getElementById('fm-search');
  var stEl = document.getElementById('fm-status');
  if (sEl && sEl.value) url += 'search=' + encodeURIComponent(sEl.value) + '&';
  if (stEl && stEl.value) url += 'status=' + stEl.value + '&';
  try {
    var r = await apiFetch(url);
    if (!r.ok) { tb.innerHTML = emptyRow('Erro ' + r.status, 7); return; }
    var data = await r.json();
    var items = getList(data);
    if (!items.length) { tb.innerHTML = emptyRow('Nenhuma ordem encontrada', 7); return; }
    var rows = '';
    for (var i = 0; i < items.length; i++) {
      var m = items[i];
      rows += '<tr><td><strong>' + (m.titulo || m.descricao || '--') + '</strong></td>' +
        '<td>' + (m.ativo_nome || m.ativo || '--') + '</td>' +
        '<td>' + badge(m.tipo) + '</td>' +
        '<td>' + badge(m.prioridade) + '</td>' +
        '<td>' + badge(m.status) + '</td>' +
        '<td>' + (m.responsavel || '--') + '</td>' +
        '<td><div class="row-acts">' +
          '<button class="btn btn-outline btn-sm" onclick="editManut(' + m.id + ')">Editar</button>' +
          '<button class="btn btn-danger" onclick="delManut(' + m.id + ')">Del</button>' +
        '</div></td></tr>';
    }
    tb.innerHTML = rows;
  } catch(e) { tb.innerHTML = emptyRow(e.message, 7); }
}

function resetManutForm() {
  ['m-id','m-titulo','m-resp','m-desc'].forEach(function(id) { document.getElementById(id).value = ''; });
  document.getElementById('m-tipo').value   = 'preventiva';
  document.getElementById('m-prior').value  = 'media';
  document.getElementById('m-status').value = 'aberta';
  document.getElementById('manut-modal-ttl').textContent = 'Nova Ordem';
}

async function editManut(id) {
  try {
    var r = await apiFetch(api('/manutencao/' + id + '/'));
    var m = await r.json();
    document.getElementById('m-id').value     = id;
    document.getElementById('m-titulo').value  = m.titulo || '';
    document.getElementById('m-tipo').value    = m.tipo || 'preventiva';
    document.getElementById('m-prior').value   = m.prioridade || 'media';
    document.getElementById('m-status').value  = m.status || 'aberta';
    document.getElementById('m-resp').value    = m.responsavel || '';
    document.getElementById('m-desc').value    = m.descricao || '';
    document.getElementById('manut-modal-ttl').textContent = 'Editar Ordem';
    openM('m-manut');
    var ativoId = m.ativo;
    setTimeout(function() { if (ativoId) document.getElementById('m-ativo').value = ativoId; }, 400);
  } catch(e) { showToast('Erro ao carregar', 'error'); }
}

async function saveManut() {
  var id     = document.getElementById('m-id').value;
  var titulo = document.getElementById('m-titulo').value;
  var ativo  = parseInt(document.getElementById('m-ativo').value);
  if (!titulo || !ativo) { showToast('Titulo e Ativo sao obrigatorios', 'error'); return; }
  var body = {
    titulo:     titulo,
    ativo:      ativo,
    tipo:       document.getElementById('m-tipo').value,
    prioridade: document.getElementById('m-prior').value,
    status:     document.getElementById('m-status').value,
    responsavel:document.getElementById('m-resp').value,
    descricao:  document.getElementById('m-desc').value
  };
  try {
    var url = id ? api('/manutencao/' + id + '/') : api('/manutencao/');
    var r = await apiFetch(url, { method: id ? 'PUT' : 'POST', body: JSON.stringify(body) });
    if (r.ok) {
      showToast(id ? 'Ordem atualizada!' : 'Ordem criada!', 'success');
      closeM('m-manut');
      loadManut();
    } else {
      var e = await r.json();
      showToast('Erro: ' + JSON.stringify(e), 'error');
    }
  } catch(e) { showToast('Erro: ' + e.message, 'error'); }
}

async function delManut(id) {
  if (!confirm('Excluir esta ordem?')) return;
  try {
    var r = await apiFetch(api('/manutencao/' + id + '/'), { method: 'DELETE' });
    if (r.ok || r.status === 204) { showToast('Ordem excluida', 'success'); loadManut(); }
    else showToast('Erro ao excluir', 'error');
  } catch(e) { showToast(e.message, 'error'); }
}

// ── Historico ────────────────────────────────────────────────

async function loadHist() {
  var tb = document.getElementById('hist-tb');
  tb.innerHTML = loadingRow(6);
  try {
    var r = await apiFetch(api('/manutencao/historico/'));
    if (!r.ok) { tb.innerHTML = emptyRow('Endpoint /manutencao/historico/ retornou ' + r.status, 6); return; }
    var data = await r.json();
    var items = getList(data);
    if (!items.length) { tb.innerHTML = emptyRow('Nenhum historico registrado', 6); return; }
    var rows = '';
    for (var i = 0; i < items.length; i++) {
      var h = items[i];
      rows += '<tr><td><code>' + fmt(h.data || h.created_at) + '</code></td>' +
        '<td>' + (h.ativo_nome || h.ativo || '--') + '</td>' +
        '<td>' + (h.descricao || '--') + '</td>' +
        '<td>' + (h.tecnico || h.responsavel || '--') + '</td>' +
        '<td>' + (h.custo != null ? 'R$ ' + parseFloat(h.custo).toFixed(2) : '--') + '</td>' +
        '<td>' + (h.duracao_horas != null ? h.duracao_horas + 'h' : '--') + '</td></tr>';
    }
    tb.innerHTML = rows;
  } catch(e) { tb.innerHTML = emptyRow(e.message, 6); }
}

// ── Sensores ─────────────────────────────────────────────────

async function loadSensores() {
  var grid = document.getElementById('sensor-grid');
  var tb   = document.getElementById('sensor-tb');
  grid.innerHTML = '<div class="loading"><div class="spin"></div>Carregando...</div>';
  tb.innerHTML   = loadingRow(7);
  try {
    var r = await apiFetch(api('/telemetria/sensores/'));
    if (!r.ok) { grid.innerHTML = ''; tb.innerHTML = emptyRow('Erro ' + r.status, 7); return; }
    var data  = await r.json();
    var items = getList(data);
    if (!items.length) {
      grid.innerHTML = '<div class="empty">Nenhum sensor cadastrado</div>';
      tb.innerHTML   = emptyRow('Nenhum sensor', 7);
      return;
    }
    var cards = '';
    var rows  = '';
    for (var i = 0; i < items.length; i++) {
      var s = items[i];
      cards += '<div class="sensor-card"><div class="pulse-dot"></div>' +
        '<div class="s-type">' + (s.tipo || '--') + '</div>' +
        '<div class="s-val">--<span class="s-unit">' + (s.unidade || '') + '</span></div>' +
        '<div class="s-name">' + (s.nome || '--') + '</div></div>';
      rows += '<tr><td><strong>' + (s.nome || '--') + '</strong></td>' +
        '<td>' + badge(s.tipo) + '</td>' +
        '<td>' + (s.ativo_nome || s.ativo || '--') + '</td>' +
        '<td>' + (s.limite_minimo != null ? s.limite_minimo : '--') + '</td>' +
        '<td>' + (s.limite_maximo != null ? s.limite_maximo : '--') + '</td>' +
        '<td>' + (s.unidade || '--') + '</td>' +
        '<td><button class="btn btn-danger" onclick="delSensor(' + s.id + ')">Del</button></td></tr>';
    }
    grid.innerHTML = cards;
    tb.innerHTML   = rows;
  } catch(e) { grid.innerHTML = ''; tb.innerHTML = emptyRow(e.message, 7); }
}

function resetSensorForm() {
  ['s-id','s-nome','s-unit','s-min','s-max'].forEach(function(id) { document.getElementById(id).value = ''; });
  document.getElementById('s-tipo').value = 'temperatura';
}

async function saveSensor() {
  var id   = document.getElementById('s-id').value;
  var nome = document.getElementById('s-nome').value;
  var ativo = parseInt(document.getElementById('s-ativo').value);
  if (!nome || !ativo) { showToast('Nome e Ativo sao obrigatorios', 'error'); return; }
  var body = {
    nome:  nome,
    ativo: ativo,
    tipo:  document.getElementById('s-tipo').value,
    unidade: document.getElementById('s-unit').value,
    limite_minimo: document.getElementById('s-min').value || null,
    limite_maximo: document.getElementById('s-max').value || null
  };
  try {
    var url = id ? api('/telemetria/sensores/' + id + '/') : api('/telemetria/sensores/');
    var r = await apiFetch(url, { method: id ? 'PUT' : 'POST', body: JSON.stringify(body) });
    if (r.ok) { showToast('Sensor salvo!', 'success'); closeM('m-sensor'); loadSensores(); }
    else { var e = await r.json(); showToast('Erro: ' + JSON.stringify(e), 'error'); }
  } catch(e) { showToast(e.message, 'error'); }
}

async function delSensor(id) {
  if (!confirm('Excluir sensor?')) return;
  try {
    var r = await apiFetch(api('/telemetria/sensores/' + id + '/'), { method: 'DELETE' });
    if (r.ok || r.status === 204) { showToast('Sensor excluido', 'success'); loadSensores(); }
    else showToast('Erro ao excluir', 'error');
  } catch(e) { showToast(e.message, 'error'); }
}

// ── Telemetria ───────────────────────────────────────────────

async function loadTele() {
  var tb = document.getElementById('tele-tb');
  tb.innerHTML = loadingRow(6);
  try {
    var r = await apiFetch(api('/telemetria/leituras/'));
    if (!r.ok) { tb.innerHTML = emptyRow('Erro ' + r.status, 6); return; }
    var data  = await r.json();
    var items = getList(data);
    if (!items.length) { tb.innerHTML = emptyRow('Nenhuma leitura registrada', 6); return; }
    var rows = '';
    for (var i = 0; i < items.length; i++) {
      var l = items[i];
      rows += '<tr><td><code>' + fmt(l.timestamp || l.criado_em || l.created_at) + '</code></td>' +
        '<td>' + (l.sensor_nome || l.sensor || '--') + '</td>' +
        '<td>' + (l.ativo_nome || l.ativo || '--') + '</td>' +
        '<td>' + badge(l.tipo) + '</td>' +
        '<td><strong style="color:var(--orange-l)">' + (l.valor != null ? l.valor : '--') + '</strong></td>' +
        '<td>' + (l.unidade || '--') + '</td></tr>';
    }
    tb.innerHTML = rows;
  } catch(e) { tb.innerHTML = emptyRow(e.message, 6); }
}

async function saveLeitura() {
  var ativo    = parseInt(document.getElementById('lt-ativo').value);
  var valorStr = document.getElementById('lt-valor').value;
  var valor    = parseFloat(valorStr);
  if (!ativo || isNaN(valor)) { showToast('Ativo e Valor sao obrigatorios', 'error'); return; }
  var body = {
    ativo:    ativo,
    tipo:     document.getElementById('lt-tipo').value,
    valor:    valor,
    unidade:  document.getElementById('lt-unit').value
  };
  var sensor = document.getElementById('lt-sensor').value;
  if (sensor) body.sensor = parseInt(sensor);
  try {
    var r = await apiFetch(api('/telemetria/leituras/'), { method: 'POST', body: JSON.stringify(body) });
    if (r.ok) { showToast('Leitura enviada! Alertas verificados.', 'success'); closeM('m-leit'); loadTele(); }
    else { var e = await r.json(); showToast('Erro: ' + JSON.stringify(e), 'error'); }
  } catch(e) { showToast(e.message, 'error'); }
}

// ── Alertas ──────────────────────────────────────────────────

async function loadAlertas() {
  var list = document.getElementById('alertas-list');
  list.innerHTML = '<div class="loading"><div class="spin"></div>Carregando...</div>';
  try {
    var r = await apiFetch(api('/alertas/'));
    if (!r.ok) { list.innerHTML = '<div class="empty">Erro ' + r.status + '</div>'; return; }
    var data  = await r.json();
    var items = getList(data);
    if (!items.length) { list.innerHTML = '<div class="empty">Nenhum alerta ativo</div>'; return; }
    var clsMap = { critico:'crit', alto:'crit', medio:'warn', baixo:'info' };
    var html = '';
    for (var i = 0; i < items.length; i++) {
      var a   = items[i];
      var sev = String(a.severidade || a.nivel || 'info').toLowerCase();
      var cls = clsMap[sev] || 'info';
      html += '<div class="alert-item ' + cls + '">' +
        '<div class="alert-ico">[!]</div>' +
        '<div class="alert-txt">' +
          '<div class="alert-ttl">' + (a.titulo || a.mensagem || 'Alerta') + '</div>' +
          '<div class="alert-dsc">' + (a.descricao || a.detalhe || '') + ' - Ativo: ' + (a.ativo_nome || a.ativo || '--') + '</div>' +
        '</div>' +
        '<div class="alert-time">' + fmt(a.criado_em || a.created_at) + '</div>' +
        '</div>';
    }
    list.innerHTML = html;
  } catch(e) { list.innerHTML = '<div class="empty">' + e.message + '</div>'; }
}

// ── Localizacao ──────────────────────────────────────────────

async function loadLocal() {
  var tb = document.getElementById('local-tb');
  tb.innerHTML = loadingRow(5);
  try {
    var r = await apiFetch(api('/localizacao/'));
    if (!r.ok) { tb.innerHTML = emptyRow('Erro ' + r.status, 5); return; }
    var data  = await r.json();
    var items = getList(data);
    if (!items.length) { tb.innerHTML = emptyRow('Nenhuma localizacao', 5); return; }
    var rows = '';
    for (var i = 0; i < items.length; i++) {
      var l = items[i];
      var coords = (l.latitude != null && l.longitude != null) ? l.latitude + ', ' + l.longitude : '--';
      rows += '<tr><td><strong>' + (l.planta || '--') + '</strong></td>' +
        '<td>' + (l.setor || '--') + '</td>' +
        '<td>' + (l.ativo_nome || l.ativo || '--') + '</td>' +
        '<td><code>' + coords + '</code></td>' +
        '<td><button class="btn btn-danger" onclick="delLocal(' + l.id + ')">Del</button></td></tr>';
    }
    tb.innerHTML = rows;
  } catch(e) { tb.innerHTML = emptyRow(e.message, 5); }
}

function resetLocalForm() {
  ['loc-id','loc-planta','loc-setor','loc-lat','loc-lng'].forEach(function(id) { document.getElementById(id).value = ''; });
}

async function saveLocal() {
  var id    = document.getElementById('loc-id').value;
  var planta = document.getElementById('loc-planta').value;
  var setor  = document.getElementById('loc-setor').value;
  var ativo  = parseInt(document.getElementById('loc-ativo').value);
  if (!planta || !setor || !ativo) { showToast('Planta, Setor e Ativo sao obrigatorios', 'error'); return; }
  var body = {
    planta: planta,
    setor:  setor,
    ativo:  ativo,
    latitude:  document.getElementById('loc-lat').value || null,
    longitude: document.getElementById('loc-lng').value || null
  };
  try {
    var url = id ? api('/localizacao/' + id + '/') : api('/localizacao/');
    var r = await apiFetch(url, { method: id ? 'PUT' : 'POST', body: JSON.stringify(body) });
    if (r.ok) { showToast('Localizacao salva!', 'success'); closeM('m-local'); loadLocal(); }
    else { var e = await r.json(); showToast('Erro: ' + JSON.stringify(e), 'error'); }
  } catch(e) { showToast(e.message, 'error'); }
}

async function delLocal(id) {
  if (!confirm('Excluir localizacao?')) return;
  try {
    var r = await apiFetch(api('/localizacao/' + id + '/'), { method: 'DELETE' });
    if (r.ok || r.status === 204) { showToast('Excluido', 'success'); loadLocal(); }
    else showToast('Erro ao excluir', 'error');
  } catch(e) { showToast(e.message, 'error'); }
}

// ── Conta ────────────────────────────────────────────────────

async function loadConta() {
  document.getElementById('token-show').value = TOKEN;
  try {
    var r = await apiFetch(BASE + '/api/auth/me/');
    if (r.ok) {
      var d = await r.json();
      document.getElementById('me-data').textContent = JSON.stringify(d, null, 2);
      document.getElementById('sb-user').textContent = d.username || d.user || '--';
    } else {
      document.getElementById('me-data').textContent = '/api/auth/me/ retornou ' + r.status;
    }
  } catch(e) { document.getElementById('me-data').textContent = 'Erro: ' + e.message; }
}

// ── Init ─────────────────────────────────────────────────────

// Sincroniza o campo da URL bar com o BASE salvo
document.getElementById('api-url').value = BASE;

if (TOKEN) {
  document.getElementById('auth-gate').style.display = 'none';
  loadDash();
}

document.getElementById('l-pass').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') doLogin();
});

document.getElementById('r-pass').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') doRegister();
});