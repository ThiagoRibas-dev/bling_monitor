"""
Servidor de webhooks Bling com validação HMAC e processamento assíncrono
"""
from flask import Flask, request, jsonify
import hmac
import hashlib
import os
import threading
import queue
from dotenv import load_dotenv

from bling_auth import ensure_authenticated
from bling_api import BlingAPI
from bling_db import BlingDatabase
from bling_utils import (
    should_ignore_product, 
    check_stock_depleted_by_sales,
    should_generate_code,
    extract_category_info
)

load_dotenv()

app = Flask(__name__)

# Configurações
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", 5000))

# Recursos
api = BlingAPI(ensure_authenticated)
db = BlingDatabase()

# Fila de eventos
event_queue = queue.Queue()


def verify_hmac_signature(payload_bytes, signature):
    """
    Verifica assinatura HMAC-SHA256 do webhook.
    
    Args:
        payload_bytes: Corpo da requisição (bytes brutos)
        signature: Header X-Bling-Signature-256
    
    Returns:
        bool
    """
    expected = 'sha256=' + hmac.new(
        CLIENT_SECRET.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)


@app.route('/webhook/bling', methods=['POST'])
def webhook_handler():
    """
    Endpoint principal de recepção de webhooks.
    DEVE responder em < 5 segundos.
    """
    # Validar assinatura HMAC
    signature = request.headers.get('X-Bling-Signature-256', '')
    
    if not verify_hmac_signature(request.get_data(), signature):
        print("❌ Assinatura HMAC inválida!")
        return jsonify({"error": "Invalid signature"}), 401
    
    # Parsear payload
    try:
        payload = request.get_json()
    except Exception as e:
        print(f"❌ Erro ao parsear JSON: {e}")
        return jsonify({"error": "Invalid JSON"}), 400
    
    event_id = payload.get('eventId')
    event_type = payload.get('event')
    
    if not event_id or not event_type:
        print("❌ Payload sem eventId ou event")
        return jsonify({"error": "Missing eventId or event"}), 400
    
    # Verificar idempotência
    if db.is_event_processed(event_id):
        print(f"ℹ️  Evento {event_id} já processado anteriormente (idempotência)")
        return jsonify({"status": "already_processed"}), 200
    
    # Enfileirar para processamento assíncrono
    event_queue.put(payload)
    
    print(f"✅ Webhook recebido: {event_type} (eventId: {event_id})")
    
    # Responder rapidamente (<5s)
    return jsonify({"status": "queued"}), 200


@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check."""
    stats = db.get_stats()
    return jsonify({
        "status": "healthy",
        "queue_size": event_queue.qsize(),
        "db_stats": stats
    }), 200


def process_stock_event(data):
    """Processa evento de estoque (stock.updated)."""
    
    product_info = data.get('produto', {})
    product_id = product_info.get('id')
    
    if not product_id:
        print("⚠️  Evento de estoque sem ID de produto")
        return
    
    print(f"📦 Processando evento de estoque para produto {product_id}")
    
    try:
        # Buscar produto completo
        response = api.get_product(product_id)
        product = response.get('data', {})
        
        # Verificar se deve ignorar
        should_ignore, reason = should_ignore_product(product)
        if should_ignore:
            print(f"   ⏭️  {reason}")
            return
        
        # Verificar estoque
        stock = product.get('estoque', {}).get('saldoVirtualTotal', 0)
        
        if stock > 0:
            print("   ✅ Estoque > 0, nada a fazer")
            return
        
        # Verificar se zerou por vendas
        is_depleted, details = check_stock_depleted_by_sales(api, product_id)
        
        if is_depleted:
            print("   🔴 Desativando produto (zerado por vendas)")
            api.update_product_situation(product_id, 'I')
            print("   ✅ Produto desativado")
        else:
            print(f"   ℹ️  Não desativar: {details['reason']}")
    
    except Exception as e:
        print(f"   ❌ Erro ao processar: {e}")


def process_product_event(data):
    """Processa evento de produto (product.created, product.updated)."""
    
    product_id = data.get('id')
    
    if not product_id:
        print("⚠️  Evento de produto sem ID")
        return
    
    print(f"📦 Processando evento de produto {product_id}")
    
    try:
        # Se já tem código, ignora
        if data.get('codigo'):
            print(f"   ℹ️  Produto já possui código: {data.get('codigo')}")
            return
        
        # Buscar detalhes completos
        response = api.get_product(product_id)
        product = response.get('data', {})
        
        # Verificar se deve gerar código
        should_gen, reason, prefix = should_generate_code(product)
        
        if not should_gen:
            print(f"   ⏭️  {reason}")
            return
        
        # Gerar código
        category, subcategory, full, cat_id = extract_category_info(product)
        new_code = db.get_next_code(
            prefix=prefix,
            category_id=cat_id,
            category_name=full
        )
        
        print(f"   🏷️  Gerando código: {new_code}")
        
        # Atualizar produto
        api.update_product(product_id, {"codigo": new_code})
        print("   ✅ Código atribuído com sucesso")
    
    except Exception as e:
        print(f"   ❌ Erro ao processar: {e}")


def event_processor_worker():
    """Thread worker que processa eventos da fila."""
    print("🔄 Worker de processamento iniciado")
    
    while True:
        try:
            # Pega evento da fila (bloqueante)
            payload = event_queue.get(timeout=1)
            
            event_id = payload.get('eventId')
            event_type = payload.get('event')
            data = payload.get('data', {})
            
            print(f"\n{'─'*60}")
            print(f"🔄 Processando evento: {event_type} (ID: {event_id})")
            print(f"{'─'*60}")
            
            # Marcar como processado
            product_id = data.get('id') or data.get('produto', {}).get('id')
            db.mark_event_processed(event_id, event_type, product_id, payload)
            
            # Rotear para processador específico
            if event_type == 'stock.updated':
                process_stock_event(data)
            
            elif event_type in ['product.created', 'product.updated']:
                process_product_event(data)
            
            else:
                print(f"⚠️  Tipo de evento desconhecido: {event_type}")
            
            event_queue.task_done()
            print("✅ Evento processado com sucesso\n")
        
        except queue.Empty:
            continue
        
        except Exception as e:
            print(f"❌ Erro ao processar evento: {e}\n")


def start_server():
    """Inicia servidor de webhooks."""
    print(f"\n{'='*80}")
    print("🚀 INICIANDO SERVIDOR DE WEBHOOKS BLING")
    print(f"{'='*80}")
    print("🌐 Host: 0.0.0.0")
    print(f"🔌 Porta: {WEBHOOK_PORT}")
    print("📍 Endpoint: http://your-domain.com/webhook/bling")
    print("❤️  Health: http://your-domain.com/health")
    print(f"{'='*80}\n")
    
    # Iniciar worker thread
    worker_thread = threading.Thread(target=event_processor_worker, daemon=True)
    worker_thread.start()
    
    # Iniciar Flask
    app.run(
        host='0.0.0.0',
        port=WEBHOOK_PORT,
        debug=False,
        threaded=True
    )


if __name__ == '__main__':
    start_server()
