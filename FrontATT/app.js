const { createApp, ref, reactive, computed, onMounted, watch } = Vue;
const BASE = 'http://localhost:8000';

createApp({
  setup() {
    const token        = ref(localStorage.getItem('sentinel_token') || '');
    const refreshTk    = ref(localStorage.getItem('sentinel_refresh') || '');
    const me           = ref(null);
    const view         = ref('dashboard');
    const loading      = ref(false);
    const loginLoading = ref(false);
    const loginError   = ref('');
    const loginForm    = reactive({ username:'', password:'' });
    const kpis         = ref(null);
    const dashAlerts   = ref([]);
    const alertCount   = ref(0);
    const toasts       = ref([]);
    const globalEmpresa = ref('');  // Filtro global por empresa (admin)

    const lists = reactive({
      equipamentos:[], alertas:[], ordens:[],
      sensores:[], leituras:[], historico:[], empresas:[],
      usuarios:[], localizacoes:[]
    });
    const pages = reactive({
      equipamentos:{ next:null, prev:null },
      alertas:     { next:null, prev:null },
      ordens:      { next:null, prev:null },
      historico:   { next:null, prev:null },
      sensores:    { next:null, prev:null },
      leituras:    { next:null, prev:null },
      empresas:    { next:null, prev:null },
      usuarios:    { next:null, prev:null },
      localizacoes:{ next:null, prev:null },
    });
    const filters = reactive({
      equipamentos:{ search:'', status:'', empresa:'' },
      alertas:{ search:'', nivel:'', status:'' },
      ordens:{ search:'', status:'' },
      historico:{ search:'', data_de:'', data_ate:'', custo_min:'', custo_max:'' },
      empresas:{ search:'' },
      usuarios:{ search:'' },
      localizacoes:{ search:'' },
    });

    // ─ Modal ─────────────────────────────────────────
    const modal      = reactive({ open:false, type:'', title:'', editId:null, saving:false });
    const fd         = reactive({});
    const formErrors = ref({});

    // ─ Computed básicos ──────────────────────────────
    const isAdmin     = computed(() => me.value?.tipo_usuario === 'admin');
    const userInitial = computed(() => (me.value?.username || 'U')[0].toUpperCase());
    const viewTitle   = computed(() => ({
      dashboard:'Dashboard', equipamentos:'Equipamentos', alertas:'Alertas',
      ordens:'Ordens de Serviço', telemetria:'Telemetria',
      historico:'Histórico de Manutenção', empresas:'Empresas',
      usuarios:'Usuários', localizacoes:'Localizações'
    }[view.value] || ''));

    // ═══════════════════════════════════════════════
    //  DASHBOARD CHARTS
    // ═══════════════════════════════════════════════

    const chartEquipStatus = computed(() => {
      const eq = lists.equipamentos;
      if (!eq.length && kpis.value) {
        const op  = kpis.value.equipamentos_operacionais ?? kpis.value.equipamentos_ativos ?? 0;
        const tot = kpis.value.total_equipamentos ?? 0;
        return [
          { label:'Ativo',      value: op,       color:'#00d4aa' },
          { label:'Inativo/Man', value: tot - op, color:'#ff3b3b' },
        ].filter(s => s.value > 0);
      }
      const counts = { ativo:0, manutencao:0, inativo:0 };
      eq.forEach(e => { if (counts[e.status] !== undefined) counts[e.status]++; });
      return [
        { label:'Ativo',      value: counts.ativo,      color:'#00d4aa' },
        { label:'Manutenção', value: counts.manutencao, color:'#ffaa00' },
        { label:'Inativo',    value: counts.inativo,    color:'#ff3b3b' },
      ].filter(s => s.value > 0);
    });

    const chartAlertNivel = computed(() => {
      const counts = { critico:0, medio:0, baixo:0 };
      dashAlerts.value.forEach(a => { if (counts[a.nivel] !== undefined) counts[a.nivel]++; });
      const max = Math.max(...Object.values(counts), 1);
      return [
        { label:'Crítico', value:counts.critico, pct: (counts.critico/max)*100, color:'#ff3b3b' },
        { label:'Médio',   value:counts.medio,   pct: (counts.medio/max)*100,   color:'#ffaa00' },
        { label:'Baixo',   value:counts.baixo,   pct: (counts.baixo/max)*100,   color:'#00d4aa' },
      ];
    });

    const chartOrdens = computed(() => {
      const counts = { pendente:0, andamento:0, concluida:0, cancelada:0 };
      lists.ordens.forEach(o => { if (counts[o.status] !== undefined) counts[o.status]++; });
      const max = Math.max(...Object.values(counts), 1);
      return [
        { label:'Pendente',  value:counts.pendente,     pct:(counts.pendente/max)*100,     color:'#4db8ff' },
        { label:'Andamento', value:counts.andamento,    pct:(counts.andamento/max)*100,    color:'#ffaa00' },
        { label:'Concluída', value:counts.concluida,    pct:(counts.concluida/max)*100,    color:'#00d4aa' },
        { label:'Cancelada', value:counts.cancelada,    pct:(counts.cancelada/max)*100,    color:'#374455' },
      ];
    });

    const chartTelemetria = computed(() => {
      const raw = lists.leituras.slice(0, 20).reverse();
      if (raw.length < 2) return { path:'', dots:[], min:0, max:0 };
      const vals = raw.map(l => parseFloat(l.valor) || 0);
      const min = Math.min(...vals);
      const max = Math.max(...vals);
      const range = max - min || 1;
      const W = 320, H = 80;
      const points = vals.map((v, i) => ({
        x: (i / (vals.length - 1)) * W,
        y: H - ((v - min) / range) * H * 0.85 - H * 0.05,
        v,
      }));
      const path = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
      const area = path + ` L${W},${H} L0,${H} Z`;
      return { path, area, dots: points, min: min.toFixed(1), max: max.toFixed(1) };
    });

    function donutArcs(segments, r=52, cx=64, cy=64) {
      const total = segments.reduce((s, g) => s + g.value, 0);
      if (!total) return [];
      let angle = -Math.PI / 2;
      return segments.map(seg => {
        const sweep = (seg.value / total) * 2 * Math.PI;
        const x1 = cx + r * Math.cos(angle);
        const y1 = cy + r * Math.sin(angle);
        const x2 = cx + r * Math.cos(angle + sweep);
        const y2 = cy + r * Math.sin(angle + sweep);
        const large = sweep > Math.PI ? 1 : 0;
        const d = `M${cx},${cy} L${x1.toFixed(2)},${y1.toFixed(2)} A${r},${r} 0 ${large},1 ${x2.toFixed(2)},${y2.toFixed(2)} Z`;
        angle += sweep;
        return { ...seg, d, pct: Math.round((seg.value / total) * 100) };
      });
    }

    const chartHistoricoTipo = computed(() => {
      // Ajustado para refletir os novos campos do Historico (custo_pecas + custo_mao_de_obra)
      const costs = {};
      lists.historico.forEach(h => {
        // Tenta pegar o tipo_os pela Ordem de Serviço aninhada, ou agrupa como 'geral'
        const k = h.ordem_servico?.tipo_os || 'geral'; 
        const custoTotal = (parseFloat(h.custo_pecas) || 0) + (parseFloat(h.custo_mao_de_obra) || 0);
        costs[k] = (costs[k] || 0) + custoTotal;
      });
      const entries = Object.entries(costs).sort((a,b) => b[1]-a[1]).slice(0,5);
      const max = Math.max(...entries.map(e=>e[1]), 1);
      const palette = ['#c6f135','#00d4aa','#4db8ff','#ffaa00','#ff3b3b'];
      return entries.map(([label, value], i) => ({
        label, value: value.toFixed(0),
        pct: (value/max)*100,
        color: palette[i % palette.length]
      }));
    });

    // ─ Toast ─────────────────────────────────────────
    function toast(msg, type='success') {
      const id = Date.now() + Math.random();
      toasts.value.push({ id, msg, type });
      setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id); }, 4500);
    }

    // ─ API ───────────────────────────────────────────
    let refreshingPromise = null;

    async function doRefreshToken() {
      if (!refreshTk.value) throw new Error('No refresh token');
      const res = await fetch(BASE + '/api/auth/refresh/', {
        method: 'POST',
        headers: { 'Content-Type':'application/json' },
        body: JSON.stringify({ refresh: refreshTk.value })
      });
      if (!res.ok) throw new Error('Refresh failed');
      const data = await res.json();
      token.value = data.access;
      localStorage.setItem('sentinel_token', data.access);
      if (data.refresh) {
        refreshTk.value = data.refresh;
        localStorage.setItem('sentinel_refresh', data.refresh);
      }
    }

    async function api(path, opts = {}) {
      const headers = { 'Content-Type': 'application/json' };
      if (token.value) headers['Authorization'] = `Bearer ${token.value}`;
      let res = await fetch(BASE + path, { headers, ...opts });

      if (res.status === 401 && refreshTk.value) {
        if (!refreshingPromise) {
          refreshingPromise = doRefreshToken().finally(() => { refreshingPromise = null; });
        }
        try {
          await refreshingPromise;
          headers['Authorization'] = `Bearer ${token.value}`;
          res = await fetch(BASE + path, { headers, ...opts });
        } catch {
          logout();
          return null;
        }
      }

      if (res.status === 401) { logout(); return null; }
      if (res.status === 204) return null;
      const body = await res.json();
      if (!res.ok) {
        const err = new Error('API error');
        err.fieldErrors = body;
        throw err;
      }
      return body;
    }

    function parseDjangoErrors(raw) {
      const out = {};
      if (!raw || typeof raw !== 'object') return out;
      for (const [key, val] of Object.entries(raw)) {
        const msg = Array.isArray(val) ? val[0] : String(val);
        if (key === 'non_field_errors' || key === 'detail') out._global = msg;
        else out[key] = msg;
      }
      return out;
    }

    const timers = {};
    function debouncedFetch(key, fn, ms = 350) {
      clearTimeout(timers[key]);
      timers[key] = setTimeout(fn, ms);
    }

    // ─ Auth ──────────────────────────────────────────
    async function doLogin() {
      loginLoading.value = true; loginError.value = '';
      try {
        const res  = await fetch(BASE + '/api/auth/login/', {
          method:'POST', headers:{ 'Content-Type':'application/json' },
          body: JSON.stringify(loginForm)
        });
        const data = await res.json();
        if (!data.access) throw new Error(data.detail || 'Credenciais inválidas');
        token.value   = data.access;
        localStorage.setItem('sentinel_token', data.access);
        if (data.refresh) {
          refreshTk.value = data.refresh;
          localStorage.setItem('sentinel_refresh', data.refresh);
        }
        await fetchMe();
        navigate('dashboard');
      } catch(e) { loginError.value = e.message; }
      finally    { loginLoading.value = false; }
    }

    async function fetchMe() {
      try { me.value = await api('/api/auth/me/'); } catch {}
    }

    function logout() {
      token.value = ''; refreshTk.value = ''; me.value = null;
      localStorage.removeItem('sentinel_token');
      localStorage.removeItem('sentinel_refresh');
    }

    // ─ Navigation ────────────────────────────────────
    const fetchers = {
      dashboard:    () => fetchDashboard(),
      equipamentos: () => fetchEquipamentos(),
      alertas:      () => fetchAlertas(),
      ordens:       () => fetchOrdens(),
      telemetria:   () => fetchTelemetria(),
      historico:    () => fetchHistorico(),
      empresas:     () => fetchEmpresas(),
      usuarios:     () => fetchUsuarios(),
      localizacoes: () => fetchLocalizacoes(),
    };
    function navigate(v) { view.value = v; fetchers[v]?.(); }

    // ─ Fetchers ──────────────────────────────────────
    async function withLoading(fn) {
      loading.value = true;
      try { await fn(); }
      finally { loading.value = false; }
    }

    function normList(d) {
      return Array.isArray(d) ? d : (d?.results ?? []);
    }
    function normPages(d) {
      return { next: d?.next ?? null, prev: d?.previous ?? null };
    }

    async function fetchDashboard() {
      try {
        const [eqRes, alertRes, ordRes, telRes, histRes] = await Promise.allSettled([
          api('/api/equipamentos/?limit=999'),
          api('/api/alertas/?status=ativo&limit=999'),
          api('/api/ordens-servico/?limit=999'),
          api('/api/telemetria/leituras/'),
          api('/api/historico/'),
        ]);

        if (eqRes.status==='fulfilled'   && eqRes.value)   lists.equipamentos = normList(eqRes.value);
        if (alertRes.status==='fulfilled' && alertRes.value) { dashAlerts.value = normList(alertRes.value); alertCount.value = dashAlerts.value.length; }
        if (ordRes.status==='fulfilled'  && ordRes.value)  lists.ordens       = normList(ordRes.value);
        if (telRes.status==='fulfilled'  && telRes.value)  lists.leituras     = normList(telRes.value);
        if (histRes.status==='fulfilled' && histRes.value) lists.historico    = normList(histRes.value);

        // Monta KPIs a partir dos dados reais
        kpis.value = {
          total_equipamentos: lists.equipamentos.length,
          alertas_ativos:     dashAlerts.value.length,
          ordens_abertas:     lists.ordens.filter(o => o.status === 'pendente' || o.status === 'andamento').length,
          leituras_hoje:      lists.leituras.length,
        };

        // Busca métricas MTTR/MTBF em paralelo (não bloqueia o dashboard)
        api('/api/dashboards/kpis/').then(d => { if (d) kpis.value._mtbf = d; }).catch(() => {});

      } catch { toast('Erro ao carregar dashboard', 'error'); }
    }

    async function fetchEquipamentos() { await withLoading(async () => {
      const p = new URLSearchParams();
      if (filters.equipamentos.search) p.set('search', filters.equipamentos.search);
      if (filters.equipamentos.status) p.set('status', filters.equipamentos.status);
      const empFilter = filters.equipamentos.empresa || globalEmpresa.value;
      if (empFilter) p.set('empresa', empFilter);
      const d = await api('/api/equipamentos/?'+p);
      lists.equipamentos = normList(d);
      Object.assign(pages.equipamentos, normPages(d));
      // Busca localizações para mostrar o setor ao lado de cada equipamento
      const locRes = await api('/api/localizacao/?limit=999');
      lists.localizacoes = normList(locRes);
    }); }

    async function fetchAlertas() { await withLoading(async () => {
      const p = new URLSearchParams();
      if (filters.alertas.search) p.set('search', filters.alertas.search);
      if (filters.alertas.nivel)  p.set('nivel',  filters.alertas.nivel);
      if (filters.alertas.status) p.set('status', filters.alertas.status);
      if (globalEmpresa.value) p.set('equipamento__empresa', globalEmpresa.value);
      const d = await api('/api/alertas/?'+p);
      lists.alertas = normList(d);
      Object.assign(pages.alertas, normPages(d));
    }); }

    async function fetchOrdens() { await withLoading(async () => {
      const p = new URLSearchParams();
      if (filters.ordens.search) p.set('search', filters.ordens.search);
      if (filters.ordens.status) p.set('status', filters.ordens.status);
      if (globalEmpresa.value) p.set('equipamento__empresa', globalEmpresa.value);
      const d = await api('/api/ordens-servico/?'+p);
      lists.ordens = normList(d);
      Object.assign(pages.ordens, normPages(d));
    }); }

    async function fetchTelemetria() { await withLoading(async () => {
      const [s,l] = await Promise.all([
        api('/api/telemetria/sensores/'),
        api('/api/telemetria/leituras/'),
      ]);
      lists.sensores = normList(s);
      Object.assign(pages.sensores, normPages(s));
      lists.leituras = normList(l);
      Object.assign(pages.leituras, normPages(l));
    }); }

    async function fetchHistorico() { await withLoading(async () => {
      const p = new URLSearchParams();
      if (filters.historico.search) p.set('search', filters.historico.search);
      if (filters.historico.data_de) p.set('data_execucao__gte', filters.historico.data_de);
      if (filters.historico.data_ate) p.set('data_execucao__lte', filters.historico.data_ate);
      if (globalEmpresa.value) p.set('ordem_servico__equipamento__empresa', globalEmpresa.value);
      const d = await api('/api/historico/?'+p);
      let items = normList(d);
      // Filtro local de custo (soma peças + mão de obra)
      if (filters.historico.custo_min) {
        const min = parseFloat(filters.historico.custo_min);
        items = items.filter(h => (parseFloat(h.custo_pecas)||0) + (parseFloat(h.custo_mao_de_obra)||0) >= min);
      }
      if (filters.historico.custo_max) {
        const max = parseFloat(filters.historico.custo_max);
        items = items.filter(h => (parseFloat(h.custo_pecas)||0) + (parseFloat(h.custo_mao_de_obra)||0) <= max);
      }
      lists.historico = items;
      Object.assign(pages.historico, normPages(d));
    }); }

    async function fetchEmpresas() { await withLoading(async () => {
      const p = new URLSearchParams();
      if (filters.empresas.search) p.set('search', filters.empresas.search);
      const d = await api('/api/empresas/?'+p);
      lists.empresas = normList(d);
      Object.assign(pages.empresas, normPages(d));
    }); }

    async function fetchUsuarios() { await withLoading(async () => {
      const p = new URLSearchParams();
      if (filters.usuarios.search) p.set('search', filters.usuarios.search);
      const d = await api('/api/usuarios/?'+p);
      lists.usuarios = normList(d);
      Object.assign(pages.usuarios, normPages(d));
    }); }

    async function fetchLocalizacoes() { await withLoading(async () => {
      const p = new URLSearchParams();
      if (filters.localizacoes.search) p.set('search', filters.localizacoes.search);
      const d = await api('/api/localizacao/?'+p);
      lists.localizacoes = normList(d);
      Object.assign(pages.localizacoes, normPages(d));
    }); }

    async function fetchEmpresasAll() {
      if (lists.empresas.length) return;
      const d = await api('/api/empresas/?limit=999');
      lists.empresas = normList(d);
    }
    async function fetchEquipamentosAll() {
      if (lists.equipamentos.length) return;
      const d = await api('/api/equipamentos/?limit=999');
      lists.equipamentos = normList(d);
    }
    async function fetchSensoresAll() {
      if (lists.sensores.length) return;
      const d = await api('/api/telemetria/sensores/?limit=999');
      lists.sensores = normList(d);
    }
    async function fetchOrdensAll() {
      if (lists.ordens.length) return;
      const d = await api('/api/ordens-servico/?limit=999');
      lists.ordens = normList(d);
    }
    async function fetchUsuariosAll() {
      if (lists.usuarios.length) return;
      const d = await api('/api/usuarios/?limit=999');
      lists.usuarios = normList(d);
    }

    async function fetchPage(resource, url) {
      if (!url) return;
      await withLoading(async () => {
        const path = url.replace(/^https?:\/\/[^\/]+/, '');
        const d = await api(path);
        lists[resource] = normList(d);
        if (pages[resource]) Object.assign(pages[resource], normPages(d));
      });
    }

    // ─ Modal / CRUD ───────────────────────────────────
    const modalConfig = {
      equipamento: { title:'Equipamento', endpoint:'/api/equipamentos/',
        defaults:{ nome:'', tipo:'', modelo:'', fabricante:'', numero_serie:'', status:'ativo', empresa:null, data_instalacao:'', descricao:'' } },
      alerta:      { title:'Alerta', endpoint:'/api/alertas/',
        defaults:{ tipo_alerta:'', nivel:'medio', descricao:'', status:'ativo', equipamento:null } },
      
      ordem:       { title:'Ordem de Serviço', endpoint:'/api/ordens-servico/',
        defaults:{ titulo:'', tipo_os:'preventiva', prioridade:'medio', status:'pendente', equipamento:null, responsavel:null, descricao:'' } },
      
      empresa:     { title:'Empresa', endpoint:'/api/empresas/',
        defaults:{ nome:'', cnpj:'', telefone:'', email:'', cidade:'', estado:'', endereco:'' } },
      sensor:      { title:'Sensor', endpoint:'/api/telemetria/sensores/',
        defaults:{ nome:'', tipo:'', unidade_medida:'', equipamento:null, ativo:true } },
      leitura:     { title:'Leitura de Telemetria', endpoint:'/api/telemetria/leituras/',
        defaults:{ sensor:null, valor:'', timestamp:'' } },
      
      // AJUSTE: Campos alinhados com o Django (ordem_servico, custo_pecas, custo_mao_de_obra, etc)
      historico:   { title:'Histórico', endpoint:'/api/historico/',
        defaults:{ ordem_servico:null, descricao_servico:'', custo_pecas:0, custo_mao_de_obra:0, data_execucao:'' } },
      
      usuario:     { title:'Usuário', endpoint:'/api/usuarios/',
        defaults:{ username:'', email:'', first_name:'', last_name:'', tipo_usuario:'tecnico', empresa:null, cargo:'', telefone:'' } },
      localizacao: { title:'Localização', endpoint:'/api/localizacao/',
        defaults:{ equipamento:null, setor:'' } },
    };

    function resetForm(defaults) {
      // Remove chaves que não existem nos novos defaults
      Object.keys(fd).forEach(k => { if (!(k in defaults)) delete fd[k]; });
      // Atribui individualmente para garantir reatividade correta no Vue 3
      const copy = JSON.parse(JSON.stringify(defaults));
      Object.keys(copy).forEach(k => { fd[k] = copy[k]; });
    }

    async function openModal(type) {
      const cfg = modalConfig[type];
      modal.type = type; modal.title = 'Novo ' + cfg.title;
      modal.editId = null; formErrors.value = {};
      resetForm(cfg.defaults); modal.open = true;
      
      if (['equipamento','alerta','ordem','sensor','localizacao','leitura'].includes(type)) {
        await fetchEquipamentosAll();
        await fetchEmpresasAll();
      }
      if (type === 'ordem') await fetchUsuariosAll();
      if (type === 'leitura') await fetchSensoresAll();
      if (type === 'usuario') await fetchEmpresasAll();
      if (type === 'historico') await fetchOrdensAll(); // Histórico precisa das ordens
    }

    async function editItem(type, item) {
      const cfg = modalConfig[type];
      modal.type = type; modal.title = 'Editar ' + cfg.title;
      modal.editId = item.id; formErrors.value = {};
      resetForm({ ...cfg.defaults, ...item }); modal.open = true;
      
      if (['equipamento','alerta','ordem','sensor','localizacao','leitura'].includes(type)) {
        await fetchEquipamentosAll();
        await fetchEmpresasAll();
      }
      if (type === 'ordem') await fetchUsuariosAll();
      if (type === 'leitura') await fetchSensoresAll();
      if (type === 'usuario') await fetchEmpresasAll();
      if (type === 'historico') await fetchOrdensAll();
    }

    async function saveItem() {
      const cfg = modalConfig[modal.type];
      modal.saving = true; formErrors.value = {};
      try {
        const payload = { ...fd };

        // Limpa FKs vazias
        ['empresa','equipamento','sensor','ordem_servico','responsavel'].forEach(k => {
          if (payload[k] === '' || payload[k] === 0) payload[k] = null;
        });

        // DEBUG — remover após confirmar
        if (modal.type === 'ordem') console.log('PAYLOAD OS →', JSON.stringify(payload));

        // Garante valores válidos para campos choice da OS
        if (modal.type === 'ordem') {
          const prioridadesValidas = ['baixo','medio','critico'];
          const statusValidos      = ['pendente','andamento','concluida','cancelada'];
          const tiposValidos       = ['preventiva','corretiva','preditiva'];
          if (!prioridadesValidas.includes(payload.prioridade)) payload.prioridade = 'medio';
          if (!statusValidos.includes(payload.status))          payload.status      = 'pendente';
          if (!tiposValidos.includes(payload.tipo_os))          payload.tipo_os     = 'preventiva';
        }

        if (modal.editId) {
          await api(cfg.endpoint + modal.editId + '/', { method:'PUT', body:JSON.stringify(payload) });
        } else {
          await api(cfg.endpoint, { method:'POST', body:JSON.stringify(payload) });
        }
        modal.open = false;
        toast(modal.editId ? 'Atualizado com sucesso!' : 'Criado com sucesso!', 'success');
        navigate(view.value);
      } catch(e) {
        if (e.fieldErrors) {
          formErrors.value = parseDjangoErrors(e.fieldErrors);
          const fields = Object.keys(formErrors.value).filter(k => k !== '_global');
          if (fields.length) toast('Preencha os campos obrigatórios: ' + fields.join(', '), 'error');
          else if (formErrors.value._global) toast(formErrors.value._global, 'error');
        } else { toast('Erro inesperado: ' + e.message, 'error'); }
      } finally { modal.saving = false; }
    }

    async function deleteItem(endpoint, id) {
      if (!confirm('Confirmar exclusão?')) return;
      try {
        await api('/api/' + endpoint + '/' + id + '/', { method:'DELETE' });
        toast('Excluído com sucesso!', 'success');
        navigate(view.value);
      } catch { toast('Erro ao excluir', 'error'); }
    }

    // ─ Helpers ───────────────────────────────────────
    function fmtDate(d) {
      if (!d) return '—';
      return new Date(d).toLocaleString('pt-BR', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' });
    }
    function nivelBadge(n)       { return {critico:'badge-red',medio:'badge-yellow',baixo:'badge-green'}[n]||'badge-gray'; }
    function nivelColor(n)       { return {critico:'var(--signal)',medio:'var(--warn)',baixo:'var(--teal)'}[n]||'var(--ink4)'; }
    function statusBadge(s)      { return {ativo:'badge-red',resolvido:'badge-green',ignorado:'badge-gray'}[s]||'badge-gray'; }
    function eqStatusBadge(s)    { return {ativo:'badge-green',manutencao:'badge-yellow',inativo:'badge-gray'}[s]||'badge-gray'; }
    function ordemStatusBadge(s) { return {pendente:'badge-blue',andamento:'badge-yellow',concluida:'badge-green',cancelada:'badge-gray'}[s]||'badge-gray'; }
    
    // AJUSTE: Classes baseadas nas novas prioridades do Django
    function prioridadeBadge(p)  { return {critico:'badge-red',medio:'badge-yellow',baixo:'badge-green'}[p]||'badge-gray'; }

    function eqNome(id) {
      if (id == null) return '—';
      const eq = lists.equipamentos.find(e => e.id === id);
      return eq ? `${eq.nome} (#${eq.id})` : `#${id}`;
    }
    function empresaNome(id) {
      if (id == null) return '—';
      const e = lists.empresas.find(e => e.id === id);
      return e ? e.nome : `#${id}`;
    }
    function sensorNome(id) {
      if (id == null) return '—';
      const s = lists.sensores.find(s => s.id === id);
      return s ? `${s.nome} (#${s.id})` : `#${id}`;
    }
    function locSetor(eqId) {
      if (eqId == null) return '—';
      const loc = lists.localizacoes.find(l => l.equipamento === eqId);
      return loc ? (loc.setor || '—') : '—';
    }
    function custoTotal(h) {
      return ((parseFloat(h.custo_pecas)||0) + (parseFloat(h.custo_mao_de_obra)||0)).toFixed(2);
    }
    function onGlobalEmpresaChange() {
      // Recarrega a aba atual ao mudar o filtro global
      fetchers[view.value]?.();
    }

    // ─ Init ──────────────────────────────────────────
    onMounted(async () => {
      if (token.value) {
        await fetchMe();
        // Carrega lista de empresas para o filtro global do admin
        await fetchEmpresasAll();
        navigate('dashboard');
      }
    });

    return {
      token, me, view, loading, loginLoading, loginError, loginForm,
      kpis, dashAlerts, alertCount, toasts, lists, pages, filters,
      modal, fd, formErrors, globalEmpresa,
      isAdmin, userInitial, viewTitle,
      doLogin, logout, navigate, debouncedFetch,
      fetchEquipamentos, fetchAlertas, fetchOrdens, fetchTelemetria,
      fetchHistorico, fetchEmpresas, fetchUsuarios, fetchLocalizacoes, fetchPage, fetchDashboard,
      openModal, editItem, saveItem, deleteItem,
      fmtDate, nivelBadge, nivelColor, statusBadge, eqStatusBadge,
      ordemStatusBadge, prioridadeBadge,
      eqNome, empresaNome, sensorNome, locSetor, custoTotal,
      onGlobalEmpresaChange,
      chartEquipStatus, chartAlertNivel, chartOrdens, chartTelemetria,
      chartHistoricoTipo, donutArcs,
    };
  }
}).mount('#app');