"""
Script de geração de códigos para produtos - COM PERSISTÊNCIA
"""
import json
import time
from datetime import datetime

# Imports dos novos módulos
from bling_auth import ensure_authenticated
from bling_api import BlingAPI
from bling_db import BlingDatabase
from bling_utils import extract_category_info, get_category_prefix, should_generate_code

# Cliente API e Database
api = BlingAPI(ensure_authenticated)
db = BlingDatabase()

OUTPUT_FILE = "products_dump.json"


def generate_and_update_code(product, product_details):
    """
    Gera código e atualiza produto na API.
    
    Returns:
        (success: bool, code: str or None, message: str)
    """
    product_id = product['id']
    product_name = product.get('nome', 'Sem nome')
    
    should_gen, reason, prefix = should_generate_code(product_details)
    
    if not should_gen:
        return False, None, reason
    
    # Gerar código usando banco de dados (thread-safe)
    category, subcategory, full, cat_id = extract_category_info(product_details)
    new_code = db.get_next_code(
        prefix=prefix,
        category_id=cat_id,
        category_name=full
    )
    
    print(f"   🏷️  Código gerado: {new_code}")
    
    # Atualizar na API
    try:
        api.update_product(product_id, {"codigo": new_code})
        return True, new_code, f"Atualizado com sucesso ({reason})"
    except Exception as e:
        return False, None, f"Erro ao atualizar: {e}"


def process_product_variations(product_details):
    """
    Processa variações de produto (se houver).
    """
    variations = product_details.get('variacoes', [])
    
    if not variations:
        return
    
    print(f"   🔀 Produto tem {len(variations)} variações")
    
    for var in variations:
        var_id = var.get('id')
        var_name = var.get('nome', 'Sem nome')
        var_code = var.get('codigo')
        
        if var_code:
            print(f"      ⏭️  Variação {var_id} já tem código: {var_code}")
            continue
        
        print(f"      🔍 Processando variação: {var_name}")
        
        # Variações herdam categoria do produto pai
        should_gen, reason, prefix = should_generate_code(product_details)
        
        if not should_gen:
            print(f"      ⏭️  {reason}")
            continue
        
        # Gerar código
        category, subcategory, full, cat_id = extract_category_info(product_details)
        new_code = db.get_next_code(
            prefix=prefix,
            category_id=cat_id,
            category_name=full
        )
        
        print(f"      🏷️  Código gerado para variação: {new_code}")
        
        # Atualizar variação
        try:
            # Endpoint de variações
            api.update_product(var_id, {"codigo": new_code})
            var['codigo'] = new_code  # Atualiza no dump também
            print(f"      ✅ Variação atualizada com sucesso")
        except Exception as e:
            print(f"      ❌ Erro ao atualizar variação: {e}")


def dump_and_update_product_codes():
    """
    Varre todos os produtos, gera códigos e atualiza na API.
    """
    print(f"\n{'='*80}")
    print(f"🚀 INICIANDO GERAÇÃO DE CÓDIGOS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    all_products = []
    page = 1
    total_processed = 0
    total_updated = 0
    total_skipped = 0
    total_errors = 0
    
    while True:
        try:
            data = api.get_products(page=page, limit=100)
            products = data.get("data", [])
            
            if not products:
                break
            
            print(f"\n{'─'*80}")
            print(f"📄 Processando página {page} ({len(products)} produtos)")
            print(f"{'─'*80}\n")
            
            for product_summary in products:
                total_processed += 1
                product_id = product_summary['id']
                product_name = product_summary.get('nome', 'Sem nome')
                
                print(f"\n[{total_processed}] 📦 {product_name}")
                print(f"    ID: {product_id}")
                
                # Buscar detalhes completos
                try:
                    details_response = api.get_product(product_id)
                    product_details = details_response.get('data', {})
                except Exception as e:
                    print(f"    ❌ Erro ao buscar detalhes: {e}")
                    total_errors += 1
                    all_products.append(product_summary)
                    continue
                
                # Gerar e atualizar código
                success, code, message = generate_and_update_code(product_summary, product_details)
                
                if success:
                    print(f"    ✅ {message}")
                    product_details['codigo'] = code  # Atualiza no dump
                    total_updated += 1
                else:
                    print(f"    ⏭️  {message}")
                    total_skipped += 1
                
                # Processar variações
                process_product_variations(product_details)
                
                all_products.append(product_details)
            
            page += 1
        
        except Exception as e:
            print(f"\n❌ Erro na página {page}: {e}")
            break
    
    # Salvar dump
    print(f"\n💾 Salvando dump em {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    
    # Relatório final
    print(f"\n{'='*80}")
    print(f"📊 RELATÓRIO FINAL")
    print(f"{'='*80}")
    print(f"✅ Produtos processados: {total_processed}")
    print(f"🏷️  Códigos gerados e atualizados: {total_updated}")
    print(f"⏭️  Ignorados (já tinham código/regra): {total_skipped}")
    print(f"❌ Erros: {total_errors}")
    print(f"💾 Dump salvo: {OUTPUT_FILE}")
    print(f"{'='*80}\n")
    
    # Estatísticas do banco
    stats = db.get_stats()
    print(f"📊 ESTATÍSTICAS DO BANCO DE DADOS")
    print(f"{'='*80}")
    print(f"Contadores de código cadastrados: {stats['counters']}")
    print(f"\nÚltimos contadores usados:")
    for counter in stats['recent_counters'][:5]:
        print(f"  • {counter['prefix']}: {counter['last_value']:05d} ({counter['category_name']})")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    dump_and_update_product_codes()
