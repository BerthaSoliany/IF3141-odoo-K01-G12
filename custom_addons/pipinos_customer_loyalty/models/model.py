from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Pelanggan(models.Model):
    _name = 'pipinos.pelanggan'
    _description = 'Data Profil Pelanggan'
    _rec_name = 'nama_lengkap'

    id_pelanggan = fields.Char(string='ID Pelanggan', required=True, copy=False, readonly=True, default=lambda self: 'Baru')
    nama_depan = fields.Char(string='Nama Depan', required=True)
    nama_belakang = fields.Char(string='Nama Belakang')
    nama_lengkap = fields.Char(string='Nama Lengkap', compute='_compute_nama_lengkap',store=True)
    no_hp = fields.Char(string='No HP')

    demografi_ids = fields.One2many('pipinos.demografi', 'id_pelanggan', string='Data Demografi')
    loyalty_ids = fields.One2many('pipinos.loyalty.member', 'id_pelanggan', string='Data Loyalty')

    usia_input = fields.Integer(string='Usia', compute='_compute_demografi_fields', inverse='_inverse_demografi_fields')
    gender_input = fields.Selection([('L', 'Laki-Laki'), ('P', 'Perempuan')], string='Gender', compute='_compute_demografi_fields', inverse='_inverse_demografi_fields')
    
    total_poin_input = fields.Integer(string='Total Poin', compute='_compute_loyalty_fields', inverse='_inverse_loyalty_fields')
    status_level_output = fields.Selection([('silver', 'Silver'), ('gold', 'Gold'), ('platinum', 'Platinum')], string='Status Level', compute='_compute_loyalty_fields')
    
    # nama depan g boleh ada spasi (kl ada nama tengah taro di nama belakang)
    @api.constrains('nama_depan')
    def _check_nama_depan(self):
        for rec in self:
            if rec.nama_depan and ' ' in rec.nama_depan:
                raise ValidationError("Nama depan tidak boleh mengandung spasi! Masukkan kata kedua di kolom Nama Belakang.")

    # buat full name
    @api.depends('nama_depan', 'nama_belakang')
    def _compute_nama_lengkap(self):
        for rec in self:
            rec.nama_lengkap = f"{rec.nama_depan or ''} {rec.nama_belakang or ''}".strip()

    # demografi dan loyalty dibuat compute+inverse supaya bisa edit langsung dari form pelanggan tanpa harus masuk ke form demografi/loyalty
    @api.depends('demografi_ids.usia', 'demografi_ids.gender')
    def _compute_demografi_fields(self):
        for rec in self:
            if rec.demografi_ids:
                rec.usia_input = rec.demografi_ids[0].usia
                rec.gender_input = rec.demografi_ids[0].gender
            else:
                rec.usia_input = 0
                rec.gender_input = False

    def _inverse_demografi_fields(self):
        for rec in self:
            if rec.demografi_ids:
                rec.demografi_ids[0].usia = rec.usia_input
                rec.demografi_ids[0].gender = rec.gender_input
            else:
                self.env['pipinos.demografi'].create({
                    'id_pelanggan': rec.id,
                    'usia': rec.usia_input,
                    'gender': rec.gender_input
                })

    @api.depends('loyalty_ids.total_poin', 'loyalty_ids.status_level')
    def _compute_loyalty_fields(self):
        for rec in self:
            if rec.loyalty_ids:
                rec.total_poin_input = rec.loyalty_ids[0].total_poin
                rec.status_level_output = rec.loyalty_ids[0].status_level
            else:
                rec.total_poin_input = 0
                rec.status_level_output = False

    def _inverse_loyalty_fields(self):
        for rec in self:
            if rec.loyalty_ids:
                rec.loyalty_ids[0].total_poin = rec.total_poin_input
            else:
                self.env['pipinos.loyalty.member'].create({
                    'id_pelanggan': rec.id,
                    'total_poin': rec.total_poin_input
                })
    
    # ini buat generate id otomatis pk sequence
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('id_pelanggan', 'Baru') == 'Baru':
                vals['id_pelanggan'] = self.env['ir.sequence'].next_by_code('pipinos.pelanggan') or 'Baru'
        return super().create(vals_list)



class Transaksi(models.Model):
    _name = 'pipinos.transaksi'
    _description = 'Data Pembelian'
    _rec_name = 'id_transaksi'

    id_transaksi = fields.Char(string='ID Transaksi', required=True, copy=False, readonly=True, default=lambda self: 'Baru')
    id_pelanggan = fields.Many2one('pipinos.pelanggan', string='Pelanggan (FK)')
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



class Demografi(models.Model):
    _name = 'pipinos.demografi'
    _description = 'Data Perilaku & Demografi'
    _rec_name = 'id_demografi'

    id_demografi = fields.Char(string='ID Demografi', required=True, copy=False, readonly=True, default=lambda self: 'Baru')
    id_pelanggan = fields.Many2one('pipinos.pelanggan', string='Pelanggan (FK)', required=True, ondelete='cascade')
    
    # usia dibuat rata2 tampilannya
    usia = fields.Integer(string='Usia', group_operator='avg')
    
    gender = fields.Selection([
        ('L', 'Laki-Laki'),
        ('P', 'Perempuan')
    ], string='Gender')

    _sql_constraints = [
        ('unique_pelanggan_demografi', 'unique(id_pelanggan)', 'Pelanggan ini sudah memiliki data demografi!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('id_demografi', 'Baru') == 'Baru':
                vals['id_demografi'] = self.env['ir.sequence'].next_by_code('pipinos.demografi') or 'Baru'
        return super().create(vals_list)



class LoyaltyMember(models.Model):
    _name = 'pipinos.loyalty.member'
    _description = 'Status Poin Loyalty'
    _rec_name = 'id_pelanggan'

    id_loyalty = fields.Char(string='ID Loyalty', required=True, copy=False, readonly=True, default=lambda self: 'Baru')
    id_pelanggan = fields.Many2one('pipinos.pelanggan', string='Pelanggan (FK)', required=True, ondelete='cascade')
    total_poin = fields.Integer(string='Total Poin')
    status_level = fields.Selection([
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum')
    ], string='Status Level', compute='_compute_status_level', store=True)

    _sql_constraints = [
        ('unique_pelanggan_loyalty', 'unique(id_pelanggan)', 'Pelanggan ini sudah terdaftar di sistem loyalty!')
    ]

    # aturan status level berdasarkan total poin (hmm, apa dibuat biar bisa diatur manual dr ui y?)
    @api.depends('total_poin')
    def _compute_status_level(self):
        for rec in self:
            if rec.total_poin >= 300:
                rec.status_level = 'platinum'
            elif rec.total_poin >= 100:
                rec.status_level = 'gold'
            else:
                rec.status_level = 'silver'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('id_loyalty', 'Baru') == 'Baru':
                vals['id_loyalty'] = self.env['ir.sequence'].next_by_code('pipinos.loyalty.member') or 'Baru'
        return super().create(vals_list)



class Staff(models.Model):
    _name = 'pipinos.staff'
    _description = 'Data Staff'
    _rec_name = 'nama_staff'

    id_staff = fields.Char(string='ID Staff', required=True, copy=False, readonly=True, default=lambda self: 'Baru')
    nama_staff = fields.Char(string='Nama Staff')
    role = fields.Selection([('admin', 'Admin'), ('kasir', 'Kasir')], string='Role')
    username = fields.Char(string='Username')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('id_staff', 'Baru') == 'Baru':
                vals['id_staff'] = self.env['ir.sequence'].next_by_code('pipinos.staff') or 'Baru'
        return super().create(vals_list)



class LogAksesStaf(models.Model):
    _name = 'pipinos.log.akses'
    _description = 'Audit Jejak'

    id_log = fields.Char(string='ID Log', required=True, copy=False, readonly=True, default=lambda self: 'Baru')
    id_staff = fields.Many2one('pipinos.staff', string='Staff (FK)')
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now)
    aksi = fields.Char(string='Aksi')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('id_log', 'Baru') == 'Baru':
                vals['id_log'] = self.env['ir.sequence'].next_by_code('pipinos.log.akses') or 'Baru'
        return super().create(vals_list)



class SegmenPelanggan(models.Model):
    _name = 'pipinos.segmen'
    _description = 'Klasifikasi Segmen'
    _rec_name = 'nama_segmen'

    id_segmen = fields.Char(string='ID Segmen', required=True, copy=False, readonly=True, default=lambda self: 'Baru')
    nama_segmen = fields.Char(string='Nama Segmen')
    kriteria = fields.Text(string='Kriteria')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('id_segmen', 'Baru') == 'Baru':
                vals['id_segmen'] = self.env['ir.sequence'].next_by_code('pipinos.segmen') or 'Baru'
        return super().create(vals_list)



class Kampanye(models.Model):
    _name = 'pipinos.kampanye'
    _description = 'Promo Aktif'
    _rec_name = 'nama_kampanye'

    id_kampanye = fields.Char(string='ID Kampanye', required=True, copy=False, readonly=True, default=lambda self: 'Baru')
    nama_kampanye = fields.Char(string='Nama Kampanye')
    tgl_mulai = fields.Date(string='Tgl Mulai')
    tgl_selesai = fields.Date(string='Tgl Selesai')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('id_kampanye', 'Baru') == 'Baru':
                vals['id_kampanye'] = self.env['ir.sequence'].next_by_code('pipinos.kampanye') or 'Baru'
        return super().create(vals_list)