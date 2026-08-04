from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    pokemon_inventory_id = fields.Char(
        string="PokemonTool Inventory ID",
        copy=False,
        index=True,
        help="UUID of the source row in PokemonTool inventory.",
    )
    pokemon_external_card_id = fields.Char(
        string="External Card ID",
        index=True,
        help="Exact-card identifier from the Pokemon market data source.",
    )
    pokemon_set_name = fields.Char(string="Set Name")
    pokemon_card_number = fields.Char(string="Card Number")
    pokemon_rarity = fields.Char(string="Rarity")
    pokemon_image_url = fields.Char(string="Market Image URL")
    pokemon_condition = fields.Selection(
        [
            ("NM", "Near Mint"),
            ("LP", "Lightly Played"),
            ("MP", "Moderately Played"),
            ("HP", "Heavily Played"),
            ("DAMAGED", "Damaged"),
            ("SEALED", "Sealed"),
            ("GRADED", "Graded"),
        ],
        string="Condition",
    )
    pokemon_asset_type = fields.Selection(
        [("RAW", "Raw Single"), ("SLAB", "Graded Slab"), ("SEALED", "Sealed Product")],
        string="Pokemon Asset Type",
        default="RAW",
    )
    pokemon_grader = fields.Char(string="Grader")
    pokemon_grade = fields.Char(string="Grade")
    pokemon_cert_number = fields.Char(string="Certification Number")
    pokemon_acquisition_cost = fields.Float(string="Acquisition Cost")
    pokemon_market_value = fields.Float(string="Market Value")
    pokemon_target_margin_pct = fields.Float(string="Target Margin %", default=30.0)
    pokemon_price_source = fields.Char(string="Price Source")
    pokemon_market_updated_at = fields.Char(string="Market Updated At")
    pokemon_sync_source = fields.Selection(
        [("manual", "Manual"), ("pokemontool", "PokemonTool")],
        string="Sync Source",
        default="manual",
        copy=False,
    )
    pokemon_last_synced_at = fields.Datetime(string="Last Synced From PokemonTool", copy=False)
