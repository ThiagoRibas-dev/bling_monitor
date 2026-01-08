"""
Funções utilitárias compartilhadas entre módulos
"""
from datetime import datetime, timedelta
from bling_logger import log


class CategoryCache:
    """Cache de categorias carregadas da API."""
    
    def __init__(self):
        self._categories = {}  # ID -> categoria completa
        self._loaded = False
    
    def load(self, api):
        """Carrega todas as categorias da API."""
        if self._loaded:
            return
        
        log.info("Carregando cache de categorias...")
        self._categories = api.get_all_categories()
        self._loaded = True
        log.info(f"✅ {len(self._categories)} categorias em cache")
    
    def get_by_id(self, category_id):
        """Obtém categoria por ID."""
        return self._categories.get(category_id)
    
    def get_name(self, category_id):
        """Obtém nome da categoria por ID."""
        cat = self._categories.get(category_id)
        
        if not cat:
            return  ''
            
        if cat.get('nome', ''):
            return cat.get('nome', '')
        
        if cat.get('descricao', ''):
            return cat.get('descricao', '')
        
        return ''
    
    def is_loaded(self):
        """Verifica se cache foi carregado."""
        return self._loaded


# Instância global do cache
_category_cache = CategoryCache()


def get_category_cache():
    """Retorna a instância global do cache."""
    return _category_cache


def extract_category_info(product, category_cache=None):
    """
    Extrai categoria e subcategoria de um produto.
    
    Args:
        product: Dicionário do produto
        category_cache: Instância de CategoryCache (opcional)
    
    Returns:
        (category_name, subcategory_name, full_hierarchy, category_id)
    """
    cat_info = product.get('categoria', '')
    cat_id = cat_info.get('id')
    
    if not cat_id:
        return None, None, None, None
    
    # Tentar obter nome do cache primeiro
    if category_cache:
        full_name = category_cache.get_name(cat_id)
    else:
        # Fallback: tentar obter do próprio produto (pode não existir)
        full_name = cat_info.get('nome', '')
    
    if not full_name:
        return None, None, None, cat_id
    
    # Extrair hierarquia (Categoria>>Subcategoria)
    if '>>' in full_name:
        parts = full_name.split('>>')
        category = parts[0].strip()
        subcategory = parts[-1].strip()
        return category, subcategory, full_name, cat_id
    else:
        return full_name, None, full_name, cat_id


def should_ignore_product(product, category_cache=None,
                         excluded_categories={'notebook', 'sff', 'mini', 'monitor'}, 
                         ignore_subcategories={'submaquina'}):
    """
    Verifica se produto deve ser ignorado baseado em categoria.
    
    Args:
        product: Dicionário do produto
        category_cache: Instância de CategoryCache
        excluded_categories: Set de categorias a excluir (lowercase)
        ignore_subcategories: Set de subcategorias a ignorar (lowercase)
    
    Returns:
        (should_ignore: bool, reason: str)
    """
    category, subcategory, full, cat_id = extract_category_info(product, category_cache)
    
    if not category:
        return False, "Sem categoria ou categoria não encontrada no cache"
    
    # Verificar categorias excluídas
    if category.lower() in excluded_categories:
        return True, f"Categoria excluída: {category}"
    
    # Verificar subcategorias ignoradas
    if subcategory and subcategory.lower() in ignore_subcategories:
        return True, f"Subcategoria ignorada: {subcategory}"
    
    return False, ""


def check_stock_depleted_by_sales(api, product_id):
    """
    Verifica se o estoque zerou ESPECIFICAMENTE por vendas.
    
    Args:
        api: Instância de BlingAPI
        product_id: ID do produto
    
    Returns:
        (is_depleted_by_sales: bool, details: dict)
    """
    try:
        # Buscar movimentações dos últimos 365 dias
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        response = api.get_stock_movements(
            product_id,
            start_date=start_date,
            end_date=end_date
        )
        
        movements = response.get('data', [])
        
        if not movements:
            return False, {
                'reason': 'Sem movimentacoes (nunca teve entrada)',
                'entries': 0,
                'sales_exits': 0
            }
        
        total_entries = 0
        total_sales_exits = 0
        
        for mov in movements:
            quantidade = mov.get('quantidade', 0)
            tipo = mov.get('tipo', '')
            operacao = mov.get('operacao', '').lower()
            
            if tipo == 'E':  # Entrada
                total_entries += quantidade
            
            elif tipo == 'S':  # Saída
                # Verificar se é saída por venda
                if any(keyword in operacao for keyword in ['venda', 'pedido', 'nfe', 'nota fiscal']):
                    total_sales_exits += quantidade
        
        # Critério: teve entradas E elas foram totalmente consumidas por vendas
        if total_entries > 0 and total_entries == total_sales_exits:
            return True, {
                'reason': 'Estoque zerado por vendas',
                'entries': total_entries,
                'sales_exits': total_sales_exits
            }
        
        return False, {
            'reason': 'Entradas nao batem com saidas por venda' if total_entries > 0 else 'Sem entradas',
            'entries': total_entries,
            'sales_exits': total_sales_exits
        }
    
    except Exception as e:
        log.error(f"    Erro ao verificar movimentacoes para o produto ID {product_id}: {e}")
        return False, {'reason': f'Erro: {e}', 'entries': 0, 'sales_exits': 0}


def get_category_prefix(category_name):
    """
    Gera prefixo de código baseado no nome da categoria.
    
    Exemplos:
        "Teclado Mouse" -> "TEMO"
        "Placa Mae" -> "PLMA"
        "Monitor" -> "MONI"
    """
    # Remove acentos comuns
    replacements = {
        'ã': 'a', 'á': 'a', 'à': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e',
        'í': 'i',
        'õ': 'o', 'ó': 'o', 'ô': 'o',
        'ú': 'u', 'ü': 'u',
        'ç': 'c'
    }
    
    clean_name = category_name.lower()
    for old, new in replacements.items():
        clean_name = clean_name.replace(old, new)
    
    parts = clean_name.split()
    
    if len(parts) > 1:
        # Pega 2 primeiras letras de cada palavra
        return (parts[0][:2] + parts[1][:2]).upper()
    else:
        # Pega 4 primeiras letras
        return clean_name[:4].upper()


def should_generate_code(product, category_cache=None):
    """
    Verifica se deve gerar código para o produto.
    
    Args:
        product: Dicionário do produto
        category_cache: Instância de CategoryCache
    
    Returns:
        (should_generate: bool, reason: str, prefix: str)
    """
    # Já tem código?
    if product.get('codigo'):
        return False, "Ja possui codigo", None
    
    category, subcategory, full, cat_id = extract_category_info(product, category_cache)
    
    if not category:
        return False, "Sem categoria ou categoria nao encontrada", None
    
    # SubMaquina: ignorar
    if subcategory and subcategory.lower() == 'submaquina':
        return False, "Subcategoria SubMaquina (ignorar)", None
    
    if category.lower() == 'submaquina':
        return False, "Categoria SubMaquina (ignorar)", None
    
    # Notebook, Mini, SFF -> NTB
    if category.lower() in ['notebook', 'mini', 'sff']:
        return True, f"Categoria {category}", "NTB"
    
    # Peças: usar subcategoria (CORRIGIDO - sem encoding corrompido)
    if category.lower() in ['pecas', 'peca'] or 'peca' in category.lower():
        if subcategory:
            prefix = get_category_prefix(subcategory)
            return True, f"Peca - Subcategoria {subcategory}", prefix
        else:
            return False, "Peca sem subcategoria", None
    
    # Outras categorias: gera prefixo da categoria
    prefix = get_category_prefix(category)
    return True, f"Categoria {category}", prefix