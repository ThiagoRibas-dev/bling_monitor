"""
Sincronizador de ordens do Bling
"""

from datetime import datetime, timedelta
from bling_logger import log


class OrderSynchronizer:
    def __init__(self, api, db):
        self.api = api
        self.db = db

    def sync_all_orders(self, force_full=False):
        """Sincroniza ordens de produção e compras."""
        log.info("🔄 Sincronizando ordens com banco local...")

        self.sync_production_orders(force_full)
        self.sync_purchase_orders(force_full)

    def sync_production_orders(self, force_full=False):
        """Sincroniza ordens de produção."""
        log.info("   📦 Sincronizando ordens de PRODUÇÃO...")

        # Determinar data inicial
        if force_full:
            start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        else:
            last_sync = self.db.get_last_sync_date("production")
            if last_sync:
                start_date = (
                    datetime.fromisoformat(last_sync) + timedelta(days=1)
                ).strftime("%Y-%m-%d")
            else:
                start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

        end_date = datetime.now().strftime("%Y-%m-%d")
        log.info(f"      Período: {start_date} até {end_date}")

        all_orders_with_details = []
        page = 1
        max_date = None

        while page <= 100:
            try:
                response = self.api.get_production_orders(
                    pagina=page,
                    limite=100,
                    dataInicial=start_date,
                    dataFinal=end_date,
                    criterio=3,
                )

                orders_summary = response.get("data", [])
                if not orders_summary:
                    break

                log.info(
                    f"      Página {page}: {len(orders_summary)} ordens encontradas"
                )

                # Buscar detalhes de cada ordem
                for order_summary in orders_summary:
                    order_id = order_summary.get("id")

                    try:
                        # Buscar detalhes completos
                        detail_response = self.api.get_production_order_details(
                            order_id
                        )

                        if order_id == 24589291193:
                            log.info("debug")

                        order_full = detail_response.get("data", {})

                        # Verificar se tem itens
                        itens = order_full.get("itens", [])
                        if itens:
                            log.info(f"         Ordem {order_id}: {len(itens)} itens")
                        else:
                            log.info(f"         Ordem {order_id}: sem itens")

                        all_orders_with_details.append(order_full)

                        # Rastrear data máxima
                        order_date = (
                            order_full.get("dataInicio")
                            or order_full.get("dataPrevisaoInicio")
                            or order_full.get("dataFim")
                            or order_full.get("dataPrevisaoFinal")
                        )

                        if order_date and (not max_date or order_date > max_date):
                            max_date = order_date

                    except Exception as e:
                        log.error(
                            f"         ❌ Erro ao buscar detalhes da ordem {order_id}: {e}"
                        )
                        # Usar dados resumidos como fallback
                        order_summary["itens"] = []  # Sem itens
                        all_orders_with_details.append(order_summary)

                page += 1

            except Exception as e:
                log.error(f"      Erro na página {page}: {e}")
                break

        if all_orders_with_details:
            self.db.save_production_orders(all_orders_with_details)
            if max_date:
                self.db.update_sync_control(
                    "production", max_date, len(all_orders_with_details)
                )
            log.info(
                f"      ✅ {len(all_orders_with_details)} ordens salvas com detalhes"
            )
        else:
            log.info("      ℹ️  Nenhuma ordem nova")

    def sync_purchase_orders(self, force_full=False):
        """Sincroniza pedidos de compra."""
        log.info("   📦 Sincronizando pedidos de COMPRA...")

        # Determinar data inicial
        if force_full:
            start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        else:
            last_sync = self.db.get_last_sync_date("purchase")
            if last_sync:
                start_date = (
                    datetime.fromisoformat(last_sync) + timedelta(days=1)
                ).strftime("%Y-%m-%d")
            else:
                start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

        end_date = datetime.now().strftime("%Y-%m-%d")
        log.info(f"      Período: {start_date} até {end_date}")

        all_orders = []
        page = 1
        max_date = None

        while page <= 100:
            try:
                response = self.api.get_purchase_orders(
                    pagina=page,
                    limite=100,
                    dataInicial=start_date,
                    dataFinal=end_date,
                    criterio=3,
                )

                # Pedidos de compra JÁ vêm com itens na listagem
                orders = response.get("data", [])
                if not orders:
                    break

                all_orders.extend(orders)

                for order in orders:
                    order_date = order.get(
                        "data"
                    )  # Pedido de compra usa 'data' como campo
                    if order_date and (not max_date or order_date > max_date):
                        max_date = order_date

                log.info(f"      Página {page}: {len(orders)} pedidos")
                page += 1

            except Exception as e:
                log.error(f"      Erro: {e}")
                break

        if all_orders:
            self.db.save_purchase_orders(all_orders)
            if max_date:
                self.db.update_sync_control("purchase", max_date, len(all_orders))
            log.info(f"      ✅ {len(all_orders)} pedidos salvos")
        else:
            log.info(f"      ℹ️  Nenhum pedido novo")
