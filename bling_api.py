"""
Cliente API Bling com retry, rate limiting e tratamento de erros
"""
import requests
import time
from collections import deque
from datetime import datetime, timedelta
from bling_logger import log


class RateLimiter:
    """Controla rate limit de 3 req/s e 120k/dia."""
    
    def __init__(self, requests_per_second=3, requests_per_day=120000):
        self.rps = requests_per_second
        self.rpd = requests_per_day
        
        # Janela deslizante para req/s
        self.second_window = deque()
        
        # Contador diário
        self.daily_count = 0
        self.daily_reset = datetime.now() + timedelta(days=1)
    
    def wait_if_needed(self):
        """Aguarda se necessário para respeitar limites."""
        now = time.time()
        
        # Reset contador diário se necessário
        if datetime.now() >= self.daily_reset:
            self.daily_count = 0
            self.daily_reset = datetime.now() + timedelta(days=1)
            log.info("📊 Rate limit diário resetado")
        
        # Verifica limite diário
        if self.daily_count >= self.rpd:
            wait_seconds = (self.daily_reset - datetime.now()).total_seconds()
            log.warning(f"⚠️ Limite diário atingido! Aguardando {wait_seconds/3600:.1f} horas...")
            time.sleep(wait_seconds)
            self.daily_count = 0
        
        # Remove requisições antigas da janela (>1s)
        while self.second_window and now - self.second_window[0] > 1:
            self.second_window.popleft()
        
        # Se atingiu limite por segundo, aguarda
        if len(self.second_window) >= self.rps:
            sleep_time = 1 - (now - self.second_window[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Registra requisição
        self.second_window.append(time.time())
        self.daily_count += 1


class BlingAPI:
    """Cliente HTTP para API Bling com retry e rate limiting."""
    
    BASE_URL = "https://api.bling.com.br/Api/v3"
    
    def __init__(self, get_token_func):
        """
        Args:
            get_token_func: Função que retorna access token válido
        """
        self.get_token = get_token_func
        self.rate_limiter = RateLimiter()
    
    def _headers(self):
        """Retorna headers com token atual."""
        return {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json"
        }
    
    def _request(self, method, endpoint, max_retries=3, **kwargs):
        """
        Faz requisição com retry automático e exponential backoff.
        
        Args:
            method: GET, POST, PATCH, DELETE
            endpoint: Ex: "/produtos" ou "/produtos/123"
            max_retries: Número máximo de tentativas
            **kwargs: Argumentos para requests (params, json, data)
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        for attempt in range(max_retries):
            try:
                # Rate limiting
                self.rate_limiter.wait_if_needed()
                
                # Fazer requisição
                response = requests.request(
                    method,
                    url,
                    headers=self._headers(),
                    timeout=30,
                    **kwargs
                )
                
                # Tratar erros HTTP
                if response.status_code == 401:
                    # Token expirado, força refresh e tenta de novo
                    log.warning("⚠️ Token expirado (401), tentando refresh...")
                    from bling_auth import refresh_access_token
                    refresh_access_token()
                    # Retry com novo token (não conta como tentativa)
                    continue
                
                elif response.status_code == 429:
                    # Rate limit excedido
                    retry_after = int(response.headers.get('Retry-After', 60))
                    log.warning(f"⏳ Rate limit (429). Aguardando {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                elif response.status_code >= 500:
                    # Erro do servidor, retry com backoff
                    if attempt < max_retries - 1:
                        wait = 2 ** attempt  # 1s, 2s, 4s
                        log.warning(f"⚠️ Erro de servidor {response.status_code}. Tentando novamente em {wait}s... (tentativa {attempt+1}/{max_retries})")
                        time.sleep(wait)
                        continue
                
                # Verificar sucesso
                response.raise_for_status()
                
                # Retornar JSON ou dict vazio
                return response.json() if response.content else {}
            
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    log.warning(f"⏱️ Timeout. Tentando novamente em {wait}s... (tentativa {attempt+1}/{max_retries})")
                    time.sleep(wait)
                    continue
                log.error("❌ Request falhou por timeout após múltiplas tentativas.")
                raise
            
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    log.warning(f"⚠️ Erro de rede: {e}. Tentando novamente em {wait}s... (tentativa {attempt+1}/{max_retries})")
                    time.sleep(wait)
                    continue
                log.error(f"❌ Request falhou por erro de rede: {e}")
                raise
        
        log.error(f"❌ Request para {endpoint} falhou após {max_retries} tentativas.")
        raise Exception(f"Falhou após {max_retries} tentativas")
    
    # === Produtos ===
    
    def get_products(self, page=1, limit=100, **filters):
        """Lista produtos com paginação."""
        params = {"pagina": page, "limite": limit, **filters}
        return self._request("GET", "/produtos", params=params)
    
    def get_product(self, product_id):
        """Obtém detalhes de um produto."""
        return self._request("GET", f"/produtos/{product_id}")
    
    def update_product(self, product_id, data):
        """Atualiza produto (PATCH)."""
        import json
        return self._request("PATCH", f"/produtos/{product_id}", data=json.dumps(data))
    
    def update_product_situation(self, product_id, situation):
        """
        Atualiza situação do produto.
        situation: 'A' (Ativo) ou 'I' (Inativo)
        """
        import json
        return self._request(
            "PATCH",
            f"/produtos/{product_id}/situacoes",
            data=json.dumps({"situacao": situation})
        )
    
    # === Categorias ===
    
    def get_categories(self, page=1, limit=100):
        """Lista categorias."""
        params = {"pagina": page, "limite": limit}
        return self._request("GET", "/categorias/produtos", params=params)
    
    def get_all_categories(self):
        """Obtém todas as categorias (auto-paginação)."""
        all_cats = {}
        page = 1
        
        while True:
            data = self.get_categories(page=page, limit=100)
            cats = data.get("data", [])
            
            if not cats:
                break
            
            for cat in cats:
                all_cats[cat['id']] = cat
            
            page += 1
        
        return all_cats
    
    # === Estoque ===
    
    def get_stock_movements(self, product_id, start_date=None, end_date=None):
        """
        Obtém movimentações de estoque de um produto.
        
        Args:
            product_id: ID do produto
            start_date: Data inicial (formato YYYY-MM-DD)
            end_date: Data final (formato YYYY-MM-DD)
        """
        params = {"idProduto": product_id}
        if start_date:
            params['dataInicial'] = start_date
        if end_date:
            params['dataFinal'] = end_date
        
        return self._request("GET", "/estoques", params=params)
    
    # === Pedidos ===
    
    def get_orders(self, page=1, limit=100, **filters):
        """Lista pedidos de venda."""
        params = {"pagina": page, "limite": limit, **filters}
        return self._request("GET", "/pedidos/vendas", params=params)
