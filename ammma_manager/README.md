# 🚀 AMMMA 3D Manager

O **AMMMA 3D Manager** é uma solução completa e profissional para gestão de oficinas de impressão 3D. O sistema integra desde o cálculo preciso de custos até o controle de produção via Kanban, gestão de estoque e monitoramento de máquinas, tudo em uma interface moderna e otimizada para dispositivos móveis (PWA).

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.10+** com **FastAPI**: Performance de alto nível e documentação automática.
- **SQLAlchemy**: ORM para manipulação robusta do banco de dados SQLite.
- **Pydantic**: Validação de dados e esquemas rigorosos.
- **JWT (JSON Web Tokens)**: Autenticação segura e controle de sessões.
- **FPDF2**: Geração dinâmica de orçamentos em PDF com alta qualidade.

### Frontend
- **HTML5 & Vanilla JavaScript (ES6+)**: Sem frameworks pesados, garantindo carregamento instantâneo.
- **CSS3 (Custom Properties & Glassmorphism)**: Design premium, responsivo e com modo escuro nativo.
- **PWA (Progressive Web App)**: Instalável no celular, com Service Workers e Manifesto.
- **Chart.js**: Visualização de métricas e evolução de vendas em tempo real.
- **Flatpickr**: Seleção de datas otimizada para agendamento de entregas.

---

## 🌟 Funcionalidades Principais

### 1. 🧮 Calculadora de Custos de Precisão
Sistema de orçamento que considera:
- **Material**: Preço do rolo, peso da peça e perda estimada.
- **Eletricidade**: Consumo da máquina e custo do kWh local.
- **Mão de Obra**: Valor da hora técnica e tempo de fatiamento/pós-processo.
- **Lucro & Impostos**: Margens configuráveis para preço sugerido final.
- **Cupons**: Aplicação de descontos fixos ou percentuais.

### 2. 🎛️ Painel de Produção (Kanban)
Gerencie o ciclo de vida dos pedidos em tempo real:
- **Orçamento ➔ A Fazer ➔ Fila ➔ Imprimindo ➔ Pronto**.
- Atualização dinâmica de status com baixa automática de estoque ao finalizar.
- Alertas visuais para prazos de entrega urgentes.

### 3. 📦 Gestão de Inventário Inteligente
- Controle de Filamentos, Resinas e Insumos (Embalagens, etc).
- **Dedução Automática**: O sistema calcula o peso utilizado e dá baixa no estoque server-side.
- **Alertas de Estoque Baixo**: Notificações visuais quando materiais atingem o nível crítico.

### 4. 📟 Monitoramento de Impressoras
- Registro de horas totais de funcionamento.
- **Alertas de Manutenção**: Notificações baseadas em horas de uso (ex: lubrificação a cada 500h).
- Gestão de status (Disponível, Ocupada, Manutenção).

### 5. 📈 Dashboard de Estatísticas
Visão clara da saúde do seu negócio:
- **Faturamento e Lucro Líquido**: Cálculos reais descontando falhas e custos fixos.
- **Ticket Médio e Margem**: Entenda a rentabilidade de cada projeto.
- **Desperdício**: Log de falhas para identificar perdas de material.

### 6. 📄 Orçamentos em PDF Profissionais
- Geração instantânea de PDF para o cliente.
- Inclusão opcional de fotos do projeto direto da galeria.
- Rodapé padrão com dados de pagamento (Pix) e contatos.

---

## 🚀 Como Iniciar

### Pré-requisitos
- Python 3.10 ou superior instalado.
- Dependências instaladas (FastAPI, Uvicorn, SQLAlchemy, FPDF2, Python-Multipart, Jose).

### Passo a Passo
1. **Instalar Dependências**:
   ```bash
   pip install fastapi uvicorn sqlalchemy fpdf2 python-multipart python-jose[cryptography] passlib[bcrypt]
   ```

2. **Iniciar o Servidor**:
   Navegue até a pasta `backend` e execute:
   ```bash
   python main.py
   ```
   *O servidor iniciará em `http://localhost:8000`.*

3. **Acessar o Sistema**:
   Abra o navegador em `http://localhost:8000/login` e use as credenciais de administrador padrão indicadas abaixo.

---

## 🔐 Segurança e Acessos

O sistema utiliza controle de acessos baseado em cargos:
- **Admin (DEV)**: Acesso total (Configurações, Financeiro, Usuários).
- **Colaborador**: Acesso operacional (Calculadora, Kanban, Pedidos).

> [!IMPORTANT]
> **Credenciais de Acesso Padrão (Admin)**:
> - **Usuário:** `admin`
> - **Senha:** `AM3D@MGR#1`

---

## 📱 Mobile & PWA
Para instalar o AMMMA 3D Manager como um aplicativo no seu celular:
1. Acesse o site pelo navegador do smartphone.
2. Clique no banner **"Instalar App"** que aparecerá no rodapé.
3. O sistema será adicionado à sua tela inicial como um aplicativo nativo.

---

## 👨‍💻 Desenvolvido Por
**Wilson Borges** - *Foco em Eficiência e Precisão para Impressão 3D.*
