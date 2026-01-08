"""
Script de teste rápido para validar módulos
"""
from bling_auth import ensure_authenticated
from bling_api import BlingAPI
from bling_db import BlingDatabase
from bling_logger import log

def test_auth():
    """Testa autenticação."""
    log.info("🔑 Testando autenticação...")
    try:
        token = ensure_authenticated()
        log.info(f"✅ Token obtido: {token[:20]}...")
        return True
    except Exception as e:
        log.error(f"❌ Erro: {e}")
        return False

def test_api():
    """Testa chamada à API."""
    log.info("📡 Testando API...")
    try:
        api = BlingAPI(ensure_authenticated)
        data = api.get_products(page=1, limit=1)
        products = data.get('data', [])
        log.info(f"✅ API funcionando. {len(products)} produto(s) retornado(s)")
        return True
    except Exception as e:
        log.error(f"❌ Erro: {e}")
        return False

def test_database():
    """Testa banco de dados."""
    log.info("💾 Testando banco de dados...")
    try:
        db = BlingDatabase()
        
        # Testa geração de código
        code1 = db.get_next_code("TEST", category_id=999, category_name="Teste")
        code2 = db.get_next_code("TEST", category_id=999, category_name="Teste")
        
        assert code1 == "TEST00001", f"Código esperado TEST00001, obtido {code1}"
        assert code2 == "TEST00002", f"Código esperado TEST00002, obtido {code2}"
        
        # Testa idempotência
        db.mark_event_processed("test_event_123", "product.created", 999, {"test": True})
        assert db.is_event_processed("test_event_123"), "Evento deveria estar marcado"
        assert not db.is_event_processed("test_event_999"), "Evento não deveria estar marcado"
        
        log.info("✅ Banco funcionando corretamente")
        
        # Mostra stats
        stats = db.get_stats()
        log.info("📊 Estatísticas:")
        log.info(f"   Contadores: {stats['counters']}")
        log.info(f"   Eventos: {stats['events']}")
        
        return True
    except Exception as e:
        log.error(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    log.info("="*60)
    log.info("🧪 TESTE DE VALIDAÇÃO DOS MÓDULOS")
    log.info("="*60)
    
    results = {
        "Autenticação": test_auth(),
        "API": test_api(),
        "Database": test_database()
    }
    
    log.info("="*60)
    log.info("📊 RESULTADO DOS TESTES")
    log.info("="*60)
    
    for test, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        log.info(f"{test}: {status}")
    
    all_passed = all(results.values())
    
    log.info("="*60)
    if all_passed:
        log.info("🎉 TODOS OS TESTES PASSARAM!")
    else:
        log.warning("⚠️  ALGUNS TESTES FALHARAM")
    log.info("="*60)
