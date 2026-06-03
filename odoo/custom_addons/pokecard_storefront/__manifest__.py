{
    "name": "PokeCard Storefront",
    "summary": "High-trust Pokemon card seller storefront for Odoo Community",
    "version": "19.0.1.1.0",
    "category": "Website/Website",
    "author": "Shopify Pokemon Workspace",
    "license": "LGPL-3",
    "depends": [
        "website",
        "website_sale",
        "website_sale_stock",
        "sale_management",
        "stock",
        "crm",
        "product",
    ],
    "data": [
        "views/product_template_views.xml",
        "views/website_pages.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "pokecard_storefront/static/src/css/pokecard_storefront.css",
        ],
    },
    "installable": True,
    "application": False,
}
