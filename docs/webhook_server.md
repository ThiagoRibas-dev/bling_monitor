# 🌐 webhook_server.py - Automação em Tempo Real

## 🎯 O Que Este Script Faz

Fica rodando **24 horas por dia** esperando o Bling avisar quando algo acontece:

1. **Produto novo cadastrado** → Cria código SKU automaticamente
2. **Estoque zerou** → Desativa o produto (se zerou por vendas)

**Exemplo de automação:**
- Você cadastra "Memória RAM 16GB" no Bling
- **5 segundos depois** o código `MEMO00009` aparece automaticamente
- Você não precisa fazer nada!

---

## ⚙️ Configuração Inicial

### 1. Criar arquivo `.env`

Renomeie `.env.example` para `.env` e preencha:

```env
CLIENT_ID=seu_client_id_do_bling
CLIENT_SECRET=seu_client_secret_do_bling
REDIRECT_URI=https://localhost/
AUTH_CODE=codigo_de_autorizacao

WEBHOOK_PORT=5000
```

### 2. Como Obter o AUTH_CODE

**Passo 1:** Acesse no navegador (substitua `SEU_CLIENT_ID`):
```
https://www.bling.com.br/Api/v3/oauth/authorize?response_type=code&client_id=SEU_CLIENT_ID&state=12345
```

**Passo 2:** Faça login e autorize

**Passo 3:** Copie o código da URL de redirecionamento:
```
https://localhost/?code=ABC123XYZ456&state=12345
                        ^^^^^^^^^^^^
```

**Passo 4:** Cole no `.env`:
```env
AUTH_CODE=ABC123XYZ456
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

---

## 🚀 Como Executar

### Teste Manual (Para Ver Funcionando)

**Windows:**
```bash
cd C:\BlingMonitor
python webhook_server.py
```

**Linux:**
```bash
cd ~/bling_monitor
python webhook_server.py
```

**O que vai aparecer:**
```
================================================================================
🚀 INICIANDO SERVIDOR DE WEBHOOKS BLING
================================================================================
🌐 Host: 0.0.0.0
🔌 Porta: 5000
📍 Endpoint: http://your-domain.com/webhook/bling
❤️  Health: http://your-domain.com/health
================================================================================

🔄 Worker de processamento iniciado

 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.100:5000

[Aguardando eventos do Bling...]
```

**✅ Se aparecer isso, está funcionando!**

Para parar: `Ctrl+C`

---

## 🔧 Configurar no Bling

### Passo 1: Acessar Configurações de Webhook

1. Login no **Bling**
2. Menu **Configurações** → **Integrações** → **Central de Extensões**
3. Clique no **seu aplicativo**
4. Aba **Webhooks**

### Passo 2: Cadastrar Webhook de Produtos

Clique em **"Adicionar Webhook"** e preencha:

| Campo | Valor |
|-------|-------|
| **Recurso** | `product` |
| **Ação** | Marcar `created` e `updated` |
| **URL** | `http://SEU_IP:5000/webhook/bling` |
| **Método** | POST |

**Exemplo de URL:**
- Se está rodando no mesmo PC: `http://192.168.1.100:5000/webhook/bling`
- Se está em servidor na nuvem: `http://meuservidor.com:5000/webhook/bling`

### Passo 3: Cadastrar Webhook de Estoque

Clique em **"Adicionar Webhook"** novamente:

| Campo | Valor |
|-------|-------|
| **Recurso** | `stock` |
| **Ação** | Marcar `updated` |
| **URL** | `http://SEU_IP:5000/webhook/bling` |
| **Método** | POST |

### Passo 4: Testar

No Bling, clique em **"Testar Webhook"**

**No terminal onde o webhook está rodando, deve aparecer:**
```
✅ Webhook recebido: product.created (eventId: test_12345)
────────────────────────────────────────────────────────────────
🔄 Processando evento: product.created (ID: test_12345)
────────────────────────────────────────────────────────────────
📦 Processando evento de produto 99999999
   ℹ️  Produto já possui código: TEST00001
✅ Evento processado com sucesso
```

**✅ Se aparecer isso, o webhook está configurado corretamente!**

---

## 🔒 Abrir Porta no Firewall

### Windows

```powershell
# Abrir PowerShell como Administrador
New-NetFirewallRule -DisplayName "Bling Webhook" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

### Linux

```bash
# Ubuntu/Debian
sudo ufw allow 5000/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

### Roteador (Se Estiver em Rede Local)

Se o Bling precisa acessar de fora da sua rede:
1. Acesse as configurações do roteador (ex: 192.168.1.1)
2. Vá em **Port Forwarding** ou **Redirecionamento de Portas**
3. Adicione:
   - Porta Externa: `5000`
   - Porta Interna: `5000`
   - IP Interno: IP do computador (ex: `192.168.1.100`)
   - Protocolo: `TCP`

---

## 🔄 Manter Rodando 24/7 (Serviço)

### Opção 1: NSSM (Windows - Recomendado)

**Instalar NSSM:**
```powershell
# Via Chocolatey
choco install nssm

# OU baixar manualmente de: https://nssm.cc/download
```

**Criar Serviço:**
```powershell
# Abrir PowerShell como Administrador
cd C:\BlingMonitor

# Criar serviço
nssm install BlingWebhook "C:\Python311\python.exe" "C:\BlingMonitor\webhook_server.py"

# Configurar
nssm set BlingWebhook AppDirectory "C:\BlingMonitor"
nssm set BlingWebhook DisplayName "Bling Webhook Server"
nssm set BlingWebhook Description "Servidor de webhooks para automação Bling"
nssm set BlingWebhook Start SERVICE_AUTO_START

# Configurar logs
nssm set BlingWebhook AppStdout "C:\BlingMonitor\logs\webhook.log"
nssm set BlingWebhook AppStderr "C:\BlingMonitor\logs\webhook-error.log"

# Iniciar
nssm start BlingWebhook
```

**Gerenciar o Serviço:**
```powershell
# Ver status
nssm status BlingWebhook

# Parar
nssm stop BlingWebhook

# Reiniciar
nssm restart BlingWebhook

# Remover (desinstalar)
nssm remove BlingWebhook confirm
```

**Ver logs:**
```powershell
Get-Content C:\BlingMonitor\logs\webhook.log -Tail 50 -Wait
```

### Opção 2: Task Scheduler (Windows - Alternativa)

1. Abrir **Agendador de Tarefas**
2. Criar Tarefa Básica
3. Nome: `BlingWebhook`
4. Disparador: **Quando o computador iniciar**
5. Ação: **Iniciar programa**
   - Programa: `C:\Python311\python.exe`
   - Argumentos: `C:\BlingMonitor\webhook_server.py`
   - Iniciar em: `C:\BlingMonitor`
6. Configurações adicionais:
   - ☑ Executar se o usuário estiver conectado ou não
   - ☑ Executar com privilégios mais altos

### Opção 3: Systemd (Linux)

**Criar arquivo de serviço:**
```bash
sudo nano /etc/systemd/system/bling-webhook.service
```

**Conteúdo:**
```ini
[Unit]
Description=Bling Webhook Server
After=network.target

[Service]
Type=simple
User=seu_usuario
WorkingDirectory=/home/seu_usuario/bling_monitor
Environment="PATH=/home/seu_usuario/bling_monitor/venv/bin"
ExecStart=/home/seu_usuario/bling_monitor/venv/bin/python webhook_server.py
Restart=always
RestartSec=10

StandardOutput=append:/var/log/bling-webhook.log
StandardError=append:/var/log/bling-webhook-error.log

[Install]
WantedBy=multi-user.target
```

**Ativar e iniciar:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable bling-webhook
sudo systemctl start bling-webhook

# Ver status
sudo systemctl status bling-webhook

# Ver logs
sudo journalctl -u bling-webhook -f
```

---

## 🎬 Como Funciona (Fluxo)

### Cenário 1: Cadastrar Produto Novo

```
1. Você cadastra no Bling
   ┌──────────────────────────┐
   │ Nome: Memória RAM 16GB   │
   │ Categoria: Peças>>Memória│
   │ Código: (vazio)          │
   │ [SALVAR]                 │
   └──────────────────────────┘
            ↓
   
2. Bling envia webhook (< 1 segundo)
   POST http://seu-servidor:5000/webhook/bling
   {
     "event": "product.created",
     "data": {
       "id": 16541000001,
       "nome": "Memória RAM 16GB",
       "codigo": ""  ← SEM CÓDIGO
     }
   }
            ↓

3. Seu servidor processa (2-3 segundos)
   ✅ Valida autenticidade (HMAC)
   ✅ Verifica se já processou (evita duplicação)
   ✅ Busca categoria: "Peças>>Memória RAM"
   ✅ Gera código: MEMO00009
   ✅ Atualiza no Bling
            ↓

4. Produto atualizado no Bling (< 5 segundos total)
   ┌──────────────────────────┐
   │ Nome: Memória RAM 16GB   │
   │ Categoria: Peças>>Memória│
   │ Código: MEMO00009  ← ✅  │
   └──────────────────────────┘
```

### Cenário 2: Estoque Zerou por Venda

```
1. Venda registrada no Bling
   Produto: "Mouse Logitech"
   Estoque antes: 1
   Estoque depois: 0
            ↓

2. Bling envia webhook
   POST http://seu-servidor:5000/webhook/bling
   {
     "event": "stock.updated",
     "data": {
       "produto": {"id": 16532000001},
       "saldo": 0
     }
   }
            ↓

3. Seu servidor verifica
   ✅ Estoque = 0? SIM
   ✅ Categoria Notebook/SFF/Mini/Monitor? NÃO
   ✅ Busca movimentações de estoque
      - Entradas: 10 unidades
      - Saídas por venda: 10 unidades
   ✅ Entradas == Saídas? SIM
            ↓

4. Desativa produto automaticamente
   Situação: Ativo → Inativo ✅
```

---

## 🏷️ Códigos Gerados Automaticamente

Mesmos padrões do `dump_products.py`:

| Categoria | Código Exemplo |
|-----------|----------------|
| Notebook, Mini, SFF | NTB00001 |
| Peças → Placa Mãe | PLMA00001 |
| Peças → Memória RAM | MEMO00001 |
| Periféricos | PERI00001 |
| Monitor | MONI00001 |

---

## 🛡️ Segurança: Validação HMAC

**O que é?** Sistema que garante que o webhook realmente veio do Bling (não é alguém tentando enganar seu sistema).

**Como funciona:**
1. Bling calcula um "código secreto" usando o `CLIENT_SECRET`
2. Envia esse código no header `X-Bling-Signature-256`
3. Seu servidor recalcula e compara
4. Se for diferente, rejeita (HTTP 401)

**Você não precisa fazer nada!** O script faz isso automaticamente.

---

## 🔍 Verificar se Está Funcionando

### Teste 1: Health Check

Abra no navegador:
```
http://localhost:5000/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "queue_size": 0,
  "db_stats": {
    "counters": 5,
    "events": 23
  }
}
```

### Teste 2: Cadastrar Produto Manualmente

1. Abra o Bling
2. Cadastre um produto **sem código**
3. Salve
4. Aguarde 5 segundos
5. Recarregue a página do produto
6. **O código deve aparecer automaticamente!**

### Teste 3: Ver Logs em Tempo Real

```powershell
# Windows (se usando NSSM)
Get-Content C:\BlingMonitor\logs\webhook.log -Tail 50 -Wait

# Windows (se rodando manualmente)
# Veja no próprio terminal onde executou

# Linux
tail -f /var/log/bling-webhook.log
```

---

## 📊 O Que Aparece nos Logs

### Quando Recebe Webhook

```
✅ Webhook recebido: product.created (eventId: evt_abc123)
────────────────────────────────────────────────────────────────
🔄 Processando evento: product.created (ID: evt_abc123)
────────────────────────────────────────────────────────────────
📦 Processando evento de produto 16541000001
   🏷️  Gerando código: MEMO00009
   ✅ Código atribuído com sucesso
✅ Evento processado com sucesso
```

### Quando Produto Já Tem Código

```
✅ Webhook recebido: product.updated (eventId: evt_xyz789)
────────────────────────────────────────────────────────────────
🔄 Processando evento: product.updated (ID: evt_xyz789)
────────────────────────────────────────────────────────────────
📦 Processando evento de produto 16541000002
   ℹ️  Produto já possui código: PERI00023
✅ Evento processado com sucesso
```

### Quando Evento Duplicado

```
✅ Webhook recebido: product.created (eventId: evt_abc123)
ℹ️  Evento evt_abc123 já processado anteriormente (idempotência)
```

### Quando Estoque Zera

```
✅ Webhook recebido: stock.updated (eventId: evt_stock_456)
────────────────────────────────────────────────────────────────
🔄 Processando evento: stock.updated (ID: evt_stock_456)
────────────────────────────────────────────────────────────────
📦 Processando evento de estoque para produto 16532000001
   🔍 Verificando movimentações de estoque...
   📊 Entradas: 10
   📊 Saídas por venda: 10
   🔴 Desativando produto (zerado por vendas)
   ✅ Produto desativado
✅ Evento processado com sucesso
```

---

## ⚠️ Produtos que NÃO São Desativados

Mesmo com estoque = 0, **não desativa** se:

- ❌ Categoria é Notebook, SFF, Mini ou Monitor
- ❌ Subcategoria é "SubMaquina"
- ❌ Produto nunca teve entrada de estoque (não foi produzido)
- ❌ Estoque zerou, mas não foi por venda (ex: ajuste manual)

**Exemplo que NÃO desativa:**
```
Produto: "Notebook Dell"
Categoria: Notebook  ← Exceção!
Estoque: 0
→ NÃO desativa (categoria excluída)
```

**Exemplo que NÃO desativa:**
```
Produto: "Mouse USB"
Entradas: 0 unidades  ← Nunca teve estoque
Saídas: 0 unidades
Estoque: 0
→ NÃO desativa (nunca foi produzido)
```

---

## ⚠️ Problemas Comuns

### ❌ Webhook não recebe eventos

**Possíveis causas:**

1. **Servidor não está rodando**
   ```bash
   # Verificar se está rodando
   # Windows
   nssm status BlingWebhook
   
   # Linux
   sudo systemctl status bling-webhook
   ```

2. **Porta 5000 bloqueada no firewall**
   ```bash
   # Testar localmente
   curl http://localhost:5000/health
   
   # Se funcionar local mas não externo → Firewall bloqueando
   ```

3. **URL incorreta no Bling**
   - Deve ser IP **público** ou domínio, não `localhost`
   - Exemplo ERRADO: `http://localhost:5000/webhook/bling`
   - Exemplo CERTO: `http://192.168.1.100:5000/webhook/bling`

**Solução:** Veja seção "Configurar no Bling" e "Abrir Porta no Firewall"

---

### ❌ Erro: "401 Unauthorized"

**Causa:** AUTH_CODE expirou (válido por ~30 dias)

**Solução:**
1. Obtenha novo AUTH_CODE (veja início deste documento)
2. Atualize no `.env`
3. Reinicie o serviço:
   ```powershell
   nssm restart BlingWebhook
   ```

---

### ❌ Erro: "Invalid signature" (HMAC)

**Causa:** `CLIENT_SECRET` no `.env` está incorreto

**Solução:**
1. Verifique o `CLIENT_SECRET` na Central de Extensões do Bling
2. Copie **exatamente** (sem espaços extras)
3. Cole no `.env`:
   ```env
   CLIENT_SECRET=5cae81f3634b69c33ba73727376acef9417fa1e552d5bd40bf075c8fb016
   ```
4. Reinicie o serviço

---

### ❌ Código não é gerado automaticamente

**Verificar:**

1. **Webhook está configurado no Bling?**
   - Central de Extensões → Webhooks → Deve ter `product.created` e `product.updated`

2. **Servidor está recebendo?**
   - Veja os logs - deve aparecer "Webhook recebido"

3. **Produto tem categoria?**
   - Produtos sem categoria não recebem código

4. **Categoria é "SubMaquina"?**
   - Essa categoria é ignorada (regra de negócio)

---

### ❌ Servidor fica caindo / parando

**Possíveis causas:**

1. **Erro não tratado no código**
   - Veja logs de erro: `webhook-error.log`

2. **Memória insuficiente**
   - Webhook usa pouca memória (~50MB), mas verifique

3. **Windows desligou o computador**
   - Configurar para não hibernar:
     ```
     Painel de Controle → Opções de Energia → 
     Nunca desligar a tela / Nunca suspender
     ```

**Solução:** Usar NSSM com reinício automático (já configurado acima)

---

## 📊 Banco de Dados

O webhook usa o mesmo banco do `dump_products.py`:

**Arquivo:** `bling_data.db`

**Contém:**
- Contadores de código (para não duplicar)
- Eventos processados (para idempotência)

**⚠️ Backup importante!**
```bash
# Fazer backup semanal
copy bling_data.db backup\bling_data_2024-01-15.db
```

---

## 🔧 Comandos Úteis

### Ver últimos eventos processados

```bash
sqlite3 bling_data.db

SELECT event_type, product_id, processed_at 
FROM processed_events 
ORDER BY processed_at DESC 
LIMIT 10;
```

### Limpar eventos antigos (se banco ficar grande)

```bash
sqlite3 bling_data.db

DELETE FROM processed_events 
WHERE processed_at < date('now', '-30 days');
```

### Ver status do serviço (Windows)

```powershell
# Via NSSM
nssm status BlingWebhook

# Via Services
Get-Service BlingWebhook

# Ver logs
Get-Content C:\BlingMonitor\logs\webhook.log -Tail 50
```

### Reiniciar serviço (Windows)

```powershell
nssm restart BlingWebhook
```

---

## ✅ Checklist de Instalação

```
□ Arquivo .env criado e preenchido
□ AUTH_CODE válido obtido
□ Dependências instaladas (pip install -r requirements.txt)
□ Porta 5000 aberta no firewall
□ Servidor executado manualmente uma vez (teste)
□ Health check funcionando (http://localhost:5000/health)
□ Webhooks cadastrados no Bling (product + stock)
□ Teste manual: cadastrar produto → código aparece
□ Serviço Windows/Linux configurado (NSSM/systemd)
□ Serviço iniciado e rodando
□ Logs sendo gravados corretamente
□ Backup de bling_data.db configurado
```

---

## 📝 Resumo Executivo

| O Que | Como |
|-------|------|
| **Executar manualmente** | `python webhook_server.py` |
| **Rodar como serviço** | `nssm start BlingWebhook` (Windows) |
| **Ver se está rodando** | `http://localhost:5000/health` |
| **Ver logs** | `Get-Content logs\webhook.log -Tail 50 -Wait` |
| **Reiniciar** | `nssm restart BlingWebhook` |
| **Parar** | `nssm stop BlingWebhook` |

**Quando está funcionando:**
- Você cadastra produto no Bling → Código aparece em 5 segundos ✅
- Estoque zera por venda → Produto desativa automaticamente ✅

---
