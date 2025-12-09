# 📚 Documentação Técnica - Sistema de Automação Bling

## 📋 Índice

1. [dump_products.py - Gerador de Códigos SKU](#dump_productspy---gerador-de-códigos-sku)
2. [webhook_server.py - Servidor de Eventos em Tempo Real](#webhook_serverpy---servidor-de-eventos-em-tempo-real)
3. [Regras de Negócio Compartilhadas](#regras-de-negócio-compartilhadas)
4. [Arquitetura Geral](#arquitetura-geral)

---

# 📦 dump_products.py - Gerador de Códigos SKU

## 🎯 Objetivo

Script de **execução única** (ou esporádica) que:
1. Varre **todos os produtos** cadastrados no Bling
2. Identifica produtos **sem código SKU**
3. Gera códigos **padronizados e sequenciais** baseados em categorias
4. Atualiza produtos na API do Bling
5. Salva snapshot completo em arquivo JSON

## 🔧 Funcionalidade Detalhada

### Fluxo de Execução

```
┌─────────────────────────────────────────────────────────────────┐
│                    DUMP_PRODUCTS.PY - FLUXO                     │
└─────────────────────────────────────────────────────────────────┘

1. INICIALIZAÇÃO
   ├─ Carregar credenciais (.env)
   ├─ Autenticar na API Bling
   ├─ Conectar ao banco SQLite (bling_data.db)
   └─ Carregar CACHE DE CATEGORIAS da API
      └─ GET /Api/v3/categorias/produtos (paginado)
          └─ Armazena mapa: ID → Nome completo
          
2. VARREDURA DE PRODUTOS
   ├─ Loop paginado (100 produtos/página)
   │  └─ GET /Api/v3/produtos?pagina={n}&limite=100
   │
   └─ Para cada produto:
       ├─ GET /Api/v3/produtos/{id} (detalhes completos)
       │
       ├─ ANÁLISE:
       │  ├─ Já tem código? → SKIP
       │  ├─ Sem categoria? → SKIP
       │  ├─ Categoria "SubMaquina"? → SKIP (regra de negócio)
       │  └─ Caso contrário → GERAR CÓDIGO
       │
       ├─ GERAÇÃO DE CÓDIGO:
       │  ├─ Determinar prefixo (baseado em categoria)
       │  ├─ Buscar último contador no banco (thread-safe)
       │  ├─ Incrementar contador
       │  ├─ Formatar: {PREFIXO}{NÚMERO:05d}
       │  └─ Exemplo: "NTB00042", "PLMA00015"
       │
       ├─ ATUALIZAÇÃO:
       │  └─ PATCH /Api/v3/produtos/{id}
       │     Body: {"codigo": "NTB00042"}
       │
       └─ VARIAÇÕES (se existirem):
          └─ Repetir processo para cada variação do produto
          
3. PERSISTÊNCIA
   ├─ Salvar contadores no SQLite (para próxima execução)
   └─ Salvar dump JSON completo (products_dump.json)
   
4. RELATÓRIO
   └─ Exibir estatísticas:
      ├─ Total processado
      ├─ Códigos gerados
      ├─ Produtos ignorados
      └─ Erros
```

### Exemplo de Execução

```
$ python dump_products.py

================================================================================
🚀 INICIANDO GERAÇÃO DE CÓDIGOS - 2024-01-15 14:30:45
================================================================================

Carregando cache de categorias...
📦 156 categorias carregadas
✅ 156 categorias em cache

────────────────────────────────────────────────────────────────────────────────
📄 Processando página 1 (100 produtos)
────────────────────────────────────────────────────────────────────────────────

[1] 📦 Notebook Dell Inspiron 3530 i7 13th 16GB 1TB
    ID: 16532547622
    ⏭️  Ja possui codigo

[2] 📦 Teclado E Mouse Sem Fio Dell Pro Abnt2
    ID: 16536153344
    🏷️  Código gerado: PERI00001
    ✅ Atualizado com sucesso (Categoria Periféricos)

[3] 📦 Placa Mãe Asus Prime B450M-Gaming
    ID: 16540021938
    🏷️  Código gerado: PLMA00001
    ✅ Atualizado com sucesso (Peca - Subcategoria Placa Mãe)
    
    🔀 Produto tem 2 variações
      🔍 Processando variação: Placa Mãe Asus Prime B450M-Gaming DDR4
      🏷️  Código gerado para variação: PLMA00002
      ✅ Variação atualizada com sucesso

[...]

📄 Página 1 processada (100 produtos)

================================================================================
📊 RELATÓRIO FINAL
================================================================================
✅ Produtos processados: 324
🏷️  Códigos gerados e atualizados: 187
⏭️  Ignorados (já tinham código/regra): 135
❌ Erros: 2
💾 Dump salvo: products_dump.json
================================================================================

📊 ESTATÍSTICAS DO BANCO DE DADOS
================================================================================
Contadores de código cadastrados: 23

Últimos contadores usados:
  • NTB: 00042 (Notebook)
  • PLMA: 00015 (Peças>>Placa Mãe)
  • MEMO: 00008 (Peças>>Memória RAM)
  • PERI: 00023 (Periféricos)
  • SSD: 00012 (Armazenamento>>SSD)
================================================================================
```

---

## 📐 Regras de Negócio - Geração de Códigos

### 1. **Produtos que NÃO recebem código**

| Condição | Motivo |
|----------|--------|
| `codigo != ""` | Já possui código (não sobrescreve) |
| `categoria == null` | Sem categoria definida |
| `categoria == "SubMaquina"` | Regra de negócio específica |
| `subcategoria == "SubMaquina"` | Regra de negócio específica |

### 2. **Padrões de Prefixo por Categoria**

#### **Categoria: Notebook, Mini, SFF**
```
Prefixo: NTB
Formato: NTB00001, NTB00002, ...
Exemplo:
  - Produto: "Notebook Dell Inspiron 15"
  - Código gerado: NTB00023
```

#### **Categoria: Peças** (usa SUBCATEGORIA)
```
Prefixo: Baseado na subcategoria
Formato: {2 letras palavra 1}{2 letras palavra 2} + número

Exemplos:
  Peças >> Placa Mãe    → PLMA00001
  Peças >> Memória RAM  → MEMO00001
  Peças >> SSD          → SSD00001
  Peças >> Cooler       → COOL00001
```

**Algoritmo de geração do prefixo:**
```python
def get_category_prefix(category_name):
    # Remove acentos: "Placa Mãe" → "Placa Mae"
    clean = remove_accents(category_name.lower())
    
    words = clean.split()
    
    if len(words) > 1:
        # 2 primeiras letras de cada palavra
        return (words[0][:2] + words[1][:2]).upper()
        # "placa mae" → "pl" + "ma" → "PLMA"
    else:
        # 4 primeiras letras
        return clean[:4].upper()
        # "ssd" → "SSD" (padding automático)
```

#### **Outras Categorias**
```
Prefixo: Baseado no nome da categoria (mesmo algoritmo)

Exemplos:
  Periféricos          → PERI00001
  Monitor              → MONI00001
  Gabinete             → GABI00001
  Fonte Alimentação    → FOAL00001
```

### 3. **Variações de Produto**

Produtos com variações (ex: cores, tamanhos):

```json
{
  "id": 16532547622,
  "nome": "Notebook Dell Inspiron 3530",
  "codigo": "NTB00042",  // ← Produto pai
  "variacoes": [
    {
      "id": 16532547623,
      "nome": "Notebook Dell Inspiron 3530 - Cinza",
      "codigo": ""  // ← Receberá NTB00043
    },
    {
      "id": 16532547624,
      "nome": "Notebook Dell Inspiron 3530 - Prata",
      "codigo": ""  // ← Receberá NTB00044
    }
  ]
}
```

**Comportamento:**
- Variações **herdam a categoria do produto pai**
- Recebem **códigos sequenciais** do mesmo prefixo
- São atualizadas via `PATCH /produtos/{variacao_id}`

---

## 🗄️ Persistência no Banco de Dados

### Tabela: `code_counters`

```sql
CREATE TABLE code_counters (
    prefix TEXT PRIMARY KEY,        -- "NTB", "PLMA", "PERI", etc
    last_value INTEGER NOT NULL,    -- Último número usado
    category_id INTEGER,            -- ID da categoria no Bling
    category_name TEXT,             -- Nome completo (ex: "Peças>>Placa Mãe")
    updated_at TEXT NOT NULL        -- Timestamp ISO 8601
);
```

**Exemplo de dados:**

| prefix | last_value | category_id | category_name | updated_at |
|--------|------------|-------------|---------------|------------|
| NTB | 42 | 1852669 | Notebook | 2024-01-15T14:32:18 |
| PLMA | 15 | 1852701 | Peças>>Placa Mãe | 2024-01-15T14:33:05 |
| MEMO | 8 | 1852702 | Peças>>Memória RAM | 2024-01-15T14:34:12 |

### Operação Thread-Safe

```python
def get_next_code(prefix):
    # 1. UPDATE (incrementa se existir)
    UPDATE code_counters 
    SET last_value = last_value + 1
    WHERE prefix = 'NTB';
    
    # 2. Se não existia, INSERT
    if rowcount == 0:
        INSERT INTO code_counters (prefix, last_value, ...)
        VALUES ('NTB', 1, ...);
        return "NTB00001"
    
    # 3. Retornar valor atualizado
    SELECT last_value FROM code_counters WHERE prefix = 'NTB';
    # Resultado: 43 → Retorna "NTB00043"
```

**Vantagem:** Evita duplicação mesmo em execuções paralelas (SQLite gerencia locks automaticamente).

---

## 📤 Output: products_dump.json

Arquivo JSON com **snapshot completo** de todos os produtos processados:

```json
[
  {
    "id": 16532547622,
    "nome": "Notebook Dell Inspiron 3530 i7 13th 16GB 1TB",
    "codigo": "NTB00042",
    "preco": 3690,
    "tipo": "P",
    "situacao": "A",
    "formato": "V",
    "estoque": {
      "minimo": 0,
      "maximo": 0,
      "saldoVirtualTotal": 0
    },
    "categoria": {
      "id": 1852669
    },
    "variacoes": [
      {
        "id": 16532547623,
        "nome": "Notebook Dell Inspiron 3530 - Cinza",
        "codigo": "NTB00043"
      }
    ]
  },
  {
    "id": 16536153344,
    "nome": "Teclado E Mouse Sem Fio Dell Pro",
    "codigo": "PERI00001",
    "categoria": {
      "id": 1852670
    }
  }
]
```

**Utilidade:**
- Backup histórico
- Análise offline
- Importação em outros sistemas
- Auditoria de códigos gerados

---

## ⚠️ Quando Executar

### ✅ Executar quando:

1. **Instalação inicial** - Popularizar códigos em produtos existentes
2. **Limpeza de dados** - Corrigir produtos sem código
3. **Migração** - Após importação em massa de produtos
4. **Auditoria** - Verificar consistência dos códigos

### ❌ NÃO executar:

1. **Em produção contínua** - Use `webhook_server.py` para automação
2. **Concorrentemente** - Risco de duplicação (embora mitigado pelo SQLite)
3. **Sem backup** - Sempre faça backup do `bling_data.db` antes

### 🔁 Re-execução

Se executar novamente:
- Produtos **com código** são **ignorados** (não sobrescreve)
- Contadores **continuam** de onde pararam (preserva sequência)
- Apenas produtos **novos sem código** são processados

---

## 🚦 Rate Limiting

```python
Rate Limit Configurado:
- 3 requisições/segundo
- 120.000 requisições/dia

Cálculo de Tempo:
- 1.000 produtos ≈ 2.000 requisições (1 lista + 1 detalhes por produto)
- Tempo estimado: ~11 minutos

- 10.000 produtos ≈ 20.000 requisições
- Tempo estimado: ~110 minutos (1h50m)
```

**Otimização:** O script respeita automaticamente os limites com `RateLimiter`.

---

## 🐛 Tratamento de Erros

| Erro | Comportamento |
|------|---------------|
| Produto sem categoria | Skip + log + continua |
| Erro ao buscar detalhes | Incrementa contador de erros + continua |
| Erro ao atualizar código | Log + não salva no dump + continua |
| Token expirado (401) | Refresh automático + retry |
| Rate limit (429) | Aguarda `Retry-After` + retry |
| Erro de rede | Retry com exponential backoff (3 tentativas) |

**Resiliência:** Um erro em um produto **não interrompe** o processamento dos demais.

---

# 🌐 webhook_server.py - Servidor de Eventos em Tempo Real

## 🎯 Objetivo

Servidor Flask que:
1. **Recebe webhooks** do Bling quando produtos/estoque são alterados
2. **Valida autenticidade** via assinatura HMAC
3. **Processa eventos** de forma **assíncrona** (não bloqueia resposta)
4. Automatiza:
   - Geração de código SKU em produtos novos
   - Desativação de produtos zerados por vendas

## 🔧 Arquitetura do Servidor

```
┌─────────────────────────────────────────────────────────────────┐
│                   WEBHOOK_SERVER.PY - ARQUITETURA               │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   BLING API      │ (quando algo acontece no Bling)
└────────┬─────────┘
         │ POST /webhook/bling
         │ Header: X-Bling-Signature-256
         │ Body: { eventId, event, data }
         ▼
┌─────────────────────────────────────────┐
│  FLASK SERVER (porta 5000)              │
│  ┌───────────────────────────────────┐  │
│  │ 1. VALIDAR HMAC                   │  │ ← Segurança
│  │    ├─ Calcular hash esperado      │  │
│  │    ├─ Comparar com header         │  │
│  │    └─ Rejeitar se inválido (401)  │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ 2. VERIFICAR IDEMPOTÊNCIA         │  │ ← Anti-duplicação
│  │    ├─ Checar eventId no SQLite    │  │
│  │    └─ Ignorar se já processado    │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ 3. ENFILEIRAR EVENTO              │  │ ← Assíncrono
│  │    └─ queue.put(payload)          │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ 4. RESPONDER IMEDIATAMENTE        │  │ ← < 5 segundos
│  │    └─ {"status": "queued"}        │  │
│  └───────────────────────────────────┘  │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  WORKER THREAD (background)             │
│  ┌───────────────────────────────────┐  │
│  │ Loop infinito:                    │  │
│  │   1. event = queue.get()          │  │
│  │   2. Marcar como processado       │  │
│  │   3. Rotear por tipo:             │  │
│  │      ├─ stock.updated             │  │
│  │      │   └─ process_stock_event() │  │
│  │      └─ product.created/updated   │  │
│  │          └─ process_product_event()│ │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
         │
         ├─────────────────┬───────────────────┐
         ▼                 ▼                   ▼
   ┌──────────┐      ┌──────────┐      ┌──────────┐
   │ Bling API│      │ SQLite DB│      │ Logs     │
   └──────────┘      └──────────┘      └──────────┘
```

---

## 🔐 Segurança: Validação HMAC

### O Que é HMAC?

**HMAC-SHA256** = Hash-based Message Authentication Code

- Garante que a requisição **realmente veio do Bling**
- Previne ataques de **replay** e **spoofing**

### Como Funciona

```python
# 1. BLING CALCULA (ao enviar webhook)
payload = '{"eventId":"abc123","event":"product.created",...}'
secret = "5cae81f3634b69c33ba73727376acef9417fa1e552d5bd40bf075c8fb016"

signature = "sha256=" + HMAC-SHA256(payload, secret)
# Resultado: "sha256=8f3d2a1b..."

# Header enviado:
# X-Bling-Signature-256: sha256=8f3d2a1b...

# 2. SEU SERVIDOR VALIDA
payload_recebido = request.get_data()  # Bytes BRUTOS (importante!)
secret_local = os.getenv("CLIENT_SECRET")

expected = "sha256=" + HMAC-SHA256(payload_recebido, secret_local)

if hmac.compare_digest(received, expected):
    # ✅ Autêntico
else:
    # ❌ Inválido - rejeitar
```

### ⚠️ Pontos Críticos

1. **Usar corpo BRUTO** (`request.get_data()`) - Não JSON parseado
2. **Comparação segura** (`hmac.compare_digest()`) - Previne timing attacks
3. **Secret correto** - Mesmo usado no cadastro do app no Bling

---

## 📨 Tipos de Eventos Processados

### 1. `stock.updated` - Atualização de Estoque

**Quando dispara:**
- Venda registrada
- Entrada manual de estoque
- Movimentação entre depósitos
- Ajuste de inventário

**Payload exemplo:**

```json
{
  "eventId": "evt_67890",
  "date": "2024-01-15T14:45:30Z",
  "version": "1.0",
  "event": "stock.updated",
  "companyId": 123456,
  "data": {
    "produto": {
      "id": 16532547622,
      "nome": "Notebook Dell Inspiron",
      "codigo": "NTB00042"
    },
    "deposito": {
      "id": 1,
      "nome": "Loja Principal"
    },
    "saldo": 0,
    "movimentacao": {
      "tipo": "S",
      "quantidade": 1,
      "operacao": "Venda"
    }
  }
}
```

**Processamento:**

```python
def process_stock_event(data):
    product_id = data['produto']['id']
    
    # 1. Buscar produto completo
    product = api.get_product(product_id)
    
    # 2. Verificar categoria (ignora Notebook, SFF, Mini, Monitor)
    if should_ignore_product(product):
        return
    
    # 3. Verificar estoque
    if product['estoque']['saldoVirtualTotal'] > 0:
        return  # Ainda tem estoque
    
    # 4. Verificar se zerou POR VENDAS
    is_depleted, details = check_stock_depleted_by_sales(api, product_id)
    
    # 5. Se zerou por vendas, desativar
    if is_depleted:
        api.update_product_situation(product_id, 'I')  # Inativo
```

**Regra de Negócio:**

```
DESATIVAR PRODUTO SE:
  ✅ Estoque == 0
  ✅ Categoria NÃO está em [Notebook, SFF, Mini, Monitor]
  ✅ Subcategoria NÃO é "SubMaquina"
  ✅ Entradas > 0  (produto já teve estoque)
  ✅ Entradas == Saídas_Vinculadas_a_Vendas

EXEMPLO:
  Entradas: 10 unidades
  Saídas por venda: 10 unidades
  Estoque atual: 0
  → DESATIVAR ✅

CONTRA-EXEMPLO:
  Entradas: 0 unidades
  Estoque atual: 0
  → NÃO DESATIVAR (nunca foi produzido) ❌
```

---

### 2. `product.created` / `product.updated` - Produto Novo/Atualizado

**Quando dispara:**
- Produto cadastrado manualmente
- Produto importado de planilha
- Produto atualizado (nome, preço, etc)

**Payload exemplo:**

```json
{
  "eventId": "evt_12345",
  "date": "2024-01-15T14:30:15Z",
  "version": "1.0",
  "event": "product.created",
  "companyId": 123456,
  "data": {
    "id": 16540021938,
    "nome": "Placa Mãe Asus Prime B450M",
    "codigo": "",  // ← SEM CÓDIGO
    "preco": 450.00,
    "tipo": "P",
    "situacao": "A",
    "categoria": {
      "id": 1852701
    }
  }
}
```

**Processamento:**

```python
def process_product_event(data):
    product_id = data['id']
    
    # 1. Já tem código? Ignorar
    if data.get('codigo'):
        return
    
    # 2. Buscar produto completo (precisa da categoria)
    product = api.get_product(product_id)
    
    # 3. Verificar se deve gerar código
    should_gen, reason, prefix = should_generate_code(product, category_cache)
    
    if not should_gen:
        return  # Ex: categoria "SubMaquina"
    
    # 4. Buscar categoria do cache
    category, subcategory, full, cat_id = extract_category_info(product, category_cache)
    
    # 5. Gerar código
    new_code = db.get_next_code(
        prefix=prefix,
        category_id=cat_id,
        category_name=full
    )
    # Exemplo resultado: "PLMA00016"
    
    # 6. Atualizar produto na API
    api.update_product(product_id, {"codigo": new_code})
```

**Resultado:**
```
ANTES:
{
  "id": 16540021938,
  "nome": "Placa Mãe Asus Prime B450M",
  "codigo": ""
}

DEPOIS:
{
  "id": 16540021938,
  "nome": "Placa Mãe Asus Prime B450M",
  "codigo": "PLMA00016"  ← Gerado automaticamente
}
```

---

## 🔄 Idempotência: Prevenção de Duplicação

### Problema

Bling pode enviar o **mesmo evento múltiplas vezes**:
- Falha de rede (retry automático)
- Timeout na resposta
- Eventos fora de ordem

### Solução

Usar `eventId` único como chave de deduplicação:

```python
# Tabela SQLite
CREATE TABLE processed_events (
    event_id TEXT PRIMARY KEY,  -- "evt_12345"
    event_type TEXT,            -- "product.created"
    product_id INTEGER,         -- 16540021938
    processed_at TEXT,          -- "2024-01-15T14:30:20"
    payload TEXT                -- JSON completo (opcional)
);

# Verificação
if db.is_event_processed("evt_12345"):
    return {"status": "already_processed"}

# Processar + Marcar
process_event(payload)
db.mark_event_processed("evt_12345", "product.created", 16540021938, payload)
```

**Garantia:** Mesmo evento **nunca é processado duas vezes**.

---

## ⚡ Processamento Assíncrono

### Por Que?

Bling espera resposta em **< 5 segundos**:
- Processamento pode demorar (consultas API, banco de dados)
- Resposta rápida evita retentativas desnecessárias

### Como Funciona

```python
# THREAD PRINCIPAL (Flask)
@app.route('/webhook/bling', methods=['POST'])
def webhook_handler():
    # 1. Validar (rápido)
    if not verify_hmac(...):
        return 401
    
    # 2. Enfileirar (rápido)
    event_queue.put(payload)  # ← Não bloqueia
    
    # 3. Responder IMEDIATAMENTE (<1ms)
    return {"status": "queued"}  # ✅ Bling recebe OK

# THREAD WORKER (background)
def event_processor_worker():
    while True:
        payload = event_queue.get()  # ← Aguarda eventos
        
        # Processar (pode demorar 10s+)
        if payload['event'] == 'stock.updated':
            process_stock_event(payload['data'])
```

**Benefício:** Flask responde instantaneamente, processamento real acontece em background.

---

## 🛡️ Tratamento de Erros no Worker

```python
def event_processor_worker():
    while True:
        try:
            payload = event_queue.get(timeout=1)
            
            # Processar
            process_event(payload)
            
        except queue.Empty:
            continue  # Aguarda próximo evento
            
        except Exception as e:
            # Log do erro (não mata o worker!)
            print(f"❌ Erro ao processar evento: {e}")
            # Worker continua rodando
```

**Resiliência:** Um erro **não derruba o servidor** - próximos eventos são processados normalmente.

---

## 🏥 Health Check Endpoint

```python
GET /health

Response:
{
  "status": "healthy",
  "queue_size": 3,  // Eventos aguardando processamento
  "categories_loaded": true,
  "db_stats": {
    "counters": 23,
    "events": 1547,
    "recent_counters": [...]
  }
}
```

**Utilidade:**
- Monitoramento (Uptime Robot, Pingdom)
- Load balancer health checks
- Debug rápido

---

## 📊 Fluxo Completo - Exemplo Real

### Cenário: Cadastro de Produto Novo

```
PASSO 1: Usuário cadastra no Bling
┌──────────────────────────────┐
│ Bling Web Interface          │
│ ┌──────────────────────────┐ │
│ │ Nome: Memória RAM 8GB    │ │
│ │ Categoria: Peças>>Memória│ │
│ │ Preço: R$ 150,00         │ │
│ │ [SALVAR]                 │ │
│ └──────────────────────────┘ │
└──────────────────────────────┘
         ↓
         
PASSO 2: Bling dispara webhook (< 1s após salvar)
POST https://sua-vps.com/webhook/bling
Headers:
  X-Bling-Signature-256: sha256=abc123...
Body:
  {
    "eventId": "evt_98765",
    "event": "product.created",
    "data": {
      "id": 16541000001,
      "nome": "Memória RAM 8GB Kingston",
      "codigo": "",  ← SEM CÓDIGO
      "categoria": { "id": 1852702 }
    }
  }
         ↓
         
PASSO 3: Seu servidor valida e enfileira (< 50ms)
✅ HMAC válido
✅ eventId novo (não processado antes)
→ Enfileira e responde HTTP 200

         ↓
         
PASSO 4: Worker processa (background, ~2-3s)
1. Busca categoria do cache:
   ID 1852702 → "Peças>>Memória RAM"
   
2. Gera prefixo:
   "Memória RAM" → "MEMO"
   
3. Busca contador no banco:
   SELECT last_value FROM code_counters WHERE prefix='MEMO'
   → 8 (último usado: MEMO00008)
   
4. Incrementa:
   UPDATE ... SET last_value = 9
   → Novo código: MEMO00009
   
5. Atualiza produto:
   PATCH /produtos/16541000001
   Body: {"codigo": "MEMO00009"}
   
         ↓
         
PASSO 5: Produto atualizado no Bling (< 5s total)
┌──────────────────────────────┐
│ Bling - Produto              │
│ ┌──────────────────────────┐ │
│ │ ID: 16541000001          │ │
│ │ Nome: Memória RAM 8GB    │ │
│ │ Código: MEMO00009  ← ✅  │ │
│ │ Categoria: Peças>>Memória│ │
│ └──────────────────────────┘ │
└──────────────────────────────┘
```

**Usuário:** Não precisa preencher código manualmente!

---

## 🔧 Configuração no Bling

### 1. Cadastrar Webhooks

Acessar: **Configurações** → **Integrações** → **Central de Extensões** → Seu App → **Webhooks**

| Campo | Valor |
|-------|-------|
| **Recurso** | `product` |
| **Ação** | `created`, `updated` |
| **URL** | `https://sua-vps.com/webhook/bling` |
| **Método** | POST |

| Campo | Valor |
|-------|-------|
| **Recurso** | `stock` |
| **Ação** | `updated` |
| **URL** | `https://sua-vps.com/webhook/bling` |
| **Método** | POST |

### 2. Testar Webhook

Bling oferece botão **"Testar Webhook"** que envia evento fictício.

**Verificar logs:**
```bash
# Windows
Get-Content C:\BlingMonitor\logs\webhook.log -Tail 50 -Wait

# Linux
tail -f /var/log/bling-webhook.log
```

**Output esperado:**
```
✅ Webhook recebido: product.created (eventId: test_12345)
🔄 Processando evento: product.created (ID: test_12345)
   ℹ️  Produto já possui código: TEST00001
✅ Evento processado com sucesso
```

---

# 🔁 Regras de Negócio Compartilhadas

## Categorias Excluídas (NÃO desativa estoque zero)

```python
EXCLUDED_CATEGORIES = {
    "notebook",  # Case-insensitive
    "sff",
    "mini",
    "monitor"
}
```

**Motivo:** Produtos de alto valor ou importados - desativação manual apenas.

## Subcategorias Ignoradas (NÃO gera código)

```python
IGNORE_SUBCATEGORIES = {
    "submaquina"  # Case-insensitive
}
```

**Motivo:** Categoria especial - pendente de definição de regra.

## Hierarquia de Categorias

Bling usa separador `>>`:

```
Categoria Pai >> Subcategoria

Exemplos:
- Peças >> Placa Mãe
- Peças >> Memória RAM
- Armazenamento >> SSD
- Armazenamento >> HDD
```

**Parsing:**
```python
full_name = "Peças >> Placa Mãe"
parts = full_name.split('>>')
category = parts[0].strip()     # "Peças"
subcategory = parts[-1].strip() # "Placa Mãe"
```

---

# 🏗️ Arquitetura Geral do Sistema

```
┌───────────────────────────────────────────────────────────────────┐
│                         BLING ERP (CLOUD)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐              │
│  │  Produtos   │  │  Categorias │  │  Estoque     │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘              │
└─────────┼─────────────────┼─────────────────┼────────────────────┘
          │                 │                 │
          │ REST API        │                 │ Webhooks
          │ (HTTPS)         │                 │ (HTTPS)
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SEU SERVIDOR (VPS/Windows)                  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  bling_auth.py                                           │  │
│  │  ├─ OAuth 2.0                                            │  │
│  │  ├─ Token Management                                     │  │
│  │  └─ Auto-refresh                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  bling_api.py                                            │  │
│  │  ├─ Rate Limiter (3 req/s, 120k/dia)                    │  │
│  │  ├─ Retry Logic                                          │  │
│  │  └─ HTTP Client                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  bling_utils.py                                          │  │
│  │  ├─ CategoryCache (ID→Nome)                              │  │
│  │  ├─ Regras de Negócio                                    │  │
│  │  └─ Helpers                                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  bling_db.py (SQLite)                                    │  │
│  │  ┌────────────────┐  ┌────────────────┐                 │  │
│  │  │ code_counters  │  │processed_events│                 │  │
│  │  │ - NTB: 42      │  │ - evt_123      │                 │  │
│  │  │ - PLMA: 15     │  │ - evt_456      │                 │  │
│  │  └────────────────┘  └────────────────┘                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────┐       ┌─────────────────────────┐    │
│  │  dump_products.py   │       │  webhook_server.py      │    │
│  │  ┌───────────────┐  │       │  ┌───────────────────┐  │    │
│  │  │Execução manual│  │       │  │ Flask Server      │  │    │
│  │  │Uma vez ou     │  │       │  │ Sempre rodando    │  │    │
│  │  │esporádica     │  │       │  │ (serviço Windows) │  │    │
│  │  └───────────────┘  │       │  └───────────────────┘  │    │
│  └─────────────────────┘       └─────────────────────────┘    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  test.py (opcional)                                      │  │
│  │  Loop contínuo: Verifica estoque zero + desativa        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

# 📝 Resumo Executivo

| Script | Propósito | Execução | Output |
|--------|-----------|----------|--------|
| **dump_products.py** | Gera códigos SKU para produtos existentes | Manual/Esporádica | JSON + Banco SQLite |
| **webhook_server.py** | Automação em tempo real (novos produtos + estoque) | Contínua (serviço) | Logs + Banco SQLite |
| **test.py** | Monitoramento periódico de estoque (alternativa a webhooks) | Loop com intervalo | Logs |

**Fluxo recomendado:**
1. **Primeira vez:** Executar `dump_products.py` (popular códigos)
2. **Produção:** Manter `webhook_server.py` rodando (automação)
3. **Opcional:** `test.py` como backup (se webhooks falharem)
