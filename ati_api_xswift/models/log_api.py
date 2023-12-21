# -*- coding: utf-8 -*-

from odoo import models, fields, api

class LogAPI(models.Model):
    _name = 'log.api'
    _order = "create_date DESC"

    sequence = fields.Integer()
    name = fields.Char(string='Name')
    xswift_response_id = fields.Char(string='Response ID')
    xswift_ticket_id = fields.Char(string='Ticket ID')
    xswift_stage_id = fields.Char(string='Stage')
    xswift_stage_date = fields.Char(string='Stage Date')
    xswift_status = fields.Char(string='Status')
    xswift_remark = fields.Char(string='Remark')
    xswift_request = fields.Text(string="Request JSON")
    xswift_response = fields.Text(string="Response JSON")
    xswift_message = fields.Text(string="Error Message")
