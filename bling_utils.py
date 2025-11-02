"""
Funções utilitárias compartilhadas entre módulos
"""
from datetime import datetime, timedelta


def extract_category_info(product):
    """
    Extrai categoria e subcategoria de um produto.
    
    Returns:
        (category_name, subcategory_name, full_hierarchy, category_id)
    """
    cat_info = product.get('categoria', {})
    cat_id = cat_info.get('id')
    full_name = cat_info.get('nome', '')
    
    if '>>' in full_name:
        parts = full_name.split('>>')
        category = parts[0].strip()
        subcategory = parts[-1].strip()
        return category, subcategory, full_name, cat_id
    else:
        return full_name, None, full_name, cat_id


def should_ignore_product(product, excluded_categories={'notebook', 'sff', 'mini', 'monitor'}, 
                         ignore_subcategories={'submaquina'}):
    """
    Verifica se produto deve ser ignorado baseado em categoria.
    
    Args:
        product: Dicionário do produto
        excluded_categories: Set de categorias a excluir (lowercase)
        ignore_subcategories: Set de subcategorias a ignorar (lowercase)
    
    Returns:
        (should_ignore: bool, reason: str)
    """
    category, subcategory, full, _ = extract_category_info(product)
    
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
        print(f"    Erro ao verificar movimentacoes: {e}")
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


def should_generate_code(product):
    """
    Verifica se deve gerar código para o produto.
    
    Returns:
        (should_generate: bool, reason: str, prefix: str)
    """
    # Já tem código?
    if product.get('codigo'):
        return False, "Ja possui codigo", None
    
    category, subcategory, full, cat_id = extract_category_info(product)
    
    if not category:
        return False, "Sem categoria", None
    
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
