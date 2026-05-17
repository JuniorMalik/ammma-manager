const userRole = localStorage.getItem('ammma_role');
const userName = localStorage.getItem('ammma_user') || 'Usuário';

// --- CONFIGURAÇÃO DE HOSTING ---
// Se o backend estiver em outro servidor (ex: Railway), coloque a URL aqui.
// Se estiver no mesmo servidor, deixe vazio: ''
const API_BASE_URL = 'https://ammma-manager-production.up.railway.app';

function escapeHTML(str) {
    if (typeof str !== 'string') return str;
    return str.replace(/[&<>'"]/g,
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag])
    );
}

if (!localStorage.getItem('ammma_token')) {
    window.location.href = 'login.html';
}

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    // Atualizar Nome de Boas-vindas
    const welcomeTitle = document.getElementById('tab-title');
    if (welcomeTitle) {
        welcomeTitle.textContent = `Bem-vindo, `;
        const nameSpan = document.createElement('span');
        nameSpan.style.color = 'var(--primary)';
        nameSpan.textContent = userName;
        welcomeTitle.appendChild(nameSpan);
    }

    if (userRole !== 'admin' && userRole !== 'DEV') {
        const settingsBtn = document.querySelector('li[onclick*="settings"]');
        if (settingsBtn) settingsBtn.style.display = 'none';

        const inventoryBtn = document.querySelector('li[onclick*="inventory-tab"]');
        if (inventoryBtn) inventoryBtn.style.display = 'none';

        const couponsBtn = document.querySelector('li[onclick*="coupons-tab"]');
        if (couponsBtn) couponsBtn.style.display = 'none';
    }
    loadOrders();
    loadUsers();
    loadConfigs();
    loadStats();

    // Inicializar Calendário Flatpickr
    flatpickr("#delivery-date", {
        locale: "pt",
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d/m/Y",
        minDate: "today",
        disableMobile: "true",
        theme: "dark"
    });

    // Registrar Service Worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('sw.js')
            .then(reg => console.log('Service Worker Registrado!', reg))
            .catch(err => console.error('Erro no Service Worker', err));
    }
});

// --- LÓGICA DE INSTALAÇÃO PWA ---
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    // Impedir que o mini-infobar apareça no mobile
    e.preventDefault();
    // Salvar o evento para ser disparado depois
    deferredPrompt = e;
    // Mostrar o banner de instalação customizado
    const banner = document.getElementById('pwa-banner');
    if (banner) banner.style.display = 'flex';
});

async function installPwa() {
    if (!deferredPrompt) return;
    // Mostrar o prompt de instalação nativo
    deferredPrompt.prompt();
    // Esperar pela resposta do usuário
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`User response to the install prompt: ${outcome}`);
    // Limpar o prompt
    deferredPrompt = null;
    // Esconder o banner
    hidePwaBanner();
}

function hidePwaBanner() {
    const banner = document.getElementById('pwa-banner');
    if (banner) banner.style.display = 'none';
}

function showToast(msg, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = '✅';
    if (type === 'error') icon = '❌';
    if (type === 'info') icon = 'ℹ️';

    // Usando pre-wrap para suportar \n e textContent para segurança
    const iconSpan = document.createElement('span');
    iconSpan.innerText = icon;

    const msgDiv = document.createElement('div');
    msgDiv.style.flex = '1';
    msgDiv.style.whiteSpace = 'pre-wrap';
    msgDiv.textContent = msg;

    toast.appendChild(iconSpan);
    toast.appendChild(msgDiv);
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

async function apiFetch(url, options = {}) {
    const token = localStorage.getItem('ammma_token');
    const defaultHeaders = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };

    // Se for FormData (upload de galeria), não envia Content-Type manual
    if (options.body instanceof FormData) {
        delete defaultHeaders['Content-Type'];
    }

    options.headers = { ...defaultHeaders, ...options.headers };

    const response = await fetch(API_BASE_URL + url, options);

    if (response.status === 401) {
        localStorage.removeItem('ammma_token');
        window.location.href = '/login';
        return;
    }

    if (response.status === 403) {
        showToast('Acesso negado para o seu cargo.', 'error');
        throw new Error('Forbidden');
    }

    return response;
}

async function loadStats() {
    try {
        const response = await apiFetch('/stats');
        if (response.ok) {
            const data = await response.json();
            document.getElementById('stat-total').innerText = data.total_orders;
            document.getElementById('stat-pending').innerText = data.pending_orders;
            document.getElementById('stat-production').innerText = data.production_orders;
            document.getElementById('stat-weight').innerText = `${data.total_weight_kg.toLocaleString('pt-BR')} kg`;

            document.getElementById('stat-inventory-value').innerText = `R$ ${data.inventory_value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
            document.getElementById('stat-gross-cost').innerText = `R$ ${data.total_cost.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
            document.getElementById('stat-total-revenue').innerText = `R$ ${data.total_revenue.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
            document.getElementById('stat-net-profit').innerText = `R$ ${data.net_profit.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;

            document.getElementById('stat-margin').innerText = `${data.avg_margin}%`;
            document.getElementById('stat-lead-time').innerText = `${data.avg_lead_time}h`;

            // Novos campos de desperdício
            document.getElementById('stat-wasted-weight').innerText = `${data.total_wasted_kg.toLocaleString('pt-BR')} kg`;
            document.getElementById('stat-wasted-cost').innerText = `R$ ${data.total_wasted_cost.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;

            // Monitor de Impressoras (Mini)
            const printerGrid = document.getElementById('printer-monitor-grid');
            printerGrid.innerHTML = '';
            if (data.printer_summary.total === 0) {
                printerGrid.innerHTML = '<p style="color: var(--text-muted); font-size: 0.8rem;">Nenhuma impressora cadastrada.</p>';
            } else {
                // Buscar detalhes das impressoras para o monitor
                const pResp = await apiFetch('/printers');
                const printers = await pResp.json();
                printers.forEach(p => {
                    const card = document.createElement('div');
                    card.className = 'stat-card';
                    card.style.padding = '1rem';
                    let statusColor = 'var(--success)';
                    if (p.status === 'Ocupada') statusColor = 'var(--accent)';
                    if (p.status === 'Manutenção') statusColor = 'var(--secondary)';

                    card.innerHTML = `
                                <div style="font-size: 0.8rem; font-weight: bold;">${p.name}</div>
                                <div style="font-size: 0.7rem; color: ${statusColor}; margin-top: 0.3rem;">● ${p.status}</div>
                                <div style="font-size: 0.65rem; color: var(--text-muted); margin-top: 0.5rem;">Total: ${p.total_hours.toFixed(1)}h</div>
                            `;
                    printerGrid.appendChild(card);
                });
            }

            // Manutenções e Alertas
            const maintList = document.getElementById('maintenance-list');
            if (maintList) {
                maintList.innerHTML = '';
                if (data.printer_summary.needing_maintenance.length === 0) {
                    maintList.innerHTML = '<p style="color: var(--success); font-size: 0.8rem;">✅ Todas as máquinas saudáveis.</p>';
                } else {
                    data.printer_summary.needing_maintenance.forEach(name => {
                        maintList.innerHTML += `<div style="color: var(--secondary); font-size: 0.85rem; margin-bottom: 0.4rem;">⚠️ ${name} precisa de revisão!</div>`;
                    });
                }
            }

            // Atividades Recentes
            const activityList = document.getElementById('recent-activities-list');
            if (activityList) {
                activityList.innerHTML = '';
                data.recent_activities.forEach(act => {
                    const date = new Date(act.time).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
                    activityList.innerHTML += `
                                <div style="margin-bottom: 0.8rem; padding-left: 0.5rem; border-left: 2px solid ${act.type === 'failure' ? 'var(--secondary)' : 'var(--primary)'}">
                                    <div style="color: var(--text-muted); font-size: 0.7rem;">${date}</div>
                                    <div style="font-weight: 500;">${act.msg}</div>
                                </div>
                            `;
                });
            }

            // Alertas de Estoque
            const lowStockList = document.getElementById('low-stock-list');
            if (lowStockList) {
                lowStockList.innerHTML = '';
                if (data.low_stock_items.length === 0) {
                    lowStockList.innerHTML = '<p style="color: var(--success); font-size: 0.9rem;">✅ Materiais em dia.</p>';
                } else {
                    data.low_stock_items.forEach(item => {
                        lowStockList.innerHTML += `
                                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border); font-size: 0.85rem;">
                                        <span>⚠️ ${item.name}</span> <b style="color: var(--secondary);">${item.current}${item.unit}</b>
                                    </div>`;
                    });
                }
            }

            renderSalesChart(data.sales_evolution);
            renderTopProjectsChart(data.top_projects);
        }
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
    }
}

let salesChart = null;
function renderSalesChart(evoData) {
    const ctx = document.getElementById('salesChart').getContext('2d');
    if (salesChart) salesChart.destroy();

    salesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: evoData.map(d => d.month),
            datasets: [
                {
                    label: 'Faturamento',
                    data: evoData.map(d => d.revenue),
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Custos',
                    data: evoData.map(d => d.cost),
                    borderColor: '#db2777',
                    backgroundColor: 'rgba(219, 39, 119, 0.1)',
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#94a3b8', font: { family: 'Outfit' } } }
            },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
            }
        }
    });
}

let topProjectsChart = null;
function renderTopProjectsChart(topData) {
    const ctx = document.getElementById('topProjectsChart').getContext('2d');
    if (topProjectsChart) topProjectsChart.destroy();

    topProjectsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topData.map(d => d.name),
            datasets: [{
                label: 'Quantidade Vendida',
                data: topData.map(d => d.count),
                backgroundColor: [
                    'rgba(56, 189, 248, 0.6)',
                    'rgba(219, 39, 119, 0.6)',
                    'rgba(168, 85, 247, 0.6)'
                ],
                borderColor: [
                    '#38bdf8',
                    '#db2777',
                    '#a855f7'
                ],
                borderWidth: 1,
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
                y: { grid: { display: false }, ticks: { color: '#94a3b8' } }
            }
        }
    });
}

async function loadConfigs() {
    try {
        const response = await apiFetch('/configs');
        if (response.ok) {
            const data = await response.json();
            if (document.getElementById('cfg-filament')) document.getElementById('cfg-filament').value = data.filament_price_kg || '';
            if (document.getElementById('cfg-work')) document.getElementById('cfg-work').value = data.hour_work_price || '';

            if (document.getElementById('cfg-owner-name')) document.getElementById('cfg-owner-name').value = data.owner_name || '';
            if (document.getElementById('cfg-owner-role')) document.getElementById('cfg-owner-role').value = data.owner_role || '';
            if (document.getElementById('cfg-owner-phone')) document.getElementById('cfg-owner-phone').value = data.owner_phone || '';
            if (document.getElementById('cfg-pix-key')) document.getElementById('cfg-pix-key').value = data.pix_key || '';
        }
    } catch (error) {
        console.error('Erro ao carregar configs:', error);
    }
}

async function updateConfigs() {
    const filament = parseFloat(document.getElementById('cfg-filament').value);
    const work = parseFloat(document.getElementById('cfg-work').value);

    const ownerName = document.getElementById('cfg-owner-name').value;
    const ownerRole = document.getElementById('cfg-owner-role').value;
    const ownerPhone = document.getElementById('cfg-owner-phone').value;
    const pixKey = document.getElementById('cfg-pix-key').value;

    const payload = [
        { key: 'filament_price_kg', value: filament },
        { key: 'hour_work_price', value: work },
        { key: 'owner_name', string_value: ownerName },
        { key: 'owner_role', string_value: ownerRole },
        { key: 'owner_phone', string_value: ownerPhone },
        { key: 'pix_key', string_value: pixKey }
    ];

    try {
        const response = await apiFetch('/configs', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            showToast('Configurações atualizadas!');
        } else {
            showToast('Erro ao atualizar configurações.', 'error');
        }
    } catch (error) {
        showToast('Erro de conexão.', 'error');
    }
}
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const main = document.getElementById('main-content');
    const footer = document.getElementById('sidebar-footer');

    sidebar.classList.toggle('collapsed');
    main.classList.toggle('expanded');

    if (sidebar.classList.contains('collapsed')) {
        footer.style.display = 'none';
    } else {
        footer.style.display = 'block';
    }
}

function toggleMobileMenu() {
    const nav = document.getElementById('mobile-nav');
    nav.classList.toggle('show');
}

let kanbanInterval = null;

function showTab(tabId, el) {
    // Fechar menu mobile se estiver aberto
    const nav = document.getElementById('mobile-nav');
    if (nav) nav.classList.remove('show');

    // Parar intervalo anterior se houver
    if (kanbanInterval) {
        clearInterval(kanbanInterval);
        kanbanInterval = null;
    }

    if (tabId === 'inventory-tab' || tabId === 'settings') {
        if (userRole !== 'admin' && userRole !== 'DEV') {
            showToast('Acesso negado: Apenas Administradores.', 'error');
            return;
        }
    }
    document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
    document.getElementById('tab-' + tabId).style.display = 'block';

    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    el.classList.add('active');

    const userName = localStorage.getItem('ammma_user') || 'Gerente';

    if (tabId === 'settings') {
        loadUsers();
        document.getElementById('tab-title').innerText = 'Configurações do Sistema';
        document.getElementById('tab-subtitle').innerText = 'Gerencie usuários e parâmetros do sistema.';
    } else if (tabId === 'kanban-tab') {
        loadKanban();
        // Iniciar atualização automática de 35s
        kanbanInterval = setInterval(loadKanban, 35000);
        document.getElementById('tab-title').innerText = 'Painel de Produção';
        document.getElementById('tab-subtitle').innerText = 'Acompanhe o fluxo de trabalho em tempo real.';
    } else if (tabId === 'inventory-tab') {
        loadInventory();
        document.getElementById('tab-title').innerText = 'Inventário de Materiais';
        document.getElementById('tab-subtitle').innerText = 'Controle seu estoque de filamentos e insumos.';
    } else if (tabId === 'coupons-tab') {
        loadCoupons();
        document.getElementById('tab-title').innerText = 'Gestão de Cupons';
        document.getElementById('tab-subtitle').innerText = 'Crie códigos de desconto para seus orçamentos.';
    } else if (tabId === 'calculator-tab') {
        document.getElementById('tab-title').innerText = 'Calculadora de Orçamentos';
        document.getElementById('tab-subtitle').innerText = 'Estime custos e preços de venda rapidamente.';
    } else if (tabId === 'printers-tab') {
        loadPrinters();
        document.getElementById('tab-title').innerText = 'Monitoramento de Impressoras';
        document.getElementById('tab-subtitle').innerText = 'Gerencie suas máquinas e acompanhe as horas de uso.';
    } else if (tabId === 'orders-tab') {
        loadOrders();
        document.getElementById('tab-title').innerText = 'Gestão de Pedidos';
        document.getElementById('tab-subtitle').innerText = 'Visualize e gerencie todos os orçamentos salvos.';
    } else if (tabId === 'gallery-tab') {
        loadGallery();
        document.getElementById('tab-title').innerText = 'Galeria de Projetos';
        document.getElementById('tab-subtitle').innerText = 'Memória visual das suas criações 3D.';
    } else if (tabId === 'clients-tab') {
        loadClients();
        document.getElementById('tab-title').innerText = 'Base de Clientes';
        document.getElementById('tab-subtitle').innerText = 'Gerencie seus contatos e clientes frequentes.';
    } else if (tabId === 'finance-tab') {
        loadExpenses();
        document.getElementById('tab-title').innerText = 'Fluxo Financeiro';
        document.getElementById('tab-subtitle').innerText = 'Controle de despesas fixas da oficina.';
    } else if (tabId === 'agenda-tab') {
        loadAgenda();
        document.getElementById('tab-title').innerText = 'Agenda de Produção';
        document.getElementById('tab-subtitle').innerText = 'Prazos e entregas em ordem cronológica.';
    } else {
        loadStats(); // Recarregar ao voltar pro dashboard
        document.getElementById('tab-title').innerHTML = `Bem-vindo, <span style="color: var(--primary);">${userName}</span>`;
        document.getElementById('tab-subtitle').innerText = 'Controle de produção e orçamentos automatizados.';
    }
}


const STATUS_FLOW = ['Orçamento', 'Aprovado', 'Fila', 'Imprimindo', 'Pronto'];

const STATUS_MAP = {
    'Orçamento': { label: 'Em Análise', icon: '⏳', class: 'status-orcamento' },
    'Aprovado': { label: 'Aprovado', icon: '✅', class: 'status-aprovado' },
    'Fila': { label: 'Na Fila', icon: '📋', class: 'status-fila' },
    'Imprimindo': { label: 'Imprimindo', icon: '⚙️', class: 'status-imprimindo' },
    'Pronto': { label: 'Concluído', icon: '📦', class: 'status-pronto' }
};

let lastResult = null;

async function calculate(event) {
    const btn = event.target;
    btn.classList.add('loading');

    const weight = parseFloat(document.getElementById('weight').value);
    const time = parseFloat(document.getElementById('time').value);
    const labor = parseFloat(document.getElementById('labor').value);
    const consumables = parseFloat(document.getElementById('packaging').value);
    const coupon = document.getElementById('coupon-code').value;

    try {
        const response = await apiFetch('/calculate', {
            method: 'POST',
            body: JSON.stringify({
                weight_g: weight,
                time_hours: time,
                labor_hours: labor,
                consumables: consumables,
                coupon_code: coupon
            })
        });

        if (response.ok) {
            const data = await response.json();
            lastResult = data;
            document.getElementById('res-cost').innerText = `R$ ${data.final_cost.toFixed(2)}`;
            document.getElementById('res-sale').innerText = `R$ ${data.suggested_sale.toFixed(2)}`;

            if (data.discount_applied > 0) {
                document.getElementById('discount-row').style.display = 'flex';
                document.getElementById('res-discount').innerText = `- R$ ${data.discount_applied.toFixed(2)}`;
            } else {
                document.getElementById('discount-row').style.display = 'none';
            }

            const panel = document.getElementById('results-panel');
            panel.style.display = 'block';
            setTimeout(() => panel.style.opacity = '1', 10);
            document.getElementById('btn-save').style.display = 'block';
        }
    } finally {
        btn.classList.remove('loading');
    }
}

async function saveOrder() {
    if (!lastResult) return;

    const projectName = document.getElementById('project-name').value;
    const clientName = document.getElementById('client-name').value;
    const clientId = document.getElementById('client-select').value;
    const deliveryDate = document.getElementById('delivery-date').value;

    try {
        const response = await apiFetch('/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_name: projectName,
                client_name: clientName,
                client_id: clientId ? parseInt(clientId) : null,
                delivery_date: deliveryDate || null,
                weight_g: lastResult.weight_g || 0,
                time_hours: lastResult.time_hours || 0,
                final_cost: lastResult.final_cost,
                suggested_price: lastResult.suggested_sale,
                original_price: lastResult.suggested_sale + lastResult.discount_applied,
                discount_amount: lastResult.discount_applied,
                notes: `Material: PLA (Ácido Poliláctico)`
            })
        });

        // Backend note logic:
        // total_cost = cost_material + cost_machine + cost_work + data.consumables + data.packaging
        // total_cost *= 1.10 # 10% de margem de segurança
        // suggested_sale = total_cost * 2

        if (response.ok) {
            showToast('Pedido salvo com sucesso!');
            loadOrders();
            loadStats();
        } else {
            showToast('Erro ao salvar pedido.', 'error');
        }
    } catch (error) {
        showToast('Erro ao conectar com o servidor.', 'error');
    }
}

let allOrders = [];
let currentFilter = 'all';

async function loadOrders() {
    try {
        const response = await apiFetch('/orders');
        allOrders = await response.json();
        renderOrders();
    } catch (error) {
        console.error('Erro ao carregar pedidos:', error);
    }
}

function filterOrders(status) {
    currentFilter = status;

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-status') === status);
    });

    renderOrders();
}

function renderOrders() {
    const tbody = document.getElementById('orders-table-body');
    tbody.innerHTML = '';

    const filteredOrders = currentFilter === 'all'
        ? allOrders
        : allOrders.filter(o => o.status === currentFilter);

    filteredOrders.forEach(order => {
        const currentStatus = STATUS_MAP[order.status] || STATUS_MAP['Orçamento'];
        const tr = document.createElement('tr');
        const projectDisplay = order.project_name ? escapeHTML(order.project_name) : '<i style="color: var(--text-muted);">Sem nome</i>';
        tr.innerHTML = `
                    <td>#${order.id}</td>
                    <td style="font-weight: 600; color: var(--primary);">${escapeHTML(order.client_name) || 'Consumidor Final'}</td>
                    <td>${projectDisplay}</td>
                    <td style="color: var(--text-muted);">R$ ${order.final_cost.toFixed(2)}</td>
                    <td style="font-weight: bold; color: var(--success);">R$ ${order.suggested_price.toFixed(2)}</td>
                    <td>
                        <div style="font-size: 0.85rem; font-weight: 600; color: ${order.payment_status === 'Pago' ? 'var(--success)' : (order.payment_status === 'Parcial' ? 'var(--accent)' : 'var(--secondary)')};">${order.payment_status || 'Pendente'}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">R$ ${(order.paid_amount || 0).toFixed(2)} / R$ ${order.suggested_price.toFixed(2)}</div>
                    </td>
                    <td style="display: flex; gap: 0.5rem; align-items: center;">
                        <div class="status-dropdown" id="dropdown-${order.id}">
                            <div class="status-current ${currentStatus.class}" onclick="advanceStatus(${order.id}, '${order.status}')" title="Clique para avançar status">
                                <span class="status-text">${currentStatus.icon} ${currentStatus.label}</span>
                                <span class="status-arrow" onclick="toggleDropdown(${order.id}, event)">▾</span>
                            </div>
                            <div class="status-menu">
                                ${Object.keys(STATUS_MAP).map(s => `
                                    <div class="status-option" onclick="updateOrderStatus(${order.id}, '${s}')">
                                        ${STATUS_MAP[s].icon} ${STATUS_MAP[s].label}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        <button class="btn-ghost" onclick="openPaymentModal(${order.id}, ${order.paid_amount || 0}, ${order.suggested_price})" title="Registrar Pagamento" style="padding: 0.3rem 0.6rem; border-radius: 0.5rem;">💸</button>
                        <button class="btn-ghost" onclick="downloadOrderPDF(${order.id})" title="Gerar PDF" style="padding: 0.3rem 0.6rem; border-radius: 0.5rem;">📄</button>
                        <button class="btn-ghost" onclick="openFailureModal(${order.id})" title="Registrar Falha" style="padding: 0.3rem 0.6rem; border-radius: 0.5rem;">🗑️</button>
                    </td>
                `;
        tbody.appendChild(tr);
    });
}

async function loadKanban() {
    try {
        const response = await apiFetch('/orders');
        const orders = await response.json();
        renderKanban(orders);
    } catch (error) {
        console.error('Erro ao carregar Kanban:', error);
    }
}

function renderKanban(orders) {
    const cols = {
        budget: { el: document.getElementById('cards-budget'), count: document.getElementById('count-budget'), items: [] },
        todo: { el: document.getElementById('cards-todo'), count: document.getElementById('count-todo'), items: [] },
        queue: { el: document.getElementById('cards-queue'), count: document.getElementById('count-queue'), items: [] },
        production: { el: document.getElementById('cards-production'), count: document.getElementById('count-production'), items: [] },
        done: { el: document.getElementById('cards-done'), count: document.getElementById('count-done'), items: [] }
    };

    Object.values(cols).forEach(c => {
        if (c.el) {
            c.el.innerHTML = '';
            c.items = [];
        }
    });

    orders.forEach(o => {
        if (o.status === 'Orçamento') cols.budget.items.push(o);
        else if (o.status === 'Aprovado') cols.todo.items.push(o);
        else if (o.status === 'Fila') cols.queue.items.push(o);
        else if (o.status === 'Imprimindo') cols.production.items.push(o);
        else if (o.status === 'Pronto') cols.done.items.push(o);
    });

    Object.keys(cols).forEach(key => {
        const col = cols[key];
        if (col.count) col.count.innerText = col.items.length;

        col.items.forEach(o => {
            const card = document.createElement('div');
            card.className = 'kanban-card';
            card.onclick = () => {
                showToast(`Pedido #${o.id}: ${o.project_name || 'Projeto sem nome'}`);
            };

            const deliveryDate = o.delivery_date ? new Date(o.delivery_date).toLocaleDateString('pt-BR') : 'Sem prazo';
            const createdAt = new Date(o.created_at).toLocaleDateString('pt-BR');

            let deliveryClass = '';
            if (o.delivery_date) {
                const diff = new Date(o.delivery_date) - new Date();
                if (diff < (1000 * 60 * 60 * 24 * 3)) deliveryClass = 'delivery-urgent';
            }

            card.innerHTML = `
                        <div class="client-name">${escapeHTML(o.client_name) || 'Consumidor Final'}</div>
                        <div class="project-title">${escapeHTML(o.project_name) || 'Sem nome'}</div>
                        <div class="card-info">
                            <div>📅 Pedido: ${createdAt}</div>
                            <div class="${deliveryClass}">🕒 Entrega: ${deliveryDate}</div>
                        </div>
                        <div class="price-tag">R$ ${o.suggested_price.toFixed(2)}</div>
                    `;
            if (col.el) col.el.appendChild(card);
        });
    });
}

// --- GESTÃO DE IMPRESSORAS (JS) ---

async function addPrinter() {
    const name = document.getElementById('prn-name').value;
    const model = document.getElementById('prn-model').value;
    const maint = document.getElementById('prn-maintenance').value;

    if (!name) return showToast('Nome é obrigatório', 'error');

    try {
        const response = await apiFetch('/printers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, model, maintenance_alert_hours: parseFloat(maint) })
        });
        if (response.ok) {
            showToast('Impressora cadastrada!');
            loadPrinters();
        }
    } catch (error) { showToast('Erro ao cadastrar', 'error'); }
}

async function loadPrinters() {
    try {
        const response = await apiFetch('/printers');
        const printers = await response.json();
        const tbody = document.getElementById('printers-table-body');
        tbody.innerHTML = '';

        printers.forEach(p => {
            const tr = document.createElement('tr');
            const needsMaint = p.total_hours >= p.maintenance_alert_hours;
            tr.innerHTML = `
                        <td><b>${escapeHTML(p.name)}</b><br><small>${escapeHTML(p.model)}</small></td>
                        <td>
                            <select onchange="updatePrinterStatus(${p.id}, this.value)" style="padding: 0.4rem; border-radius: 0.4rem; background: var(--bg-dark); color: white; border: 1px solid var(--border);">
                                <option value="Disponível" ${p.status === 'Disponível' ? 'selected' : ''}>🟢 Disponível</option>
                                <option value="Ocupada" ${p.status === 'Ocupada' ? 'selected' : ''}>🔵 Ocupada</option>
                                <option value="Manutenção" ${p.status === 'Manutenção' ? 'selected' : ''}>🔴 Manutenção</option>
                            </select>
                        </td>
                        <td style="${needsMaint ? 'color: var(--secondary); font-weight: bold;' : ''}">
                            ${p.total_hours.toFixed(1)}h / ${p.maintenance_alert_hours}h
                        </td>
                        <td>
                            <button onclick="addPrinterHours(${p.id})" class="btn-ghost" style="padding: 0.3rem 0.6rem;">➕ Horas</button>
                            <button onclick="deletePrinter(${p.id})" class="btn-ghost" style="color: var(--secondary); padding: 0.3rem 0.6rem;">🗑️</button>
                        </td>
                    `;
            tbody.appendChild(tr);
        });
    } catch (error) { console.error(error); }
}

async function updatePrinterStatus(id, status) {
    await apiFetch(`/printers/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
    });
    showToast('Status da impressora atualizado');
    loadStats();
}

async function addPrinterHours(id) {
    const hours = await showModal('Adicionar Horas', 'Quantas horas de uso deseja adicionar à máquina?', true);
    if (hours && !isNaN(parseFloat(hours))) {
        await apiFetch(`/printers/${id}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ add_hours: parseFloat(hours) })
        });
        loadPrinters();
        loadStats();
    }
}

async function deletePrinter(id) {
    const confirm = await showModal('Excluir Impressora', 'Tem certeza que deseja remover esta máquina do sistema?');
    if (confirm) {
        await apiFetch(`/printers/${id}`, { method: 'DELETE' });
        showToast('Impressora removida!');
        loadPrinters();
    }
}

// --- GESTÃO DE FALHAS (JS) ---
let currentFailureOrderId = null;

function openFailureModal(orderId = null) {
    currentFailureOrderId = orderId;
    document.getElementById('failure-modal').style.display = 'flex';
}

function closeFailureModal() {
    document.getElementById('failure-modal').style.display = 'none';
}

async function confirmLogFailure() {
    const weight = document.getElementById('fail-weight').value;
    const reason = document.getElementById('fail-reason').value;

    if (!weight || !reason) return showToast('Preencha os dados', 'error');

    try {
        await apiFetch('/failures', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                order_id: currentFailureOrderId,
                weight_wasted_g: parseFloat(weight),
                reason: reason
            })
        });
        showToast('Falha registrada e custo descontado.');
        closeFailureModal();
        loadStats();
    } catch (error) { showToast('Erro ao registrar', 'error'); }
}

async function advanceStatus(id, currentStatus) {
    const currentIndex = STATUS_FLOW.indexOf(currentStatus);
    if (currentIndex >= 0 && currentIndex < STATUS_FLOW.length - 1) {
        const nextStatus = STATUS_FLOW[currentIndex + 1];
        // Feedback visual imediato
        const el = document.querySelector(`#dropdown-${id} .status-current`);
        if (el) el.style.opacity = '0.5';

        await updateOrderStatus(id, nextStatus);
    } else if (currentIndex === STATUS_FLOW.length - 1) {
        showToast('Pedido já concluído!', 'info');
    }
}

function toggleDropdown(id, event) {
    event.stopPropagation();
    const el = document.getElementById(`dropdown-${id}`);
    const isActive = el.classList.contains('active');

    // Fechar todos outros
    document.querySelectorAll('.status-dropdown').forEach(d => d.classList.remove('active'));

    if (!isActive) el.classList.add('active');
}

// Fechar dropdown ao clicar fora
window.addEventListener('click', () => {
    document.querySelectorAll('.status-dropdown').forEach(d => d.classList.remove('active'));
});

async function updateOrderStatus(orderId, newStatus) {
    // Se o status for "Pronto", interceptar para dar baixa no estoque
    if (newStatus === 'Pronto') {
        openConsumeModal(orderId);
        return;
    }
    // Se o status for "Imprimindo", interceptar para escolher impressora
    if (newStatus === 'Imprimindo') {
        openPrinterAssignModal(orderId);
        return;
    }
    try {
        const response = await apiFetch('/orders/' + orderId + '/status', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });

        if (response.ok) {
            showToast('Status atualizado!');
            loadOrders();
            loadStats();
        } else {
            showToast('Erro ao atualizar status.', 'error');
        }
    } catch (error) {
        showToast('Erro ao conectar servidor.', 'error');
    }
}

// --- GESTÃO DE USUÁRIOS (JS) ---

async function createUser() {
    const user = document.getElementById('new-username').value;
    const pass = document.getElementById('new-password').value;
    const role = document.getElementById('new-role').value;

    if (!user || !pass) {
        showToast('Preencha usuário e senha.', 'error');
        return;
    }

    try {
        const response = await apiFetch('/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass, role: role })
        });

        if (response.ok) {
            showToast('Usuário criado com sucesso!');
            document.getElementById('new-username').value = '';
            document.getElementById('new-password').value = '';
            loadUsers();
        } else {
            const err = await response.json();
            showToast(err.detail, 'error');
        }
    } catch (error) {
        showToast('Erro ao criar usuário.', 'error');
    }
}

async function loadUsers() {
    try {
        const response = await apiFetch('/users');
        const users = await response.json();

        const tbody = document.getElementById('users-table-body');
        tbody.innerHTML = '';

        users.forEach(user => {
            const statusClass = user.is_active ? 'status-success' : 'status-pending';
            const statusText = user.is_active ? 'Ativo' : 'Inativo';
            const btnIcon = user.is_active ? '🚫 Desativar' : '✅ Ativar';

            let roleDisplay = '👤 Colaborador';
            if (user.role === 'admin') roleDisplay = '⭐ Admin';
            if (user.role === 'DEV') roleDisplay = '💻 DEV';

            const isMaster = user.username === 'admin';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                        <td>#${user.id}</td>
                        <td>${user.username}</td>
                        <td>${roleDisplay}</td>
                        <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                        <td>
                            ${!isMaster ? `
                                <button onclick="toggleRole('${user.username}')" style="background: none; border: none; color: var(--text-main); cursor: pointer; margin-right: 1rem;">🔄 Alternar Cargo</button>
                                <button onclick="toggleStatus('${user.username}')" style="background: none; border: none; color: var(--accent); cursor: pointer; margin-right: 1rem;">${btnIcon}</button>
                                <button onclick="resetPassword('${user.username}')" style="background: none; border: none; color: var(--primary); cursor: pointer; margin-right: 1rem;">🔑 Alterar Senha</button>
                                <button onclick="deleteUser('${user.username}')" style="background: none; border: none; color: var(--secondary); cursor: pointer;">🗑️ Excluir</button>
                            ` : '<span style="color: var(--text-muted); font-size: 0.8rem;">[Conta Mestra Protegida]</span>'}
                        </td>
                    `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar usuários:', error);
    }
}

async function toggleRole(username) {
    try {
        const response = await apiFetch(`/users/${username}/role`, { method: 'PATCH' });
        if (response.ok) {
            const data = await response.json();
            showToast(data.message);
            loadUsers();
        } else {
            const err = await response.json();
            showToast(err.detail, 'error');
        }
    } catch (error) {
        showToast('Erro ao alterar cargo.', 'error');
    }
}

async function toggleStatus(username) {
    try {
        const response = await apiFetch(`/users/${username}/status`, { method: 'PATCH' });
        if (response.ok) {
            const data = await response.json();
            showToast(data.message);
            loadUsers();
        } else {
            const err = await response.json();
            showToast(err.detail, 'error');
        }
    } catch (error) {
        showToast('Erro ao alterar status.', 'error');
    }
}

// --- MODAL SYSTEM ---
let modalResolve = null;

function showModal(title, msg, isPrompt = false) {
    document.getElementById('modal-title').innerText = title;
    document.getElementById('modal-msg').innerText = msg;
    document.getElementById('modal-overlay').style.display = 'flex';
    document.getElementById('modal-input-container').style.display = isPrompt ? 'block' : 'none';
    if (isPrompt) document.getElementById('modal-input').value = '';

    return new Promise((resolve) => {
        modalResolve = resolve;
    });
}

function closeModal(result) {
    document.getElementById('modal-overlay').style.display = 'none';
    if (modalResolve) {
        if (document.getElementById('modal-input-container').style.display === 'block') {
            modalResolve(result ? document.getElementById('modal-input').value : null);
        } else {
            modalResolve(result);
        }
    }
}

async function resetPassword(username) {
    const newPass = await showModal('Resetar Senha', `Digite a nova senha para ${username}:`, true);
    if (!newPass) return;

    try {
        const response = await apiFetch(`/users/${username}/password`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_password: newPass })
        });

        if (response.ok) {
            showToast(`Senha de ${username} alterada!`);
        } else {
            const err = await response.json();
            showToast(err.detail, 'error');
        }
    } catch (error) {
        showToast('Erro ao alterar senha.', 'error');
    }
}

async function deleteUser(username) {
    const confirm = await showModal('Excluir Usuário', `Tem certeza que deseja excluir o usuário ${username}?`);
    if (!confirm) return;

    try {
        const response = await apiFetch(`/users/${username}`, { method: 'DELETE' });
        if (response.ok) {
            showToast('Usuário removido!');
            loadUsers();
        } else {
            const err = await response.json();
            showToast(err.detail, 'error');
        }
    } catch (error) {
        showToast('Erro ao deletar usuário.', 'error');
    }
}

function logout() {
    localStorage.removeItem('ammma_token');
    localStorage.removeItem('ammma_role');
    localStorage.removeItem('ammma_user');
    window.location.href = 'login.html';
}

// --- CUPONS (JS) ---

async function createCoupon() {
    const codeEl = document.getElementById('cp-code');
    const valueEl = document.getElementById('cp-value');
    const typeEl = document.getElementById('cp-type');

    const code = codeEl.value.toUpperCase().trim();
    const type = typeEl.value;
    const value = parseFloat(valueEl.value);

    if (!code || isNaN(value)) {
        showToast('Preencha código e valor corretamente.', 'error');
        return;
    }

    try {
        const response = await apiFetch('/discounts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, type, value })
        });

        if (response.ok) {
            showToast('Cupom criado com sucesso!');
            codeEl.value = '';
            valueEl.value = '';
            loadCoupons();
        } else {
            const err = await response.json();
            showToast(err.detail || 'Erro ao criar cupom.', 'error');
        }
    } catch (error) {
        console.error('Erro na criação:', error);
        showToast('Falha na comunicação com o servidor.', 'error');
    }
}

async function loadCoupons() {
    try {
        const response = await apiFetch('/discounts');
        const coupons = await response.json();
        const tbody = document.getElementById('coupons-table-body');
        tbody.innerHTML = '';

        coupons.forEach(c => {
            const typeDisplay = c.type === 'percentage' ? 'Porcentagem (%)' : 'Fixo (R$)';
            const valueDisplay = c.type === 'percentage' ? `${c.value}%` : `R$ ${c.value.toFixed(2)}`;

            const tr = document.createElement('tr');
            tr.innerHTML = `
                        <td style="font-weight: bold; color: var(--primary);">${c.code}</td>
                        <td>${typeDisplay}</td>
                        <td style="color: var(--success); font-weight: bold;">${valueDisplay}</td>
                        <td>
                            <button onclick="deleteCoupon(${c.id})" style="background: none; border: none; color: var(--secondary); cursor: pointer;">🗑️ Excluir</button>
                        </td>
                    `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar cupons:', error);
    }
}

async function deleteCoupon(id) {
    const confirm = await showModal('Excluir Cupom', 'Tem certeza que deseja remover este código de desconto?');
    if (!confirm) return;

    try {
        const response = await apiFetch(`/discounts/${id}`, { method: 'DELETE' });
        if (response.ok) {
            showToast('Cupom removido!');
            loadCoupons();
        }
    } catch (error) {
        showToast('Erro ao excluir cupom.', 'error');
    }
}

// --- ATRIBUIÇÃO DE IMPRESSORA ---

let assignOrderId = null;

async function openPrinterAssignModal(orderId) {
    assignOrderId = orderId;
    const order = allOrders.find(o => o.id === orderId);
    if (!order) return;

    document.getElementById('assign-project-name').innerText = order.project_name || 'Sem nome';

    try {
        const response = await apiFetch('/printers');
        const printers = await response.json();
        const select = document.getElementById('assign-printer-id');
        select.innerHTML = '';

        const availablePrinters = printers.filter(p => p.status === 'Disponível');

        if (availablePrinters.length === 0) {
            const option = document.createElement('option');
            option.value = "";
            option.innerText = "❌ Nenhuma impressora disponível";
            select.appendChild(option);
        } else {
            availablePrinters.forEach(p => {
                const option = document.createElement('option');
                option.value = p.id;
                option.innerText = `${p.name} (${p.model})`;
                select.appendChild(option);
            });
        }

        document.getElementById('printer-assign-modal').style.display = 'flex';
    } catch (error) {
        showToast('Erro ao carregar impressoras.', 'error');
    }
}

function closePrinterAssignModal() {
    document.getElementById('printer-assign-modal').style.display = 'none';
    assignOrderId = null;
}

async function confirmPrinterAssign() {
    const printerId = document.getElementById('assign-printer-id').value;
    if (!printerId) {
        showToast('Selecione uma impressora válida.', 'error');
        return;
    }

    try {
        const response = await apiFetch(`/orders/${assignOrderId}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                status: 'Imprimindo',
                printer_id: parseInt(printerId)
            })
        });

        if (response.ok) {
            showToast('Impressão iniciada!');
            closePrinterAssignModal();
            loadOrders();
            loadStats();
        } else {
            showToast('Erro ao iniciar impressão.', 'error');
        }
    } catch (error) {
        showToast('Erro de conexão.', 'error');
    }
}

// --- FINALIZAÇÃO COM BAIXA DE ESTOQUE ---

let pendingOrderId = null;

async function openConsumeModal(order_id) {
    pendingOrderId = order_id;
    const order = allOrders.find(o => o.id === order_id);
    if (!order) return;

    document.getElementById('consume-project-name').innerText = order.project_name;
    document.getElementById('consume-weight').value = order.weight_g;

    // Carregar materiais do inventário
    try {
        const response = await apiFetch('/inventory');
        const materials = await response.json();
        const select = document.getElementById('consume-material-id');
        select.innerHTML = '';

        materials.filter(m => m.category === 'Filamento').forEach(m => {
            const option = document.createElement('option');
            option.value = m.id;
            option.innerText = `${m.material_name} ${m.color} (${m.brand}) - Saldo: ${m.weight_g}g`;
            select.appendChild(option);
        });

        document.getElementById('inventory-consume-modal').style.display = 'flex';
    } catch (error) {
        showToast('Erro ao carregar materiais.', 'error');
    }
}

function closeConsumeModal() {
    document.getElementById('inventory-consume-modal').style.display = 'none';
    pendingOrderId = null;
}

async function confirmFinishOrder() {
    const materialId = document.getElementById('consume-material-id').value;
    const weightToSubtract = parseFloat(document.getElementById('consume-weight').value);

    if (!materialId || isNaN(weightToSubtract)) {
        showToast('Selecione o material e o peso.', 'error');
        return;
    }

    const btn = document.getElementById('btn-confirm-finish');
    btn.disabled = true;
    btn.innerText = 'Processando...';

    try {
        // 1. Dar baixa no inventário através do novo endpoint /consume
        const invResponse = await apiFetch('/inventory');
        const inventory = await invResponse.json();
        const item = inventory.find(i => i.id == materialId);

        if (item) {
            await apiFetch(`/inventory/${materialId}/consume`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ weight_g: weightToSubtract })
            });
        }

        // 2. Atualizar status do pedido (agora forçando via bypass interno se necessário, ou apenas chamando a API normal)
        const response = await apiFetch(`/orders/${pendingOrderId}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'Pronto' })
        });

        if (response.ok) {
            const order = allOrders.find(o => o.id === pendingOrderId);
            const net = order.suggested_price - order.final_cost;

            const summaryMsg = `Pedido #${pendingOrderId} Concluído!\n` +
                `Custo Bruto: R$ ${order.final_cost.toFixed(2)}\n` +
                `Valor Total: R$ ${order.suggested_price.toFixed(2)}\n` +
                `Líquido: R$ ${net.toFixed(2)}`;

            showToast(summaryMsg);
            closeConsumeModal();
            loadOrders();
            loadStats();
        }
    } catch (error) {
        showToast('Erro ao finalizar pedido.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerText = 'Finalizar e Dar Baixa';
    }
}

// --- INVENTÁRIO (JS) ---

function updateInvUnitHint() {
    const cat = document.getElementById('inv-category').value;
    const unit = document.getElementById('inv-unit');
    const label = document.getElementById('inv-weight-label');

    if (cat === 'Filamento') {
        unit.value = 'g';
        label.innerText = 'Peso Atual (g)';
    } else if (cat === 'Embalagem') {
        unit.value = 'un';
        label.innerText = 'Quantidade (un)';
    } else {
        label.innerText = 'Quantidade / Medida';
    }
}

async function loadInventory() {
    try {
        const response = await apiFetch('/inventory');
        const items = await response.json();
        const tbody = document.getElementById('inventory-table-body');
        tbody.innerHTML = '';

        items.forEach(item => {
            const isLow = item.weight_g <= item.min_weight_g;
            const weightColor = isLow ? 'var(--secondary)' : 'var(--text-main)';
            const weightLabel = isLow ? '⚠️' : '';

            let catIcon = '🧵';
            if (item.category === 'Embalagem') catIcon = '📦';
            if (item.category === 'Insumos') catIcon = '🛠️';

            // Cálculos Financeiros
            const vUnit = (item.price_paid && item.initial_amount) ? (item.price_paid / item.initial_amount) : 0;
            const vUnitStr = vUnit.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 3 });
            const vTotalStr = (item.price_paid || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

            // Formatação de Estoque
            let stockDisplay = `${item.weight_g}${item.unit}`;
            if (item.unit === 'g' && item.category === 'Filamento') {
                const kg = (item.weight_g / 1000).toFixed(2);
                stockDisplay = `${item.weight_g}g <br><small style="opacity:0.6;">(${kg}kg)</small>`;
            }

            const tr = document.createElement('tr');
            tr.innerHTML = `
                        <td>
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span style="font-size: 1.2rem;">${catIcon}</span>
                                <div>
                                    <span style="font-weight: 600;">${item.material_name}</span><br>
                                    <small style="color: var(--text-muted);">${item.color} | ${item.brand || '-'}</small>
                                </div>
                            </div>
                        </td>
                        <td style="font-family: monospace; color: var(--primary); font-weight: bold;">
                            ${vUnitStr} <small style="font-weight: normal; color: var(--text-muted);">/${item.unit}</small>
                        </td>
                        <td style="color: var(--text-main);">${vTotalStr}</td>
                        <td style="color: ${weightColor}; font-weight: bold;">
                            ${stockDisplay} <span style="font-size: 0.7rem;">${weightLabel}</span>
                        </td>
                        <td>
                            <button onclick="updateWeight(${item.id}, ${item.weight_g}, '${item.unit}')" style="background: none; border: none; color: var(--primary); cursor: pointer; margin-right: 0.5rem;" title="Ajustar Estoque">⚖️</button>
                            <button onclick="deleteInventory(${item.id})" style="background: none; border: none; color: var(--secondary); cursor: pointer;" title="Remover">🗑️</button>
                        </td>
                    `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao carregar inventário:', error);
    }
}

async function addInventory() {
    const cat = document.getElementById('inv-category').value;
    const unit = document.getElementById('inv-unit').value;
    const material = document.getElementById('inv-material').value;
    const color = document.getElementById('inv-color').value;
    const brand = document.getElementById('inv-brand').value;
    const weight = parseFloat(document.getElementById('inv-weight').value);
    const price = parseFloat(document.getElementById('inv-price').value);

    if (!material || isNaN(weight)) {
        showToast('Preencha o nome e a quantidade.', 'error');
        return;
    }

    try {
        const response = await apiFetch('/inventory', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                category: cat,
                unit: unit,
                material_name: material,
                color: color || '-',
                brand: brand,
                weight_g: weight,
                initial_amount: weight,
                price_paid: price || 0
            })
        });

        if (response.ok) {
            showToast('Item adicionado ao estoque!');
            loadInventory();
            // Limpar campos principais
            document.getElementById('inv-material').value = '';
            document.getElementById('inv-color').value = '';
            document.getElementById('inv-weight').value = '';
        }
    } catch (error) {
        showToast('Erro ao conectar servidor.', 'error');
    }
}

async function updateWeight(id, currentWeight, unit) {
    const newWeight = await showModal('Ajustar Estoque', `Quantidade atual: ${currentWeight}${unit}. Digite o novo valor:`, true);
    if (newWeight === null || isNaN(parseFloat(newWeight))) return;

    try {
        const response = await apiFetch(`/inventory/${id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ weight_g: parseFloat(newWeight) })
        });

        if (response.ok) {
            showToast('Estoque atualizado!');
            loadInventory();
        }
    } catch (error) {
        showToast('Erro ao atualizar peso.', 'error');
    }
}

async function deleteInventory(id) {
    const confirm = await showModal('Remover Material', 'Tem certeza que deseja excluir este item do inventário?');
    if (!confirm) return;

    try {
        const response = await apiFetch(`/inventory/${id}`, { method: 'DELETE' });
        if (response.ok) {
            showToast('Item removido!');
            loadInventory();
        }
    } catch (error) {
        showToast('Erro ao deletar item.', 'error');
    }
}

// --- GALERIA (JS) ---
function openGalleryUpload() { document.getElementById('gallery-modal').style.display = 'flex'; }
function closeGalleryModal() { document.getElementById('gallery-modal').style.display = 'none'; }

async function confirmGalleryUpload() {
    const form = document.getElementById('gallery-form');
    const formData = new FormData(form);

    try {
        const response = await apiFetch('/gallery', { method: 'POST', body: formData });
        if (response.ok) {
            showToast('Projeto adicionado à galeria!');
            closeGalleryModal();
            loadGallery();
            form.reset();
        }
    } catch (error) { showToast('Erro no upload', 'error'); }
}

async function loadGallery() {
    const response = await apiFetch('/gallery');
    const items = await response.json();
    const grid = document.getElementById('gallery-grid');
    grid.innerHTML = '';
    items.forEach(item => {
        grid.innerHTML += `
                    <div class="card" style="padding: 0; overflow: hidden; position: relative;">
                        <img src="${item.image_path}" style="width: 100%; height: 200px; object-fit: cover;">
                        <div style="padding: 1rem;">
                            <h3 style="margin: 0; font-size: 1rem;">${item.project_name}</h3>
                            <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.5rem;">${item.notes || ''}</p>
                            <button onclick="deleteGallery(${item.id})" class="btn-ghost" style="position: absolute; top: 0.5rem; right: 0.5rem; background: rgba(0,0,0,0.5); border-radius: 50%; width: 30px; height: 30px; padding: 0;">🗑️</button>
                        </div>
                    </div>
                `;
    });
}

async function deleteGallery(id) {
    const confirm = await showModal('Remover da Galeria', 'Deseja excluir permanentemente este registro da galeria?');
    if (confirm) {
        await apiFetch(`/gallery/${id}`, { method: 'DELETE' });
        showToast('Projeto removido da galeria.');
        loadGallery();
    }
}

// --- CLIENTES (JS) ---
async function addClient() {
    const name = document.getElementById('cl-name').value;
    const email = document.getElementById('cl-email').value;
    const phone = document.getElementById('cl-phone').value;
    if (!name) return showToast('Nome é obrigatório', 'error');

    await apiFetch('/clients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, phone })
    });
    showToast('Cliente cadastrado!');
    loadClients();
    document.getElementById('cl-name').value = '';
    document.getElementById('cl-email').value = '';
    document.getElementById('cl-phone').value = '';
}

async function loadClients() {
    const response = await apiFetch('/clients');
    const clients = await response.json();
    const tbody = document.getElementById('clients-table-body');
    const select = document.getElementById('client-select');

    tbody.innerHTML = '';
    select.innerHTML = '<option value="">-- Selecione ou digite acima --</option>';

    clients.forEach(c => {
        tbody.innerHTML += `
                    <tr>
                        <td><b>${c.name}</b></td>
                        <td>${c.email || ''}<br><small>${c.phone || ''}</small></td>
                        <td><button onclick="deleteClient(${c.id})" class="btn-ghost" style="color: var(--secondary);">🗑️</button></td>
                    </tr>
                `;
        select.innerHTML += `<option value="${c.id}" data-name="${c.name}">${c.name}</option>`;
    });
}

function updateClientFromSelect(select) {
    const option = select.options[select.selectedIndex];
    if (option.value) {
        document.getElementById('client-name').value = option.getAttribute('data-name');
    }
}

async function deleteClient(id) {
    const confirm = await showModal('Excluir Cliente', 'Tem certeza que deseja remover este cliente da base de dados?');
    if (confirm) {
        await apiFetch(`/clients/${id}`, { method: 'DELETE' });
        showToast('Cliente removido!');
        loadClients();
    }
}

// --- FINANCEIRO (JS) ---
async function addExpense() {
    const description = document.getElementById('ex-desc').value;
    const value = parseFloat(document.getElementById('ex-value').value);
    if (!description || isNaN(value)) return showToast('Preencha os dados', 'error');

    await apiFetch('/expenses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description, value })
    });
    showToast('Despesa registrada!');
    loadExpenses();
    loadStats();
    document.getElementById('ex-desc').value = '';
    document.getElementById('ex-value').value = '';
}

async function loadExpenses() {
    const response = await apiFetch('/expenses');
    const expenses = await response.json();
    const tbody = document.getElementById('expenses-table-body');
    tbody.innerHTML = '';
    expenses.forEach(e => {
        const date = new Date(e.date).toLocaleDateString('pt-BR');
        tbody.innerHTML += `
                    <tr>
                        <td>${e.description}</td>
                        <td>${date}</td>
                        <td style="color: var(--secondary); font-weight: bold;">R$ ${e.value.toFixed(2)}</td>
                        <td><button onclick="deleteExpense(${e.id})" class="btn-ghost" style="color: var(--secondary);">🗑️</button></td>
                    </tr>
                `;
    });
}

async function deleteExpense(id) {
    const confirm = await showModal('Excluir Despesa', 'Deseja remover este registro financeiro?');
    if (confirm) {
        await apiFetch(`/expenses/${id}`, { method: 'DELETE' });
        showToast('Despesa removida!');
        loadExpenses();
        loadStats();
    }
}

// --- AGENDA (JS) ---
async function loadAgenda() {
    const response = await apiFetch('/orders');
    let orders = await response.json();
    const container = document.getElementById('agenda-list');
    container.innerHTML = '';

    // Filtrar apenas os que não estão prontos e têm data de entrega
    orders = orders.filter(o => o.status !== 'Pronto' && o.delivery_date)
        .sort((a, b) => new Date(a.delivery_date) - new Date(b.delivery_date));

    if (orders.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">Nenhum prazo próximo definido.</p>';
        return;
    }

    orders.forEach(o => {
        const delivery = new Date(o.delivery_date);
        const today = new Date();
        const diffDays = Math.ceil((delivery - today) / (1000 * 60 * 60 * 24));
        let color = 'var(--primary)';
        if (diffDays <= 2) color = 'var(--secondary)';
        else if (diffDays <= 5) color = 'var(--accent)';

        container.innerHTML += `
                    <div class="card" style="border-left: 5px solid ${color}; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: bold; font-size: 1.1rem;">${o.project_name || 'Projeto sem Nome'}</div>
                            <div style="color: var(--text-muted); font-size: 0.85rem;">Cliente: ${o.client_name} | Status: ${o.status}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: ${color}; font-weight: bold;">Entrega: ${delivery.toLocaleDateString('pt-BR')}</div>
                            <div style="font-size: 0.75rem; opacity: 0.7;">Faltam ${diffDays} dias</div>
                        </div>
                    </div>
                `;
    });
}

// --- PDF (JS) ---
let currentPdfOrderId = null;
let selectedPdfGalleryId = null;

async function openPdfGalleryModal(orderId) {
    currentPdfOrderId = orderId;
    selectedPdfGalleryId = null;
    document.getElementById('pdf-gallery-modal').style.display = 'flex';

    const grid = document.getElementById('pdf-gallery-grid');
    grid.innerHTML = '<p style="color: var(--text-muted); font-size: 0.8rem;">Carregando galeria...</p>';

    try {
        const response = await apiFetch('/gallery');
        const items = await response.json();
        grid.innerHTML = '';

        if (items.length === 0) {
            grid.innerHTML = '<p style="color: var(--text-muted); font-size: 0.8rem;">Nenhuma foto na galeria.</p>';
        } else {
            items.forEach(item => {
                const imgDiv = document.createElement('div');
                imgDiv.style.cursor = 'pointer';
                imgDiv.style.border = '2px solid transparent';
                imgDiv.style.borderRadius = '0.5rem';
                imgDiv.style.overflow = 'hidden';
                imgDiv.onclick = () => {
                    document.querySelectorAll('#pdf-gallery-grid div').forEach(d => d.style.borderColor = 'transparent');
                    imgDiv.style.borderColor = 'var(--primary)';
                    selectedPdfGalleryId = item.id;
                };

                imgDiv.innerHTML = `
                            <img src="${item.image_path}" style="width: 100%; height: 100px; object-fit: cover; display: block;">
                            <div style="font-size: 0.7rem; text-align: center; padding: 0.3rem; background: var(--bg-dark); text-overflow: ellipsis; white-space: nowrap; overflow: hidden;">${item.project_name}</div>
                        `;
                grid.appendChild(imgDiv);
            });
        }
    } catch (error) {
        grid.innerHTML = '<p style="color: var(--secondary); font-size: 0.8rem;">Erro ao carregar galeria.</p>';
    }
}

function closePdfGalleryModal() {
    document.getElementById('pdf-gallery-modal').style.display = 'none';
}

function generatePdfWithImage(galleryId) {
    if (!currentPdfOrderId) return;
    const token = localStorage.getItem('ammma_token');
    let url = API_BASE_URL + `/orders/${currentPdfOrderId}/pdf_pro`;
    if (galleryId) {
        url += `?gallery_id=${galleryId}&token=${token}`;
    } else {
        url += `?token=${token}`;
    }
    window.open(url, '_blank');
    closePdfGalleryModal();
}

function generatePdfWithSelectedImage() {
    if (!selectedPdfGalleryId) {
        showToast('Selecione uma foto da galeria primeiro!', 'error');
        return;
    }
    generatePdfWithImage(selectedPdfGalleryId);
}

async function downloadOrderPDF(orderId) {
    openPdfGalleryModal(orderId);
}
let currentPaymentOrderId = null;
function openPaymentModal(orderId, currentPaid, totalValue) {
    currentPaymentOrderId = orderId;
    document.getElementById('pay-amount').value = currentPaid;
    document.getElementById('pay-total-lbl').innerText = `R$ ${totalValue.toFixed(2)}`;
    document.getElementById('payment-modal').style.display = 'flex';
}
function closePaymentModal() {
    document.getElementById('payment-modal').style.display = 'none';
}
async function confirmPayment() {
    const amount = parseFloat(document.getElementById('pay-amount').value);
    if (isNaN(amount) || amount < 0) return showToast('Valor inválido', 'error');

    try {
        const response = await apiFetch(`/orders/${currentPaymentOrderId}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paid_amount: amount })
        });
        if (response.ok) {
            showToast('Pagamento atualizado!');
            closePaymentModal();
            loadOrders();
            loadStats();
        } else {
            showToast('Erro ao atualizar.', 'error');
        }
    } catch (error) {
        showToast('Erro de conexão', 'error');
    }
}

