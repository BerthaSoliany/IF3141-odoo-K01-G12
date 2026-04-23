from odoo import api, fields, models
from odoo.exceptions import ValidationError

class Pengunjung(models.Model):
    _name = 'pipinos.pengunjung'
    _description = 'Data Profil pengunjung'
    _rec_name = 'nama_lengkap'

    id_pengunjung = fields.Char(string='ID pengunjung', required=True, copy=False, readonly=True, default=lambda self: 'Baru')
    nama_depan = fields.Char(string='Nama Depan', required=True)
    nama_belakang = fields.Char(string='Nama Belakang')
    nama_lengkap = fields.Char(string='Nama Lengkap', compute='_compute_nama_lengkap', store=True)
    no_hp = fields.Char(string='No HP')
    favorite_menu_id = fields.Many2one('pipinos.item.menu', string='Menu Favorit', compute='_compute_favorite_menu')
    terdaftar_ids = fields.One2many('pipinos.terdaftar', 'pengunjung_id', string='Terdaftar Segmen')
    segmen_ids = fields.Many2many('pipinos.segmen', string='Segmen pengunjung', compute='_compute_segmen_ids', inverse='_inverse_segmen_ids')

    demografi_ids = fields.One2many('pipinos.demografi', 'id_pengunjung', string='Data Demografi')
    loyalty_ids = fields.One2many('pipinos.loyalty.member', 'id_pengunjung', string='Data Loyalty')

    usia_input = fields.Integer(string='Usia', compute='_compute_demografi_fields', inverse='_inverse_demografi_fields')
    gender_input = fields.Selection([('L', 'Laki-Laki'), ('P', 'Perempuan')], string='Gender', compute='_compute_demografi_fields', inverse='_inverse_demografi_fields')

    total_poin_input = fields.Integer(string='Total Poin', compute='_compute_loyalty_fields', inverse='_inverse_loyalty_fields')
    status_level_output = fields.Selection([('silver', 'Silver'), ('gold', 'Gold'), ('platinum', 'Platinum')], string='Status Level', compute='_compute_loyalty_fields')

    @api.constrains('nama_depan')
    def _check_nama_depan(self):
        for rec in self:
            if rec.nama_depan and ' ' in rec.nama_depan:
                raise ValidationError('Nama depan tidak boleh mengandung spasi! Masukkan kata kedua di kolom Nama Belakang.')

    @api.depends('nama_depan', 'nama_belakang')
    def _compute_nama_lengkap(self):
        for rec in self:
            rec.nama_lengkap = f"{rec.nama_depan or ''} {rec.nama_belakang or ''}".strip()

    @api.depends('terdaftar_ids.segmen_id')
    def _compute_segmen_ids(self):
        for rec in self:
            rec.segmen_ids = rec.terdaftar_ids.mapped('segmen_id')

    def _compute_favorite_menu(self):
        detail_obj = self.env['pipinos.detail.transaksi']
        for rec in self:
            grouped = detail_obj.read_group(
                domain=[('id_pengunjung', '=', rec.id), ('id_menu', '!=', False)],
                fields=['qty:sum', 'id_menu'],
                groupby=['id_menu'],
            )
            if grouped:
                best = max(grouped, key=lambda x: x.get('qty_sum', 0))
            else:
                best = False
            if best and best.get('id_menu'):
                rec.favorite_menu_id = best['id_menu'][0]
            else:
                rec.favorite_menu_id = False

    def _inverse_segmen_ids(self):
        for rec in self:
            current_segmen = rec.terdaftar_ids.mapped('segmen_id')
            to_add = rec.segmen_ids - current_segmen
            to_remove = current_segmen - rec.segmen_ids

            for segmen in to_add:
                self.env['pipinos.terdaftar'].create({
                    'pengunjung_id': rec.id,
                    'segmen_id': segmen.id,
                })

            if to_remove:
                rel_to_remove = rec.terdaftar_ids.filtered(lambda r: r.segmen_id in to_remove)
                rel_to_remove.unlink()

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
                    'id_pengunjung': rec.id,
                    'usia': rec.usia_input,
                    'gender': rec.gender_input,
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
                    'id_pengunjung': rec.id,
                    'total_poin': rec.total_poin_input,
                })

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('id_pengunjung', 'Baru') == 'Baru':
                vals['id_pengunjung'] = self.env['ir.sequence'].next_by_code('pipinos.pengunjung') or 'Baru'
        return super().create(vals_list)

class Demografi(models.Model):
    _name = 'pipinos.demografi'
    _description = 'Data Perilaku & Demografi'
    _rec_name = 'id_demografi'

    id_demografi = fields.Char(string='ID Demografi', required=True, copy=False, readonly=True, default=lambda self: 'Baru')
    id_pengunjung = fields.Many2one('pipinos.pengunjung', string='pengunjung (FK)', required=True, ondelete='cascade')
    usia = fields.Integer(string='Usia', group_operator='avg')
    gender = fields.Selection([
        ('L', 'Laki-Laki'),
        ('P', 'Perempuan'),
    ], string='Gender')

    _sql_constraints = [
        ('unique_pengunjung_demografi', 'unique(id_pengunjung)', 'pengunjung ini sudah memiliki data demografi!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('id_demografi', 'Baru') == 'Baru':
                vals['id_demografi'] = self.env['ir.sequence'].next_by_code('pipinos.demografi') or 'Baru'
        return super().create(vals_list)



class SegmenPengunjung(models.Model):
    _name = 'pipinos.segmen'
    _description = 'Klasifikasi Segmen'
    _rec_name = 'nama_segmen'

    id_segmen = fields.Char(string='ID Segmen', required=True, copy=False, readonly=True, default=lambda self: 'Baru')
    nama_segmen = fields.Char(string='Nama Segmen')
    kriteria = fields.Text(string='Kriteria')
    terdaftar_ids = fields.One2many('pipinos.terdaftar', 'segmen_id', string='Data Pendaftaran')
    pengunjung_ids = fields.Many2many('pipinos.pengunjung', string='pengunjung Terdaftar', compute='_compute_pengunjung_ids')

    @api.depends('terdaftar_ids.pengunjung_id')
    def _compute_pengunjung_ids(self):
        for rec in self:
            rec.pengunjung_ids = rec.terdaftar_ids.mapped('pengunjung_id')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('id_segmen', 'Baru') == 'Baru':
                vals['id_segmen'] = self.env['ir.sequence'].next_by_code('pipinos.segmen') or 'Baru'
        return super().create(vals_list)


class Terdaftar(models.Model):
    _name = 'pipinos.terdaftar'
    _description = 'pengunjung Terdaftar pada Segmen'

    pengunjung_id = fields.Many2one('pipinos.pengunjung', string='pengunjung', required=True, ondelete='cascade')
    segmen_id = fields.Many2one('pipinos.segmen', string='Segmen', required=True, ondelete='cascade')
    daftar_sejak = fields.Date(string='Terdaftar Sejak', default=fields.Date.context_today)

    _sql_constraints = [
        ('unique_pengunjung_segmen', 'unique(pengunjung_id, segmen_id)', 'pengunjung ini sudah terdaftar pada segmen tersebut!')
    ]


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