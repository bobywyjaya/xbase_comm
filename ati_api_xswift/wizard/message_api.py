# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo import api, models
from odoo.exceptions import UserError


class MessageApiWizard(models.TransientModel):
    _name = 'message.api.wizard'


    message = fields.Text('Message', required=True)

    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}