# 🖥️ Manual da Interface React — Assistente Médico

> Documentação completa de uso da interface web (React + Vite) do Tech Challenge Fase 3

## 🚀 Quick Start (60 segundos)

```bash
# 1. Instalar dependências do frontend
cd frontend
npm install

# 2. Rodar em modo desenvolvimento
npm run dev -- --host 127.0.0.1 --port 3000

# 3. Acessar no navegador
# http://127.0.0.1:3000
# Login: medico / demo123
```

**O que acontece**:
- Vite sobe servidor de dev com hot-reload
- React monta a aplicação no `<div id="root">`
- Login aparece primeiro, depois libera as 4 abas

**Pré-requisitos**:
- Node.js 18+ (testado com 18.17)
- npm 9+ (vem com Node)

---

## 📂 Estrutura do Frontend

```
frontend/
├── index.html                  # HTML raiz (carrega main.jsx)
├── package.json                # Deps React 18, Vite 5
├── vite.config.js              # Config Vite (porta 3000)
└── src/
    ├── main.jsx                # Entry point (ReactDOM.createRoot)
    ├── App.jsx                 # Componente principal (4 abas)
    └── styles.css              # Tema dark + estilos custom
```

**Tecnologias**:
- **React 18.3.1** — UI declarativa com hooks
- **Vite 5.4** — Bundler dev com hot-reload
- **Sem libs extras** — apenas `react` e `react-dom`

---

## 🎯 Estrutura da Interface (4 Abas)

### 📋 Aba 1: Consulta

**Função**: Médico insere relato e recebe triagem + RAG + síntese.

**Componentes**:
- Textarea com relato do paciente (editável)
- Botão **"Iniciar consulta"** (processa o relato)
- Botão **"Limpar"** (zera textarea)
- 3 boxes de resultado:
  - **🚨 Triagem** — categoria + justificativa + red flags + confiança
  - **📚 RAG** — top-K trechos relevantes do ChromaDB
  - **🧠 Síntese** — resumo + exames sugeridos + medicações

**Estado atual**: dados mockados (em `App.jsx`). Para integrar com backend, substituir `handleProcess` por chamada à API Python.

### 📊 Aba 2: Auditoria

**Função**: Dashboard de logs SQLite e métricas.

**Componentes**:
- 4 cards de métricas: Total de eventos, Sessões ativas, Latência média, Custo estimado
- Tabela de eventos recentes (hora, agente, evento, status)

**Estado atual**: dados mockados (`mockMetrics`, `auditEvents`). Conectar com `src/logging/dashboard.py` para dados reais.

### 📁 Aba 3: Documentos

**Função**: Lista de PDFs gerados pelo sistema.

**Componentes**:
- Cards por documento (nome, data, tamanho)
- Background gradient

**Estado atual**: dados mockados (`documents`). Integrar com `src/docs/generator.py`.

### ⚙️ Aba 4: Config

**Função**: Informações do sistema.

**Componentes**:
- Tabela com 6 linhas: Modelo, Status do RAG, Banco, Documentos, Frontend, GitHub

**Estado atual**: hardcoded (`systemInfo`). Pode ser alimentado por endpoint `/api/info`.

---

## 🔐 Autenticação

**Estado atual**: client-side (mock)

```javascript
// App.jsx (linha 35)
const [login, setLogin] = useState({ username: 'medico', password: 'demo123' });

const canLogin = useMemo(
  () => login.username === 'medico' && login.password === 'demo123',
  [login]
);
```

**Credenciais padrão**:
- Usuário: `medico`
- Senha: `demo123`

**Para produção**, substituir por:
- JWT com backend Python (`src/auth/`)
- OAuth2 (Google/Microsoft)
- Integração com SSO do hospital

---

## 🛠️ Customizações Comuns

### Mudar porta (dev)

Editar `frontend/vite.config.js`:
```javascript
export default defineConfig({
  server: {
    host: '127.0.0.1',
    port: 3000,  // ← mudar aqui
  },
});
```

### Mudar tema (cores)

Editar `frontend/src/styles.css` (linha 1-10):
```css
:root {
  background: #0b1220;  /* cor de fundo dark */
  color: #e5eefb;       /* cor de texto */
}
```

### Adicionar nova aba

Em `App.jsx`:
```javascript
// 1. Adicionar no array
{['consulta', 'auditoria', 'documentos', 'config', 'relatorios'].map(...)}

// 2. Criar conteúdo
relatorios: (
  <div className="panel">
    <h3>Relatórios</h3>
    ...
  </div>
)
```

### Build de produção

```bash
cd frontend
npm run build
# Gera dist/ pronto pra deploy
```

Para servir o build:
```bash
npm run preview -- --host 127.0.0.1 --port 4173
# Abre em http://127.0.0.1:4173
```

---

## 🔌 Integração com Backend Python

**Estado atual**: frontend standalone com mocks.

**Para conectar com backend** (próximo passo):

### 1. Criar API em Python (FastAPI/Flask)

```python
# src/api/server.py
from fastapi import FastAPI
from src.agents.triagem import TriagemAgent

app = FastAPI()

@app.post("/api/consulta")
async def consulta(relato: str):
    # Roda LangGraph com RAG + LLM
    resultado = await run_pipeline(relato)
    return resultado
```

### 2. Chamar API no React

```javascript
// App.jsx
const handleProcess = async () => {
  const response = await fetch('http://localhost:8000/api/consulta', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ relato }),
  });
  const data = await response.json();
  setResult(data);
};
```

### 3. Habilitar CORS

```python
# src/api/server.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📱 Acesso pelo Celular

### Opção 1: Mesma WiFi (rede local)

**Vantagens**: gratuito, sem limite de tempo
**Quando usar**: médico no hospital/clínica com WiFi compartilhada

**Como configurar**:

1. **Descobrir IP do seu PC**:
```bash
# Windows (CMD)
ipconfig
# Procure "IPv4 Address" — geralmente 192.168.X.X

# Ou PowerShell
Get-NetIPAddress | Where-Object {$_.AddressFamily -eq "IPv4"}
```

2. **Liberar firewall** (Windows):
```
Configurações → Firewall → Configurações avançadas
→ Regras de entrada → Nova regra
→ Porta 3000 → Permitir conexão
```

3. **Rodar Vite com --host 0.0.0.0**:
```bash
cd frontend
npm run dev -- --host 0.0.0.0 --port 3000
```

4. **No celular** (mesma WiFi):
```
http://192.168.X.X:3000
```

### Opção 2: Build + deploy em servidor

```bash
cd frontend
npm run build
# Copiar pasta dist/ pro servidor (nginx, Apache, etc.)
```

Configuração nginx exemplo:
```nginx
server {
  listen 80;
  server_name assistente.exemplo.com;
  root /var/www/assistente/dist;
  index index.html;
}
```

### Opção 3: HuggingFace Spaces (Static)

**Vantagens**: URL permanente, grátis
**Quando usar**: deploy de longa duração para equipe

**Como fazer**:
1. Criar Space Static em https://huggingface.co/new-space
2. Upload do conteúdo de `frontend/dist/` (gerado por `npm run build`)
3. URL: `https://huggingface.co/spaces/<user>/<space-name>`

---

## 📊 Performance Esperada

| Cenário | Tempo |
|---|---|
| Carregar página inicial (cold start) | < 1s |
| Navegar entre abas (sem backend) | Instantâneo |
| Rodar `npm run dev` | ~3-5s |
| Rodar `npm run build` | ~10-15s |
| Tamanho do build (dist/) | ~150 KB gzipped |

**Para mobile**: já é responsivo (CSS usa viewport units e flexbox).

---

## 🐛 Troubleshooting

### "Port 3000 is already in use"

Outro processo está usando a porta 3000. Soluções:

```bash
# 1. Matar o processo (Windows)
netstat -ano | findstr :3000
taskkill /PID <PID_encontrado> /F

# 2. Ou mudar a porta
npm run dev -- --port 3001
```

### "npm: command not found"

Node.js não está instalado. Baixar de https://nodejs.org/

### "Cannot find module 'react'"

```bash
cd frontend
rm -rf node_modules
npm install
```

### Página carrega mas fica em branco

Verificar console do navegador (F12). Geralmente é erro de import no `App.jsx`.

```bash
# Reiniciar Vite
Ctrl+C
npm run dev
```

### Build falha com erro de memória

```bash
# Aumentar heap do Node
NODE_OPTIONS=--max-old-space-size=4096 npm run build
```

---

## 🎯 Para o Tech Challenge

### Demonstração no vídeo (15min):

1. **Login** (30s)
   - Abre `http://localhost:3000`
   - Mostra tela de login
   - Entra com `medico` / `demo123`

2. **Aba Consulta** (5min)
   - Digita relato: "Paciente 45 anos, dor torácica..."
   - Clica "Iniciar consulta"
   - Mostra triagem + RAG + síntese

3. **Aba Auditoria** (3min)
   - Mostra dashboard com métricas
   - Explica que cada chamada LLM/RAG é logada em SQLite

4. **Aba Documentos** (2min)
   - Lista PDFs gerados (prontuário, atestado, receita)

5. **Aba Config** (2min)
   - Mostra info do sistema
   - Confirma modelo fine-tunado carregado

6. **Código** (3min)
   - Mostra `frontend/src/App.jsx`
   - Explica componentes React

---

## 🔗 Links Úteis

- **React docs**: https://react.dev
- **Vite docs**: https://vitejs.dev
- **Backend (LangGraph)**: `src/graph/workflow.py`
- **RAG**: `src/rag/retriever.py`
- **LLM**: `src/llm/client.py`
- **Notebook de execução**: `notebooks/rodarcolab.ipynb`

---

## ⚠️ Limitações Conhecidas

| Limitação | Workaround |
|---|---|
| Dados são mockados em `App.jsx` | Substituir por fetch() no backend |
| Sem auth real | Adicionar JWT/OAuth em produção |
| Sem histórico de consultas | Adicionar localStorage ou backend |
| Sem upload de imagens/exames | Adicionar componente de upload |

---

**Versão**: 2.0 (React)  
**Stack**: React 18.3.1 + Vite 5.4.10  
**Última atualização**: 08/09/2026
