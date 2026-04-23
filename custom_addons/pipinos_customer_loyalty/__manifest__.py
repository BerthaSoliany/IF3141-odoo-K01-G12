{
    "name": "PIPINOS Customer Intelligence & Loyalty System",
    "summary": "Sistem demografi, loyalty, dan analitik pengunjung untuk PIPINOS",
    "version": "1.0",
    "author": "G12",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/menus.xml",
        "views/pengunjung_views.xml",
        "views/loyalty_views.xml",
        "views/transaksi_views.xml",
        "views/dashboard_analitik_views.xml",
        "views/sequences.xml",
        "data/sample_data.xml"
    ],
    "application": True,
    "installable": True
}
