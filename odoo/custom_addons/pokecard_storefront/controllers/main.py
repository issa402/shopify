from odoo import http
from odoo.http import request


class PokeCardStorefront(http.Controller):
    @http.route("/pokecard-store", type="http", auth="public", website=True, sitemap=True)
    def pokecard_store(self, **kwargs):
        products = request.env["product.template"].sudo().search(
            [
                ("pokemon_inventory_id", "!=", False),
                ("sale_ok", "=", True),
                ("is_published", "=", True),
            ],
            order="pokemon_last_synced_at desc, write_date desc",
            limit=24,
        )
        raw_count = len(products.filtered(lambda product: product.pokemon_asset_type == "RAW"))
        slab_count = len(products.filtered(lambda product: product.pokemon_asset_type == "SLAB"))
        return request.render(
            "pokecard_storefront.pokecard_store_homepage",
            {
                "pokemon_products": products,
                "pokemon_product_count": len(products),
                "pokemon_raw_count": raw_count,
                "pokemon_slab_count": slab_count,
            },
        )
