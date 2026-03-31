/* ═══════════════════════════════════════════════════════════════
   INFRASMART — script.js v4.0
   Integração completa com API NanaSmart (Django REST Framework)
   Base URL: http://localhost:8000/api
═══════════════════════════════════════════════════════════════ */

// ════════════════════════════════════════════════════════════
// CONFIGURAÇÃO DA API
// ════════════════════════════════════════════════════════════
const API_BASE = 'http://localhost:8000/api';
let AUTH_TOKEN  = sessionStorage.getItem('auth_token') || null;
let API_ONLINE  = false; // será verificado no login

/**
 * Realiza uma chamada à API com autenticação por Token.
 * Retorna o JSON da resposta ou null em caso de erro/offline.
 */
async function apiCall(method, endpoint, body = null, suppressError = false) {
  const headers = { 'Content-Type': 'application/json' };
  if (AUTH_TOKEN) headers['Authorization'] = `Token ${AUTH_TOKEN}`;

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    // 204 No Content
    if (res.status === 204) return { ok: true };

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      if (!suppressError) {
        const msg = data?.detail || data?.non_field_errors?.[0]
          || Object.values(data)[0]?.[0] || `Erro ${res.status}`;
        toast(String(msg), 'error');
      }
      return { error: true, status: res.status, data };
    }

    return data;
  } catch (err) {
    if (!suppressError) console.warn('[API] Offline ou erro de rede:', err.message);
    API_ONLINE = false;
    updateApiStatus();
    return null;
  }
}

function updateApiStatus() {
  const dot  = document.querySelector('.status-dot');
  const txt  = document.querySelector('.status-text');
  if (!dot || !txt) return;
  if (API_ONLINE) {
    dot.style.background  = 'var(--green-500)';
    txt.textContent = 'API Online';
  } else {
    dot.style.background  = 'var(--orange-500)';
    txt.textContent = 'Modo Demo';
  }
}

// Extrai array de uma resposta paginada ou retorna diretamente
function extractList(data) {
  if (!data) return null;
  if (Array.isArray(data)) return data;
  if (Array.isArray(data.results)) return data.results;
  return null;
}

// ════════════════════════════════════════════════════════════
// NORMALIZADORES  (API → formato interno do frontend)
// ════════════════════════════════════════════════════════════
function normalizeAtivo(a) {
  return {
    id_equipamento : a.id,
    nome           : a.nome || '',
    tipo           : a.tipo || '',
    fabricante     : a.fabricante || '',
    modelo         : a.modelo || '',
    numero_serie   : a.numero_serie || '',
    status         : a.status || 'operacional',
    localizacao    : a.localizacao || { setor: '—' },
    qtd_sensores   : a.qtd_sensores ?? a.sensores?.length ?? 0,
  };
}

function normalizeAlerta(a) {
  const nivel = a.severidade || a.nivel || 'medio';
  const resolvido = !!(a.resolvido_em || a.status === 'resolvido');
  return {
    id_alerta         : a.id,
    tipo_alerta       : a.tipo || a.tipo_alerta || 'Alerta',
    nivel             : nivel,
    descricao         : a.descricao || '',
    id_equipamento    : a.ativo?.id ?? a.ativo ?? a.id_equipamento ?? null,
    data_alerta       : a.criado_em || a.data_alerta || new Date().toISOString(),
    status            : resolvido ? 'resolvido' : 'aberto',
    tecnico_resolveu  : a.resolvido_por?.nome || a.tecnico_resolveu || null,
    id_tecnico_resolveu: a.resolvido_por?.id || a.id_tecnico_resolveu || null,
    equipamento       : a.ativo
      ? { nome: a.ativo.nome || String(a.ativo) }
      : (a.equipamento || null),
  };
}

function normalizeManutencao(m) {
  return {
    id_manutencao  : m.id,
    tipo           : m.tipo || 'preventiva',
    descricao      : m.descricao || m.titulo || '',
    data_programada: m.data_programada || m.data_abertura || '',
    id_equipamento : m.ativo?.id ?? m.ativo ?? m.id_equipamento ?? null,
    status         : m.status || 'agendada',
    equipamento    : m.ativo
      ? { nome: m.ativo.nome || String(m.ativo) }
      : (m.equipamento || null),
  };
}

function normalizeOrdem(o) {
  return {
    id_ordem_servico : o.id,
    numero_os        : o.numero_os || o.titulo || `OS-${o.id}`,
    descricao        : o.descricao || o.titulo || '',
    prioridade       : o.prioridade || 'media',
    status           : o.status || 'aberta',
    data_abertura    : o.data_abertura || o.criado_em || '',
    id_tecnico       : o.tecnico?.id ?? o.tecnico ?? o.id_tecnico ?? null,
    id_manutencao    : o.manutencao?.id ?? o.manutencao ?? o.id_manutencao ?? null,
    tecnico          : o.tecnico
      ? (typeof o.tecnico === 'object' ? { nome: o.tecnico.nome || o.tecnico.username } : { nome: String(o.tecnico) })
      : null,
  };
}

function normalizeSensor(s) {
  return {
    id_sensor      : s.id,
    tipo_sensor    : s.tipo || s.tipo_sensor || '',
    unidade_medida : s.unidade || s.unidade_medida || '',
    id_equipamento : s.ativo?.id ?? s.ativo ?? s.equipamento ?? s.id_equipamento ?? null,
    limite_min     : s.limite_min ?? null,
    limite_max     : s.limite_max ?? null,
    ultimo_valor   : s.ultimo_valor ?? null,
  };
}

function normalizeLeitura(l) {
  return {
    id_leitura : l.id,
    id_sensor  : l.sensor?.id ?? l.sensor,
    valor      : l.valor,
    data_hora  : l.data_leitura || l.data_hora,
  };
}

function normalizeHistorico(h) {
  const custo = parseFloat(
    h.custo_total ?? h.custo_pecas ?? h.custo_mao_de_obra ?? h.custo ?? 0
  );
  return {
    id_historico       : h.id,
    id_ordem_servico   : h.ordem_servico?.id ?? h.ordem_servico ?? h.id_ordem_servico ?? null,
    id_tecnico         : h.tecnico?.id ?? h.tecnico ?? h.id_tecnico ?? null,
    descricao_servico  : h.descricao || h.descricao_servico || '',
    data_execucao      : h.data_execucao || h.criado_em || '',
    custo,
    ordem_servico      : h.ordem_servico
      ? (typeof h.ordem_servico === 'object'
        ? { numero_os: h.ordem_servico.numero_os || h.ordem_servico.titulo || `#${h.ordem_servico.id}` }
        : { numero_os: `#${h.ordem_servico}` })
      : null,
    tecnico: h.tecnico
      ? (typeof h.tecnico === 'object'
        ? { nome: h.tecnico.nome || h.tecnico.username || '' }
        : { nome: String(h.tecnico) })
      : null,
  };
}

function normalizeUsuario(u) {
  const nome = u.nome
    || `${u.first_name || ''} ${u.last_name || ''}`.trim()
    || u.username || '';
  return {
    id         : u.id,
    email      : u.email || '',
    nome,
    cargo      : u.cargo || u.tipo_usuario || '',
    role       : u.tipo_usuario === 'admin' ? 'admin'
               : u.tipo_usuario === 'tecnico' ? 'tecnico'
               : u.tipo_usuario === 'viewer'  ? 'viewer'
               : 'user',
    status     : u.is_active === false ? 'suspenso' : (u.status || 'ativo'),
    id_tecnico : u.id_tecnico || null,
    createdAt  : u.date_joined?.split('T')[0] || u.criado_em?.split('T')[0] || '',
  };
}

function normalizeTecnico(u) {
  return {
    id_tecnico   : u.id,
    nome         : u.nome || `${u.first_name||''} ${u.last_name||''}`.trim() || u.username || '',
    especialidade: u.especialidade || u.cargo || '',
    telefone     : u.telefone || '',
    email        : u.email || '',
    area         : u.area || '',
    ativo        : u.is_active !== false && u.status !== 'suspenso',
  };
}

// ─── USUÁRIOS (auth local / fallback) ────────────────────────
let USERS = [
  { id:1, email:'admin@infrasmart.com',  senha:'admin123', nome:'Carlos Administrador', cargo:'Gerente de Planta',  role:'admin',   status:'ativo',   id_tecnico:null, createdAt:'2024-01-10' },
  { id:2, email:'user@infrasmart.com',   senha:'user123',  nome:'Ana Operadora',        cargo:'Operadora de Campo', role:'user',    status:'ativo',   id_tecnico:null, createdAt:'2024-02-15' },
  { id:3, email:'carlos@infrasmart.com', senha:'carlos123',nome:'Carlos Mendes',        cargo:'Técnico Mecânico',   role:'tecnico', status:'ativo',   id_tecnico:1,    createdAt:'2024-03-01' },
  { id:4, email:'novo@infrasmart.com',   senha:'novo123',  nome:'Pedro Novo',           cargo:'',                   role:'user',    status:'pendente',id_tecnico:null, createdAt:'2026-03-25' },
];
let nextUserId = 5;

// ─── BANCO DE DADOS (cache + fallback offline) ─────────────────
let DB = {
  equipamentos: [
    { id_equipamento:1, nome:'Compressor Atlas CA-200', tipo:'Compressor',   fabricante:'Atlas Copco',    modelo:'CA-200', numero_serie:'SN-10021', status:'operacional', localizacao:{setor:'Setor A'}, qtd_sensores:3 },
    { id_equipamento:2, nome:'Bomba Centrífuga BC-50',  tipo:'Bomba',        fabricante:'Grundfos',       modelo:'BC-50',  numero_serie:'SN-10022', status:'alerta',      localizacao:{setor:'Setor B'}, qtd_sensores:2 },
    { id_equipamento:3, nome:'Gerador GE-500',          tipo:'Gerador',      fabricante:'Cummins',        modelo:'GE-500', numero_serie:'SN-10023', status:'operacional', localizacao:{setor:'Setor C'}, qtd_sensores:4 },
    { id_equipamento:4, nome:'Painel Solar PS-100',     tipo:'Painel Solar', fabricante:'SolarEdge',      modelo:'PS-100', numero_serie:'SN-10024', status:'manutencao',  localizacao:{setor:'Telhado'}, qtd_sensores:2 },
    { id_equipamento:5, nome:'Motor Elétrico ME-75',    tipo:'Motor',        fabricante:'WEG',            modelo:'ME-75',  numero_serie:'SN-10025', status:'operacional', localizacao:{setor:'Setor A'}, qtd_sensores:3 },
    { id_equipamento:6, nome:'Turbina Eólica TE-300',   tipo:'Turbina',      fabricante:'Siemens Gamesa', modelo:'TE-300', numero_serie:'SN-10026', status:'inativo',     localizacao:{setor:'Campo'},   qtd_sensores:2 },
  ],
  sensores: [
    { id_sensor:1, tipo_sensor:'Temperatura', unidade_medida:'°C',   id_equipamento:1 },
    { id_sensor:2, tipo_sensor:'Pressão',     unidade_medida:'bar',  id_equipamento:1 },
    { id_sensor:3, tipo_sensor:'Vibração',    unidade_medida:'mm/s', id_equipamento:2 },
    { id_sensor:4, tipo_sensor:'Temperatura', unidade_medida:'°C',   id_equipamento:3 },
    { id_sensor:5, tipo_sensor:'Corrente',    unidade_medida:'A',    id_equipamento:5 },
    { id_sensor:6, tipo_sensor:'Potência',    unidade_medida:'kW',   id_equipamento:3 },
  ],
  alertas: [
    { id_alerta:1, tipo_alerta:'Temperatura Alta',      nivel:'critico', descricao:'Temperatura acima do limite operacional em 15°C', id_equipamento:2, data_alerta:new Date(Date.now()-3600000).toISOString(),  status:'aberto',   tecnico_resolveu:null, id_tecnico_resolveu:null, equipamento:{nome:'Bomba Centrífuga BC-50'} },
    { id_alerta:2, tipo_alerta:'Vibração Excessiva',    nivel:'alto',    descricao:'Nível de vibração 2x acima do normal',             id_equipamento:2, data_alerta:new Date(Date.now()-7200000).toISOString(),  status:'aberto',   tecnico_resolveu:null, id_tecnico_resolveu:null, equipamento:{nome:'Bomba Centrífuga BC-50'} },
    { id_alerta:3, tipo_alerta:'Manutenção Preventiva', nivel:'medio',   descricao:'Intervalo de manutenção atingido (500h)',           id_equipamento:1, data_alerta:new Date(Date.now()-86400000).toISOString(), status:'resolvido',tecnico_resolveu:'Carlos Mendes', id_tecnico_resolveu:1, equipamento:{nome:'Compressor Atlas CA-200'} },
  ],
  manutencao: [
    { id_manutencao:1, tipo:'preventiva', descricao:'Troca de filtros e lubrificação geral',  data_programada:'2026-04-10', id_equipamento:1, status:'agendada',     equipamento:{nome:'Compressor Atlas CA-200'} },
    { id_manutencao:2, tipo:'corretiva',  descricao:'Substituição do selo mecânico',          data_programada:'2026-03-28', id_equipamento:2, status:'em_andamento', equipamento:{nome:'Bomba Centrífuga BC-50'} },
    { id_manutencao:3, tipo:'preditiva',  descricao:'Análise de vibração e balanceamento',    data_programada:'2026-04-20', id_equipamento:3, status:'agendada',     equipamento:{nome:'Gerador GE-500'} },
  ],
  tecnicos: [
    { id_tecnico:1, nome:'Carlos Mendes',  especialidade:'Mecânica Industrial',  telefone:'(19) 99812-3456', email:'carlos@infrasmart.com', area:'Mecânica',  ativo:true  },
    { id_tecnico:2, nome:'Ana Ribeiro',    especialidade:'Elétrica Industrial',  telefone:'(19) 99823-4567', email:'ana@infrasmart.com',    area:'Elétrica',  ativo:true  },
    { id_tecnico:3, nome:'Lucas Oliveira', especialidade:'Automação e Controle', telefone:'(19) 99834-5678', email:'lucas@infrasmart.com',  area:'Automação', ativo:true  },
    { id_tecnico:4, nome:'Fernanda Costa', especialidade:'Hidráulica Industrial',telefone:'(19) 99845-6789', email:'fern@infrasmart.com',   area:'Hidráulica',ativo:false },
  ],
  ordens: [
    { id_ordem_servico:1, numero_os:'OS-2026-001', descricao:'Substituição de selo mecânico da bomba BC-50',  prioridade:'alta',  status:'em_andamento', data_abertura:'2026-03-20', id_tecnico:1, id_manutencao:2, tecnico:{nome:'Carlos Mendes'} },
    { id_ordem_servico:2, numero_os:'OS-2026-002', descricao:'Manutenção preventiva compressor CA-200',       prioridade:'media', status:'aberta',       data_abertura:'2026-03-22', id_tecnico:2, id_manutencao:1, tecnico:{nome:'Ana Ribeiro'} },
    { id_ordem_servico:3, numero_os:'OS-2025-045', descricao:'Revisão sistema elétrico gerador GE-500',       prioridade:'baixa', status:'concluida',    data_abertura:'2025-12-10', id_tecnico:3, id_manutencao:3, tecnico:{nome:'Lucas Oliveira'} },
    { id_ordem_servico:4, numero_os:'OS-2025-044', descricao:'Troca de correias do motor ME-75',              prioridade:'media', status:'concluida',    data_abertura:'2025-11-05', id_tecnico:1, id_manutencao:1, tecnico:{nome:'Carlos Mendes'} },
    { id_ordem_servico:5, numero_os:'OS-2025-040', descricao:'Manutenção preventiva painel elétrico',         prioridade:'baixa', status:'concluida',    data_abertura:'2025-10-15', id_tecnico:2, id_manutencao:1, tecnico:{nome:'Ana Ribeiro'} },
  ],
  historico: [
    { id_historico:1, id_ordem_servico:3, id_tecnico:3, descricao_servico:'Revisão completa sistema elétrico, substituição de fusíveis e ajuste de tensão', data_execucao:'2025-12-15', custo:1850.00, ordem_servico:{numero_os:'OS-2025-045'}, tecnico:{nome:'Lucas Oliveira'} },
    { id_historico:2, id_ordem_servico:1, id_tecnico:1, descricao_servico:'Desmontagem parcial para avaliação do selo mecânico',                             data_execucao:'2026-03-21', custo:320.00,  ordem_servico:{numero_os:'OS-2026-001'}, tecnico:{nome:'Carlos Mendes'} },
    { id_historico:3, id_ordem_servico:4, id_tecnico:1, descricao_servico:'Substituição de 3 correias e alinhamento completo do motor',                      data_execucao:'2025-11-10', custo:890.00,  ordem_servico:{numero_os:'OS-2025-044'}, tecnico:{nome:'Carlos Mendes'} },
    { id_historico:4, id_ordem_servico:5, id_tecnico:2, descricao_servico:'Limpeza, inspeção e substituição de disjuntores do painel elétrico',              data_execucao:'2025-10-20', custo:640.00,  ordem_servico:{numero_os:'OS-2025-040'}, tecnico:{nome:'Ana Ribeiro'} },
  ],
  leituras: [],
  kpis: null,
  logs: [
    { id_log:1, acao:'Sistema inicializado',        usuario:'Sistema', nivel:'info',    data_hora:new Date(Date.now()-86400000).toISOString() },
    { id_log:2, acao:'Alerta crítico: Temp. Alta',  usuario:'Admin',   nivel:'warning', data_hora:new Date(Date.now()-3600000).toISOString() },
    { id_log:3, acao:'OS-2026-002 criada',          usuario:'Admin',   nivel:'info',    data_hora:new Date(Date.now()-86400000).toISOString() },
  ],
  notificacoes: [
    { id:1, texto:'Alerta crítico: Temperatura Alta na Bomba BC-50', icone:'🚨', lida:false, hora:new Date(Date.now()-3600000).toISOString() },
    { id:2, texto:'Manutenção agendada para 28/03 — Bomba BC-50',   icone:'🔧', lida:false, hora:new Date(Date.now()-7200000).toISOString() },
    { id:3, texto:'Novo usuário aguarda aprovação: Pedro Novo',      icone:'👤', lida:false, hora:new Date(Date.now()-600000).toISOString() },
  ],
};

// ─── ESTADO ───────────────────────────────────────────────────
let currentUser  = null;
let charts       = {};
let nextIds      = { alerta:4, equipamento:7, manutencao:4, ordem:6, historico:5, tecnico:5, log:4 };
let activeFilters = {};
let clockInterval = null;
let tecView       = 'grid';

// ════════════════════════════════════════════════════════════
// UTILITÁRIOS
// ════════════════════════════════════════════════════════════
const fmtDate     = d => d ? new Date(d).toLocaleDateString('pt-BR')  : '—';
const fmtDateTime = d => d ? new Date(d).toLocaleString('pt-BR')      : '—';
const fmtCurrency = v => `R$ ${parseFloat(v||0).toFixed(2).replace('.',',')}`;

function timeAgo(d) {
  const s = (Date.now() - new Date(d)) / 1000;
  if (s < 60)    return 'agora';
  if (s < 3600)  return `${Math.floor(s/60)}min atrás`;
  if (s < 86400) return `${Math.floor(s/3600)}h atrás`;
  return fmtDate(d);
}

function genTelemetria(horas=24, base=70, variance=10) {
  return Array.from({length:horas}, (_,i) => ({
    data_hora: new Date(Date.now() - (horas-i)*3600000).toISOString(),
    valor: +(base + (Math.random()-.5)*variance*2).toFixed(1)
  }));
}

const BADGE_MAP = {
  operacional:'badge-green', manutencao:'badge-orange', alerta:'badge-red', inativo:'badge-gray',
  aberto:'badge-red', resolvido:'badge-green', agendada:'badge-blue', em_andamento:'badge-orange',
  concluida:'badge-green', aberta:'badge-red', preventiva:'badge-blue', corretiva:'badge-red',
  preditiva:'badge-yellow', critica:'badge-red', alta:'badge-red', media:'badge-orange',
  baixa:'badge-blue', critico:'badge-red', alto:'badge-orange', medio:'badge-yellow',
  admin:'badge-orange', tecnico:'badge-green', user:'badge-blue', viewer:'badge-gray',
  ativo:'badge-green', pendente:'badge-yellow', suspenso:'badge-red',
};
const BADGE_LABEL = {
  operacional:'Operacional', manutencao:'Manutenção', alerta:'Alerta', inativo:'Inativo',
  aberto:'Aberto', resolvido:'Resolvido', agendada:'Agendada', em_andamento:'Em Andamento',
  concluida:'Concluída', aberta:'Aberta', preventiva:'Preventiva', corretiva:'Corretiva',
  preditiva:'Preditiva', critica:'Crítica', alta:'Alta', media:'Média', baixa:'Baixa',
  critico:'Crítico', alto:'Alto', medio:'Médio',
  admin:'Admin', tecnico:'Técnico', user:'Usuário', viewer:'Visualizador',
  ativo:'Ativo', pendente:'Pendente', suspenso:'Suspenso',
};

function statusBadge(s) {
  return `<span class="badge ${BADGE_MAP[s]||'badge-gray'}">${BADGE_LABEL[s]||s}</span>`;
}
function roleBadge(r) {
  const icons = { admin:'👑', user:'👤', tecnico:'🔧', viewer:'👁️' };
  return `<span class="badge ${BADGE_MAP[r]||'badge-gray'}">${icons[r]||''} ${BADGE_LABEL[r]||r}</span>`;
}

// ─── TOAST ────────────────────────────────────────────────────
function toast(msg, type='success', dur=3500) {
  const icons = { success:'✅', error:'❌', warning:'⚠️', info:'ℹ️' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span class="toast-icon">${icons[type]}</span><span class="toast-msg">${msg}</span>`;
  document.getElementById('toast-container').appendChild(t);
  setTimeout(()=>{ t.style.animation='toastIn .3s ease reverse'; setTimeout(()=>t.remove(),280); }, dur);
}

// ─── LOG ──────────────────────────────────────────────────────
function addLog(acao, nivel='info') {
  DB.logs.unshift({
    id_log: nextIds.log++, acao,
    usuario: currentUser?.nome?.split(' ')[0] || 'Sistema',
    nivel, data_hora: new Date().toISOString()
  });
}

// ════════════════════════════════════════════════════════════
// LOGIN / CADASTRO
// ════════════════════════════════════════════════════════════
function switchTab(tab) {
  document.getElementById('tab-login').classList.toggle('active', tab==='login');
  document.getElementById('tab-register').classList.toggle('active', tab==='register');
  document.getElementById('panel-login').classList.toggle('active', tab==='login');
  document.getElementById('panel-register').classList.toggle('active', tab==='register');
  clearLoginErrors();
}

function togglePw(inputId, iconId) {
  const inp = document.getElementById(inputId);
  const ico = document.getElementById(iconId);
  if (inp.type==='password') { inp.type='text'; ico.textContent='🙈'; }
  else { inp.type='password'; ico.textContent='👁️'; }
}

function checkPwStrength() {
  const pw = document.getElementById('reg-senha').value;
  const bars = [document.getElementById('bar1'), document.getElementById('bar2'), document.getElementById('bar3')];
  const label = document.getElementById('pw-strength-label');
  bars.forEach(b=>{ b.className='pw-strength-bar'; });
  if (!pw) { label.textContent='—'; return; }
  let score = 0;
  if (pw.length >= 6)  score++;
  if (pw.length >= 10) score++;
  if (/[A-Z]/.test(pw) && /[0-9]/.test(pw)) score++;
  const lvl = ['weak','medium','strong'];
  const lbl = ['Fraca','Média','Forte'];
  for (let i=0; i<score; i++) bars[i].classList.add(lvl[score-1]);
  label.textContent = lbl[score-1] || 'Fraca';
  label.style.color = score===3 ? 'var(--green-500)' : score===2 ? 'var(--yellow-500)' : 'var(--red-400)';
}

function showAuthError(panelPrefix, msg) {
  const el = document.getElementById(panelPrefix+'-error');
  document.getElementById(panelPrefix+'-error-msg').textContent = msg;
  el.style.display = 'flex';
}

function clearLoginErrors() {
  ['login-error','register-error','register-success'].forEach(id=>{
    const el=document.getElementById(id); if(el) el.style.display='none';
  });
  document.querySelectorAll('.form-input').forEach(i=>i.classList.remove('error'));
}

async function doLogin() {
  clearLoginErrors();
  const email = document.getElementById('login-email').value.trim();
  const senha  = document.getElementById('login-senha').value;
  if (!email) { showAuthError('login','Informe seu e-mail.'); document.getElementById('login-email').classList.add('error'); return; }
  if (!senha)  { showAuthError('login','Informe sua senha.');  document.getElementById('login-senha').classList.add('error'); return; }

  const btn = document.getElementById('btn-login');
  const txt = document.getElementById('login-btn-text');
  btn.disabled = true;
  txt.innerHTML = '<span class="spinner"></span> Autenticando...';

  // ── Tenta autenticar na API ──────────────────────────────
  const apiRes = await apiCall('POST', '/accounts/login/', { username: email, password: senha }, true);

  if (apiRes && apiRes.token && !apiRes.error) {
    // ✅ Login via API
    AUTH_TOKEN = apiRes.token;
    sessionStorage.setItem('auth_token', AUTH_TOKEN);
    API_ONLINE = true;

    // Busca dados do usuário logado
    const me = await apiCall('GET', '/accounts/me/');
    currentUser = me ? normalizeUsuario(me) : {
      id: apiRes.user_id || 1, email, nome: email.split('@')[0],
      cargo: '', role: 'user', status: 'ativo', id_tecnico: null,
    };

    // Adiciona password dummy para compatibilidade
    currentUser.senha = '';

    btn.disabled = false; txt.textContent = 'Acessar o sistema';
    addLog(`Login via API: ${currentUser.nome}`);
    sessionStorage.setItem('is_session', JSON.stringify({ id: currentUser.id, email: currentUser.email, token: AUTH_TOKEN }));
    initApp();
    return;
  }

  // ── Fallback: login local (modo demo) ────────────────────
  await new Promise(r=>setTimeout(r,500));
  const user = USERS.find(u => u.email===email && u.senha===senha);
  btn.disabled = false; txt.textContent = 'Acessar o sistema';

  if (!user) {
    const exists = USERS.find(u=>u.email===email);
    showAuthError('login', exists ? 'Senha incorreta. Tente novamente.' : 'E-mail não encontrado.');
    document.getElementById('login-senha').classList.add('error');
    return;
  }
  if (user.status === 'pendente')  { showAuthError('login','Sua conta aguarda aprovação de um administrador.'); return; }
  if (user.status === 'suspenso')  { showAuthError('login','Conta suspensa. Contate o administrador.'); return; }

  API_ONLINE  = false;
  currentUser = user;
  addLog(`Login (demo): ${user.nome}`);
  sessionStorage.setItem('is_session', JSON.stringify({ id: user.id, email: user.email }));
  initApp();
}

async function doRegister() {
  clearLoginErrors();
  const nome      = document.getElementById('reg-nome').value.trim();
  const sobrenome = document.getElementById('reg-sobrenome').value.trim();
  const email     = document.getElementById('reg-email').value.trim();
  const senha     = document.getElementById('reg-senha').value;
  const confirm   = document.getElementById('reg-confirm').value;

  if (!nome)    { showAuthError('register','Informe seu nome.');    return; }
  if (!email)   { showAuthError('register','Informe o e-mail.');    return; }
  if (!senha)   { showAuthError('register','Informe uma senha.');   return; }
  if (senha.length < 6) { showAuthError('register','Senha muito curta (mín. 6 caracteres).'); return; }
  if (senha !== confirm) { showAuthError('register','As senhas não coincidem.'); return; }

  const btn = document.getElementById('btn-register');
  const txt = document.getElementById('register-btn-text');
  btn.disabled = true; txt.innerHTML = '<span class="spinner"></span> Criando conta...';

  // ── Tenta cadastro via API ────────────────────────────────
  const apiRes = await apiCall('POST', '/accounts/register/', {
    username   : email,
    email,
    password   : senha,
    first_name : nome,
    last_name  : sobrenome,
  }, true);

  btn.disabled = false; txt.textContent = 'Criar Conta';

  if (apiRes && !apiRes.error) {
    document.getElementById('register-error').style.display   = 'none';
    document.getElementById('register-success').style.display = 'flex';
    addLog(`Cadastro via API: ${nome} ${sobrenome}`);
    setTimeout(()=>switchTab('login'), 2000);
    return;
  }

  // ── Fallback local ────────────────────────────────────────
  if (USERS.find(u=>u.email===email)) { showAuthError('register','Este e-mail já está cadastrado.'); return; }

  const newUser = {
    id: nextUserId++, email, senha,
    nome: `${nome} ${sobrenome}`.trim(),
    cargo: '', role: 'user', status: 'pendente',
    id_tecnico: null, createdAt: new Date().toISOString().split('T')[0]
  };
  USERS.push(newUser);
  DB.notificacoes.unshift({ id:Date.now(), texto:`Novo cadastro aguarda aprovação: ${newUser.nome}`, icone:'👤', lida:false, hora:new Date().toISOString() });

  document.getElementById('register-error').style.display   = 'none';
  document.getElementById('register-success').style.display = 'flex';
  setTimeout(()=>switchTab('login'), 2000);
}

async function doLogout() {
  addLog(`Logout: ${currentUser?.nome}`);
  if (AUTH_TOKEN) {
    await apiCall('POST', '/accounts/logout/', {}, true);
    AUTH_TOKEN = null;
    sessionStorage.removeItem('auth_token');
  }
  currentUser = null;
  API_ONLINE  = false;
  sessionStorage.removeItem('is_session');
  if (clockInterval) { clearInterval(clockInterval); clockInterval=null; }
  document.getElementById('app').classList.remove('visible');
  document.getElementById('app').style.display = 'none';
  document.getElementById('login-screen').style.display = 'flex';
  document.getElementById('login-email').value = '';
  document.getElementById('login-senha').value = '';
  clearLoginErrors();
  switchTab('login');
}

async function restoreSession() {
  const s = sessionStorage.getItem('is_session');
  if (!s) return;
  try {
    const saved = JSON.parse(s);

    if (saved.token) {
      AUTH_TOKEN = saved.token;
      const me = await apiCall('GET', '/accounts/me/', null, true);
      if (me && !me.error) {
        API_ONLINE  = true;
        currentUser = normalizeUsuario(me);
        currentUser.senha = '';
        initApp();
        return;
      }
    }

    // Fallback local
    const user = USERS.find(u=>u.id===saved.id && u.email===saved.email && u.status==='ativo');
    if (user) { currentUser=user; initApp(); }
    else sessionStorage.removeItem('is_session');
  } catch { sessionStorage.removeItem('is_session'); }
}

// ════════════════════════════════════════════════════════════
// INIT APP
// ════════════════════════════════════════════════════════════
function initApp() {
  document.getElementById('login-screen').style.display = 'none';
  const app = document.getElementById('app');
  app.style.display = 'flex'; app.classList.add('visible');

  document.getElementById('user-name').textContent     = currentUser.nome;
  document.getElementById('user-avatar').textContent   = currentUser.nome[0];
  document.getElementById('topbar-avatar').textContent = currentUser.nome[0];
  document.getElementById('topbar-name').textContent   = currentUser.nome.split(' ')[0];

  const badge = document.getElementById('user-role-badge');
  badge.textContent = BADGE_LABEL[currentUser.role] || currentUser.role;
  badge.className   = `user-role-badge ${currentUser.role}`;

  applyRoleRestrictions();
  updateApiStatus();
  startClock();
  loadNotificacoes();
  loadDashboard();
  startAlertPolling();
}

// ════════════════════════════════════════════════════════════
// RBAC
// ════════════════════════════════════════════════════════════
const ADMIN_PAGES   = ['logs','usuarios'];
const VIEWER_DENIED = ['modal-equipamento','modal-alerta','modal-manutencao','modal-os','modal-tecnico','modal-historico'];

function isAdmin()  { return currentUser?.role === 'admin'; }
function isViewer() { return currentUser?.role === 'viewer'; }
function canWrite() { return !isViewer(); }

function applyRoleRestrictions() {
  if (isAdmin()) {
    document.querySelectorAll('.admin-only').forEach(el=>{ el.style.display=''; el.classList.remove('locked'); });
    document.querySelectorAll('.admin-action').forEach(el=>{ el.style.display=''; el.disabled=false; });
  } else {
    document.querySelectorAll('.admin-action').forEach(el=>el.style.display='none');
    document.querySelectorAll('.admin-only').forEach(el=>{
      if (el.classList.contains('nav-item')) el.classList.add('locked');
      else el.style.display='none';
    });
  }
}

function checkPageAccess(page) {
  if (ADMIN_PAGES.includes(page) && !isAdmin()) {
    toast('Apenas administradores podem acessar esta área.','warning');
    return false;
  }
  return true;
}

// ════════════════════════════════════════════════════════════
// NAVEGAÇÃO
// ════════════════════════════════════════════════════════════
const PAGE_NAMES = {
  dashboard:'Dashboard', equipamentos:'Equipamentos', sensores:'Sensores & Telemetria',
  alertas:'Central de Alertas', manutencao:'Gestão de Manutenção',
  ordens:'Ordens de Serviço', historico:'Histórico', tecnicos:'Equipe Técnica',
  usuarios:'Gerenciar Usuários', logs:'Logs do Sistema'
};
const PAGE_LOADERS = {
  dashboard:loadDashboard, equipamentos:loadEquipamentos, sensores:loadSensores,
  alertas:loadAlertas, manutencao:loadManutencao, ordens:loadOrdens,
  historico:loadHistorico, tecnicos:loadTecnicos, usuarios:loadUsuarios, logs:loadLogs
};

function goTo(page) {
  if (!checkPageAccess(page)) return;
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  document.getElementById('page-'+page).classList.add('active');
  document.querySelector(`.nav-item[data-page="${page}"]`)?.classList.add('active');
  document.getElementById('page-title').textContent = PAGE_NAMES[page];
  if (PAGE_LOADERS[page]) PAGE_LOADERS[page]();
}

// ─── MODAIS ───────────────────────────────────────────────────
function openModal(id) {
  if (isViewer() && VIEWER_DENIED.includes(id)) {
    toast('Modo visualizador: sem permissão para criar ou editar.','warning'); return;
  }
  if (!isAdmin() && ['modal-edit-user'].includes(id)) {
    toast('Apenas administradores podem gerenciar usuários.','warning'); return;
  }
  document.getElementById(id).classList.add('open');
}
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

// ─── RELÓGIO ─────────────────────────────────────────────────
function startClock() {
  const el = document.getElementById('clock');
  el.textContent = new Date().toLocaleTimeString('pt-BR');
  clockInterval = setInterval(()=>{ el.textContent = new Date().toLocaleTimeString('pt-BR'); },1000);
}

// ════════════════════════════════════════════════════════════
// FILTROS GENÉRICOS
// ════════════════════════════════════════════════════════════
function filterChip(el, group) {
  document.querySelectorAll(`[data-filter="${group}"]`).forEach(c=>c.classList.remove('active'));
  el.classList.add('active');
  activeFilters[group] = el.dataset.value;
  const map = {
    'eq-status':filterEquipamentos,
    'al-status':renderAlertas, 'al-nivel':renderAlertas,
    'mn-tipo':renderManutencao, 'mn-status':renderManutencao,
    'os-status':renderOrdens, 'os-prior':renderOrdens,
    'tc-status':renderTecnicos,
  };
  if (map[group]) map[group]();
}
const getFilter = key => activeFilters[key] || '';

// ════════════════════════════════════════════════════════════
// NOTIFICAÇÕES
// ════════════════════════════════════════════════════════════
function loadNotificacoes() {
  const unread = DB.notificacoes.filter(n=>!n.lida).length;
  const el = document.getElementById('notif-count');
  el.textContent = unread; el.style.display = unread>0 ? 'flex' : 'none';
  document.getElementById('notif-list').innerHTML = DB.notificacoes.map(n=>`
    <div class="notif-item ${n.lida?'':'unread'}" onclick="markNotifRead(${n.id})">
      <div class="notif-icon">${n.icone}</div>
      <div><div class="notif-text">${n.texto}</div><div class="notif-time">${timeAgo(n.hora)}</div></div>
    </div>
  `).join('') || '<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:.83rem">Nenhuma notificação</div>';
}
function markNotifRead(id) { DB.notificacoes = DB.notificacoes.map(n=>n.id===id?{...n,lida:true}:n); loadNotificacoes(); }
function markAllRead()     { DB.notificacoes = DB.notificacoes.map(n=>({...n,lida:true})); loadNotificacoes(); toast('Notificações marcadas como lidas','info'); }
function toggleNotifPanel() { document.getElementById('notif-panel').classList.toggle('open'); }

document.addEventListener('click', e=>{
  const p=document.getElementById('notif-panel');
  if (p?.classList.contains('open') && !p.contains(e.target) && !e.target.closest('.topbar-notif')) p.classList.remove('open');
});

// ════════════════════════════════════════════════════════════
// DASHBOARD
// ════════════════════════════════════════════════════════════
async function loadDashboard() {
  // Busca KPIs da API
  if (API_ONLINE) {
    const kpiData = await apiCall('GET', '/dashboards/kpis/');
    if (kpiData && !kpiData.error) DB.kpis = kpiData;

    const alertasData = await apiCall('GET', '/alertas/');
    const alertasList = extractList(alertasData);
    if (alertasList) DB.alertas = alertasList.map(normalizeAlerta);

    const ativosData = await apiCall('GET', '/ativos/');
    const ativosList = extractList(ativosData);
    if (ativosList) DB.equipamentos = ativosList.map(normalizeAtivo);
  }

  renderDashboard();
}

function renderDashboard() {
  const total   = DB.equipamentos.length;
  const oper    = DB.equipamentos.filter(e=>e.status==='operacional').length;
  const alertas = DB.alertas.filter(a=>a.status==='aberto').length;
  const os      = DB.ordens.filter(o=>o.status!=='concluida').length;
  const disp    = total ? (oper/total*100).toFixed(1) : '0.0';

  // KPIs da API ou calculados localmente
  const kpis = DB.kpis;
  const mtbf = kpis?.mtbf_hours  ?? kpis?.[0]?.mtbf_hours  ?? 342;
  const mttr = kpis?.mttr_hours  ?? kpis?.[0]?.mttr_hours  ?? 4.2;
  const disp_api = kpis?.disponibilidade ?? kpis?.[0]?.disponibilidade ?? parseFloat(disp);

  document.getElementById('kpi-grid').innerHTML = `
    <div class="kpi blue">
      <div class="kpi-header"><div class="kpi-icon">⚙️</div><span class="kpi-trend up">+2%</span></div>
      <div class="kpi-value">${oper}</div><div class="kpi-label">Equipamentos Operacionais</div>
      <div class="kpi-sub">de ${total} ativos ${API_ONLINE?'<span style="font-size:.65rem;color:var(--green-500)">● API</span>':''}</div>
      <div class="progress-bar"><div class="progress-fill" style="width:${(oper/(total||1)*100).toFixed(0)}%"></div></div>
    </div>
    <div class="kpi orange">
      <div class="kpi-header"><div class="kpi-icon">🔔</div><span class="kpi-trend ${alertas>0?'down':'up'}">${alertas>0?'Atenção':'Ok'}</span></div>
      <div class="kpi-value">${alertas}</div><div class="kpi-label">Alertas Ativos</div>
      <div class="kpi-sub">requerem atenção</div>
    </div>
    <div class="kpi ${os>0?'orange':'green'}">
      <div class="kpi-header"><div class="kpi-icon">📋</div><span class="kpi-trend ${os>2?'down':'up'}">${os} abertas</span></div>
      <div class="kpi-value">${os}</div><div class="kpi-label">OS em Aberto</div>
      <div class="kpi-sub">ordens de serviço</div>
    </div>
    <div class="kpi green">
      <div class="kpi-header"><div class="kpi-icon">📊</div><span class="kpi-trend up">OEE</span></div>
      <div class="kpi-value">${disp_api}%</div><div class="kpi-label">Disponibilidade</div>
      <div class="kpi-sub">indicador consolidado</div>
      <div class="progress-bar"><div class="progress-fill" style="width:${Math.min(100,disp_api)}%"></div></div>
    </div>
  `;

  document.getElementById('alert-badge').textContent = alertas;

  document.getElementById('dash-alertas').innerHTML = DB.alertas.slice(0,5).map(a=>`
    <div class="alert-item">
      <div class="alert-dot ${a.nivel}"></div>
      <div style="flex:1;min-width:0">
        <div class="alert-title">${a.tipo_alerta}</div>
        <div class="alert-desc">${a.descricao}</div>
        ${a.tecnico_resolveu?`<div class="alert-meta">✅ ${a.tecnico_resolveu}</div>`:''}
        <div class="alert-time">${timeAgo(a.data_alerta)}</div>
      </div>
      ${statusBadge(a.status)}
    </div>
  `).join('') || '<div class="empty-state"><div class="empty-state-icon">✅</div><div class="empty-state-text">Sem alertas</div></div>';

  document.getElementById('dash-kpis').innerHTML = [
    {label:'Disponibilidade', valor:parseFloat(disp_api),  color:'var(--blue-600)',   suffix:'%', max:100},
    {label:'MTBF (horas)',    valor:parseFloat(mtbf),       color:'var(--orange-600)', suffix:'',  max:500},
    {label:'MTTR (horas)',    valor:parseFloat(mttr),       color:'var(--green-600)',  suffix:'',  max:20 },
    {label:'OEE',             valor:78.5,                   color:'var(--purple-500)', suffix:'%', max:100},
  ].map(i=>`
    <div class="gauge-row">
      <div class="gauge-label">${i.label}</div>
      <div class="gauge-bar"><div class="gauge-bar-fill" style="width:${Math.min(100,i.valor/i.max*100)}%;background:${i.color}"></div></div>
      <div class="gauge-value" style="color:${i.color}">${i.valor}${i.suffix}</div>
    </div>
  `).join('');

  buildDashCharts();
}

async function buildDashCharts() {
  let tempData = null;

  if (API_ONLINE) {
    // Tenta buscar leituras reais de telemetria (sensor de temperatura)
    const leiturasData = await apiCall('GET', '/telemetria/leituras/?ordering=-data_leitura&limit=24', null, true);
    const leiturasList = extractList(leiturasData);
    if (leiturasList && leiturasList.length > 0) {
      tempData = leiturasList.reverse().map(l => ({
        data_hora: l.data_leitura || l.data_hora,
        valor: parseFloat(l.valor)
      }));
    }
  }

  const t = tempData || genTelemetria(24,72,8);
  const e = genTelemetria(24,180,40);

  buildChart('chart-temp','line', t.map(x=>new Date(x.data_hora).getHours()+'h'),
    [{label:'Temperatura (°C)', data:t.map(x=>x.valor), borderColor:'#ea580c', backgroundColor:'rgba(234,88,12,.08)', fill:true, tension:.4, pointRadius:2}]);
  buildChart('chart-energy','bar', e.map(x=>new Date(x.data_hora).getHours()+'h'),
    [{label:'Potência (kW)', data:e.map(x=>x.valor), backgroundColor:'rgba(37,99,235,.12)', borderColor:'#2563eb', borderWidth:1.5, borderRadius:3}]);
}

function buildChart(id, type, labels, datasets) {
  if (charts[id]) charts[id].destroy();
  const ctx = document.getElementById(id); if (!ctx) return;
  charts[id] = new Chart(ctx, {
    type, data:{labels,datasets},
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{legend:{labels:{color:'#6b7280',font:{size:11,family:"'Instrument Sans',sans-serif"}}}},
      scales:{
        x:{ticks:{color:'#94a3b8',font:{size:10}},grid:{color:'rgba(0,0,0,.03)'}},
        y:{ticks:{color:'#94a3b8',font:{size:10}},grid:{color:'rgba(0,0,0,.03)'}}
      }
    }
  });
}

// ════════════════════════════════════════════════════════════
// EQUIPAMENTOS / ATIVOS
// ════════════════════════════════════════════════════════════
async function loadEquipamentos() {
  if (API_ONLINE) {
    const data = await apiCall('GET', '/ativos/');
    const list = extractList(data);
    if (list) DB.equipamentos = list.map(normalizeAtivo);
  }
  renderEquipamentos();
}

function filterEquipamentos() { renderEquipamentos(); }

function renderEquipamentos() {
  const q      = (document.getElementById('eq-search')?.value||'').toLowerCase();
  const status = getFilter('eq-status');
  const setor  = document.getElementById('eq-setor-filter')?.value||'';
  const list   = DB.equipamentos.filter(e =>
    (!q || e.nome.toLowerCase().includes(q) || e.tipo.toLowerCase().includes(q) || e.fabricante.toLowerCase().includes(q)) &&
    (!status || e.status===status) && (!setor || e.localizacao?.setor===setor)
  );
  document.getElementById('eq-table').innerHTML = list.map(eq=>`
    <tr>
      <td><strong>${eq.nome}</strong></td>
      <td style="color:var(--text-secondary)">${eq.tipo}</td>
      <td>${eq.fabricante}</td>
      <td><code style="font-family:var(--font-mono);font-size:.78rem;color:var(--blue-700);background:var(--blue-50);padding:2px 6px;border-radius:4px">${eq.numero_serie}</code></td>
      <td><span style="font-size:.8rem;color:var(--text-muted)">${eq.localizacao?.setor||'—'}</span></td>
      <td>${statusBadge(eq.status)}</td>
      <td><span class="badge badge-blue">${eq.qtd_sensores} sensor${eq.qtd_sensores!==1?'es':''}</span></td>
      <td>
        ${isAdmin()?`
          <div style="display:flex;gap:6px">
            <button class="btn btn-ghost btn-sm" onclick="editEquipStatus(${eq.id_equipamento},'${eq.status}')">⚙️</button>
            <button class="btn btn-danger btn-sm" onclick="delEquip(${eq.id_equipamento})">🗑️</button>
          </div>
        `:'<span style="color:var(--text-muted);font-size:.78rem">—</span>'}
      </td>
    </tr>
  `).join('') || `<tr><td colspan="8"><div class="empty-state"><div class="empty-state-icon">⚙️</div><div class="empty-state-text">Nenhum equipamento</div></div></td></tr>`;
}

async function saveEquipamento() {
  const nome = document.getElementById('eq-nome').value.trim();
  if (!nome) { toast('Preencha o nome','error'); return; }

  const payload = {
    nome,
    tipo        : document.getElementById('eq-tipo').value,
    fabricante  : document.getElementById('eq-fabricante').value,
    modelo      : document.getElementById('eq-modelo').value,
    numero_serie: document.getElementById('eq-serie').value || `SN-${Date.now()}`,
    status      : document.getElementById('eq-status').value,
  };

  if (API_ONLINE) {
    const res = await apiCall('POST', '/ativos/', payload);
    if (!res || res.error) return;
    DB.equipamentos.push(normalizeAtivo(res));
  } else {
    DB.equipamentos.push({
      id_equipamento: nextIds.equipamento++, ...payload,
      localizacao: { setor: 'Geral' }, qtd_sensores: 0
    });
  }

  ['eq-nome','eq-fabricante','eq-modelo','eq-serie'].forEach(id=>document.getElementById(id).value='');
  closeModal('modal-equipamento');
  addLog(`Equipamento "${nome}" cadastrado`);
  toast('Equipamento cadastrado!');
  loadEquipamentos();
}

async function editEquipStatus(id, current) {
  const opts  = ['operacional','manutencao','alerta','inativo'];
  const next  = opts[(opts.indexOf(current)+1)%opts.length];

  if (API_ONLINE) {
    const res = await apiCall('PATCH', `/ativos/${id}/`, { status: next });
    if (!res || res.error) return;
  }

  DB.equipamentos = DB.equipamentos.map(e=>e.id_equipamento===id?{...e,status:next}:e);
  addLog(`Equipamento #${id} → ${next}`);
  toast(`Status → ${next}`);
  renderEquipamentos();
}

async function delEquip(id) {
  const eq = DB.equipamentos.find(e=>e.id_equipamento===id);
  if (!confirm(`Remover "${eq?.nome}"?`)) return;

  if (API_ONLINE) {
    const res = await apiCall('DELETE', `/ativos/${id}/`);
    if (res?.error) return;
  }

  DB.equipamentos = DB.equipamentos.filter(e=>e.id_equipamento!==id);
  addLog(`Equipamento "${eq?.nome}" removido`,'warning');
  toast('Removido');
  loadEquipamentos();
}

// ════════════════════════════════════════════════════════════
// SENSORES & TELEMETRIA
// ════════════════════════════════════════════════════════════
async function loadSensores() {
  if (API_ONLINE) {
    // Carrega sensores
    const sensData = await apiCall('GET', '/telemetria/sensores/');
    const sensList = extractList(sensData);
    if (sensList) DB.sensores = sensList.map(normalizeSensor);

    // Carrega equipamentos para o filtro
    const ativosData = await apiCall('GET', '/ativos/');
    const ativosList = extractList(ativosData);
    if (ativosList) DB.equipamentos = ativosList.map(normalizeAtivo);
  }

  const sel = document.getElementById('sensor-equip-filter');
  if (sel.children.length <= 1) {
    DB.equipamentos.forEach(e=>{
      const o=document.createElement('option');
      o.value=e.id_equipamento; o.textContent=e.nome;
      sel.appendChild(o);
    });
  }

  const fid  = sel.value ? parseInt(sel.value) : null;
  const list = fid ? DB.sensores.filter(s=>s.id_equipamento===fid) : DB.sensores;

  // Últimas leituras da API
  let ultimasLeituras = {};
  if (API_ONLINE) {
    const lData = await apiCall('GET', '/telemetria/leituras/?ordering=-data_leitura&limit=50', null, true);
    const lList = extractList(lData);
    if (lList) {
      lList.forEach(l=>{
        const sid = l.sensor?.id ?? l.sensor;
        if (!ultimasLeituras[sid]) ultimasLeituras[sid] = parseFloat(l.valor);
      });
    }
  }

  const vals = {'°C':'72.4','bar':'5.8','mm/s':'1.2','A':'42.1','kW':'185.3'};
  document.getElementById('sensor-cards').innerHTML = list.map(s=>{
    const eq = DB.equipamentos.find(e=>e.id_equipamento===s.id_equipamento);
    const v  = ultimasLeituras[s.id_sensor] !== undefined
      ? ultimasLeituras[s.id_sensor].toFixed(1)
      : (s.ultimo_valor !== null ? s.ultimo_valor : (vals[s.unidade_medida]||'—'));
    return `
      <div class="card" style="cursor:pointer" onclick="loadSensorChart(${s.id_sensor},'${s.tipo_sensor}')">
        <div class="card-body" style="padding:18px">
          <div style="font-size:.7rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px">${s.tipo_sensor}</div>
          <div style="font-family:var(--font-display);font-size:1.9rem;font-weight:800;color:var(--blue-600);letter-spacing:-0.04em">${v}<span style="font-size:.9rem;color:var(--text-muted);font-weight:400;margin-left:4px">${s.unidade_medida}</span></div>
          <div style="font-size:.8rem;color:var(--text-secondary);margin-top:8px">${eq?.nome||'—'}</div>
          ${s.limite_max?`<div style="font-size:.72rem;color:var(--orange-600);margin-top:4px">⚠️ Limite máx: ${s.limite_max} ${s.unidade_medida}</div>`:''}
          <div style="margin-top:12px;font-size:.75rem;color:var(--orange-600);font-weight:600">▶ Ver histórico</div>
        </div>
      </div>`;
  }).join('') || '<div class="empty-state" style="grid-column:1/-1"><div class="empty-state-icon">📡</div><div class="empty-state-text">Nenhum sensor</div></div>';
}

async function loadSensorChart(id, tipo) {
  let leituras = null;

  if (API_ONLINE) {
    const data = await apiCall('GET', `/telemetria/leituras/?sensor=${id}&ordering=data_leitura&limit=24`, null, true);
    const list = extractList(data);
    if (list && list.length > 0) {
      leituras = list.map(l => ({
        data_hora: l.data_leitura || l.data_hora,
        valor: parseFloat(l.valor),
      }));
    }
  }

  const s    = DB.sensores.find(x=>x.id_sensor===id);
  const bases= {'°C':72,'bar':6,'mm/s':1.2,'A':42,'kW':180};
  const base = s ? (bases[s.unidade_medida]||50) : 50;
  const tel  = leituras || genTelemetria(24,base,base*.1);

  buildChart('chart-sensor','line', tel.map(t=>new Date(t.data_hora).getHours()+'h'),
    [{label:tipo, data:tel.map(t=>t.valor), borderColor:'#2563eb', backgroundColor:'rgba(37,99,235,.08)', fill:true, tension:.4, pointRadius:2}]);
}

async function enviarLeitura(sensorId, valor) {
  if (!API_ONLINE) return null;
  const res = await apiCall('POST', '/telemetria/leituras/', { sensor: sensorId, valor: parseFloat(valor) });
  if (res && !res.error) {
    toast(`Leitura enviada: ${valor}`, 'success');
    // Verifica se gerou alertas novos
    setTimeout(() => loadAlertas(), 1000);
  }
  return res;
}

// ════════════════════════════════════════════════════════════
// ALERTAS
// ════════════════════════════════════════════════════════════
async function loadAlertas() {
  if (API_ONLINE) {
    const data = await apiCall('GET', '/alertas/');
    const list = extractList(data);
    if (list) {
      DB.alertas = list.map(normalizeAlerta);
      // Atualiza badge
      const abertos = DB.alertas.filter(a=>a.status==='aberto').length;
      document.getElementById('alert-badge').textContent = abertos;
    }
  }
  document.getElementById('al-equip').innerHTML = DB.equipamentos.map(e=>`<option value="${e.id_equipamento}">${e.nome}</option>`).join('');
  renderAlertas();
}

function renderAlertas() {
  const sf  = getFilter('al-status');
  const nf  = getFilter('al-nivel');
  const ord = document.getElementById('al-ordem')?.value||'recente';
  let list  = DB.alertas.filter(a=>(!sf||a.status===sf)&&(!nf||a.nivel===nf))
    .sort((a,b)=>{ const da=new Date(a.data_alerta),db=new Date(b.data_alerta); return ord==='recente'?db-da:da-db; });
  document.getElementById('alertas-table').innerHTML = list.map(a=>`
    <tr>
      <td>${statusBadge(a.nivel)}</td>
      <td><strong>${a.tipo_alerta}</strong></td>
      <td style="max-width:200px;font-size:.82rem;color:var(--text-secondary)">${a.descricao}</td>
      <td style="font-size:.82rem">${a.equipamento?.nome||'—'}</td>
      <td style="font-size:.8rem;white-space:nowrap">${fmtDateTime(a.data_alerta)}</td>
      <td>${statusBadge(a.status)}</td>
      <td style="font-size:.8rem;color:var(--blue-600)">${a.tecnico_resolveu||'—'}</td>
      <td>${a.status==='aberto'&&canWrite()?`<button class="btn btn-success btn-sm" onclick="resolveAlerta(${a.id_alerta})">✅ Resolver</button>`:'<span style="color:var(--text-muted);font-size:.78rem">—</span>'}</td>
    </tr>
  `).join('') || `<tr><td colspan="8"><div class="empty-state"><div class="empty-state-icon">🔔</div><div class="empty-state-text">Nenhum alerta</div></div></td></tr>`;
}

async function saveAlerta() {
  const tipo = document.getElementById('al-tipo').value.trim();
  if (!tipo) { toast('Preencha o tipo','error'); return; }
  const idEq = parseInt(document.getElementById('al-equip').value);
  const eq   = DB.equipamentos.find(e=>e.id_equipamento===idEq);

  if (API_ONLINE) {
    const res = await apiCall('POST', '/alertas/', {
      tipo      : tipo,
      nivel     : document.getElementById('al-nivel').value,
      descricao : document.getElementById('al-desc').value,
      ativo     : idEq,
    });
    if (!res || res.error) return;
    DB.alertas.unshift(normalizeAlerta(res));
  } else {
    DB.alertas.unshift({
      id_alerta: nextIds.alerta++, tipo_alerta:tipo,
      nivel: document.getElementById('al-nivel').value,
      descricao: document.getElementById('al-desc').value,
      id_equipamento:idEq, data_alerta:new Date().toISOString(),
      status:'aberto', tecnico_resolveu:null, id_tecnico_resolveu:null,
      equipamento: eq?{nome:eq.nome}:null
    });
  }

  DB.notificacoes.unshift({id:Date.now(),texto:`Alerta: ${tipo}`,icone:'🚨',lida:false,hora:new Date().toISOString()});
  document.getElementById('al-tipo').value=''; document.getElementById('al-desc').value='';
  closeModal('modal-alerta');
  addLog(`Alerta criado: "${tipo}"`,'warning');
  toast('Alerta registrado!','warning');
  loadAlertas(); loadNotificacoes();
  document.getElementById('alert-badge').textContent = DB.alertas.filter(a=>a.status==='aberto').length;
}

async function resolveAlerta(id) {
  const a = DB.alertas.find(x=>x.id_alerta===id);

  if (API_ONLINE) {
    const res = await apiCall('PATCH', `/alertas/${id}/`, { status: 'resolvido' });
    if (!res || res.error) return;
  }

  const nomeTec = currentUser.nome;
  DB.alertas = DB.alertas.map(al=>al.id_alerta===id
    ? {...al, status:'resolvido', tecnico_resolveu:nomeTec, id_tecnico_resolveu:currentUser.id_tecnico||null}
    : al);
  addLog(`Alerta "${a?.tipo_alerta}" resolvido`);
  toast('Alerta resolvido!');
  renderAlertas();
  document.getElementById('alert-badge').textContent = DB.alertas.filter(a=>a.status==='aberto').length;
}

// ════════════════════════════════════════════════════════════
// MANUTENÇÃO
// ════════════════════════════════════════════════════════════
async function loadManutencao() {
  if (API_ONLINE) {
    const data = await apiCall('GET', '/manutencao/');
    const list = extractList(data);
    if (list) DB.manutencao = list.map(normalizeManutencao);
  }
  document.getElementById('mn-equip').innerHTML = DB.equipamentos.map(e=>`<option value="${e.id_equipamento}">${e.nome}</option>`).join('');
  renderManutencao();
}

function renderManutencao() {
  const tf = getFilter('mn-tipo'), sf = getFilter('mn-status');
  const list = DB.manutencao.filter(m=>(!tf||m.tipo===tf)&&(!sf||m.status===sf));
  document.getElementById('manut-table').innerHTML = list.map(m=>`
    <tr>
      <td>${statusBadge(m.tipo)}</td>
      <td>${m.equipamento?.nome||'—'}</td>
      <td style="max-width:200px;font-size:.82rem;color:var(--text-secondary)">${m.descricao}</td>
      <td style="font-size:.82rem;white-space:nowrap">${fmtDate(m.data_programada)}</td>
      <td>${statusBadge(m.status)}</td>
      <td>${canWrite()?`<button class="btn btn-ghost btn-sm" onclick="changeManutStatus(${m.id_manutencao})">⬆ Avançar</button>`:'—'}</td>
    </tr>
  `).join('') || `<tr><td colspan="6"><div class="empty-state"><div class="empty-state-icon">🔧</div><div class="empty-state-text">Nenhuma manutenção</div></div></td></tr>`;
}

async function saveManutencao() {
  const desc = document.getElementById('mn-desc').value.trim();
  if (!desc) { toast('Preencha a descrição','error'); return; }
  const idEq = parseInt(document.getElementById('mn-equip').value);
  const eq   = DB.equipamentos.find(e=>e.id_equipamento===idEq);

  const payload = {
    tipo           : document.getElementById('mn-tipo').value,
    descricao      : desc,
    data_programada: document.getElementById('mn-data').value,
    ativo          : idEq,
    status         : 'agendada',
  };

  if (API_ONLINE) {
    const res = await apiCall('POST', '/manutencao/', payload);
    if (!res || res.error) return;
    DB.manutencao.push(normalizeManutencao(res));
  } else {
    DB.manutencao.push({
      id_manutencao: nextIds.manutencao++, ...payload,
      id_equipamento: idEq, equipamento: eq?{nome:eq.nome}:null
    });
  }

  document.getElementById('mn-desc').value=''; document.getElementById('mn-data').value='';
  closeModal('modal-manutencao');
  addLog('Manutenção agendada');
  toast('Agendada!');
  loadManutencao();
}

async function changeManutStatus(id) {
  const opts = ['agendada','em_andamento','concluida'];
  const m    = DB.manutencao.find(x=>x.id_manutencao===id);
  const next = opts[(opts.indexOf(m?.status)+1)%opts.length];

  if (API_ONLINE) {
    const res = await apiCall('PATCH', `/manutencao/${id}/`, { status: next });
    if (!res || res.error) return;
  }

  DB.manutencao = DB.manutencao.map(m=>{ if(m.id_manutencao!==id)return m; toast(`→ ${next}`); addLog(`Manutenção #${id} → ${next}`); return {...m,status:next}; });
  renderManutencao();
}

// ════════════════════════════════════════════════════════════
// ORDENS DE SERVIÇO
// ════════════════════════════════════════════════════════════
async function loadOrdens() {
  if (API_ONLINE) {
    // Tenta buscar ordens de serviço
    const data = await apiCall('GET', '/ordens-servico/', null, true);
    const list = extractList(data);
    if (list) {
      // Filtra apenas ordens (se a API misturar os tipos)
      DB.ordens = list.map(normalizeOrdem);
    }
  }

  document.getElementById('os-tecnico').innerHTML = DB.tecnicos.filter(t=>t.ativo).map(t=>`<option value="${t.id_tecnico}">${t.nome}</option>`).join('');
  document.getElementById('os-manut').innerHTML   = DB.manutencao.map(m=>`<option value="${m.id_manutencao}">${m.id_manutencao} — ${m.descricao.slice(0,40)}</option>`).join('');
  renderOrdens();
}

function renderOrdens() {
  const sf = getFilter('os-status'), pf = getFilter('os-prior');
  const list = DB.ordens.filter(o=>(!sf||o.status===sf)&&(!pf||o.prioridade===pf));
  document.getElementById('os-table').innerHTML = list.map(os=>`
    <tr>
      <td><code style="font-family:var(--font-mono);font-size:.79rem;color:var(--orange-700);background:var(--orange-50);padding:2px 7px;border-radius:4px">${os.numero_os}</code></td>
      <td style="max-width:200px;font-size:.83rem">${os.descricao}</td>
      <td style="font-size:.82rem">${os.tecnico?.nome||'—'}</td>
      <td style="font-size:.8rem;color:var(--text-muted);white-space:nowrap">${fmtDate(os.data_abertura)}</td>
      <td>${statusBadge(os.prioridade)}</td>
      <td>${statusBadge(os.status)}</td>
      <td>${os.status!=='concluida'&&canWrite()?`<button class="btn btn-success btn-sm" onclick="closeOS(${os.id_ordem_servico})">✅</button>`:'<span style="color:var(--text-muted);font-size:.78rem">—</span>'}</td>
    </tr>
  `).join('') || `<tr><td colspan="7"><div class="empty-state"><div class="empty-state-icon">📋</div><div class="empty-state-text">Nenhuma OS</div></div></td></tr>`;
}

async function saveOS() {
  const desc  = document.getElementById('os-desc').value.trim();
  if (!desc) { toast('Preencha a descrição','error'); return; }
  const idTec  = parseInt(document.getElementById('os-tecnico').value);
  const tec    = DB.tecnicos.find(t=>t.id_tecnico===idTec);
  const num    = `OS-${new Date().getFullYear()}-${String(nextIds.ordem).padStart(3,'0')}`;

  const payload = {
    descricao    : desc,
    titulo       : desc,
    prioridade   : document.getElementById('os-prior').value,
    status       : document.getElementById('os-status').value,
    tecnico      : idTec,
    manutencao   : parseInt(document.getElementById('os-manut').value) || null,
    numero_os    : num,
  };

  if (API_ONLINE) {
    // Tenta POST em /ordens-servico/ primeiro, depois /manutencao/
    let res = await apiCall('POST', '/ordens-servico/', payload, true);
    if (!res || res.error) res = await apiCall('POST', '/manutencao/', payload, true);
    if (res && !res.error) {
      DB.ordens.unshift(normalizeOrdem(res));
      document.getElementById('os-desc').value='';
      closeModal('modal-os'); addLog(`OS ${num} criada`); toast(`OS ${num} criada!`); loadOrdens();
      return;
    }
  }

  DB.ordens.unshift({
    id_ordem_servico:nextIds.ordem++, numero_os:num, descricao:desc,
    prioridade:payload.prioridade, status:payload.status,
    data_abertura:new Date().toISOString().split('T')[0],
    id_tecnico:idTec, id_manutencao:payload.manutencao,
    tecnico: tec?{nome:tec.nome}:null
  });
  document.getElementById('os-desc').value='';
  closeModal('modal-os'); addLog(`OS ${num} criada`); toast(`OS ${num} criada!`); loadOrdens();
}

async function closeOS(id) {
  const os = DB.ordens.find(o=>o.id_ordem_servico===id);

  if (API_ONLINE) {
    let res = await apiCall('PATCH', `/ordens-servico/${id}/`, { status: 'concluida' }, true);
    if (!res || res.error) res = await apiCall('PATCH', `/manutencao/${id}/`, { status: 'concluida' }, true);
    if (res?.error) return;
  }

  DB.ordens = DB.ordens.map(o=>o.id_ordem_servico===id?{...o,status:'concluida'}:o);
  addLog(`OS ${os?.numero_os} concluída`);
  toast('OS concluída!');
  renderOrdens();
}

// ════════════════════════════════════════════════════════════
// HISTÓRICO
// ════════════════════════════════════════════════════════════
async function loadHistorico() {
  if (API_ONLINE) {
    const data = await apiCall('GET', '/manutencao/historico/');
    const list = extractList(data);
    if (list) DB.historico = list.map(normalizeHistorico);
  }

  const sel = document.getElementById('hist-tecnico-filter');
  if (sel) {
    const current = sel.value;
    sel.innerHTML = '<option value="">Todos os técnicos</option>' +
      DB.tecnicos.map(t=>`<option value="${t.id_tecnico}" ${current==t.id_tecnico?'selected':''}>${t.nome}</option>`).join('');
  }

  document.getElementById('hst-os').innerHTML      = DB.ordens.map(o=>`<option value="${o.id_ordem_servico}">${o.numero_os} — ${o.descricao.slice(0,30)}</option>`).join('');
  document.getElementById('hst-tecnico').innerHTML = DB.tecnicos.filter(t=>t.ativo).map(t=>`<option value="${t.id_tecnico}">${t.nome}</option>`).join('');
  renderHistorico();
}

function renderHistorico() {
  const tecFilter = parseInt(document.getElementById('hist-tecnico-filter')?.value)||0;
  const list      = DB.historico.filter(h => !tecFilter || h.id_tecnico===tecFilter);
  document.getElementById('hist-table').innerHTML = list.map(h=>`
    <tr>
      <td><code style="font-family:var(--font-mono);font-size:.79rem;color:var(--orange-700);background:var(--orange-50);padding:2px 7px;border-radius:4px">${h.ordem_servico?.numero_os||'—'}</code></td>
      <td>
        <div style="display:flex;align-items:center;gap:8px">
          <div style="width:28px;height:28px;border-radius:50%;background:var(--logo-gradient);display:flex;align-items:center;justify-content:center;color:#fff;font-size:.75rem;font-weight:700;flex-shrink:0">${h.tecnico?.nome?.[0]||'?'}</div>
          <span style="font-size:.83rem;font-weight:600">${h.tecnico?.nome||'—'}</span>
        </div>
      </td>
      <td style="font-size:.83rem;color:var(--text-secondary);max-width:250px">${h.descricao_servico}</td>
      <td style="font-size:.82rem;white-space:nowrap">${fmtDate(h.data_execucao)}</td>
      <td style="color:var(--blue-700);font-weight:700;font-family:var(--font-display)">${fmtCurrency(h.custo)}</td>
    </tr>
  `).join('') || `<tr><td colspan="5"><div class="empty-state"><div class="empty-state-icon">🗂️</div><div class="empty-state-text">Nenhum registro</div></div></td></tr>`;
}

async function saveHistorico() {
  const desc  = document.getElementById('hst-desc').value.trim();
  if (!desc) { toast('Preencha a descrição','error'); return; }
  const idOS  = parseInt(document.getElementById('hst-os').value);
  const idTec = parseInt(document.getElementById('hst-tecnico').value);
  const os    = DB.ordens.find(o=>o.id_ordem_servico===idOS);
  const tec   = DB.tecnicos.find(t=>t.id_tecnico===idTec);
  const custo = parseFloat(document.getElementById('hst-custo').value)||0;

  const payload = {
    descricao        : desc,
    ordem_servico    : idOS,
    tecnico          : idTec,
    custo_total      : custo,
    custo_pecas      : custo,
    data_execucao    : new Date().toISOString().split('T')[0],
  };

  if (API_ONLINE) {
    const res = await apiCall('POST', '/manutencao/historico/', payload);
    if (!res || res.error) return;
    DB.historico.unshift(normalizeHistorico(res));
  } else {
    DB.historico.unshift({
      id_historico: nextIds.historico++, id_ordem_servico:idOS, id_tecnico:idTec,
      descricao_servico:desc, data_execucao:new Date().toISOString().split('T')[0], custo,
      ordem_servico: os?{numero_os:os.numero_os}:null,
      tecnico: tec?{nome:tec.nome}:null
    });
  }

  document.getElementById('hst-desc').value=''; document.getElementById('hst-custo').value='';
  closeModal('modal-historico');
  addLog(`Execução registrada — ${os?.numero_os}`);
  toast('Execução registrada!');
  loadHistorico();
}

// ════════════════════════════════════════════════════════════
// TÉCNICOS
// ════════════════════════════════════════════════════════════
function setTecView(v) {
  tecView = v;
  document.getElementById('tec-view-grid').style.display  = v==='grid'?'':'none';
  document.getElementById('tec-view-table').style.display = v==='table'?'':'none';
  document.getElementById('view-grid-btn').classList.toggle('active', v==='grid');
  document.getElementById('view-table-btn').classList.toggle('active', v==='table');
  renderTecnicos();
}

async function loadTecnicos() {
  if (API_ONLINE) {
    // Técnicos são usuários com tipo_usuario=tecnico
    const data = await apiCall('GET', '/usuarios/?tipo_usuario=tecnico', null, true);
    const list = extractList(data);
    if (list && list.length > 0) {
      DB.tecnicos = list.map(normalizeTecnico);
    } else {
      // Tenta buscar todos os usuários e filtra
      const allData = await apiCall('GET', '/usuarios/', null, true);
      const allList = extractList(allData);
      if (allList) {
        const tecs = allList.filter(u=>u.tipo_usuario==='tecnico'||u.role==='tecnico');
        if (tecs.length > 0) DB.tecnicos = tecs.map(normalizeTecnico);
      }
    }
  }
  renderTecnicos();
}

function renderTecnicos() {
  const sf   = getFilter('tc-status');
  const area = document.getElementById('tc-area-filter')?.value||'';
  const q    = (document.getElementById('tc-search')?.value||'').toLowerCase();
  const list = DB.tecnicos.filter(t=>
    (!sf || (sf==='ativo'?t.ativo:!t.ativo)) &&
    (!area || t.area?.includes(area)) &&
    (!q || t.nome.toLowerCase().includes(q) || t.especialidade.toLowerCase().includes(q))
  );

  function tecStats(t) {
    const os_concluidas     = DB.ordens.filter(o=>o.id_tecnico===t.id_tecnico&&o.status==='concluida').length;
    const hist              = DB.historico.filter(h=>h.id_tecnico===t.id_tecnico);
    const custo_total       = hist.reduce((s,h)=>s+(h.custo||0),0);
    const alertas_resolvidos= DB.alertas.filter(a=>a.id_tecnico_resolveu===t.id_tecnico).length;
    return { os_concluidas, custo_total, alertas_resolvidos };
  }

  document.getElementById('tecnicos-grid').innerHTML = list.map(t=>{
    const s = tecStats(t);
    return `
      <div class="tecnico-card ${t.ativo?'':'inactive'}">
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:14px">
          <div class="tecnico-avatar">${t.nome[0]}</div>
          <div style="flex:1;min-width:0">
            <div class="tecnico-name">${t.nome}</div>
            <div class="tecnico-esp">${t.especialidade}</div>
          </div>
          ${statusBadge(t.ativo?'operacional':'inativo')}
        </div>
        <div class="tecnico-info" style="display:flex;flex-direction:column;gap:5px;margin-bottom:14px">
          <div>📞 ${t.telefone}</div>
          <div>✉️ ${t.email}</div>
          <div>🏷️ ${t.area||'—'}</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-bottom:14px">
          <div style="background:var(--blue-50);border:1px solid var(--blue-100);border-radius:var(--r);padding:8px 6px;text-align:center">
            <div style="font-family:var(--font-display);font-weight:800;font-size:1.1rem;color:var(--blue-600)">${s.os_concluidas}</div>
            <div style="font-size:.65rem;color:var(--text-muted);margin-top:1px">OS Concl.</div>
          </div>
          <div style="background:var(--orange-50);border:1px solid var(--orange-100);border-radius:var(--r);padding:8px 6px;text-align:center">
            <div style="font-family:var(--font-display);font-weight:800;font-size:1.1rem;color:var(--orange-600)">${s.alertas_resolvidos}</div>
            <div style="font-size:.65rem;color:var(--text-muted);margin-top:1px">Alertas</div>
          </div>
          <div style="background:var(--green-50);border:1px solid var(--green-100);border-radius:var(--r);padding:8px 6px;text-align:center">
            <div style="font-family:var(--font-display);font-weight:800;font-size:.85rem;color:var(--green-600)">R$${(s.custo_total/1000).toFixed(1)}k</div>
            <div style="font-size:.65rem;color:var(--text-muted);margin-top:1px">Custo</div>
          </div>
        </div>
        <div style="display:flex;gap:6px">
          <button class="btn btn-primary btn-sm" style="flex:1" onclick="openTecnicoPerfil(${t.id_tecnico})">👁️ Histórico</button>
          ${isAdmin()?`<button class="btn btn-ghost btn-sm" onclick="toggleTecnicoStatus(${t.id_tecnico})">${t.ativo?'⏸':'▶'}</button>`:''}
        </div>
      </div>`;
  }).join('') || `<div class="empty-state" style="grid-column:1/-1"><div class="empty-state-icon">👷</div><div class="empty-state-text">Nenhum técnico encontrado</div></div>`;

  document.getElementById('tecnicos-table').innerHTML = list.map(t=>{
    const s = tecStats(t);
    return `
      <tr>
        <td>
          <div style="display:flex;align-items:center;gap:10px">
            <div style="width:34px;height:34px;border-radius:50%;background:var(--logo-gradient);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:.85rem;flex-shrink:0">${t.nome[0]}</div>
            <div><div style="font-weight:600">${t.nome}</div><div style="font-size:.75rem;color:var(--text-muted)">${t.email}</div></div>
          </div>
        </td>
        <td style="font-size:.83rem;color:var(--text-secondary)">${t.especialidade}</td>
        <td><span class="badge badge-blue">${t.area||'—'}</span></td>
        <td style="font-size:.82rem">${t.telefone}</td>
        <td style="font-family:var(--font-display);font-weight:700;color:var(--blue-600)">${s.os_concluidas}</td>
        <td>${statusBadge(t.ativo?'operacional':'inativo')}</td>
        <td>
          <div style="display:flex;gap:6px">
            <button class="btn btn-ghost btn-sm" onclick="openTecnicoPerfil(${t.id_tecnico})">👁️</button>
            ${isAdmin()?`<button class="btn btn-ghost btn-sm" onclick="toggleTecnicoStatus(${t.id_tecnico})">${t.ativo?'⏸':'▶'}</button>`:''}
          </div>
        </td>
      </tr>`;
  }).join('') || `<tr><td colspan="7"><div class="empty-state"><div class="empty-state-icon">👷</div><div class="empty-state-text">Nenhum técnico</div></div></td></tr>`;
}

function openTecnicoPerfil(id) {
  const t = DB.tecnicos.find(x=>x.id_tecnico===id); if (!t) return;
  const os_todas       = DB.ordens.filter(o=>o.id_tecnico===id);
  const os_concluidas  = os_todas.filter(o=>o.status==='concluida');
  const os_andamento   = os_todas.filter(o=>o.status==='em_andamento');
  const hist           = DB.historico.filter(h=>h.id_tecnico===id);
  const custo_total    = hist.reduce((s,h)=>s+(h.custo||0),0);
  const alertas_resol  = DB.alertas.filter(a=>a.id_tecnico_resolveu===id);

  document.getElementById('modal-perfil-tecnico-content').innerHTML = `
    <div style="background:var(--logo-gradient);padding:28px 28px 24px;border-radius:var(--r-xl) var(--r-xl) 0 0">
      <div style="display:flex;align-items:center;gap:18px">
        <div style="width:72px;height:72px;border-radius:50%;background:rgba(255,255,255,.2);border:3px solid rgba(255,255,255,.5);display:flex;align-items:center;justify-content:center;font-family:var(--font-display);font-size:1.8rem;font-weight:800;color:#fff;flex-shrink:0">${t.nome[0]}</div>
        <div>
          <div style="font-family:var(--font-display);font-size:1.3rem;font-weight:800;color:#fff">${t.nome}</div>
          <div style="color:rgba(255,255,255,.75);font-size:.85rem;margin-top:2px">${t.especialidade}</div>
          <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap">
            <span style="background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:#fff;font-size:.68rem;font-weight:600;padding:2px 10px;border-radius:20px">${t.area||'—'}</span>
            <span style="background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:#fff;font-size:.68rem;font-weight:600;padding:2px 10px;border-radius:20px">${t.ativo?'✅ Ativo':'🚫 Inativo'}</span>
          </div>
        </div>
      </div>
    </div>
    <div style="padding:20px 24px;background:var(--surface-2);border-bottom:1px solid var(--border)">
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px">
        ${[
          {v:os_concluidas.length, l:'OS Concluídas',      c:'var(--blue-600)'},
          {v:os_andamento.length,  l:'Em Andamento',       c:'var(--orange-600)'},
          {v:alertas_resol.length, l:'Alertas Resolvidos', c:'var(--green-600)'},
          {v:fmtCurrency(custo_total),l:'Custo Total',     c:'var(--purple-500)'},
        ].map(s=>`
          <div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--r-lg);padding:14px 12px;text-align:center">
            <div style="font-family:var(--font-display);font-weight:800;font-size:${s.v.toString().length>6?'1rem':'1.4rem'};color:${s.c};letter-spacing:-0.03em;line-height:1">${s.v}</div>
            <div style="font-size:.68rem;color:var(--text-muted);margin-top:4px">${s.l}</div>
          </div>`).join('')}
      </div>
    </div>
    <div style="padding:20px 24px">
      <div style="display:flex;gap:16px;margin-bottom:20px;flex-wrap:wrap">
        <div style="display:flex;align-items:center;gap:7px;font-size:.83rem;color:var(--text-secondary)"><span>📞</span>${t.telefone}</div>
        <div style="display:flex;align-items:center;gap:7px;font-size:.83rem;color:var(--text-secondary)"><span>✉️</span>${t.email}</div>
      </div>
      <div style="font-family:var(--font-display);font-weight:700;font-size:.9rem;color:var(--text);margin-bottom:12px">🗂️ Histórico de Execuções</div>
      ${hist.length ? `
        <div style="border:1px solid var(--border);border-radius:var(--r-lg);overflow:hidden">
          ${hist.map((h,i)=>`
            <div style="padding:14px 16px;${i>0?'border-top:1px solid var(--border)':''}${i%2===1?'background:var(--surface-2)':''}">
              <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px">
                <div style="flex:1;min-width:0">
                  <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
                    <code style="font-family:var(--font-mono);font-size:.75rem;color:var(--orange-700);background:var(--orange-50);padding:2px 6px;border-radius:4px">${h.ordem_servico?.numero_os||'—'}</code>
                    <span style="font-size:.75rem;color:var(--text-muted)">${fmtDate(h.data_execucao)}</span>
                  </div>
                  <div style="font-size:.84rem;color:var(--text)">${h.descricao_servico}</div>
                </div>
                <div style="font-family:var(--font-display);font-weight:700;color:var(--blue-700);white-space:nowrap;font-size:.9rem">${fmtCurrency(h.custo)}</div>
              </div>
            </div>`).join('')}
        </div>` : '<div class="empty-state"><div class="empty-state-icon">🗂️</div><div class="empty-state-text">Sem execuções registradas</div></div>'}
      ${alertas_resol.length ? `
        <div style="font-family:var(--font-display);font-weight:700;font-size:.9rem;color:var(--text);margin:20px 0 12px">✅ Alertas Resolvidos</div>
        <div style="border:1px solid var(--border);border-radius:var(--r-lg);overflow:hidden">
          ${alertas_resol.map((a,i)=>`
            <div style="padding:12px 16px;display:flex;align-items:center;gap:12px;${i>0?'border-top:1px solid var(--border)':''}">
              <div class="alert-dot ${a.nivel}" style="flex-shrink:0"></div>
              <div style="flex:1;min-width:0">
                <div style="font-size:.83rem;font-weight:600">${a.tipo_alerta}</div>
                <div style="font-size:.76rem;color:var(--text-muted)">${a.equipamento?.nome||'—'} · ${fmtDate(a.data_alerta)}</div>
              </div>
              ${statusBadge(a.nivel)}
            </div>`).join('')}
        </div>` : ''}
    </div>`;
  openModal('modal-perfil-tecnico');
}

async function toggleTecnicoStatus(id) {
  const t = DB.tecnicos.find(x=>x.id_tecnico===id);
  const novoAtivo = !t?.ativo;

  if (API_ONLINE) {
    const res = await apiCall('PATCH', `/usuarios/${id}/`, { is_active: novoAtivo }, true);
    if (res?.error) {
      // Fallback silencioso
    }
  }

  DB.tecnicos = DB.tecnicos.map(tc=>tc.id_tecnico===id?{...tc,ativo:novoAtivo}:tc);
  addLog(`Técnico "${t?.nome}" ${novoAtivo?'reativado':'desativado'}`);
  toast(`${t?.nome} ${novoAtivo?'reativado':'desativado'}!`);
  renderTecnicos();
}

async function saveTecnico() {
  const nome = document.getElementById('tc-nome').value.trim();
  if (!nome) { toast('Preencha o nome','error'); return; }

  const payload = {
    username      : document.getElementById('tc-email').value || nome.toLowerCase().replace(/\s+/g,'_'),
    nome,
    email         : document.getElementById('tc-email').value,
    especialidade : document.getElementById('tc-esp').value,
    telefone      : document.getElementById('tc-tel').value,
    area          : document.getElementById('tc-area').value,
    tipo_usuario  : 'tecnico',
    is_active     : true,
  };

  if (API_ONLINE) {
    const res = await apiCall('POST', '/usuarios/', payload);
    if (!res || res.error) return;
    DB.tecnicos.push(normalizeTecnico(res));
  } else {
    DB.tecnicos.push({
      id_tecnico: nextIds.tecnico++, nome,
      especialidade: payload.especialidade,
      telefone: payload.telefone,
      email: payload.email,
      area: payload.area,
      ativo: true
    });
  }

  ['tc-nome','tc-esp','tc-tel','tc-email'].forEach(id=>document.getElementById(id).value='');
  closeModal('modal-tecnico');
  addLog(`Técnico "${nome}" cadastrado`);
  toast('Técnico cadastrado!');
  loadTecnicos();
}

// ════════════════════════════════════════════════════════════
// GERENCIAMENTO DE USUÁRIOS (admin)
// ════════════════════════════════════════════════════════════
async function loadUsuarios() {
  const accEl  = document.getElementById('usuarios-access-check');
  const contEl = document.getElementById('usuarios-content');
  if (!isAdmin()) {
    accEl.innerHTML = `<div class="access-denied"><div class="access-denied-icon">🔒</div><h3>Acesso Restrito</h3><p>Apenas administradores podem gerenciar usuários.</p></div>`;
    contEl.style.display='none'; return;
  }
  accEl.innerHTML=''; contEl.style.display='';

  if (API_ONLINE) {
    const data = await apiCall('GET', '/usuarios/');
    const list = extractList(data);
    if (list) {
      const apiUsers = list.map(normalizeUsuario);
      // Merge com USERS locais (mantém logins de demo)
      apiUsers.forEach(au => {
        const idx = USERS.findIndex(u=>u.id===au.id);
        if (idx>=0) USERS[idx] = {...USERS[idx], ...au};
        else USERS.push(au);
      });
    }
  }

  renderUsuarios();
}

function renderUsuarios() {
  const q        = (document.getElementById('usr-search')?.value||'').toLowerCase();
  const pendentes= USERS.filter(u=>u.status==='pendente');
  const todos    = USERS.filter(u=>!q||u.nome.toLowerCase().includes(q)||u.email.toLowerCase().includes(q));

  const pendSec = document.getElementById('pending-section');
  pendSec.style.display = pendentes.length>0 ? '' : 'none';
  document.getElementById('pending-count-badge').textContent = pendentes.length;
  document.getElementById('pending-list').innerHTML = pendentes.map(u=>`
    <div class="user-row">
      <div class="user-row-avatar">${u.nome[0]}</div>
      <div class="user-row-info">
        <div class="user-row-name">${u.nome}</div>
        <div class="user-row-email">${u.email} · cadastrado em ${fmtDate(u.createdAt)}</div>
      </div>
      <div style="display:flex;gap:6px">
        <button class="btn btn-success btn-sm" onclick="approveUser(${u.id})">✅ Aprovar</button>
        <button class="btn btn-danger btn-sm"  onclick="rejectUser(${u.id})">🚫 Rejeitar</button>
      </div>
    </div>
  `).join('');

  document.getElementById('users-total-badge').textContent = todos.filter(u=>u.status!=='pendente').length;
  document.getElementById('users-list').innerHTML = todos.filter(u=>u.status!=='pendente').map(u=>`
    <div class="user-row">
      <div class="user-row-avatar">${u.nome[0]}</div>
      <div class="user-row-info">
        <div class="user-row-name">${u.nome} ${u.id===currentUser.id?'<span style="font-size:.7rem;color:var(--text-muted)">(você)</span>':''}</div>
        <div class="user-row-email">${u.email} · ${u.cargo||'Sem cargo'}</div>
      </div>
      <div style="display:flex;align-items:center;gap:8px">
        ${roleBadge(u.role)}
        ${statusBadge(u.status)}
        <button class="btn btn-ghost btn-sm" onclick="openEditUser(${u.id})">✏️ Editar</button>
      </div>
    </div>
  `).join('') || '<div class="empty-state"><div class="empty-state-icon">👥</div><div class="empty-state-text">Nenhum usuário</div></div>';
}

async function approveUser(id) {
  if (API_ONLINE) {
    await apiCall('PATCH', `/usuarios/${id}/`, { is_active: true, status: 'ativo' }, true);
  }
  USERS = USERS.map(u=>u.id===id?{...u,status:'ativo'}:u);
  const u=USERS.find(x=>x.id===id);
  addLog(`Usuário "${u?.nome}" aprovado`); toast(`${u?.nome} aprovado!`,'success'); renderUsuarios();
}

async function rejectUser(id) {
  const u=USERS.find(x=>x.id===id);
  if (!confirm(`Rejeitar e remover "${u?.nome}"?`)) return;
  if (API_ONLINE) {
    await apiCall('DELETE', `/usuarios/${id}/`, null, true);
  }
  USERS=USERS.filter(x=>x.id!==id);
  addLog(`Usuário "${u?.nome}" rejeitado`,'warning'); toast('Usuário rejeitado.','warning'); renderUsuarios();
}

function openEditUser(id) {
  const u=USERS.find(x=>x.id===id); if (!u) return;
  document.getElementById('edit-user-id').value    = u.id;
  document.getElementById('edit-user-nome').value  = u.nome;
  document.getElementById('edit-user-email').value = u.email;
  document.getElementById('edit-user-cargo').value = u.cargo||'';
  document.getElementById('edit-user-role').value  = u.role;
  document.getElementById('edit-user-status').value= u.status;
  document.getElementById('edit-user-tecnico').innerHTML =
    '<option value="">— Nenhum —</option>' +
    DB.tecnicos.map(t=>`<option value="${t.id_tecnico}" ${u.id_tecnico===t.id_tecnico?'selected':''}>${t.nome}</option>`).join('');
  openModal('modal-edit-user');
}

async function saveEditUser() {
  const id   = parseInt(document.getElementById('edit-user-id').value);
  const nome = document.getElementById('edit-user-nome').value.trim();
  if (!nome) { toast('Nome obrigatório','error'); return; }
  const tecId = document.getElementById('edit-user-tecnico').value;
  const role  = document.getElementById('edit-user-role').value;

  if (API_ONLINE) {
    await apiCall('PATCH', `/usuarios/${id}/`, {
      nome, email: document.getElementById('edit-user-email').value,
      cargo: document.getElementById('edit-user-cargo').value,
      tipo_usuario: role,
      is_active: document.getElementById('edit-user-status').value === 'ativo',
    }, true);
  }

  USERS = USERS.map(u=>u.id===id?{
    ...u, nome, email:document.getElementById('edit-user-email').value,
    cargo:document.getElementById('edit-user-cargo').value,
    role, status:document.getElementById('edit-user-status').value,
    id_tecnico:tecId?parseInt(tecId):null
  }:u);
  closeModal('modal-edit-user');
  addLog(`Usuário #${id} atualizado`); toast('Usuário atualizado!'); renderUsuarios();
}

async function deleteUser() {
  const id=parseInt(document.getElementById('edit-user-id').value);
  if (id===currentUser.id) { toast('Não é possível excluir a própria conta.','error'); return; }
  const u=USERS.find(x=>x.id===id);
  if (!confirm(`Excluir permanentemente "${u?.nome}"?`)) return;
  if (API_ONLINE) {
    const res = await apiCall('DELETE', `/usuarios/${id}/`, null, true);
    if (res?.error) return;
  }
  USERS=USERS.filter(x=>x.id!==id);
  closeModal('modal-edit-user');
  addLog(`Usuário "${u?.nome}" excluído`,'warning'); toast('Usuário excluído.'); renderUsuarios();
}

// ════════════════════════════════════════════════════════════
// MEU PERFIL
// ════════════════════════════════════════════════════════════
function openMyProfile() {
  const u = currentUser;
  const tecvinc = u.id_tecnico ? DB.tecnicos.find(t=>t.id_tecnico===u.id_tecnico) : null;
  document.getElementById('meu-perfil-body').innerHTML = `
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px;padding:20px;background:var(--logo-gradient);border-radius:var(--r-lg)">
      <div style="width:60px;height:60px;border-radius:50%;background:rgba(255,255,255,.2);border:3px solid rgba(255,255,255,.5);display:flex;align-items:center;justify-content:center;font-family:var(--font-display);font-size:1.5rem;font-weight:800;color:#fff">${u.nome[0]}</div>
      <div>
        <div style="font-family:var(--font-display);font-size:1.1rem;font-weight:700;color:#fff">${u.nome}</div>
        <div style="color:rgba(255,255,255,.7);font-size:.82rem;margin-top:2px">${u.cargo||'Sem cargo'}</div>
        <div style="margin-top:6px">${roleBadge(u.role)}</div>
      </div>
    </div>
    ${API_ONLINE?`<div style="background:var(--green-50);border:1px solid var(--green-200);border-radius:var(--r);padding:10px 14px;font-size:.8rem;color:var(--green-700);margin-bottom:16px;display:flex;align-items:center;gap:8px"><span>🟢</span>Conectado à API NanaSmart</div>`:''}
    <div class="form-row">
      <div class="form-group-m">
        <label class="form-label-m">Nome</label>
        <input class="form-control" id="mp-nome" value="${u.nome}">
      </div>
      <div class="form-group-m">
        <label class="form-label-m">Cargo</label>
        <input class="form-control" id="mp-cargo" value="${u.cargo||''}" placeholder="Seu cargo/função">
      </div>
    </div>
    <div class="form-group-m">
      <label class="form-label-m">E-mail</label>
      <input class="form-control" id="mp-email" value="${u.email}" readonly style="opacity:.6;cursor:not-allowed">
    </div>
    ${tecvinc?`<div style="background:var(--blue-50);border:1px solid var(--blue-200);border-radius:var(--r);padding:12px 14px;font-size:.83rem;display:flex;align-items:center;gap:8px"><span>🔧</span>Vinculado ao técnico: <strong>${tecvinc.nome}</strong></div>`:''}
    <div class="login-divider"></div>
    <div class="form-group-m">
      <label class="form-label-m">Nova Senha (deixe vazio para manter)</label>
      <div class="password-wrap">
        <input class="form-control" type="password" id="mp-senha" placeholder="Nova senha">
        <button class="btn-toggle-pw" style="color:var(--text-muted)" type="button" onclick="togglePw('mp-senha','eye-mp')"><span id="eye-mp">👁️</span></button>
      </div>
    </div>
  `;
  openModal('modal-meu-perfil');
}

async function saveMeuPerfil() {
  const nome  = document.getElementById('mp-nome').value.trim();
  const cargo = document.getElementById('mp-cargo').value.trim();
  const senha = document.getElementById('mp-senha').value;
  if (!nome) { toast('Nome obrigatório','error'); return; }
  if (senha && senha.length<6) { toast('Senha muito curta (mín. 6)','error'); return; }

  if (API_ONLINE) {
    const payload = { nome, cargo };
    if (senha) payload.password = senha;
    await apiCall('PATCH', `/accounts/me/`, payload, true);
  }

  USERS = USERS.map(u=>u.id===currentUser.id?{...u,nome,cargo,...(senha?{senha}:{})  }:u);
  currentUser = {...currentUser, nome, cargo, ...(senha?{senha}:{})};
  document.getElementById('user-name').textContent    = nome;
  document.getElementById('user-avatar').textContent  = nome[0];
  document.getElementById('topbar-avatar').textContent= nome[0];
  document.getElementById('topbar-name').textContent  = nome.split(' ')[0];
  closeModal('modal-meu-perfil'); addLog('Perfil atualizado'); toast('Perfil atualizado!');
}

// ════════════════════════════════════════════════════════════
// LOGS (admin)
// ════════════════════════════════════════════════════════════
function loadLogs() {
  const acc=document.getElementById('logs-access-check'), card=document.getElementById('logs-card');
  if (!isAdmin()) {
    acc.innerHTML=`<div class="access-denied"><div class="access-denied-icon">🔒</div><h3>Acesso Restrito</h3><p>Apenas administradores.</p></div>`;
    card.style.display='none'; return;
  }
  acc.innerHTML=''; card.style.display='';
  const colors={info:'var(--blue-600)',warning:'var(--orange-600)',error:'var(--red-600)'};
  document.getElementById('logs-table').innerHTML = DB.logs.length
    ? DB.logs.map(l=>`
      <tr>
        <td style="font-family:var(--font-mono);font-size:.77rem;color:var(--text-muted);white-space:nowrap">${fmtDateTime(l.data_hora)}</td>
        <td style="font-size:.83rem">${l.acao}</td>
        <td style="font-size:.8rem;color:var(--blue-600);font-weight:600">${l.usuario||'Sistema'}</td>
        <td><span class="badge" style="background:transparent;border:1px solid ${colors[l.nivel]||'var(--border)'};color:${colors[l.nivel]||'var(--text-muted)'}">${l.nivel||'info'}</span></td>
      </tr>`).join('')
    : `<tr><td colspan="4"><div class="empty-state"><div class="empty-state-icon">📜</div><div class="empty-state-text">Nenhum log</div></div></td></tr>`;
}

function clearLogs() {
  if (!confirm('Limpar todos os logs?')) return;
  DB.logs=[]; addLog('Logs limpos','warning'); loadLogs(); toast('Logs limpos','info');
}

// ════════════════════════════════════════════════════════════
// LOCALIZAÇÃO (API adicional)
// ════════════════════════════════════════════════════════════
async function salvarLocalizacao(equipamentoId, setor, planta='') {
  if (!API_ONLINE) return;
  const res = await apiCall('POST', '/localizacao/', { equipamento: equipamentoId, setor, planta });
  if (res && !res.error) {
    DB.equipamentos = DB.equipamentos.map(e=>e.id_equipamento===equipamentoId
      ? {...e, localizacao:{setor, planta}}
      : e);
    toast('Localização atualizada!');
  }
}

// ════════════════════════════════════════════════════════════
// POLLING DE ALERTAS (verifica a cada 60s quando API está online)
// ════════════════════════════════════════════════════════════
let alertPollingInterval = null;

function startAlertPolling() {
  if (alertPollingInterval) clearInterval(alertPollingInterval);
  alertPollingInterval = setInterval(async () => {
    if (!API_ONLINE || !currentUser) return;
    const data = await apiCall('GET', '/alertas/?status=aberto', null, true);
    const list = extractList(data);
    if (!list) return;
    const novosAlertas = list.map(normalizeAlerta);
    const prevAbertos  = DB.alertas.filter(a=>a.status==='aberto').length;
    const novoAbertos  = novosAlertas.filter(a=>a.status==='aberto').length;
    if (novoAbertos > prevAbertos) {
      DB.alertas = [...novosAlertas, ...DB.alertas.filter(a=>a.status==='resolvido')];
      const diff = novoAbertos - prevAbertos;
      toast(`🚨 ${diff} novo${diff>1?'s':''} alerta${diff>1?'s':''}!`, 'warning');
      document.getElementById('alert-badge').textContent = novoAbertos;
      loadNotificacoes();
    }
  }, 60000); // 60 segundos
}

// ════════════════════════════════════════════════════════════
// INIT
// ════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', ()=>{
  document.querySelectorAll('.modal-overlay').forEach(o=>
    o.addEventListener('click', e=>{ if(e.target===o) o.classList.remove('open'); })
  );
  document.getElementById('login-senha').addEventListener('keydown', e=>{ if(e.key==='Enter') doLogin(); });
  document.getElementById('login-email').addEventListener('keydown', e=>{ if(e.key==='Enter') document.getElementById('login-senha').focus(); });
  ['login-email','login-senha'].forEach(id=>{
    document.getElementById(id)?.addEventListener('input', ()=>{
      document.getElementById('login-error').style.display='none';
      document.getElementById(id).classList.remove('error');
    });
  });
  document.getElementById('mn-data').min = new Date().toISOString().split('T')[0];
  restoreSession();
});
