# 📦 dump_products.py - Gerador de Códigos SKU

## 🎯 O Que Este Script Faz

Varre **todos os produtos** cadastrados no Bling e cria códigos SKU automáticos para produtos que não têm código.

**Exemplo:**
- **Antes:** Produto "Placa Mãe Asus" sem código
- **Depois:** Produto "Placa Mãe Asus" com código `PLMA00001`

---

## ⚙️ Configuração Inicial

### 1. Criar arquivo `.env`

Renomeie `.env.example` para `.env` e preencha:

```env
CLIENT_ID=seu_client_id_do_bling
CLIENT_SECRET=seu_client_secret_do_bling
REDIRECT_URI=https://localhost/
AUTH_CODE=codigo_de_autorizacao
```

### 2. Como Obter o AUTH_CODE

**Passo 1:** Acesse no navegador (substitua `SEU_CLIENT_ID` pelo seu Client ID):
```
https://www.bling.com.br/Api/v3/oauth/authorize?response_type=code&client_id=SEU_CLIENT_ID&state=12345
```

**Passo 2:** Faça login no Bling e clique em "Autorizar"

**Passo 3:** Você será redirecionado para uma URL como:
```
https://localhost/?code=ABC123XYZ456&state=12345
```

**Passo 4:** Copie o valor após `code=` (exemplo: `ABC123XYZ456`)

**Passo 5:** Cole no arquivo `.env`:
```env
AUTH_CODE=ABC123XYZ456
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

---

## 🚀 Como Executar

### Windows
```bash
cd C:\BlingMonitor
python dump_products.py
```

### Linux/Mac
```bash
cd ~/bling_monitor
python dump_products.py
```

---

## ⏱️ Quanto Tempo Demora?

| Quantidade de Produtos | Tempo Estimado |
|------------------------|----------------|
| 100 produtos | ~2 minutos |
| 500 produtos | ~10 minutos |
| 1.000 produtos | ~20 minutos |
| 5.000 produtos | ~1h45min |
| 10.000 produtos | ~3h30min |

**Por quê demora?** O Bling limita em 3 requisições por segundo. O script respeita esse limite automaticamente.

---

## 📊 O Que Aparece na Tela

```
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

[4] 📦 Memória RAM Kingston 8GB DDR4
    ID: 16540022105
    🏷️  Código gerado: MEMO00001
    ✅ Atualizado com sucesso (Peca - Subcategoria Memória RAM)

[...]

📄 Página 1 processada (100 produtos)

────────────────────────────────────────────────────────────────────────────────
📄 Processando página 2 (100 produtos)
────────────────────────────────────────────────────────────────────────────────

[...]

💾 Salvando dump em products_dump.json...

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

## 🏷️ Padrões de Código Gerados

### Categorias Especiais

| Categoria | Prefixo | Exemplo | Observação |
|-----------|---------|---------|------------|
| Notebook | NTB | NTB00001, NTB00002... | Fixo |
| Mini | NTB | NTB00043, NTB00044... | Fixo |
| SFF | NTB | NTB00045, NTB00046... | Fixo |

### Categoria "Peças" (usa subcategoria)

| Subcategoria | Prefixo | Exemplo |
|--------------|---------|---------|
| Placa Mãe | PLMA | PLMA00001 |
| Memória RAM | MEMO | MEMO00001 |
| Processador | PROC | PROC00001 |
| SSD | SSD | SSD00001 |
| HD | HD | HD00001 |
| Fonte | FONT | FONT00001 |
| Cooler | COOL | COOL00001 |

### Outras Categorias (usa nome da categoria)

| Categoria | Prefixo | Exemplo |
|-----------|---------|---------|
| Periféricos | PERI | PERI00001 |
| Monitor | MONI | MONI00001 |
| Gabinete | GABI | GABI00001 |
| Mouse Teclado | MOTE | MOTE00001 |
| Webcam | WEBC | WEBC00001 |

**Como o prefixo é gerado:**
- Se a categoria tem 2+ palavras: Pega 2 letras de cada palavra
  - "Mouse Teclado" → **MO**use **TE**clado → `MOTE`
- Se tem 1 palavra: Pega 4 primeiras letras
  - "Webcam" → `WEBC`

---

## ✅ Produtos que RECEBEM Código

- ✅ Produto **sem código** (campo vazio)
- ✅ Tem **categoria** definida
- ✅ Categoria **não é** "SubMaquina"

## ❌ Produtos que NÃO Recebem Código

- ❌ Já tem código preenchido → **Ignora** (não sobrescreve)
- ❌ Categoria é "SubMaquina" → **Ignora** (regra de negócio)
- ❌ Subcategoria é "SubMaquina" → **Ignora**
- ❌ Não tem categoria → **Ignora**

---

## 🔢 Sistema de Numeração Sequencial

Os códigos são sequenciais **por prefixo**:

```
Primeira execução:
  - Placa Mãe Asus → PLMA00001
  - Memória Kingston → MEMO00001
  - Placa Mãe Gigabyte → PLMA00002
  - Memória Corsair → MEMO00002

Segunda execução (semana depois):
  - Nova Placa Mãe MSI → PLMA00003  ← Continua de onde parou
  - Nova Memória HyperX → MEMO00003
```

**Onde fica salvo?** No arquivo `bling_data.db` (banco SQLite)

---

## 📁 Arquivos Gerados

### `bling_data.db` (Banco de Dados)

**Contém:**
- Último número usado para cada prefixo
- Histórico de processamento

**⚠️ IMPORTANTE:** 
- **Faça backup** deste arquivo regularmente
- Se perder, os códigos começam do 1 novamente (risco de duplicação!)

**Backup manual:**
```bash
# Windows
copy bling_data.db backup\bling_data_2024-01-15.db

# Linux
cp bling_data.db backup/bling_data_2024-01-15.db
```

### `products_dump.json` (Snapshot)

**Contém:** Cópia de todos os produtos processados em formato JSON

**Utilidade:**
- Backup histórico
- Importar em Excel (converter JSON → CSV)
- Análise de dados

---

## 🔁 Posso Executar Novamente?

**✅ SIM!** É seguro executar múltiplas vezes.

**O que acontece:**
- Produtos **com código** são **ignorados**
- Produtos **sem código** recebem o **próximo número** da sequência
- **Não duplica** códigos existentes

**Exemplo:**

```
Primeira execução:
  - 100 produtos sem código → gera códigos

Segunda execução (1 mês depois):
  - 100 produtos antigos → ignora (já têm código)
  - 20 produtos novos → gera códigos (continua numeração)
```

---

## 🕐 Quando Executar

### ✅ Deve Executar

1. **Primeira instalação** - Popular códigos em produtos existentes
2. **Após importar planilha** - Novos produtos sem código
3. **Limpeza de dados** - Corrigir produtos que ficaram sem código
4. **Periodicamente** - Garantir que nada ficou sem código

### ❌ Não Precisa Executar

- Diariamente (use o `webhook_server.py` para automação)
- Se todos os produtos já têm código
- Concorrentemente em vários computadores

---

## ⚠️ Problemas Comuns

### ❌ Erro: "401 Unauthorized"

**Causa:** O AUTH_CODE expirou (válido por ~30 dias)

**Solução:**
1. Acesse novamente o link de autorização
2. Pegue o novo código
3. Atualize no `.env`
4. Execute novamente

---

### ❌ Erro: "No tokens found and no AUTH_CODE"

**Causa:** Arquivo `.env` não encontrado ou AUTH_CODE vazio

**Solução:**
1. Verifique se o arquivo `.env` existe na mesma pasta do script
2. Verifique se `AUTH_CODE=...` está preenchido
3. Não deixe espaços: `AUTH_CODE=ABC123` ✅ | `AUTH_CODE = ABC123` ❌

---

### ❌ Produto da categoria "Peças" não recebe código

**Causa:** Produto não tem subcategoria definida

**Exemplo:**
```
Categoria: Peças
Subcategoria: (vazio) ← PROBLEMA
```

**Solução:** No Bling, edite o produto e defina a subcategoria:
- Peças → Placa Mãe
- Peças → Memória RAM
- Peças → SSD
- etc.

---

### ❌ Script travou / parou de responder

**Possíveis causas:**
1. **Internet caiu** → O script aguarda 30s e tenta novamente
2. **Rate limit** → Aguarde 1 minuto e execute novamente
3. **Servidor Bling fora do ar** → Aguarde e tente mais tarde

**O script salva o progresso?** 
- ✅ SIM - Os códigos já gerados estão salvos no banco
- ✅ Pode parar e continuar depois sem problemas

---

## 🧪 Testar Antes de Rodar em Todos os Produtos

### Teste Rápido (10 produtos)

Edite o arquivo `dump_products.py` temporariamente:

**Linha 152, mude:**
```python
# ANTES
data = api.get_products(page=page, limit=100)

# DEPOIS (teste com 10 produtos apenas)
data = api.get_products(page=1, limit=10)
if page > 1:  # Para após primeira página
    break
```

Execute e veja se funcionou. Se OK, desfaça a alteração e rode completo.

---

## 📊 Consultar Códigos Gerados

### Ver últimos códigos no banco

```bash
sqlite3 bling_data.db
```

Dentro do SQLite:
```sql
-- Ver todos os contadores
SELECT prefix, last_value, category_name 
FROM code_counters 
ORDER BY last_value DESC;

-- Resultado:
-- NTB|42|Notebook
-- PERI|23|Periféricos
-- PLMA|15|Peças>>Placa Mãe
```

### Ver no Excel

Abra o arquivo `products_dump.json` em:
- **Excel:** Dados → Obter Dados → De Arquivo → JSON
- **Google Sheets:** Importar → Carregar → JSON
- **Online:** https://jsonviewer.stack.hu/ (colar o conteúdo)

---

## ✅ Checklist de Execução

Antes de executar, verifique:

```
□ Arquivo .env existe e está preenchido
□ AUTH_CODE está válido (recente)
□ pip install -r requirements.txt executado
□ Backup do bling_data.db feito (se já existe)
□ Internet estável
□ Tempo disponível (veja tabela de tempo estimado)
```

Durante a execução:

```
□ Números estão sendo gerados corretamente
□ Nenhum erro crítico aparece
□ Produtos estão sendo atualizados no Bling
```

Após a execução:

```
□ Relatório final mostra sucesso
□ Verificar alguns produtos no Bling manualmente
□ Fazer backup do bling_data.db atualizado
□ Guardar o products_dump.json
```

---

## 🆘 Suporte

### Informações para Enviar ao Suporte

Se precisar de ajuda, envie:

```bash
# 1. Últimas 100 linhas do log (se houver erro)
# Copie o que apareceu na tela

# 2. Estatísticas do banco
sqlite3 bling_data.db "SELECT * FROM code_counters ORDER BY updated_at DESC LIMIT 20;"

# 3. Versão do Python
python --version

# 4. Dependências instaladas
pip list
```

---

## 📝 Resumo Executivo

| O Que | Como |
|-------|------|
| **Executar** | `python dump_products.py` |
| **Quando** | Uma vez na instalação inicial, depois esporadicamente |
| **Tempo** | ~2 minutos para cada 100 produtos |
| **Output** | Produtos atualizados no Bling + arquivos `bling_data.db` e `products_dump.json` |
| **Seguro re-executar?** | SIM - Não duplica códigos existentes |
| **Backup importante** | `bling_data.db` |

---
