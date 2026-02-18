from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    x_group_code = fields.Char(string='Group Code')
