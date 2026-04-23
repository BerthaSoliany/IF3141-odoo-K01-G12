from odoo import api, fields, models

class Transaksi(models.Model):
    _name = 'pipinos.transaksi'
    _description = 'Data Pembelian'
    _rec_name = 'id_transaksi'

    id_transaksi = fields.Char(string='ID Transaksi', required=True, copy=False, readonly=True, default=lambda self: 'Baru')
    id_pengunjung = fields.Many2one('pipinos.pengunjung', string='pengunjung (FK)')
    tanggal = fields.Datetime(string='Tanggal Transaksi', default=fields.Datetime.now)
    total_nominal = fields.Float(string='Total Nominal')

    detail_ids = fields.One2many('pipinos.detail.transaksi', 'id_transaksi', string='Rincian Menu')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('id_transaksi', 'Baru') == 'Baru':
                vals['id_transaksi'] = self.env['ir.sequence'].next_by_code('pipinos.transaksi') or 'Baru'
        return super().create(vals_list)


class DetailTransaksi(models.Model):
    _name = 'pipinos.detail.transaksi'
    _description = 'Rincian Menu'

    id_detail = fields.Char(string='ID Detail', required=True, copy=False, readonly=True, default=lambda self: 'Baru')
    id_transaksi = fields.Many2one('pipinos.transaksi', string='Transaksi (FK)')
    id_pengunjung = fields.Many2one('pipinos.pengunjung', string='pengunjung (FK)', related='id_transaksi.id_pengunjung', store=True, readonly=True)
    id_menu = fields.Many2one('pipinos.item.menu', string='Menu (FK)')
    qty = fields.Integer(string='Qty')
    subtotal = fields.Float(string='Subtotal')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('id_detail', 'Baru') == 'Baru':
                vals['id_detail'] = self.env['ir.sequence'].next_by_code('pipinos.detail.transaksi') or 'Baru'
        return super().create(vals_list)


class ItemMenu(models.Model):
    _name = 'pipinos.item.menu'
    _description = 'Data Menu'
    _rec_name = 'nama_menu'

    id_menu = fields.Char(string='ID Menu', required=True, copy=False, readonly=True, default=lambda self: 'Baru')
    nama_menu = fields.Char(string='Nama Menu', required=True)
    harga = fields.Float(string='Harga')
    kategori = fields.Char(string='Kategori')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('id_menu', 'Baru') == 'Baru':
                vals['id_menu'] = self.env['ir.sequence'].next_by_code('pipinos.item.menu') or 'Baru'
        return super().create(vals_list)
