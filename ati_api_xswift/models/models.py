# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, time, timedelta
import base64
import json
import requests
from requests.auth import HTTPBasicAuth
import logging
from odoo import http
from odoo.http import request

# logging.warning("waring")
_logger = logging.getLogger(__name__)

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r

class AtiApiXswift(models.Model):
    _inherit = 'request.request'
    
    x_is_post = fields.Boolean('Is Post?', default=False)
    x_is_xswift = fields.Boolean('IS Xswift?', default=False)
    x_current_stage = fields.Char('Current Stage', default="assigned")
    x_hours_gmt = fields.Integer(string="GMT", default=7)
    x_date_closed_result = fields.Char(string='Result of Date Closed', copy=False, compute="_onchange_convert_date")
    x_xswift_submit_time = fields.Datetime('XSWIFT Submit Date', default=datetime.now())
    x_current_date_time = fields.Datetime('Current Date', default=datetime.now())
    x_onhold_note = fields.Text('On-Hold Note')
    x_xswift_attachment = fields.Char("Attachment")
    sync_error_message = fields.Text('Error Message')
    x_response_status = fields.Char('Response Status')
    
    @api.depends('date_closed','x_hours_gmt')
    def _onchange_convert_date(self):
        for rec in self:
            if rec.date_closed:
                gmt_date_closed = rec.date_closed + relativedelta(hours=rec.x_hours_gmt)
                year = datetime.strptime(str(gmt_date_closed), "%Y-%m-%d %H:%M:%S").strftime("%Y")
                month = datetime.strptime(str(gmt_date_closed), "%Y-%m-%d %H:%M:%S").strftime("%m")
                day = datetime.strptime(str(gmt_date_closed), "%Y-%m-%d %H:%M:%S").strftime("%d")
                hour = datetime.strptime(str(gmt_date_closed), "%Y-%m-%d %H:%M:%S").strftime("%H")
                minute = datetime.strptime(str(gmt_date_closed), "%Y-%m-%d %H:%M:%S").strftime("%M")
                second_a = datetime.strptime(str(gmt_date_closed), "%Y-%m-%d %H:%M:%S").strftime("%S")
                second = second_a[:2]
                rec.x_date_closed_result = year+"-"+month+"-"+day+"T"+hour+":"+minute+":"+second+"Z"
            else:
                # now = datetime.now() + relativedelta(hours=7)
                gmt_date_now = datetime.now() + relativedelta(hours=7)
                # date = datetime.strptime(gmt_date_now, "%Y-%m-%d %H:%M:%S.%f")
                # year = str(date.year)
                # month = str(date.month)
                # day = str(date.day)
                # hour = str(date.hour)
                # minute = str(date.minute)
                # second = str(date.second) 
                # rec.x_date_closed_result = year+"-"+month+"-"+day+"T"+hour+":"+minute+":"+second+"Z"
                year_now = datetime.strptime(str(gmt_date_now), "%Y-%m-%d %H:%M:%S.%f").strftime("%Y")
                month_now = datetime.strptime(str(gmt_date_now), "%Y-%m-%d %H:%M:%S.%f").strftime("%m")
                day_now = datetime.strptime(str(gmt_date_now), "%Y-%m-%d %H:%M:%S.%f").strftime("%d")
                hour_now = datetime.strptime(str(gmt_date_now), "%Y-%m-%d %H:%M:%S.%f").strftime("%H")
                minute_now = datetime.strptime(str(gmt_date_now), "%Y-%m-%d %H:%M:%S.%f").strftime("%M")
                second_a_now = datetime.strptime(str(gmt_date_now), "%Y-%m-%d %H:%M:%S.%f").strftime("%S.%f")
                second_now = second_a_now[:2]
                rec.x_date_closed_result = year_now+"-"+month_now+"-"+day_now+"T"+hour_now+":"+minute_now+":"+second_now+"Z"
    
    @api.model
    def cron_update_is_post(self):
        tickets = self.env['request.request'].search([('x_is_post', '=', False)])
        for rec in tickets:
            rec.x_is_post = True

    # def _get_duration(self, now, created_time):
    #     if not created_time or not now:
    #         return 0
    #     actual = now - created_time
    #     return actual.minutes

    def test_ping(self):
        core_url = self.env['ir.config_parameter'].sudo().get_param('api_url_key')
        password = self.env['ir.config_parameter'].sudo().get_param('api_password')
        headers = {"Content-type": "application/json"}
        data = {'id': 1}
        try:
            send_data = None
            if password:
                send_data = requests.post(core_url, auth=BearerAuth(str(password)), data=json.dumps(data), headers=headers)
            else:
                send_data = requests.post(core_url, data=json.dumps(data), headers=headers)
            rec = send_data.json()
            print("Result=======", rec)
            if rec['responses'] == 200:
                message_id = self.env['message.api.wizard'].create({'message': _("SUCCESS.")})
                return {
                    'name': _('Successfull'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'message.api.wizard',
                    'res_id': message_id.id,
                    'target': 'new'
                }
        
            if rec['responses'] != 200:
                message_id = self.env['message.api.wizard'].create({'message': _("FAILED!")})
                return {
                    'name': _('Unsuccessful'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'message.api.wizard',
                    'res_id': message_id.id,
                    'target': 'new'
                }
        except Exception as exc:
            message_id = self.env['message.api.wizard'].create({'message': _(exc)})
            return {
                'name': _('Exc'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'message.api.wizard',
                'res_id': message_id.id,
                'target': 'new'
            }
        

    def sync_to_xswift(self):
        for recs in self:
            core_url = self.env['ir.config_parameter'].sudo().get_param('api_url_key')
            password = self.env['ir.config_parameter'].sudo().get_param('api_password')
            date_assign = recs.date_assigned + relativedelta(hours=7)
            try:
                date_a = datetime.strptime(str(date_assign), "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d")
                time_a = datetime.strptime(str(date_assign), "%Y-%m-%d %H:%M:%S.%f").strftime("%H:%M:%S")
            except:
                date_a = datetime.strptime(str(date_assign), "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                time_a = datetime.strptime(str(date_assign), "%Y-%m-%d %H:%M:%S").strftime("%H:%M:%S")
        
            assign_time = date_a+"T"+time_a+"Z"
            headers = {"Content-type": "application/json",
                       "User-Agent" : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"}
            
            orf_number = recs.orf_number
            if orf_number[:4] == "ORF-":
                split_orf_number = orf_number[4:]
            else:
                split_orf_number = orf_number
            ticket_data = {
                "ticket_id": recs.id,
                "ticket_number": recs.name or "",
                "stage_id": recs.stage_id.code or "",
                "stage_date": recs.x_date_closed_result,
                "cancel_reason": recs.response_text or "",
                "onhold_reason": recs.x_onhold_note or "",
                "assign_date": assign_time,
                "technician_id": recs.user_id.id,
                "technician_name": recs.user_id.name or "",
                "technician_email": recs.user_id.login or "",
                "request_number": split_orf_number or "",
            }
            print("Ticket Data===", ticket_data)
            # Sync to odoo Core
            # try:
            try:
                # send_data = None
                if password:
                    send_data = requests.post(core_url, auth=BearerAuth(str(password)), data=json.dumps(ticket_data), headers=headers)
                else:
                    send_data = requests.post(core_url, data=json.dumps(ticket_data), headers=headers)
                print("Send Data===", send_data)
                
                rec = send_data.json()
                print("Result=======", rec)
                data_return = json.dumps(rec)
                print("Send Data====", send_data)
                if send_data.json().get("responses") == 200:
                    # if rec['responses'] == 200:
                    name = recs.name
                    response_id = rec['responses']
                    ticket_id = rec['ticket_id']
                    status = rec['status']
                    remark = rec['remark']
                    stage_name = recs.stage_id.code
                    stage_date = recs.x_date_closed_result
                    data_response = data_return
                    data_request = json.dumps(ticket_data)
                    recs._create_log_api(name,response_id,ticket_id,status,remark,stage_name,stage_date,data_response,data_request)
                    recs.x_is_post == True

                else:
                    name = recs.name
                    response_id = rec['responses']
                    ticket_id = rec['ticket_id']
                    status = rec['status']
                    remark = rec['remark']
                    stage_name = recs.stage_id.code
                    stage_date = recs.x_date_closed_result
                    data_response = data_return
                    data_request = json.dumps(ticket_data)
                    recs._create_log_api(name,response_id,recs.id,status,remark,stage_name,stage_date,data_response,data_request)
                                
                # else:
                #     self._create_log_api(recs.name, "500",recs.id,"Failed","Failed",recs.stage_id.code,recs.x_date_closed_result,send_data.json().get("remark"),ticket_data)
            except Exception as exc:
                recs._create_log_api(recs.name,"400",recs.id,"Failed","Failed",recs.stage_id.code,recs.x_date_closed_result,exc,ticket_data)


    def write(self, values):
        record = super(AtiApiXswift, self).write(values)
        for recs in self:
            if recs.x_is_xswift == True and recs.type_id.id == 2 and recs.stage_id.code not in ('new-request', 'assigned'):
                recs.sync_to_xswift()
                # core_url = self.env['ir.config_parameter'].sudo().get_param('api_url_key')
                # password = self.env['ir.config_parameter'].sudo().get_param('api_password')
                # date_assign = recs.date_assigned + relativedelta(hours=7)
                # try:
                #     date_a = datetime.strptime(str(date_assign), "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d")
                #     time_a = datetime.strptime(str(date_assign), "%Y-%m-%d %H:%M:%S.%f").strftime("%H:%M:%S")
                # except:
                #     date_a = datetime.strptime(str(date_assign), "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                #     time_a = datetime.strptime(str(date_assign), "%Y-%m-%d %H:%M:%S").strftime("%H:%M:%S")
            
                # assign_time = date_a+"T"+time_a+"Z"
                # headers = {"Content-type": "application/json",
                #            "User-Agent" : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"}
                
                # orf_number = recs.orf_number
                # if orf_number[:4] == "ORF-":
                #     split_orf_number = orf_number[4:]
                # else:
                #     split_orf_number = orf_number
                # ticket_data = {
                #     "ticket_id": recs.id,
                #     "ticket_number": recs.name or "",
                #     "stage_id": recs.stage_id.code or "",
                #     "stage_date": recs.x_date_closed_result,
                #     "cancel_reason": recs.response_text or "",
                #     "onhold_reason": recs.x_onhold_note or "",
                #     "assign_date": assign_time,
                #     "technician_id": recs.user_id.id,
                #     "technician_name": recs.user_id.name or "",
                #     "technician_email": recs.user_id.login or "",
                #     "request_number": split_orf_number or "",
                # }
                # # Sync to odoo Core
                # try:
                #     try:
                #         if password:
                #             send_data = requests.post(core_url, auth=BearerAuth(str(password)), data=json.dumps(ticket_data), headers=headers)
                #         else:
                #             send_data = requests.post(core_url, data=json.dumps(ticket_data), headers=headers)

                #         print("Send Data====", send_data)
                #         rec = send_data.json()
                #         print("Result=======", rec)
                #         data_return = json.dumps(rec)
                #         if rec['responses'] == 200:
                #             name = recs.name
                #             response_id = rec['responses']
                #             ticket_id = rec['ticket_id']
                #             status = rec['status']
                #             remark = rec['remark']
                #             stage_name = recs.stage_id.code
                #             stage_date = recs.x_date_closed_result
                #             data_response = data_return
                #             data_request = json.dumps(ticket_data)
                #             recs._create_log_api(name,response_id,ticket_id,status,remark,stage_name,stage_date,data_response,data_request)
                #             recs.x_is_post == True

                #         if rec['responses'] != 200:
                #             name = recs.name
                #             response_id = rec['responses']
                #             ticket_id = rec['ticket_id']
                #             status = rec['status']
                #             remark = rec['remark']
                #             stage_name = recs.stage_id.code
                #             stage_date = recs.x_date_closed_result
                #             data_response = data_return
                #             data_request = json.dumps(ticket_data)
                #             recs._create_log_api(name,response_id,ticket_id,status,remark,stage_name,stage_date,data_response,data_request)
                    
                #     except Exception as exc:
                #         recs._create_log_api(recs.name,"400",recs.id,"Failed","Failed",recs.stage_id.code,recs.x_date_closed_result,exc,ticket_data)
                # except Exception as exc:
                #     recs.sync_error_message = exc
                #     message_id = self.env['message.api.wizard'].create({'message': _("Server is not responding, please try again")})
                #     return {
                #         'name': _('Unsuccessful'),
                #         'type': 'ir.actions.act_window',
                #         'view_mode': 'form',
                #         'res_model': 'message.api.wizard',
                #         'res_id': message_id.id,
                #         'target': 'new'
                #     }
        return record
    
    def post_data(self):
        if self.x_current_stage != self.stage_id.code:
            self.x_current_stage = self.stage_id.code
            self.x_current_date_time = fields.datetime.now()
            core_url = self.env['ir.config_parameter'].sudo().get_param('api_url_key')
            # if self.stage_id.name > masih perlu ada modifikasi
            date_assign = self.date_assigned + relativedelta(hours=7)
            try:
                date_a = datetime.strptime(str(date_assign), "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d")
                time_a = datetime.strptime(str(date_assign), "%Y-%m-%d %H:%M:%S.%f").strftime("%H:%M:%S")
            except:
                date_a = datetime.strptime(str(date_assign), "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                time_a = datetime.strptime(str(date_assign), "%Y-%m-%d %H:%M:%S").strftime("%H:%M:%S")
            
            assign_time = date_a+"T"+time_a+"Z"
            headers = {'Content-type': 'application/json'}
            ticket_data = {
                    "ticket_id": self.id,
                    "ticket_number": self.name or "",
                    "stage_id": self.stage_id.code or "",
                    "stage_date": self.x_date_closed_result,
                    "cancel_reason": self.response_text or "",
                    "onhold_reason": self.x_onhold_note or "",
                    "assign_date": assign_time,
                    "technician_id": self.user_id.id,
                    "technician_name": self.user_id.name or "",
                    "technician_email": self.user_id.login or "",
                }
            # Sync to odoo Core
            send_data = requests.post(core_url, data=json.dumps(ticket_data), headers=headers)
            print("Send Data====", send_data)
            rec = send_data.json()
            print("Result=======", rec)
            if rec['responses'] == 200:
                name = self.name
                response_id = rec['responses']
                ticket_id = rec['ticket_id']
                status = rec['status']
                remark = rec['remark']
                stage_name = self.stage_id.code
                stage_date = self.x_date_closed_result
                self._create_log_api(name,response_id,ticket_id,status,remark,stage_name,stage_date)
                self.x_is_post = True
                message_id = self.env['message.api.wizard'].create({'message': _("Post to XSWIFT SUCCESS.")})
                return {
                    'name': _('Successfull'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'message.api.wizard',
                    'res_id': message_id.id,
                    'target': 'new'
                }
        
            if rec['responses'] != 200:
                name = self.name
                response_id = rec['responses']
                ticket_id = rec['ticket_id']
                status = rec['status']
                remark = rec['remark']
                stage_name = self.stage_id.code
                stage_date = self.x_date_closed_result
                self._create_log_api(name,response_id,ticket_id,status,remark,stage_name,stage_date)
                message_id = self.env['message.api.wizard'].create({'message': _("Post to XSWIFT FAILED!")})
                return {
                    'name': _('Unsuccessful'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'message.api.wizard',
                    'res_id': message_id.id,
                    'target': 'new'
                }

    @api.model
    def cron_post_data(self):
        tickets = self.env['request.request'].search([('x_is_xswift', '=', True)])
        for res in tickets:
            if res.x_current_stage != res.stage_id.code:
                res.x_current_stage = res.stage_id.code
                core_url = self.env['ir.config_parameter'].sudo().get_param('api_url_key')
                headers = {'Content-type': 'application/json'}
                ticket_data = {
                        "ticket_id": res.id,
                        "ticket_number": res.name,
                        "stage_id": res.stage_id.code,
                        "stage_date": res.x_date_closed_result,
                    }
                # Sync to odoo Core
                send_data = requests.post(core_url, data=json.dumps(ticket_data), headers=headers)
                print("Send Data====", send_data)
                rec = send_data.json()
                print("Result=======", rec)
                if rec['responses'] == 200:
                    name = res.name
                    response_id = rec['responses']
                    ticket_id = rec['ticket_id']
                    status = rec['status']
                    remark = rec['remark']
                    stage_name = res.stage_id.code
                    stage_date = res.x_date_closed_result
                    self._create_log_api(name,response_id,ticket_id,status,remark,stage_name,stage_date)
                    res.x_is_post == True
                    message_id = self.env['message.api.wizard'].create({'message': _("Post to XSWIFT SUCCESS.")})
            
                if rec['responses'] != 200:
                    name = res.name
                    response_id = rec['responses']
                    ticket_id = rec['ticket_id']
                    status = rec['status']
                    remark = rec['remark']
                    stage_name = res.stage_id.code
                    stage_date = res.x_date_closed_result
                    self._create_log_api(name,response_id,ticket_id,status,remark,stage_name,stage_date)
                    message_id = self.env['message.api.wizard'].create({'message': _("Post to XSWIFT FAILED!")})
                
    def _create_log_api(self, name, response_id, ticket_id, status, remark, stage_name, stage_date, data_response, data_request):
        log_api = self.env['log.api']
        # error_message = exc if exc else ""
        values = {
            'name': name,
            'xswift_response_id': response_id,
            'xswift_ticket_id': ticket_id,
            'xswift_status': status,
            'xswift_remark': remark,
            'xswift_stage_id': stage_name,
            'xswift_stage_date': stage_date,
            'xswift_response': data_response,
            'xswift_request': data_request,
            # 'xswift_message': error_message
        }
        log_api.create(values)

class AtiApiXswiftSaleOrder(models.Model):
    _inherit = 'sale.order'

    x_is_post = fields.Boolean('Is Post to Xswift?', default=False)
    x_is_xswift = fields.Boolean('IS Xswift?', default=False)
    x_xswift_ticket = fields.Char('XSwift Ticket')
    x_xswift_date = fields.Date('XSwift Date')
    x_total_period = fields.Integer('Period(month)')

class AtiApiXswiftSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_xswift_ticket = fields.Char('XSwift Ticket')
    x_xswift_date   = fields.Date('XSwift Date')
    x_start_period  = fields.Date('Start Period')
    x_total_period  = fields.Integer('Total Period')

class AtiApiXswiftProductCategory(models.Model):
    _inherit = 'product.category'

    x_connect_to_xswift = fields.Boolean('Connect to XSWIFT', default=False, help="Check this field, if this category need to be apply on XSWIFT")