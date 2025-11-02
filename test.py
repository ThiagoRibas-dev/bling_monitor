"""
Script de monitoramento contínuo - Desativa produtos com estoque zerado POR VENDAS
"""
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Imports dos novos módulos
from bling_auth import ensure_authenticated
from bling_api import BlingAPI
from bling_utils import extract_category_info, should_ignore_product, check_stock_depleted_by_sales

load_dotenv()

# Configurações
MINUTES_BETWEEN_RUNS = int(os.getenv("MINUTES_BETWEEN_RUNS", 60))  # Aumentado para 1h
EXCLUDED_CATEGORIES = {"notebook", "sff", "mini", "monitor"}  # lowercase para comparação
IGNORE_SUBCATEGORIES = {"submaquina"}  # lowercase

# Cliente API
api = BlingAPI(ensure_authenticated)


def process_zero_stock_products():
    """
    Processa produtos com estoque zero, desativando apenas os que zeraram por vendas.
    """
    print(f"\n{'='*80}")
    print(f"🔍 INICIANDO VARREDURA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    page = 1
    checked_count = 0
    zero_stock_count = 0
    deactivated_count = 0
    ignored_count = 0
    
    while True:
        try:
            data = api.get_products(page=page, limit=100)
            products = data.get("data", [])
            
            if not products:
                break
            
            for p in products:
                checked_count += 1
                stock = p.get("estoqueAtual", 0)
                
                if stock != 0:
                    continue  # Pula produtos com estoque
                
                zero_stock_count += 1
                product_id = p.get("id")
                product_name = p.get("nome", "Sem nome")
                
                print(f"\n📦 Produto com estoque ZERO encontrado:")
                print(f"   ID: {product_id}")
                print(f"   Nome: {product_name}")
                
                # Buscar detalhes completos
                try:
                    details_response = api.get_product(product_id)
                    product_details = details_response.get("data", {})
                except Exception as e:
                    print(f"   ❌ Erro ao buscar detalhes: {e}")
                    continue
                
                # Verificar se deve ignorar
                should_ignore, ignore_reason = should_ignore_product(product_details, EXCLUDED_CATEGORIES, IGNORE_SUBCATEGORIES)
                if should_ignore:
                    ignored_count += 1
                    print(f"   ⏭️  IGNORADO: {ignore_reason}")
                    continue
                
                # Verificar se zerou por vendas
                print(f"   🔍 Verificando movimentações de estoque...")
                is_depleted, details = check_stock_depleted_by_sales(api, product_id)
                
                print(f"   📊 Entradas: {details['entries']}")
                print(f"   📊 Saídas por venda: {details['sales_exits']}")
                print(f"   📊 Motivo: {details['reason']}")
                
                if is_depleted:
                    print(f"   🔴 DESATIVANDO produto...")
                    try:
                        api.update_product_situation(product_id, 'I')
                        deactivated_count += 1
                        print(f"   ✅ Produto DESATIVADO com sucesso")
                    except Exception as e:
                        print(f"   ❌ Erro ao desativar: {e}")
                else:
                    print(f"   ✅ Produto NÃO será desativado (não zerou por vendas)")
            
            print(f"\n📄 Página {page} processada ({len(products)} produtos)")
            page += 1
        
        except Exception as e:
            print(f"\n❌ Erro na página {page}: {e}")
            break
    
    # Relatório final
    print(f"\n{'='*80}")
    print(f"📊 RELATÓRIO FINAL")
    print(f"{'='*80}")
    print(f"✅ Produtos verificados: {checked_count}")
    print(f"⚠️  Com estoque zero: {zero_stock_count}")
    print(f"⏭️  Ignorados (categoria): {ignored_count}")
    print(f"🔴 Desativados (zerado por vendas): {deactivated_count}")
    print(f"{'='*80}\n")


def main():
    """Loop principal."""
    print("🚀 Iniciando monitoramento Bling...")
    print(f"⏱️  Intervalo entre execuções: {MINUTES_BETWEEN_RUNS} minutos\n")
    
    try:
        while True:
            process_zero_stock_products()
            
            print(f"⏳ Aguardando {MINUTES_BETWEEN_RUNS} minutos até próxima execução...")
            print(f"   (Pressione Ctrl+C para interromper)\n")
            
            time.sleep(MINUTES_BETWEEN_RUNS * 60)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Script interrompido pelo usuário. Encerrando...")


if __name__ == "__main__":
    main()
