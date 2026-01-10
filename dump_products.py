"""
Script de geração de códigos para produtos - COM PERSISTÊNCIA
"""

import json

# Imports dos novos módulos
from bling_logger import log
from bling_auth import ensure_authenticated
from bling_api import BlingAPI
from bling_sync import OrderSynchronizer
from bling_db import BlingDatabase
from bling_utils import (
    get_category_cache,
    extract_category_info,
    should_generate_code,
    should_ignore_product,
)

# Cliente API e Database
api = BlingAPI(ensure_authenticated)
db = BlingDatabase()

# Cache de categorias (NOVO)
category_cache = get_category_cache()

# Configurações de desativação (importado de test.py)
EXCLUDED_CATEGORIES = {"notebook", "sff", "mini", "monitor"}
IGNORE_SUBCATEGORIES = {"submaquina"}

OUTPUT_FILE = "products_dump.json"


def generate_and_update_code(product, product_details):
    """
    Gera código e atualiza produto na API.

    Returns:
        (success: bool, code: str or None, message: str)
    """
    product_id = product["id"]

    # Passa o cache para should_generate_code (ATUALIZADO)
    should_gen, reason, prefix = should_generate_code(product_details, category_cache)

    if not should_gen:
        return False, None, reason

    # Gerar código usando banco de dados (thread-safe)
    category, subcategory, full, cat_id = extract_category_info(
        product_details, category_cache
    )
    new_code = db.get_next_code(prefix=prefix, category_id=cat_id, category_name=full)

    log.info(f"   🏷️  Código gerado: {new_code}")

    # Atualizar na API
    try:
        api.update_product(product_id, {"codigo": new_code})
        return True, new_code, f"Atualizado com sucesso ({reason})"
    except Exception as e:
        log.error(f"Erro ao atualizar produto {product_id}: {e}")
        return False, None, f"Erro ao atualizar: {e}"


def process_product_variations(product_details):
    """
    Processa variações de produto (se houver).
    """
    variations = product_details.get("variacoes", [])

    if not variations:
        return

    log.info(f"   🔀 Produto tem {len(variations)} variações")

    for var in variations:
        var_id = var.get("id")
        var_name = var.get("nome", "Sem nome")
        var_code = var.get("codigo")

        if var_code:
            log.info(f"      ⏭️  Variação {var_id} já tem código: {var_code}")
            continue

        log.info(f"      🔍 Processando variação: {var_name}")

        # Variações herdam categoria do produto pai
        should_gen, reason, prefix = should_generate_code(
            product_details, category_cache
        )

        if not should_gen:
            log.info(f"      ⏭️  {reason}")
            continue

        # Gerar código
        category, subcategory, full, cat_id = extract_category_info(
            product_details, category_cache
        )
        new_code = db.get_next_code(
            prefix=prefix, category_id=cat_id, category_name=full
        )

        log.info(f"      🏷️  Código gerado para variação: {new_code}")

        # Atualizar variação
        try:
            api.update_product(var_id, {"codigo": new_code})
            var["codigo"] = new_code
            log.info("      ✅ Variação atualizada com sucesso")
        except Exception as e:
            log.error(f"      ❌ Erro ao atualizar variação {var_id}: {e}")


def dump_update_and_deactivate_products():
    """
    Varre todos os produtos para:
    1. Gerar códigos para produtos e variações sem código.
    2. Desativar produtos com estoque zerado por vendas.
    """
    log.info(f"{'=' * 80}")
    log.info("🚀 INICIANDO PROCESSAMENTO DE PRODUTOS")
    log.info(f"{'=' * 80}")

    # Sincronizar ordens antes de processar produtos
    log.info("\n📥 PASSO 1: Sincronizando ordens...")
    syncer = OrderSynchronizer(api, db)
    syncer.sync_all_orders(force_full=False)  # Incremental por padrão

    # Carregar cache de categorias
    log.info("\n📥 PASSO 2: Carregando categorias...")
    category_cache.load(api)

    log.info("\n📥 PASSO 3: Processando produtos...")
    all_products = []
    page = 1
    total_processed = 0
    total_updated = 0
    total_skipped = 0
    total_errors = 0
    deactivated_count = 0
    ignored_count = 0

    while True:
        try:
            data = api.get_products(page=page, limit=100)
            products = data.get("data", [])

            if not products:
                break

            log.info(f"{'─' * 80}")
            log.info(f"📄 Processando página {page} ({len(products)} produtos)")
            log.info(f"{'─' * 80}")

            for product_summary in products:
                total_processed += 1
                product_id = product_summary["id"]
                product_name = product_summary.get("nome", "Sem nome")

                log.info(f"[{total_processed}] 📦 {product_name} (ID: {product_id})")

                # Buscar detalhes completos
                try:
                    details_response = api.get_product(product_id)
                    product_details = details_response.get("data", {})
                except Exception as e:
                    log.error(f"    ❌ Erro ao buscar detalhes: {e}")
                    total_errors += 1
                    all_products.append(product_summary)
                    continue

                # Gerar e atualizar código
                success, code, message = generate_and_update_code(
                    product_summary, product_details
                )

                if success:
                    log.info(f"    ✅ {message}")
                    product_details["codigo"] = code
                    total_updated += 1
                else:
                    log.info(f"    ⏭️  {message}")
                    total_skipped += 1

                # Processar variações
                process_product_variations(product_details)

                # Checar estoque usando banco local
                stock = product_details.get("estoqueAtual", 0)
                if stock <= 0 and product_summary["estoque"]:
                    stock = product_summary["estoque"].get("saldoVirtualTotal", 0)

                if stock <= 0:
                    log.info("   📉 Estoque zerado ou negativo encontrado.")

                    # Verificar se deve ignorar por categoria
                    should_ignore, ignore_reason = should_ignore_product(
                        product_details,
                        category_cache,
                        EXCLUDED_CATEGORIES,
                        IGNORE_SUBCATEGORIES,
                    )

                    if should_ignore:
                        ignored_count += 1
                        log.info(f"   ⏭️  IGNORADO para desativação: {ignore_reason}")
                    else:
                        # Verificar no banco local se teve entrada
                        log.info(
                            "   🔍 Verificando histórico de entradas no banco local..."
                        )
                        has_entry, entry_details = db.product_has_entry(product_id)

                        if has_entry:
                            log.info("   📊 Entrada encontrada!")
                            log.info(
                                f"   📊 Tipo: {entry_details.get('source', 'N/A')}"
                            )
                            log.info(
                                f"   📊 Pedido: {entry_details.get('order_number', 'N/A')}"
                            )
                            log.info(
                                f"   📊 Data: {entry_details.get('order_date', 'N/A')}"
                            )
                            log.info(
                                f"   📊 Quantidade: {entry_details.get('quantity', 0)}"
                            )

                            # Somente desativa se estiver ativo
                            if product_details.get("situacao") == "A":
                                log.warning("   🔴 DESATIVANDO produto...")
                                try:
                                    api.update_product_situation(product_id, "I")
                                    deactivated_count += 1
                                    product_details["situacao"] = "I"
                                    log.info("   ✅ Produto DESATIVADO com sucesso")
                                except Exception as e:
                                    log.error(
                                        f"   ❌ Erro ao desativar produto {product_id}: {e}"
                                    )
                                    total_errors += 1
                            else:
                                log.info("   ✅ Produto já estava INATIVO.")
                        else:
                            log.info(
                                "   ✅ Produto sem histórico de entradas (não será desativado)"
                            )

                all_products.append(product_details)

            page += 1

        except Exception as e:
            log.error(f"❌ Erro fatal na página {page}: {e}")
            break

    # Salvar dump
    log.info(f"💾 Salvando dump em {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    # Relatório final
    log.info(f"{'=' * 80}")
    log.info("📊 RELATÓRIO FINAL")
    log.info(f"{'=' * 80}")
    log.info("--- Geração de Códigos ---")
    log.info(f"✅ Produtos processados: {total_processed}")
    log.info(f"🏷️  Códigos gerados/atualizados: {total_updated}")
    log.info(f"⏭️  Ignorados (código existente/regra): {total_skipped}")
    log.info("--- Desativação de Produtos ---")
    log.info(f"🔴 Desativados (zerado por vendas): {deactivated_count}")
    log.info(f"⏭️  Ignorados para desativação (categoria): {ignored_count}")
    log.info("--- Resumo ---")
    log.info(f"❌ Erros totais (API/DB): {total_errors}")
    log.info(f"💾 Dump salvo em: {OUTPUT_FILE}")
    log.info(f"{'=' * 80}")

    # Estatísticas do banco
    stats = db.get_stats()
    log.info("📊 ESTATÍSTICAS DO BANCO DE DADOS")
    log.info(f"{'=' * 80}")
    log.info(f"Contadores de código cadastrados: {stats['counters']}")
    if stats["recent_counters"]:
        log.info("Últimos contadores usados:")
        for counter in stats["recent_counters"][:5]:
            log.info(
                f"  • {counter['prefix']}: {counter['last_value']:05d} ({counter['category_name']})"
            )
    log.info(f"{'=' * 80}")


if __name__ == "__main__":
    try:
        dump_update_and_deactivate_products()
    except Exception as e:
        log.error(f"❌ Erro fatal {e}")

    input("Pressione Enter para sair...")
