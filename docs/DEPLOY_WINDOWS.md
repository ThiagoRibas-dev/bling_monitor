# 📖 DOCUMENTAÇÃO DE USO - DEPLOY EM WINDOWS SERVER

## 📝 Tabela de Conteúdos

1.  [🎯 Pré-requisitos](#-pré-requisitos)
2.  [🚀 Instalação Inicial](#-instalação-inicial)
    *   [1. Conectar no servidor via RDP](#1-conectar-no-servidor-via-rdp)
    *   [2. Instalar Python](#2-instalar-python)
    *   [3. Instalar Git (opcional, mas recomendado)](#3-instalar-git-opcional-mas-recomendado)
    *   [4. Criar estrutura de diretórios](#4-criar-estrutura-de-diretórios)
    *   [5. Transferir código para o servidor](#5-transferir-código-para-o-servidor)
    *   [6. Criar ambiente virtual](#6-criar-ambiente-virtual)
    *   [7. Instalar dependências](#7-instalar-dependências)
    *   [8. Configurar variáveis de ambiente](#8-configurar-variáveis-de-ambiente)
    *   [9. Obter AUTH_CODE inicial](#9-obter-auth_code-inicial)
    *   [10. Aplicar patches de correção](#10-aplicar-patches-de-correção)
3.  [⚙️ Configurar Serviços Windows](#-configurar-serviços-windows)
    *   [Opção A - NSSM (Non-Sucking Service Manager) - **RECOMENDADO**](#opção-a---nssm-non-sucking-service-manager---recomendado)
        *   [1. Instalar NSSM](#1-instalar-nssm)
        *   [2. Criar serviço de monitoramento](#2-criar-serviço-de-monitoramento)
        *   [3. Criar serviço de webhook](#3-criar-serviço-de-webhook)
        *   [4. Criar diretório de logs](#4-criar-diretório-de-logs)
        *   [5. Verificar serviços](#5-verificar-serviços)
    *   [Opção B - Task Scheduler (alternativa sem NSSM)](#opção-b---task-scheduler-alternativa-sem-nssm)
        *   [1. Criar tarefa de monitoramento](#1-criar-tarefa-de-monitoramento)
        *   [2. Criar tarefa de webhook](#2-criar-tarefa-de-webhook)
        *   [3. Iniciar tarefas](#3-iniciar-tarefas)
4.  [🌐 Configuração IIS + SSL (Reverse Proxy para Webhook)](#-configuração-iis--ssl-reverse-proxy-para-webhook)
    *   [1. Instalar IIS](#1-instalar-iis)
    *   [2. Habilitar Proxy no ARR](#2-habilitar-proxy-no-arr)
    *   [3. Criar site no IIS](#3-criar-site-no-iis)
    *   [4. Configurar URL Rewrite (Reverse Proxy)](#4-configurar-url-rewrite-reverse-proxy)
    *   [5. Instalar Certificado SSL](#5-instalar-certificado-ssl)
    *   [6. Adicionar binding HTTPS ao site](#6-adicionar-binding-https-ao-site)
    *   [7. Configurar firewall](#7-configurar-firewall)
    *   [8. Testar configuração](#8-testar-configuração)
5.  [📊 Comandos de Gerenciamento](#-comandos-de-gerenciamento)
    *   [Gerenciar serviços NSSM](#gerenciar-serviços-nssm)
    *   [Gerenciar via Services (GUI)](#gerenciar-via-services-gui)
    *   [Ver logs](#ver-logs)
    *   [Ver logs do Event Viewer (se usar Task Scheduler)](#ver-logs-do-event-viewer-se-usar-task-scheduler)
6.  [🔧 Execuções Manuais (Tarefas Únicas)](#-execuções-manuais-tarefas-únicas)
    *   [1. Gerar códigos para produtos existentes](#1-gerar-códigos-para-produtos-existentes)
    *   [2. Testar autenticação](#2-testar-autenticação)
    *   [3. Executar manualmente (debug)](#3-executar-manualmente-debug)
7.  [📅 Configuração no Bling (Webhooks)](#-configuração-no-bling-webhooks)
    *   [1. Acessar Central de Extensões](#1-acessar-central-de-extensões)
    *   [2. Cadastrar webhooks](#2-cadastrar-webhooks)
    *   [3. Testar webhook](#3-testar-webhook)
8.  [🔍 Monitoramento e Manutenção](#-monitoramento-e-manutenção)
    *   [Rotação de logs (evitar disco cheio)](#rotação-de-logs-evitar-disco-cheio)
    *   [Backup do banco de dados](#backup-do-banco-de-dados)
    *   [Monitorar uso de disco](#monitorar-uso-de-disco)
    *   [Script de monitoramento de saúde](#script-de-monitoramento-de-saúde)
9.  [🚨 Troubleshooting](#-troubleshooting)
    *   [Problema: Serviço não inicia](#problema-serviço-não-inicia)
    *   [Problema: Erro "Python não encontrado"](#problema-erro-python-não-encontrado)
    *   [Problema: Porta 5000 já em uso](#problema-porta-5000-já-em-uso)
    *   [Problema: Certificado SSL não funciona](#problema-certificado-ssl-não-funciona)
    *   [Problema: Webhook retorna 500 Internal Server Error](#problema-webhook-retorna-500-internal-server-error)
    *   [Problema: Rate limit excedido](#problema-rate-limit-excedido)
    *   [Problema: Imports circulares (ImportError)](#problema-imports-circulares-importerror)
10. [📈 Métricas e Relatórios](#-métricas-e-relatórios)
    *   [Script de relatório diário](#script-de-relatório-diário)
    *   [Ver últimos produtos processados](#ver-últimos-produtos-processados)
    *   [Dashboard em tempo real (PowerShell)](#dashboard-em-tempo-real-powershell)
11. [🔄 Atualização do Código](#-atualização-do-código)
12. [✅ Checklist Pós-Instalação](#-checklist-pós-instalação)
13. [📞 Scripts Úteis Adicionais](#-scripts-úteis-adicionais)
    *   [Restart completo (quando algo der errado)](#restart-completo-quando-algo-der-errado)
    *   [Uninstall completo](#uninstall-completo)

---

## 🎯 Pré-requisitos

-   Windows Server 2016+ ou Windows 10/11 Pro
-   Acesso RDP (Remote Desktop) como Administrador
-   Python 3.8+ instalado
-   Domínio apontando para o IP da VPS (para webhook)
-   Portas liberadas: 80, 443, 5000 (ou porta customizada)

---

## 🚀 Instalação Inicial

### 1. Conectar no servidor via RDP

```
Executar (Win+R): mstsc
Servidor: seu-ip-da-vps
Usuário: Administrator
```

### 2. Instalar Python

**Opção A - Download Manual:**

1.  Acesse: https://www.python.org/downloads/windows/
2.  Baixe **Python 3.11.x** (versão estável mais recente)
3.  Execute o instalador
4.  ✅ **IMPORTANTE:** Marque "Add Python to PATH"
5.  Clique em "Install Now"

**Opção B - Via Chocolatey (recomendado):**

```powershell
# Abrir PowerShell como Administrador
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Instalar Python
choco install python -y

# Verificar instalação
python --version
```

### 3. Instalar Git (opcional, mas recomendado)

```powershell
choco install git -y
```

### 4. Criar estrutura de diretórios

```powershell
# Abrir PowerShell como Administrador
cd C:\

# Criar diretório do projeto
New-Item -ItemType Directory -Path "C:\BlingMonitor"
cd C:\BlingMonitor
```

### 5. Transferir código para o servidor

**Opção A - Via Git:**

```powershell
cd C:\BlingMonitor
git clone https://github.com/seu-usuario/bling_monitor.git .
```

**Opção B - Via Área de Transferência RDP:**

1.  No seu PC local, copie a pasta `bling_monitor`
2.  Na sessão RDP, cole em `C:\BlingMonitor`

**Opção C - Via PowerShell remoto (do seu PC):**

```powershell
# No seu PC local
$Session = New-PSSession -ComputerName SEU_IP -Credential Administrator
Copy-Item -Path "D:\Projects\bling_monitor\*" -Destination "C:\BlingMonitor" -ToSession $Session -Recurse
```

### 6. Criar ambiente virtual

```powershell
cd C:\BlingMonitor
python -m venv venv

# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Se houver erro de execução de scripts:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 7. Instalar dependências

```powershell
# Com ambiente virtual ativado
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 8. Configurar variáveis de ambiente

Criar arquivo `.env` no diretório `C:\BlingMonitor`:

```powershell
notepad .env
```

Conteúdo do arquivo:

```env
# Credenciais Bling API
CLIENT_ID=seu_client_id_aqui
CLIENT_SECRET=seu_client_secret_aqui
REDIRECT_URI=https://sua-vps.com/callback
AUTH_CODE=codigo_obtido_na_primeira_execucao

# Configurações de execução
MINUTES_BETWEEN_RUNS=60

# Webhook
WEBHOOK_PORT=5000

# Database
DATABASE_PATH=C:\BlingMonitor\bling_data.db
```

Salvar e fechar.

### 9. Obter AUTH_CODE inicial

1.  Abra o navegador no servidor
2.  Acesse:
    ```
    https://www.bling.com.br/Api/v3/oauth/authorize?response_type=code&client_id=SEU_CLIENT_ID&redirect_uri=https://sua-vps.com/callback
    ```
3.  Autorize o aplicativo
4.  Copie o `code` da URL de redirecionamento
5.  Adicione no `.env`:
    ```env
    AUTH_CODE=codigo_copiado
    ```

### 10. Aplicar patches de correção

Criar arquivo `C:\BlingMonitor\bling_utils.py` com o conteúdo do **Patch 2** da análise anterior.

Editar arquivos existentes conforme **Patches 3, 4 e 5**.

---

## ⚙️ Configurar Serviços Windows

### Opção A - NSSM (Non-Sucking Service Manager) - **RECOMENDADO**

#### 1. Instalar NSSM

```powershell
# Via Chocolatey
choco install nssm -y

# OU baixar manualmente
# https://nssm.cc/download
# Extrair para C:\Program Files\nssm\
```

#### 2. Criar serviço de monitoramento

```powershell
# Abrir PowerShell como Administrador
cd C:\BlingMonitor

# Criar serviço
nssm install BlingMonitor "C:\BlingMonitor\venv\Scripts\python.exe" "C:\BlingMonitor\test.py"

# Configurar parâmetros
nssm set BlingMonitor AppDirectory "C:\BlingMonitor"
nssm set BlingMonitor DisplayName "Bling Monitor - Desativação Automática"
nssm set BlingMonitor Description "Monitora estoque e desativa produtos zerados por vendas"
nssm set BlingMonitor Start SERVICE_AUTO_START

# Configurar logs
nssm set BlingMonitor AppStdout "C:\BlingMonitor\logs\monitor.log"
nssm set BlingMonitor AppStderr "C:\BlingMonitor\logs\monitor-error.log"

# Configurar restart automático
nssm set BlingMonitor AppRestartDelay 10000
nssm set BlingMonitor AppExit Default Restart

# Iniciar serviço
nssm start BlingMonitor
```

#### 3. Criar serviço de webhook

```powershell
# Criar serviço
nssm install BlingWebhook "C:\BlingMonitor\venv\Scripts\python.exe" "C:\BlingMonitor\webhook_server.py"

# Configurar parâmetros
nssm set BlingWebhook AppDirectory "C:\BlingMonitor"
nssm set BlingWebhook DisplayName "Bling Webhook Server"
nssm set BlingWebhook Description "Servidor de webhooks para eventos do Bling"
nssm set BlingWebhook Start SERVICE_AUTO_START

# Configurar logs
nssm set BlingWebhook AppStdout "C:\BlingMonitor\logs\webhook.log"
nssm set BlingWebhook AppStderr "C:\BlingMonitor\logs\webhook-error.log"

# Configurar restart automático
nssm set BlingWebhook AppRestartDelay 10000
nssm set BlingWebhook AppExit Default Restart

# Iniciar serviço
nssm start BlingWebhook
```

#### 4. Criar diretório de logs

```powershell
New-Item -ItemType Directory -Path "C:\BlingMonitor\logs"
```

#### 5. Verificar serviços

```powershell
# Via PowerShell
Get-Service Bling*

# OU abrir Gerenciador de Serviços
services.msc
```

### Opção B - Task Scheduler (alternativa sem NSSM)

#### 1. Criar tarefa de monitoramento

```powershell
# Script PowerShell auxiliar
$Script = @'
Set-Location "C:\BlingMonitor"
.\venv\Scripts\Activate.ps1
python test.py
'@

$Script | Out-File -FilePath "C:\BlingMonitor\run_monitor.ps1" -Encoding UTF8

# Criar tarefa agendada
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File C:\BlingMonitor\run_monitor.ps1"
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Settings = New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "BlingMonitor" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Monitora estoque Bling"
```

#### 2. Criar tarefa de webhook

```powershell
# Script PowerShell auxiliar
$Script = @'
Set-Location "C:\BlingMonitor"
.\venv\Scripts\Activate.ps1
python webhook_server.py
'@

$Script | Out-File -FilePath "C:\BlingMonitor\run_webhook.ps1" -Encoding UTF8

# Criar tarefa agendada
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File C:\BlingMonitor\run_webhook.ps1"
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Settings = New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "BlingWebhook" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Servidor webhook Bling"
```

#### 3. Iniciar tarefas

```powershell
Start-ScheduledTask -TaskName "BlingMonitor"
Start-ScheduledTask -TaskName "BlingWebhook"
```

---

## 🌐 Configuração IIS + SSL (Reverse Proxy para Webhook)

### 1. Instalar IIS

```powershell
# PowerShell como Administrador
Install-WindowsFeature -Name Web-Server -IncludeManagementTools
Install-WindowsFeature -Name Web-WebSockets

# Instalar URL Rewrite Module
# Baixar de: https://www.iis.net/downloads/microsoft/url-rewrite
# OU via Chocolatey:
choco install urlrewrite -y

# Instalar Application Request Routing (ARR)
# Baixar de: https://www.iis.net/downloads/microsoft/application-request-routing
choco install iis-arr -y
```

### 2. Habilitar Proxy no ARR

```powershell
# Abrir IIS Manager
inetmgr

# 1. Clique no servidor (nível raiz)
# 2. Abra "Application Request Routing Cache"
# 3. No painel direito, clique "Server Proxy Settings"
# 4. Marque "Enable proxy"
# 5. Clique "Apply"
```

**OU via PowerShell:**

```powershell
Set-WebConfigurationProperty -PSPath 'MACHINE/WEBROOT/APPHOST' -Filter "system.webServer/proxy" -Name "enabled" -Value "True"
```

### 3. Criar site no IIS

```powershell
# Criar diretório web
New-Item -ItemType Directory -Path "C:\inetpub\bling-webhook"

# Criar arquivo index.html (placeholder)
@"
<!DOCTYPE html>
<html>
<head><title>Bling Webhook</title></head>
<body><h1>Bling Integration Active</h1></body>
</html>
"@ | Out-File -FilePath "C:\inetpub\bling-webhook\index.html" -Encoding UTF8

# Criar site
New-IISSite -Name "BlingWebhook" -PhysicalPath "C:\inetpub\bling-webhook" -BindingInformation "*:80:seu-dominio.com"
```

### 4. Configurar URL Rewrite (Reverse Proxy)

Criar arquivo `C:\inetpub\bling-webhook\web.config`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <rule name="Webhook Proxy" stopProcessing="true">
                    <match url="^webhook/bling(.*)$" />
                    <action type="Rewrite" url="http://localhost:5000/webhook/bling{R:1}" />
                    <serverVariables>
                        <set name="HTTP_X_ORIGINAL_HOST" value="{HTTP_HOST}" />
                    </serverVariables>
                </rule>
                <rule name="Health Check Proxy" stopProcessing="true">
                    <match url="^health$" />
                    <action type="Rewrite" url="http://localhost:5000/health" />
                </rule>
            </rules>
        </rewrite>
        <httpProtocol>
            <customHeaders>
                <add name="X-Content-Type-Options" value="nosniff" />
            </customHeaders>
        </httpProtocol>
    </system.webServer>
</configuration>
```

### 5. Instalar Certificado SSL

#### Opção A - Win-ACME (Let's Encrypt para Windows)

```powershell
# Instalar via Chocolatey
choco install win-acme -y

# Executar configuração
wacs.exe

# Siga o assistente:
# 1. Escolha "N: Create certificate (default settings)"
# 2. Escolha "1: Single binding of an IIS site"
# 3. Selecione o site "BlingWebhook"
# 4. Escolha validação (recomendado: http-01)
# 5. Aguarde instalação
```

#### Opção B - Certificado Manual

```powershell
# 1. No IIS Manager, clique no servidor
# 2. Abra "Server Certificates"
# 3. No painel direito, "Create Certificate Request"
# 4. Preencha:
#    - Common Name: seu-dominio.com
#    - Organization: Sua Empresa
#    - Country: BR
# 5. Salve o CSR
# 6. Envie para CA (ex: Let's Encrypt, DigiCert)
# 7. Importe certificado recebido
# 8. No site, adicione binding HTTPS
```

### 6. Adicionar binding HTTPS ao site

```powershell
# Via PowerShell
New-IISSiteBinding -Name "BlingWebhook" -BindingInformation "*:443:seu-dominio.com" -Protocol https -CertificateThumbPrint "THUMBPRINT_DO_CERTIFICADO"

# OU via IIS Manager:
# 1. Clique no site "BlingWebhook"
# 2. Painel direito > "Bindings"
# 3. "Add" > Type: https, Port: 443, SSL Certificate: (selecionar)
```

### 7. Configurar firewall

```powershell
# Permitir HTTP
New-NetFirewallRule -DisplayName "HTTP Bling" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow

# Permitir HTTPS
New-NetFirewallRule -DisplayName "HTTPS Bling" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow

# Permitir porta do Flask (apenas localhost - segurança)
New-NetFirewallRule -DisplayName "Flask Bling" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow -RemoteAddress LocalSubnet
```

### 8. Testar configuração

```powershell
# Teste local
Invoke-WebRequest -Uri "http://localhost/health" -UseBasicParsing

# Teste externo (do seu PC)
Invoke-WebRequest -Uri "https://seu-dominio.com/health" -UseBasicParsing
```

---

## 📊 Comandos de Gerenciamento

### Gerenciar serviços NSSM

```powershell
# Ver status
nssm status BlingMonitor
nssm status BlingWebhook

# Iniciar
nssm start BlingMonitor
nssm start BlingWebhook

# Parar
nssm stop BlingMonitor
nssm stop BlingWebhook

# Reiniciar
nssm restart BlingMonitor
nssm restart BlingWebhook

# Ver configuração
nssm dump BlingMonitor

# Remover serviço
nssm remove BlingMonitor confirm
```

### Gerenciar via Services (GUI)

```powershell
# Abrir gerenciador de serviços
services.msc

# OU via PowerShell
Get-Service Bling*
Start-Service BlingMonitor
Stop-Service BlingMonitor
Restart-Service BlingMonitor
```

### Ver logs

```powershell
# Logs do monitor
Get-Content C:\BlingMonitor\logs\monitor.log -Tail 50 -Wait

# Logs do webhook
Get-Content C:\BlingMonitor\logs\webhook.log -Tail 50 -Wait

# Logs de erro
Get-Content C:\BlingMonitor\logs\monitor-error.log -Tail 50 -Wait
Get-Content C:\BlingMonitor\logs\webhook-error.log -Tail 50 -Wait
```

### Ver logs do Event Viewer (se usar Task Scheduler)

```powershell
# Abrir Event Viewer
eventvwr.msc

# Ver logs da tarefa
Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" | Where-Object {$_.Message -like "*BlingMonitor*"} | Select-Object -First 10
```

---

## 🔧 Execuções Manuais (Tarefas Únicas)

### 1. Gerar códigos para produtos existentes

```powershell
cd C:\BlingMonitor
.\venv\Scripts\Activate.ps1
python dump_products.py
```

### 2. Testar autenticação

```powershell
cd C:\BlingMonitor
.\venv\Scripts\Activate.ps1
python quick_test.py
```

**Output esperado:**

```
✅ Token obtido: eyJhbGciOiJSUzI1NiIs...
✅ API funcionando. 1 produto(s) retornado(s)
✅ Banco funcionando corretamente
🎉 TODOS OS TESTES PASSARAM!
```

### 3. Executar manualmente (debug)

```powershell
# Monitor
cd C:\BlingMonitor
.\venv\Scripts\Activate.ps1
python test.py

# Webhook
cd C:\BlingMonitor
.\venv\Scripts\Activate.ps1
python webhook_server.py
```

---

## 📅 Configuração no Bling (Webhooks)

### 1. Acessar Central de Extensões

1.  Login no Bling
2.  Menu → **Configurações** → **Integrações** → **Central de Extensões**
3.  Selecionar seu app
4.  Aba **Webhooks**

### 2. Cadastrar webhooks

| Evento | URL | Método |
|--------|-----|--------|
| `product.created` | `https://seu-dominio.com/webhook/bling` | POST |
| `product.updated` | `https://seu-dominio.com/webhook/bling` | POST |
| `stock.updated` | `https://seu-dominio.com/webhook/bling` | POST |

### 3. Testar webhook

```powershell
# Monitorar logs em tempo real
Get-Content C:\BlingMonitor\logs\webhook.log -Tail 50 -Wait

# No Bling, clique "Testar webhook"
```

Deve aparecer:

```
✅ Webhook recebido: product.created (eventId: abc123...)
✅ Evento processado com sucesso
```

---

## 🔍 Monitoramento e Manutenção

### Rotação de logs (evitar disco cheio)

Criar script `C:\BlingMonitor\rotate-logs.ps1`:

```powershell
# Rotação de logs - manter últimos 30 dias
$LogPath = "C:\BlingMonitor\logs"
$DaysToKeep = 30

Get-ChildItem -Path $LogPath -Filter "*.log" | ForEach-Object {
    $NewName = "$($_.BaseName)_$(Get-Date -Format 'yyyyMMdd')$($_.Extension)"
    $NewPath = Join-Path -Path $LogPath -ChildPath "archive"
    
    if (-not (Test-Path $NewPath)) {
        New-Item -ItemType Directory -Path $NewPath
    }
    
    if ($_.Length -gt 10MB) {
        Move-Item -Path $_.FullName -Destination (Join-Path $NewPath $NewName)
        New-Item -ItemType File -Path $_.FullName
    }
}

# Limpar arquivos antigos
Get-ChildItem -Path "$LogPath\archive" -Recurse | Where-Object {
    $_.LastWriteTime -lt (Get-Date).AddDays(-$DaysToKeep)
} | Remove-Item -Force
```

Agendar no Task Scheduler:

```powershell
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File C:\BlingMonitor\rotate-logs.ps1"
$Trigger = New-ScheduledTaskTrigger -Daily -At 3am
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "BlingLogRotation" -Action $Action -Trigger $Trigger -Principal $Principal
```

### Backup do banco de dados

Criar script `C:\BlingMonitor\backup-db.ps1`:

```powershell
# Backup do banco de dados
$BackupDir = "C:\BlingMonitor\backups"
$DBPath = "C:\BlingMonitor\bling_data.db"
$Date = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = Join-Path $BackupDir "bling_data_$Date.db"

# Criar diretório se não existir
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir
}

# Copiar banco
Copy-Item -Path $DBPath -Destination $BackupFile

# Manter apenas últimos 7 dias
Get-ChildItem -Path $BackupDir -Filter "bling_data_*.db" | Where-Object {
    $_.LastWriteTime -lt (Get-Date).AddDays(-7)
} | Remove-Item -Force

Write-Host "Backup concluído: $BackupFile"
```

Agendar:

```powershell
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File C:\BlingMonitor\backup-db.ps1"
$Trigger = New-ScheduledTaskTrigger -Daily -At 3am
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "BlingDatabaseBackup" -Action $Action -Trigger $Trigger -Principal $Principal
```

### Monitorar uso de disco

```powershell
# Ver espaço em disco
Get-PSDrive C | Select-Object Used,Free,@{Name="PercentFree";Expression={"{0:P}" -f ($_.Free/$_.Used)}}

# Ver tamanho do diretório
Get-ChildItem C:\BlingMonitor -Recurse | Measure-Object -Property Length -Sum | Select-Object @{Name="Size(MB)";Expression={"{0:N2}" -f ($_.Sum / 1MB)}}
```

### Script de monitoramento de saúde

Criar `C:\BlingMonitor\health-check.ps1`:

```powershell
# Health check completo
$Report = @()

# Verificar serviços
$Services = @("BlingMonitor", "BlingWebhook")
foreach ($Service in $Services) {
    $Status = (Get-Service $Service -ErrorAction SilentlyContinue).Status
    $Report += [PSCustomObject]@{
        Component = "Service: $Service"
        Status = if ($Status -eq "Running") { "OK" } else { "FAIL" }
        Details = $Status
    }
}

# Verificar endpoint webhook
try {
    $Response = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -TimeoutSec 5
    $WebhookStatus = if ($Response.StatusCode -eq 200) { "OK" } else { "FAIL" }
} catch {
    $WebhookStatus = "FAIL"
}

$Report += [PSCustomObject]@{
    Component = "Webhook Endpoint"
    Status = $WebhookStatus
    Details = $Response.StatusCode
}

# Verificar banco de dados
$DBExists = Test-Path "C:\BlingMonitor\bling_data.db"
$Report += [PSCustomObject]@{
    Component = "Database"
    Status = if ($DBExists) { "OK" } else { "FAIL" }
    Details = if ($DBExists) { "File exists" } else { "Not found" }
}

# Verificar espaço em disco
$Drive = Get-PSDrive C
$FreePercent = ($Drive.Free / ($Drive.Used + $Drive.Free)) * 100
$DiskStatus = if ($FreePercent -gt 10) { "OK" } else { "WARNING" }
$Report += [PSCustomObject]@{
    Component = "Disk Space"
    Status = $DiskStatus
    Details = "{0:N2}% free" -f $FreePercent
}

# Exibir relatório
$Report | Format-Table -AutoSize

# Salvar log
$LogFile = "C:\BlingMonitor\logs\health-$(Get-Date -Format 'yyyyMMdd').log"
$Report | Out-File -FilePath $LogFile -Append
```

Agendar para executar a cada hora:

```powershell
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File C:\BlingMonitor\health-check.ps1"
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([TimeSpan]::MaxValue)
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount

Register-ScheduledTask -TaskName "BlingHealthCheck" -Action $Action -Trigger $Trigger -Principal $Principal
```

---

## 🚨 Troubleshooting

### Problema: Serviço não inicia

```powershell
# Ver logs de erro
Get-Content C:\BlingMonitor\logs\monitor-error.log -Tail 50

# Ver eventos do sistema
Get-EventLog -LogName Application -Source "BlingMonitor" -Newest 10

# Testar manualmente
cd C:\BlingMonitor
.\venv\Scripts\Activate.ps1
python test.py
```

### Problema: Erro "Python não encontrado"

```powershell
# Verificar caminho do Python
Get-Command python

# Reconfigurar serviço com caminho completo
nssm set BlingMonitor Application "C:\Python311\python.exe"
```

### Problema: Porta 5000 já em uso

```powershell
# Ver qual processo está usando
Get-NetTCPConnection -LocalPort 5000 | Select-Object State,OwningProcess
Get-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess

# Matar processo (se necessário)
Stop-Process -Id PROCESS_ID -Force

# OU alterar porta no .env
notepad C:\BlingMonitor\.env
# Alterar: WEBHOOK_PORT=5001
```

### Problema: Certificado SSL não funciona

```powershell
# Ver certificados instalados
Get-ChildItem Cert:\LocalMachine\My

# Testar binding HTTPS
Test-NetConnection -ComputerName seu-dominio.com -Port 443

# Ver logs IIS
Get-Content C:\inetpub\logs\LogFiles\W3SVC1\u_ex*.log -Tail 50
```

### Problema: Webhook retorna 500 Internal Server Error

```powershell
# Habilitar detailed errors no IIS
# Editar C:\inetpub\bling-webhook\web.config:
<system.webServer>
    <httpErrors errorMode="Detailed" />
</system.webServer>

# Verificar logs do Flask
Get-Content C:\BlingMonitor\logs\webhook-error.log -Tail 50

# Verificar configuração ARR
Get-WebConfigurationProperty -PSPath 'MACHINE/WEBROOT/APPHOST' -Filter "system.webServer/proxy" -Name "enabled"
```

### Problema: Rate limit excedido

```powershell
# Editar .env
notepad C:\BlingMonitor\.env
# Alterar: MINUTES_BETWEEN_RUNS=120

# Reiniciar serviço
Restart-Service BlingMonitor
```

### Problema: Imports circulares (ImportError)

Certifique-se de que criou o arquivo `bling_utils.py` e atualizou os imports conforme os patches.

---

## 📈 Métricas e Relatórios

### Script de relatório diário

Criar `C:\BlingMonitor\daily-report.ps1`:

```powershell
# Relatório diário
cd C:\BlingMonitor
.\venv\Scripts\Activate.ps1

$Report = @"
========================================
RELATÓRIO BLING - $(Get-Date -Format 'dd/MM/yyyy')
========================================

"@

# Estatísticas do banco
$Stats = python -c "from bling_db import BlingDatabase; import json; db = BlingDatabase(); print(json.dumps(db.get_stats()))" | ConvertFrom-Json

$Report += @"
BANCO DE DADOS:
- Contadores de código: $($Stats.counters)
- Eventos processados: $($Stats.events)

ÚLTIMOS CONTADORES:
"@

foreach ($Counter in $Stats.recent_counters[0..4]) {
    $Report += "`n  • $($Counter.prefix): $($Counter.last_value) ($($Counter.category_name))"
}

# Eventos do dia
$Today = Get-Date -Format "yyyy-MM-dd"
$TodayEvents = sqlite3.exe C:\BlingMonitor\bling_data.db "SELECT COUNT(*) FROM processed_events WHERE DATE(processed_at) = '$Today';"
$Report += "`n`nEVENTOS HOJE: $TodayEvents"

# Tamanho do banco
$DBSize = (Get-Item C:\BlingMonitor\bling_data.db).Length / 1MB
$Report += "`nTAMANHO DO BANCO: $("{0:N2}" -f $DBSize) MB"

# Status dos serviços
$MonitorStatus = (Get-Service BlingMonitor).Status
$WebhookStatus = (Get-Service BlingWebhook).Status
$Report += @"

SERVIÇOS:
- BlingMonitor: $MonitorStatus
- BlingWebhook: $WebhookStatus

========================================
"@

# Salvar relatório
$ReportFile = "C:\BlingMonitor\reports\report_$(Get-Date -Format 'yyyyMMdd').txt"
if (-not (Test-Path "C:\BlingMonitor\reports")) {
    New-Item -ItemType Directory -Path "C:\BlingMonitor\reports"
}
$Report | Out-File -FilePath $ReportFile

# Exibir no console
Write-Host $Report

# Enviar por email (opcional - configurar SMTP)
# Send-MailMessage -From "bling@sua-empresa.com" -To "admin@sua-empresa.com" -Subject "Relatório Bling $(Get-Date -Format 'dd/MM')" -Body $Report -SmtpServer "smtp.gmail.com" -Port 587 -UseSsl -Credential (Get-Credential)
```

### Ver últimos produtos processados

```powershell
cd C:\BlingMonitor

# Via SQLite (instalar: choco install sqlite -y)
sqlite3 bling_data.db "SELECT event_type, product_id, processed_at FROM processed_events ORDER BY processed_at DESC LIMIT 10;"
```

### Dashboard em tempo real (PowerShell)

Criar `C:\BlingMonitor\dashboard.ps1`:

```powershell
# Dashboard em tempo real
while ($true) {
    Clear-Host
    
    Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║             BLING MONITOR - DASHBOARD                              ║" -ForegroundColor Cyan
    Write-Host "║             $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')                           ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    
    # Status serviços
    Write-Host "`nSERVIÇOS:" -ForegroundColor Yellow
    $Services = @("BlingMonitor", "BlingWebhook")
    foreach ($Service in $Services) {
        $Status = (Get-Service $Service -ErrorAction SilentlyContinue).Status
        $Color = if ($Status -eq "Running") { "Green" } else { "Red" }
        Write-Host "  $Service : " -NoNewline
        Write-Host "$Status" -ForegroundColor $Color
    }
    
    # Logs recentes
    Write-Host "`nÚLTIMOS EVENTOS:" -ForegroundColor Yellow
    Get-Content C:\BlingMonitor\logs\webhook.log -Tail 5 | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Gray
    }
    
    # Espaço em disco
    Write-Host "`nDISCO:" -ForegroundColor Yellow
    $Drive = Get-PSDrive C
    $FreePercent = ($Drive.Free / ($Drive.Used + $Drive.Free)) * 100
    $Color = if ($FreePercent -gt 20) { "Green" } elseif ($FreePercent -gt 10) { "Yellow" } else { "Red" }
    Write-Host "  Espaço livre: " -NoNewline
    Write-Host ("{0:N2}%" -f $FreePercent) -ForegroundColor $Color
    
    Write-Host "`n[Pressione Ctrl+C para sair]" -ForegroundColor DarkGray
    Start-Sleep -Seconds 5
}
```

Executar:

```powershell
.\dashboard.ps1
```

---

## 🔄 Atualização do Código

Quando houver alterações:

```powershell
# Parar serviços
Stop-Service BlingMonitor
Stop-Service BlingWebhook

# Backup do banco
Copy-Item C:\BlingMonitor\bling_data.db C:\BlingMonitor\bling_data.db.backup

# Atualizar código (via Git)
cd C:\BlingMonitor
git pull

# OU copiar arquivos manualmente via RDP

# Reinstalar dependências (se necessário)
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt --upgrade

# Reiniciar serviços
Start-Service BlingMonitor
Start-Service BlingWebhook

# Verificar
Get-Service Bling*
```

---

## ✅ Checklist Pós-Instalação

```
□ Python 3.8+ instalado e no PATH
□ Git instalado (opcional)
□ Código transferido para C:\BlingMonitor
□ Ambiente virtual criado
□ Dependências instaladas (pip install -r requirements.txt)
□ Arquivo .env configurado com credenciais
□ AUTH_CODE obtido e testado
□ bling_utils.py criado
□ Patches aplicados (imports corrigidos)
□ quick_test.py executado com sucesso
□ NSSM instalado
□ Serviços Windows criados (BlingMonitor, BlingWebhook)
□ Serviços iniciados e funcionando
□ IIS instalado e configurado
□ URL Rewrite e ARR instalados
□ Site IIS criado
□ Reverse proxy configurado (web.config)
□ Certificado SSL instalado
□ Firewall configurado (portas 80, 443)
□ Webhooks cadastrados no Bling
□ Teste de webhook bem-sucedido
□ Scripts de backup/rotação agendados
□ dump_products.py executado (primeira vez)
□ Logs sendo escritos corretamente
□ Health check funcionando
```

---

## 📞 Scripts Úteis Adicionais

### Restart completo (quando algo der errado)

Criar `C:\BlingMonitor\emergency-restart.ps1`:

```powershell
Write-Host "=== REINÍCIO DE EMERGÊNCIA ===" -ForegroundColor Red

# Parar serviços
Write-Host "Parando serviços..." -ForegroundColor Yellow
Stop-Service BlingMonitor -Force -ErrorAction SilentlyContinue
Stop-Service BlingWebhook -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

# Matar processos Python (se travados)
Write-Host "Matando processos Python travados..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# Limpar cache Python
Write-Host "Limpando cache..." -ForegroundColor Yellow
Get-ChildItem C:\BlingMonitor -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

# Recriar logs
Write-Host "Rotacionando logs..." -ForegroundColor Yellow
$Date = Get-Date -Format "yyyyMMdd_HHmmss"
Move-Item C:\BlingMonitor\logs\*.log "C:\BlingMonitor\logs\archive\backup_$Date" -ErrorAction SilentlyContinue

# Reiniciar serviços
Write-Host "Reiniciando serviços..." -ForegroundColor Yellow
Start-Service BlingMonitor
Start-Service BlingWebhook
Start-Sleep -Seconds 5

# Verificar
Write-Host "`n=== STATUS ===" -ForegroundColor Green
Get-Service Bling* | Format-Table -AutoSize

Write-Host "`nReinício concluído!" -ForegroundColor Green
```

### Uninstall completo

Criar `C:\BlingMonitor\uninstall.ps1`:

```powershell
Write-Host "=== DESINSTALAÇÃO BLING MONITOR ===" -ForegroundColor Red
$Confirm = Read-Host "Tem certeza? (sim/não)"

if ($Confirm -ne "sim") {
    Write-Host "Cancelado." -ForegroundColor Yellow
    exit
}

# Parar e remover serviços
Write-Host "Removendo serviços..." -ForegroundColor Yellow
nssm stop BlingMonitor
nssm stop BlingWebhook
nssm remove BlingMonitor confirm
nssm remove BlingWebhook confirm

# Remover tarefas agendadas
Write-Host "Removendo tarefas agendadas..." -ForegroundColor Yellow
Unregister-ScheduledTask -TaskName "BlingLogRotation" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "BlingDatabaseBackup" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "BlingHealthCheck" -Confirm:$false -ErrorAction SilentlyContinue

# Remover site IIS
Write-Host "Removendo site IIS..." -ForegroundColor Yellow
Remove-IISSite -Name "BlingWebhook" -Confirm:$false -ErrorAction SilentlyContinue
Remove-Item -Path "C:\inetpub\bling-webhook" -Recurse -Force -ErrorAction SilentlyContinue

# Backup final
Write-Host "Criando backup final..." -ForegroundColor Yellow
$BackupPath = "C:\BlingMonitor_Backup_$(Get-Date -Format 'yyyyMMdd')"
Copy-Item -Path "C:\BlingMonitor" -Destination $BackupPath -Recurse

Write-Host "`nDesinstalação concluída!" -ForegroundColor Green
Write-Host "Backup salvo em: $BackupPath" -ForegroundColor Cyan
Write-Host "`nPara remover completamente:" -ForegroundColor Yellow
Write-Host "  Remove-Item -Path 'C:\BlingMonitor' -Recurse -Force"
