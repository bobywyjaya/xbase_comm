# -*- coding: utf-8 -*-
import json
import logging
import requests
import datetime

from odoo import api, fields, models
from odoo import http, _, exceptions
from odoo.tests import Form
from odoo.http import request
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
import logging
import werkzeug.wrappers
import base64

logging.warning("waring")

_logger = logging.getLogger(__name__)

class ati_api_xsift(http.Controller):
    @http.route('/get_sales_order', type='json', auth='user', method='GET')
    def get_sales_order(self, **kwargs):
        sales_id = request.env['sale.order'].search([])
        orders_line = request.env['sale.order.line'].search([])
        sale = []
        data = []
        for rec in sales_id:
            order_line = []
            for line in rec.order_line:
                if line.product_id.list_price > 1 and line.product_id.categ_id.x_connect_to_xswift == True:
                    tax_ids = []
                    tax_name = []
                    for tax in line.tax_id:
                        account_tax_obj = request.env['account.tax'].sudo().search([
                            ('id', '=', tax.id)
                        ], limit=1)
                        if account_tax_obj:
                            tax_ids.append(account_tax_obj.id)
                            tax_name.append(account_tax_obj.name)

                    valss = {
                        'id': line.id or False,
                        'product_id': line.product_id.id or False,
                        'product_name': line.product_id.name or "",
                        'product_code': line.product_id.default_code or "",
                        'description': line.name or "",
                        'project_id': line.project_id.id or False,
                        'project_name': line.project_id.name or "",
                        'quantity': line.product_uom_qty or "",
                        'uom_id': line.product_uom.id or False,
                        'uom_name': line.product_uom.name or "",
                        'price_unit': line.price_unit or "",
                        'tax_id': tax_ids or False,
                        'tax_name': tax_name or "",
                        'discount': line.discount or "",
                        'price_subtotal': line.price_subtotal or "",
                    }
                    order_line.append(valss)
            
            if order_line:
                if rec.validity_date and rec.date_order:
                    vals = {
                        'id': rec.id or False,
                        'name': rec.name or "",
                        'customer_id': rec.partner_id.id or False,
                        'customer_name': rec.partner_id.name or "",
                        'invoice_address_id': rec.partner_invoice_id.id or False,
                        'invoice_address_name': rec.partner_invoice_id.name or "",
                        'delivery_address_id': rec.partner_shipping_id.id or False,
                        'delivery_address_name': rec.partner_shipping_id.name or "",
                        'expiration_date': rec.validity_date or False,
                        'quotation_date': rec.date_order or False,
                        'pricelist_id': rec.pricelist_id.id or False,
                        'pricelist_name': rec.pricelist_id.name or "",
                        'payment_terms_id': rec.payment_term_id.id or False,
                        'payment_terms_name': rec.payment_term_id.name or "",
                        'client_attn': rec.x_attention or "",
                        'sales_person_id': rec.user_id.id or False,
                        'sales_person_name': rec.user_id.name or "",
                        'sales_team_id': rec.team_id.id or False,
                        'sales_team_name': rec.team_id.name or "",
                        'note': rec.note or "",
                        'order_line': order_line
                    }
                sale.append(vals)

        data = {'status': 200, 'response': sale, 'message': 'Done All Sale Order Returned'}
        return data

    @http.route('/get_customer_master', type='json', auth='user', method='GET')
    def get_customer_master(self):
        obj_customer = request.env['res.partner'].search([('active','=', True)])
        customers_data = []
        for rec in obj_customer:
            vals = {
                'customer_id': rec.id,
                'customer_name': rec.name or "",
                'customer_type': rec.company_type,
                'customer_business_unit': rec.is_xapiens_business_unit,
                'customer_code': rec.bu_code or "",
                'customer_phone': rec.phone or "",
                'customer_mobile': rec.mobile or "",
                'customer_email': rec.email or "",
                'active': rec.active or False,
            }
            customers_data.append(vals)
        data = {'status': 200, 'response': customers_data, 'message': 'Done. All Customers Returned'}
        return data

    @http.route('/get_pricelist_master', type='json', auth='user', method='GET')
    def get_pricelist_master(self):
        obj_pricelist = request.env['product.pricelist'].search([('active','=', True)])
        pricelist_data = []
        for rec in obj_pricelist:
            vals = {
                'pricelist_id': rec.id,
                'pricelist_name': rec.name or "",
                'pricelist_currency_id': rec.currency_id.id or False,
                'pricelist_currency_name': rec.currency_id.name or "",
                'active': rec.active or False,
            }
            pricelist_data.append(vals)
        data = {'status': 200, 'response': pricelist_data, 'message': 'Done. All Pricelists Returned'}
        return data
    
    @http.route('/get_taxes_master', type='json', auth='user', method='GET')
    def get_taxes_master(self):
        obj_taxes = request.env['account.tax'].search([('active','=', True)])
        taxes_data = []
        for rec in obj_taxes:
            vals = {
                'taxes_id': rec.id,
                'taxes_name': rec.name or "",
                'amount_type': rec.amount_type or "",
                'type_tax_use': rec.type_tax_use or "",
                'amount': rec.amount or 0.0,
                'active': rec.active or False,
            }
            taxes_data.append(vals)
        data = {'status': 200, 'response': taxes_data, 'message': 'Done. All Taxes Returned'}
        return data

    @http.route('/get_product_master', type='json', auth='user', method='GET')
    def get_product_master(self):
        obj_product = request.env['product.template'].search([('active','=', True), ('list_price','>', 1), ('categ_id.x_connect_to_xswift','=', True)])
        product_data = []
        for rec in obj_product:
            vals = {
                'product_id': rec.id,
                'product_name': rec.name or "",
                'product_can_sold': rec.sale_ok,
                'product_can_purchase': rec.purchase_ok,
                'product_type': rec.type,
                'product_internal_ref': rec.default_code or "",
                'product_categ_id': rec.categ_id.id or False,
                'product_categ_name': rec.categ_id.name or "",
                'product_sales_price': int(rec.list_price) or "",
                'product_uom_id': rec.uom_id.id,
                'product_uom_name': rec.uom_id.name,
                'product_invoice_policy': rec.service_policy,
                'product_service_tracking': rec.service_tracking,
                'product_project_id': rec.project_id.id or False,
                'product_project_name': rec.project_id.name or "",
                'product_re-invoice_expense': rec.expense_policy,
                'active': rec.active or False,
            }
            product_data.append(vals)
        data = {'status': 200, 'response': product_data, 'message': 'Done. All Products Returned'}
        return data

    # @http.route(['/api/get-project-master/'], type='http', auth='public', methods=['GET'], csrf=False)
    # def get_projects_master(self, **params):
    #     get_name = params.get('name')
    #     project_project_obj = request.env['project.project'].sudo().search([('name', 'ilike', get_name)])
    #     project_data = []
    #     for rec in project_project_obj:
    #         vals = {
    #                 'project_id': rec.id,
    #                 'project_no': rec.project_no or "",
    #                 'project_name': rec.name or "",
    #                 'project_name_tasks': rec.label_tasks or "",
    #                 'project_manager_id': rec.user_id.id or False,
    #                 'project_manager_name': rec.user_id.name or "",
    #                 'project_customer_id': rec.partner_id.id or False,
    #                 'project_customer_name': rec.partner_id.name or "",
    #                 'active': rec.active or False,
    #                 }

    #         project_data.append(vals)
    #     data = {
    #         'status': 200,
    #         'message': 'success',
    #         'response': project_data
    #     }
    #     try:
    #         return werkzeug.wrappers.Response(
    #             status=200,
    #             content_type='application/json; charset=utf-8',
    #             response=json.dumps(data)
    #         )
    #     except:
    #         return werkzeug.wrappers.Response(
    #             status=400,
    #             content_type='application/json; charset=utf-8',
    #             headers=[('Access-Control-Allow-Origin', '*')],
    #             response=json.dumps({
    #                 'error': 'Error',
    #                 'error_descrip': 'Error Description',
    #             })
    #         )
    
    @http.route(['/get_project_master'], type='json', auth='user', methods=['GET'])
    def get_project_master(self, **recs):
        if recs.get("name"):
            get_name = recs.get("name")
            obj_project = request.env['project.project'].sudo().search([('name','ilike', get_name), ('active','=', True)])
        else:
            obj_project = request.env['project.project'].sudo().search([('active','=', True)])
        project_data = []
        for rec in obj_project:
            vals = {
                'project_id': rec.id,
                'project_no': rec.project_no or "",
                'project_name': rec.name or "",
                'project_name_tasks': rec.label_tasks or "",
                'project_manager_id': rec.user_id.id or False,
                'project_manager_name': rec.user_id.name or "",
                'project_customer_id': rec.partner_id.id or False,
                'project_customer_name': rec.partner_id.name or "",
                'active': rec.active or False,
            }
            project_data.append(vals)
        data = {'status': 200, 'response': project_data, 'message': 'Done. All Projects Returned'}
        return data

    @http.route('/get_service_master', type='json', auth='user', method='GET')
    def get_data_master(self):
        obj_service = request.env['generic.service'].search([('active','=', True)])
        service_data = []
        for rec in obj_service:
            for categ in rec.category_ids:
                vals = {
                    'service_id': rec.id,
                    'service_name': rec.name,
                    'service_category_id': categ.id,
                    'service_category_name': categ.name,
                    'service_type_id': categ.parent_id.id,
                    'service_type_name': categ.parent_id.name,
                    'create_date': rec.create_date,
                    'active': rec.active or False,
                }
                service_data.append(vals)
        data = {'status': 200, 'response': service_data, 'message': 'Done All User Returned'}
        print("New Data User Is", service_data)
        return data

    @http.route('/terminate_sales_order', type='json', auth='user', method='POST')
    def terminate_sales_order(self, **rec):
        rec_sales = http.request.env['sale.order'].sudo()
        sales_order = rec['sales_order']
        sales_orders = []
        for so in sales_order:
            sales = rec_sales.search([('id','=', so['id']), ('name','=', so['number'])])
            print("Sales", sales)
            if sales and sales.state != 'sent':
                message = _('Forbidden Cancel, Status for SO [%s] is [%s], to Cancel SO Status must be [Quotation Sent]' %(so['number'] or '-', sales.state or '-'))
                return {'responses': 404, 'sales_order': so['number'], 'status': 'Forbidden', 'remark': message}
            elif sales and sales.state == 'sent':
                sale_id = sales
                print("sale_id", sale_id)
            else:
                message = _('Sale Order Not Found')
                return {'responses': 404, 'sales_order': so['number'], 'status': 'Not Found', 'remark': message}

            if sales:
                cancel = sale_id.action_cancel()
                for s in sales:
                    so_vals = {
                        'id': s.id,
                        'number': s.name,
                        'state': s.state
                    }
                    sales_orders.append(so_vals)
                args = {'responses': 200, 
                        'sales_order': sales_orders,
                        'status': 'Successfully Cancel Sale Order', 
                        'Remark': 'Cancelled'}
            else:
                args = {'responses': 404,  
                        'sales_order': so['number'],
                        'status': 'Failed', 
                        'Remark': 'Sale Order Number Not Found'}
        return args

    @http.route('/update_sales_order', type='json', auth='user', method='POST')
    def update_sales_order(self, **rec):
        rec_sales = http.request.env['sale.order'].sudo()
        rec_pricelist = http.request.env['product.pricelist'].sudo()

        sales = rec_sales.search([('id','=', rec['id']), ('name','=', rec['number'])])
        if sales and sales.state != 'sent':
            message = _('Forbidden Update, Status for SO [%s] is [%s], to update SO Status must be [Quotation Sent]' %(rec['number'] or '-', sales.state or '-'))
            return {'responses': 404, 'sales_order': rec['number'], 'status': 'Forbidden', 'remark': message}
        elif sales and sales.state == 'sent':
            sale_id = sales.id
        else:
            message = _('Sale Order Not Found')
            return {'responses': 404, 'sales_order': rec['number'] , 'status': 'Not Found', 'remark': message}
        
        # update_pricelist_product = http.request.env['ir.config_parameter'].sudo().get_param('update_pricelist_product') if self.env['ir.config_parameter'].sudo().get_param('update_pricelist_product') else 0
        # i_update_pricelist_product = int(update_pricelist_product)
        # print("RUN========",i_update_pricelist_product)
        # if i_update_pricelist_product > 0:
        #     print("RUN========")
        #     if rec['pricelist_name']:
        #         pricelist_id = False
        #         search_pricelist_id = rec_pricelist.search([('name', '=', rec['pricelist_name'])], limit=1)
        #         if search_pricelist_id:
        #             pricelist_id = search_pricelist_id.id
        #             sales.write({'pricelist_id': pricelist_id})
        #         else:
        #             message = _('Pricelist [%s] Not Found' %(rec['pricelist_name'] or '-'))
        #             return {'responses': 404, 'sales_order': rec['number'], 'status': 'Not Found', 'remark': message}


        print("rec", rec)
        sale_lines = rec['sale_line']
        print("aaaa", sale_lines)
        if sales:
            sales_order = []
            for order_line in sale_lines:
                print("bbbb", order_line)
                vals = []
                rec_order_line = http.request.env['sale.order.line'].sudo()
                filter_id = rec_order_line.search([('id','=', order_line['id'])])
                taxes_id = []
                if order_line['taxes']:
                    rec_taxes = http.request.env['account.tax'].sudo()
                    search_taxes_id = rec_taxes.search([('name', '=', order_line['taxes'])], limit=1)
                    if search_taxes_id:
                        taxes_id.append(search_taxes_id.id)
                    else:
                        message = _('Taxes [%s] Not Found' %(order_line['taxes'] or '-'))
                        return {'responses': 404, 'sales_order': rec['number'], 'status': 'Not Found', 'remark': message}
                else:
                    taxes_id = False

                if filter_id:
                    for line in filter_id:
                        # if i_update_pricelist_product > 0:
                        #     product_categ_id = False
                        #     rec_product_categ = http.request.env['product.category'].sudo()
                        #     search_product_categ_id = rec_product_categ.search([('name', '=', sales.pricelist_id.name)], limit=1)
                        #     if search_product_categ_id:
                        #         product_categ_id = search_product_categ_id
                        #     else:
                        #         message = _('This Product Category [%s] Not Found' %(search_product_categ_id.name or '-'))
                        #         return {'responses': 404, 'sales_order': rec['number'], 'status': 'Not Found', 'remark': message}
                        
                        #     rec_product = http.request.env['product.product'].sudo()
                        #     rec_template = http.request.env['product.template'].sudo()
                        #     search_product_tmpl_id = rec_template.search([('name', '=', order_line['product_name']), ('categ_id', '=', product_categ_id.id)],limit=1)
                        #     if search_product_tmpl_id:
                        #         search_product_id = rec_product.search([('product_tmpl_id', '=', search_product_tmpl_id.id)],limit=1)
                        #         product_id = search_product_id
                        #     else:
                        #         message = _('This Product [%s] with Category [%s] Not Found' %(order_line['product_name'] or '-', sales.pricelist_id.name or '-'))
                        #         return {'responses': 404, 'sales_order': rec['number'], 'status': 'Not Found', 'remark': message}

                        #     rec_project = http.request.env['project.project'].sudo()
                        #     search_project_id = rec_project.search([('name', '=', order_line['project_name'])])
                        #     if search_project_id:
                        #         project_id = search_project_id.id
                        #     else:
                        #         message = _('This Project [%s] Not Found' %(order_line['project_name'] or '-'))
                        #         return {'responses': 404, 'sales_order': rec['number'], 'status': 'Not Found', 'remark': message}
                        
                        #     vals = {
                        #         'product_id': product_id.id,
                        #         'name': order_line['description']+ ".; Note: " + order_line['note'],
                        #         'project_id': project_id,
                        #         'product_uom_qty': order_line['quantity'],
                        #         'price_unit': order_line['price_unit'],
                        #         'tax_id': taxes_id or False,
                        #     }
                        #     line.write(vals)
                        # else:
                        rec_project = http.request.env['project.project'].sudo()
                        search_project_id = rec_project.search([('name', '=', order_line['project_name'])])
                        if search_project_id:
                            project_id = search_project_id.id
                        else:
                            message = _('This Project [%s] Not Found' %(order_line['project_name'] or '-'))
                            return {'responses': 404, 'sales_order': rec['number'], 'status': 'Not Found', 'remark': message}
                    
                        vals = {
                            'name': order_line['description']+ ".; Note: " + order_line['note'],
                            'project_id': project_id,
                            'product_uom_qty': order_line['quantity'],
                            'price_unit': order_line['price_unit'],
                            'tax_id': taxes_id or False,
                            'discount': order_line['discount'],
                        }
                        line.write(vals)
                else:
                    rec_project = http.request.env['project.project'].sudo()
                    search_project_id = rec_project.search([('name', '=', order_line['project_name'])])
                    if search_project_id:
                        project_id = search_project_id.id
                    else:
                        message = _('This Project [%s] Not Found' %(order_line['project_name'] or '-'))
                        return {'responses': 404, 'sales_order': rec['number'], 'status': 'Not Found', 'remark': message}

                    product_categ_id = False
                    rec_product_categ = http.request.env['product.category'].sudo()
                    search_product_categ_id = rec_product_categ.search([('name', '=', sales.pricelist_id.name)], limit=1)
                    if search_product_categ_id:
                        product_categ_id = search_product_categ_id
                    else:
                        message = _('This Product Category [%s] Not Found' %(search_product_categ_id.name or '-'))
                        return {'responses': 404, 'sales_order': rec['number'], 'status': 'Not Found', 'remark': message}

                    rec_new_product = http.request.env['product.product'].sudo()
                    rec_new_product_tmpl = http.request.env['product.template'].sudo()
                    search_new_product_tmpl_id = rec_new_product_tmpl.search([('name', '=', order_line['product_name']), ('categ_id', '=', product_categ_id.id)],limit=1)
                    if search_new_product_tmpl_id:
                        search_product_id = rec_new_product.search([('product_tmpl_id', '=', search_new_product_tmpl_id.id)],limit=1)
                        product_new_id = search_product_id
                    else:
                        message = _('This Product [%s] with Category [%s] Not Found' %(order_line['product_name'] or '-', sales.pricelist_id.name or '-'))
                        return {'responses': 404, 'sales_order': rec['number'], 'status': 'Not Found', 'remark': message}

                    val_order_line = {
                        'order_id': sales.id,
                        'product_id': product_new_id.id,
                        'name': order_line['description']+ ".; Note: " + order_line['note'],
                        'project_id': project_id,
                        'product_uom_qty': order_line['quantity'],
                        'product_uom': product_new_id.uom_id.id,
                        'price_unit': order_line['price_unit'],
                        'tax_id': taxes_id or False,
                        'discount': order_line['discount'],
                    }
                    new_line = rec_order_line.create(val_order_line)
                
            for s in sales:
                ed = datetime.strptime(str(s.effective_date), "%Y-%m-%d").strftime("%Y-%m-%d")
                sale_ids = []
                url = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                pdf_link = url+"/pdf/sale_order_quotation/%s" %(s.id)
                for sales_line in s.order_line:
                    if sales_line:
                        valss = {
                            'id': sales_line.id or 0,
                            'product': sales_line.product_id.name or "",
                            'description': sales_line.name or "",
                            'project': sales_line.project_id.name or "",
                            'quantity': int(sales_line.product_uom_qty),
                            'unit_of_measure': sales_line.product_uom.name or "",
                            'price_unit': sales_line.price_unit or 0,
                            'taxes': sales_line.tax_id.name or "",
                            'discount': sales_line.discount or 0,
                            'subtotal': sales_line.price_subtotal or 0
                            }
                        sale_ids.append(valss)
                if sale_ids:
                    so_vals = {
                        'id': s.id,
                        'number': s.name,
                        'periode': ed,
                        'link_download': pdf_link,
                        'sale_line': sale_ids
                    }
                    sales_order.append(so_vals)    
                else:
                    so_vals = {
                        'id': s.id,
                        'number': s.name,
                        'periode': ed,
                        'link_download': pdf_link,
                        'sale_line': sale_ids
                    }
                    sales_order.append(so_vals)   

            args = {'responses': 200, 
                    'sales_order': sales_order,
                    'status': 'Successfully Update Sale Order', 
                    'Remark': 'Done'}
        else:
            args = {'responses': 404,  
                    'sales_order': rec['number'],
                    'status': 'Failed', 
                    'Remark': 'Sale Order Number Not Found'}
        return args

    @http.route('/pdf/sale_order_quotation/<int:i_id>', type='http', auth='user')
    def sale_order_quotation_pdf(self, i_id, **post):
        #i_id = 882
        sale_order = request.env['sale.order'].browse([i_id])
        so_sudo = sale_order.sudo()

        pdf = request.env.ref('sale.action_report_saleorder').sudo().render_qweb_pdf([so_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)
    
    @http.route('/pdf/shipment_incoming_task/<int:i_id>', type='http', auth='user')
    def shipment_incoming_task_pdf(self, i_id, **post):
        #i_id = 882
        incoming_task_obj = request.env['ship.task'].browse([i_id])
        incoming_task_sudo = incoming_task_obj.sudo()

        pdf = request.env.ref('ati_ap_wj.doc_report_wj_list').sudo().render_qweb_pdf([incoming_task_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)
    
    @http.route('/create_sales_order', type='json', auth='user')
    def create_sales_order(self, **rec):
        rec_customer = http.request.env['res.partner'].sudo()
        rec_pricelist = http.request.env['product.pricelist'].sudo()
        rec_payment_term = http.request.env['account.payment.term'].sudo()
        rec_sale_order_line = http.request.env['sale.order.line'].sudo()
        rec_res_users = http.request.env['res.users'].sudo()

        search_customer_id = rec_customer.search([('name', '=', rec['customer_name'])], limit=1)
        if search_customer_id:
            customer_id = search_customer_id.id
        else:
            message = _('This Customer [%s] Not Found' %(search_customer_id.name or '-'))
            return {'responses': 404, 'sales_order': [], 'status': 'Not Found', 'remark': message}
        
        search_pricelist_id = rec_pricelist.search([('name', '=', rec['pricelist_name'])], limit=1)
        if search_pricelist_id:
            pricelist_id = search_pricelist_id.id
        else:
            # message = _('This Pricelist Not Found')
            # return {'responses': 404, 'status': 'Not Found', 'remark': message}
            pricelist_id = rec_pricelist.create({'name': rec['pricelist_name']}).id

        search_payment_term_id = rec_payment_term.search([('name', 'ilike', '30 days after invoice and supporting documents received correctly, paid on Thursdays')], limit=1)
        if search_payment_term_id:
            payment_term_id = search_payment_term_id.id
        else:
            message = _('This Payment Terms [%s] Not Found' %(search_payment_term_id.name or '-'))
            return {'responses': 404, 'sales_order': [], 'status': 'Not Found', 'remark': message}

        search_users_id = rec_res_users.search([('login', 'ilike', rec['salesperson'])], limit=1)
        if search_users_id:
            user_id = search_users_id.id
        else:
            message = _('This User [%s] Not Found' %(rec['salesperson'] or '-'))
            return {'responses': 404, 'status': 'User Not Found', 'remark': message}
                
        order_line = rec['order_line']
        periods = rec['total_period']
        sales_order = []
        month = 0
        orderdate = False
        sales_order = []
        for i in range(periods):
            if rec['customer_name']:
                vals = {
                    'partner_id': customer_id,
                    'partner_invoice_id': customer_id,
                    'partner_shipping_id': customer_id,
                    'pricelist_id': pricelist_id,
                    'payment_term_id': payment_term_id,
                    'x_attention': rec['client_attn'],
                    'client_order_ref': rec['xswift_ticket'],
                    'x_xswift_date': rec['xswift_date'],
                    'x_total_period': rec['total_period'],
                    'user_id': user_id,
                    'state': 'sent',
                    'x_is_xswift': True,
                    'note': rec['terms_conditions']
                }
            
                new_data = request.env['sale.order'].sudo().create(vals)
                if not orderdate:
                    orderdate = fields.Date.from_string(new_data.x_xswift_date)
                    print("Order DAte", orderdate, type(orderdate), type(new_data.x_xswift_date))
                
                a = orderdate + relativedelta(months=month)
                print("Date date_order", a, type(a))  
                b = orderdate + relativedelta(months=month)
                print("Date effective_date", b)  
                c = orderdate + relativedelta(months=month)
                print("Date commitment_date", c)  
                d = orderdate + relativedelta(months=month)
                print("Date validity_date", d)  
                month += 1
                print("Month", month)
                print("============================================")

                date_order = datetime.strptime(str(a), "%Y-%m-%d").strftime("%Y-%m-01")
                print("Date order", date_order, type(date_order))
                validity_date = datetime.strptime(str(d), "%Y-%m-%d").strftime("%Y-%m-28")
                print("Date validity", validity_date, type(validity_date))
                effective_date = datetime.strptime(str(b), "%Y-%m-%d").strftime("%Y-%m-01")
                print("Date effective", effective_date, type(effective_date))
                commitment_date = datetime.strptime(str(c), "%Y-%m-%d").strftime("%Y-%m-28")
                print("Date commitment", commitment_date, type(commitment_date))
                
                years = datetime.strptime(str(effective_date), "%Y-%m-%d").strftime("%Y")
                months = datetime.strptime(str(effective_date), "%Y-%m-%d").strftime("%m")
                year_month = years+"/"+months

                new_data.update({'x_xswift_ticket': rec['xswift_ticket']+"/"+year_month+"/"+new_data.name,
                                 'date_order': date_order,
                                 'validity_date': validity_date,
                                 'effective_date': effective_date,
                                 'commitment_date': commitment_date})
                print("New Data", new_data)
                for line in order_line:
                    rec_template = http.request.env['product.template'].sudo()
                    rec_product = http.request.env['product.product'].sudo()
                    rec_product_categ = http.request.env['product.category'].sudo()
                    search_product_categ_id = rec_product_categ.search([('name', '=', rec['pricelist_name'])], limit=1)
                    if search_product_categ_id:
                        product_categ_id = search_product_categ_id.id
                    else:
                        message = _('This Product Category [%s] Not Found' %(rec['pricelist_name'] or '-'))
                        return {'responses': 404, 'sales_order': [], 'status': 'Not Found', 'remark': message}
                    
                    search_product_tmpl_id = rec_template.search([('name', '=', line['product_name']), ('categ_id', '=', product_categ_id)],limit=1)
                    if search_product_tmpl_id:
                        search_product_id = rec_product.search([('product_tmpl_id', '=', search_product_tmpl_id.id)])
                        if search_product_id:
                            product_id = search_product_id
                    else:
                        vals_template = {
                                        'name': line['product_name'],
                                        'sale_ok': True,
                                        'purchase_ok': True,
                                        'type': 'service',
                                        'categ_id': product_categ_id,
                                        'uom_id': 147,
                                        'uom_po_id': 147,
                                        'service_policy': 'ordered_timesheet',
                                        'service_tracking': 'no',
                                        'expense_policy': 'no',
                                        }
                        product_tmpl_id = rec_template.create(vals_template)
                        product_id = rec_product.search([('product_tmpl_id', '=', product_tmpl_id.id)])
                        
                    rec_project = http.request.env['project.project'].sudo()
                    search_project_id = rec_project.search([('name', '=', line['project_name'])])
                    if search_project_id:
                        project_id = search_project_id.id
                    else:
                        message = _('This Project [%s] Not Found' %(line['project_name'] or '-'))
                        return {'responses': 404, 'sales_order': [], 'status': 'Not Found', 'remark': message}
                    
                    taxes_id = []
                    if line['taxes']:
                        rec_taxes = http.request.env['account.tax'].sudo()
                        search_taxes_id = rec_taxes.search([('name', '=', line['taxes'])], limit=1)
                        if search_taxes_id:
                            taxes_id.append(search_taxes_id.id)
                        else:
                            message = _('Taxes [%s] Not Found' %(line['taxes'] or '-'))
                            return {'responses': 404, 'sales_order': [], 'status': 'Not Found', 'remark': message}
                    else:
                        taxes_id = False
                    
                    period_dates = line['period_dates']
                    for period_dates_ in period_dates:
                        str_period_dates = period_dates_
                        dt_period_dates = datetime.strptime(str(str_period_dates), "%Y-%m-%d")
                        print("Period Date===", dt_period_dates, type(dt_period_dates))
                        print("Order Dates===", new_data.date_order, type(new_data.date_order))

                        if dt_period_dates == new_data.date_order:
                            val_order_line = {
                                'order_id': new_data.id,
                                'product_id': product_id.id,
                                'name': line['description']+ ".; Note: " + line['note'],
                                'project_id': project_id,
                                'product_uom_qty': line['quantity'],
                                'product_uom': product_id.uom_id.id,
                                'price_unit': line['price_unit'],
                                'tax_id': taxes_id or False,
                                'discount': line['discount'],
                            }
                            rec_sale_order_line.create(val_order_line)
                for s in new_data:
                    ed = datetime.strptime(str(s.effective_date), "%Y-%m-%d").strftime("%Y-%m-%d")
                    sale_ids = []
                    url = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    pdf_link = url+"/pdf/sale_order_quotation/%s" %(s.id)
                    for sales_line in s.order_line:
                        if sales_line:
                            valss = {
                                'id': sales_line.id or 0,
                                'product': sales_line.product_id.name or "",
                                'description': sales_line.name or "",
                                'project': sales_line.project_id.name or "",
                                'quantity': int(sales_line.product_uom_qty),
                                'unit_of_measure': sales_line.product_uom.name or "",
                                'price_unit': sales_line.price_unit or 0,
                                'taxes': sales_line.tax_id.name or "",
                                'discount': sales_line.discount or 0,
                                'subtotal': sales_line.price_subtotal or 0
                            }
                            sale_ids.append(valss)
                    if sale_ids:
                        so_vals = {
                            'id': s.id,
                            'number': s.name,
                            'periode': ed,
                            'salesperson': s.user_id.name,
                            'link_download': str(pdf_link),
                            'sale_line': sale_ids
                        }
                        sales_order.append(so_vals)
                    else:
                        so_vals = {
                            'id': s.id,
                            'number': s.name,
                            'periode': ed,
                            'salesperson': s.user_id.name,
                            'link_download': str(pdf_link),
                            'sale_line': sale_ids
                        }
                        sales_order.append(so_vals)
                args = {'responses': 200, 
                        'sales_order': sales_order, 
                        'status': 'Successfully Created to XBase', 
                        'remark': '-'}
            else:
                args = {'responses': 500, 
                        'sales_order': [], 
                        'status': 'Failed', 
                        'remark': 'Failed to Create Ticket'}
        return args

    @http.route('/complete_request', type='json', auth='user', method='POST')
    def complete_request(self, **rec):
        rec_ticket = http.request.env['request.request'].sudo()
        ticket = rec_ticket.search([('id','=', rec['id']), ('name','=', rec['name'])])
        if ticket:
            ticket_id = ticket
        else:
            message = _('Ticket Not Found')
            return {'responses': 404, 'ticket_name': 'Not Found', 'status': 'Not Found', 'remark': message}

        if ticket_id:
            vals = {'response_text': "Complete",
                    'stage_id': 8}
            
            ticket_id.update(vals)
            args = {'responses': 200, 
                    'ticket_name': ticket.name,
                    'status': 'Successfully Complete Ticket', 
                    'Remark': 'Completed'}
        else:
            args = {'responses': 404,  
                    'ticket_name': 'Not Found',
                    'status': 'Failed', 
                    'Remark': 'Ticket Number Not Found'}
        return args

    @http.route('/create_request', type='json', auth='user')
    def create_request(self, **rec):
        rec_contact = http.request.env['res.partner'].sudo() 
        rec_request_type = http.request.env['request.type'].sudo() 
        rec_request_category = http.request.env['request.category'].sudo() 
        rec_generic_service = http.request.env['generic.service'].sudo() 
        rec_generic_team = http.request.env['generic.team'].sudo() 
        rec_generic_team_member = http.request.env['generic.team.member'].sudo()
        rec_users = http.request.env['res.users'].sudo() 
        rec_partner = http.request.env['res.partner'].sudo() 
        rec_stage = http.request.env['request.stage'].sudo() 
        rec_company = http.request.env['res.partner'].sudo()

        author = rec['author_id']
        i = author.split(", ")
        company = i[0]
        user = i[1]
        # search_contact_id = rec_contact.search([('name', 'ilike', user),('parent_id.name', 'ilike', company)], limit=1)
        search_contact_name = rec_contact.search([('name', 'ilike', user)], limit=1)
        search_contact_company = rec_contact.search([('is_company', '=', True), ('name', 'ilike', company)], limit=1)
        
        # if not search_contact_id:
        #     message = _('Combination between Technician Name and Company Not Found in XBASE System, Please Check!')
        #     return {'responses': 404, 'status': 'Not Found', 'remark': message}
        # elif not search_contact_name:
        #     message = _('Author Name Not Found in XBASE System, Please Check!')
        #     return {'responses': 404, 'status': 'Not Found', 'remark': message}
        # elif not search_contact_company:
        #     message = _('Company Name Not Found in XBASE System, Please Check!')
        #     return {'responses': 404, 'status': 'Not Found', 'remark': message}
        # else:
        #     contact_id = search_contact_id.id
            
        search_contact_id = rec_contact.search([('name', '=ilike', user),('parent_id.name', '=ilike', company)], limit=1)
        if search_contact_id:
            if not search_contact_id.email or search_contact_id.email == "":
                search_contact_id.email = rec['email_requestor'] or ""
            contact_id = search_contact_id.id
        else:
            search_parent_id = rec_contact.search([('name', '=ilike', company)], limit=1)
            if search_parent_id:
                contact_id = rec_contact.create({'name': user, 'company_type': 'person', 'parent_id': search_parent_id.id, 'email': rec['email_requestor'] or ""}).id
            else:
                company_new = rec_contact.create({'name': company, 'company_type': 'company'}).id
                contact_id = rec_contact.create({'name': user, 'parent_id': company_new, 'email': rec['email_requestor'] or ""}).id
    
        search_request_type_id = rec_request_type.search([('name', '=', rec['type_id'])], limit=1)
        if search_request_type_id:
            type_id = search_request_type_id.id
        else:
            type_id = rec_request_type.create({'name': rec['type_id']}).id
    
        search_request_category_id = rec_request_category.search([('name', '=', rec['category_id'])], limit=1)
        if search_request_category_id:
            category_id = search_request_category_id.id
        else:
            category_id = rec_request_category.create({'name': rec['category_id']}).id

        search_generic_service_id = rec_generic_service.search([('name', '=', rec['service_id'])], limit=1)
        if search_generic_service_id:
            service_id = search_generic_service_id.id
        else:
            service_id = rec_generic_service.create({'name': rec['service_id']}).id
        
        search_generic_team_member_id = rec_generic_team_member.search(['&', ('user_id.login','ilike',rec['email']), ('team_id.active','=',True)], limit=1)
        if search_generic_team_member_id:
            assign_team_id = search_generic_team_member_id.team_id.id
        else:
            message = _('This member not assigned to any Team')
            return {'responses': 404, 'status': 'Member not Found', 'remark': message}

        search_users_id = rec_users.search([('login', 'ilike', rec['email'])], limit=1)
        if search_users_id:
            user_id = search_users_id.id
        else:
            message = _('This user not registered in XBase System, please create or change with existing user')
            return {'responses': 404, 'status': 'User Not Found', 'remark': message}
    
        search_partner_id = rec_partner.search([('name', 'ilike', rec['partner_id'])], limit=1)
        if search_partner_id:
            partner_id = search_partner_id.id
        else:
            message = _('Partner not Found in XBase System, Please create or change with existing Partner')
            return {'responses': 404, 'status': 'Subject Empty', 'remark': message}

        search_company_id = rec_company.search([('name', 'ilike', rec['x_company_id'])], limit=1)
        if search_company_id:
            x_company_id = search_company_id.id
        else:
            message = _('Company not Found in XBase System, Please create or change with existing Company')
            return {'responses': 404, 'status': 'Subject Empty', 'remark': message}

        if rec['subject']:
            subject = rec['subject']
        else:
            message = _('Subject is a Mandatory field, Please fill the subject')
            return {'responses': 404, 'status': 'Subject Empty', 'remark': message}
        
        if rec['request_text']:
            request_text = rec['request_text']
        else:
            message = _('Request Text is a Mandatory field, Please fill the Request Text')
            return {'responses': 404, 'status': 'Request Text Empty', 'remark': message}
        
        if rec['subject']:
            vals = []
            if service_id == 1111:
                vals = {
                    'subject': subject,
                    'request_text': request_text,
                    'orf_number': "ORF-"+rec['orf_number'],
                    'location': rec['location'],
                    'svc_catalog': rec['svc_catalog'],
                    'author_id': 10220,
                    'type_id': type_id,
                    'category_id': category_id,
                    'service_id': service_id,
                    'assign_team_id': assign_team_id,
                    'user_id': user_id,
                    'partner_id': partner_id,
                    'stage_id': 11,
                    'x_company_id': x_company_id,
                    'priority': rec['priority'],
                    'urgency': rec['urgency'],
                    'impact': rec['impact'],
                    'x_is_xswift': True,
                }
            else:
                vals = {
                    'subject': subject,
                    'request_text': request_text,
                    'orf_number': "ORF-"+rec['orf_number'],
                    'location': rec['location'],
                    'svc_catalog': rec['svc_catalog'],
                    'author_id': contact_id,
                    'type_id': type_id,
                    'category_id': category_id,
                    'service_id': service_id,
                    'assign_team_id': assign_team_id,
                    'user_id': user_id,
                    'partner_id': partner_id,
                    'stage_id': 11,
                    'x_company_id': x_company_id,
                    'priority': rec['priority'],
                    'urgency': rec['urgency'],
                    'impact': rec['impact'],
                    'x_is_xswift': True,
                }
            new_data = request.env['request.request'].sudo().create(vals)
            assigned = new_data.write({'stage_id': 11})
            args = {'responses': 200, 
                    'ticket_id': new_data.id, 
                    'ticket_name': new_data.name, 
                    'status': 'Successfully Created to XBase', 
                    'remark': '-'}
        else:
            args = {'responses': 500, 
                    'ticket_id': 'Not Found', 
                    'ticket_name': 'Not Found', 
                    'status': 'Failed', 
                    'remark': 'Failed to Create Ticket'}
        return args

    @http.route('/incident_ticket_create', type='json', auth='user')
    def incident_ticket_create(self, **rec):
        rec_contact = http.request.env['res.partner'].sudo()
        rec_request_type = http.request.env['request.type'].sudo()
        rec_request_category = http.request.env['request.category'].sudo()
        rec_generic_service = http.request.env['generic.service'].sudo()
        rec_generic_team_member = http.request.env['generic.team.member'].sudo()
        rec_users = http.request.env['res.users'].sudo()
        rec_partner = http.request.env['res.partner'].sudo()
        rec_company = http.request.env['res.partner'].sudo()

        author = rec['author_id']
        i = author.split(", ")
        company = i[0]
        user = i[1]
        search_contact_name = rec_contact.search([('name', 'ilike', user)], limit=1)
        search_contact_company = rec_contact.search([('is_company', '=', True), ('name', 'ilike', company)], limit=1)
            
        search_contact_id = rec_contact.search([('name', '=ilike', user),('parent_id.name', '=ilike', company)], limit=1)
        if search_contact_id:
            contact_id = search_contact_id.id
        else:
            search_parent_id = rec_contact.search([('name', '=ilike', company)], limit=1)
            if search_parent_id:
                contact_id = rec_contact.create({'name': user, 'company_type': 'person', 'parent_id': search_parent_id.id}).id
            else:
                company_new = rec_contact.create({'name': company, 'company_type': 'company'}).id
                contact_id = rec_contact.create({'name': user, 'parent_id': company_new}).id
    
        search_request_type_id = rec_request_type.search([('name', '=', rec['type_id'])], limit=1)
        if search_request_type_id:
            type_id = search_request_type_id.id
        else:
            message = _('This Type not registered in XBase System, please create one!')
            return {'responses': 404, 'status': 'Type [%s] not Found' %(rec['type_id']), 'remark': message}
    
        search_request_category_id = rec_request_category.search([('name', '=ilike', rec['category_id'])], limit=1)
        if search_request_category_id:
            category_id = search_request_category_id.id
        else:
            category_id = rec_request_category.create({'name': rec['category_id']}).id

        search_generic_service_id = rec_generic_service.search([('name', '=ilike', rec['service_id'])], limit=1)
        if search_generic_service_id:
            service_id = search_generic_service_id.id
        else:
            service_id = rec_generic_service.create({'name': rec['service_id']}).id
        
        search_generic_team_member_id = rec_generic_team_member.search(['&', ('user_id.login','ilike',rec['email']), ('team_id.active','=',True)], limit=1)
        if search_generic_team_member_id:
            assign_team_id = search_generic_team_member_id.team_id.id
        else:
            message = _('This member not assigned to any Team')
            return {'responses': 404, 'status': 'Member not Found', 'remark': message}

        search_users_id = rec_users.search([('login', '=ilike', rec['email'])], limit=1)
        if search_users_id:
            user_id = search_users_id.id
        else:
            message = _('This user not registered in XBase System, please create or change with existing user')
            return {'responses': 404, 'status': 'User Not Found', 'remark': message}
    
        search_partner_id = rec_partner.search([('name', '=ilike', rec['partner_id'])], limit=1)
        if search_partner_id:
            partner_id = search_partner_id.id
        else:
            message = _('Partner not Found in XBase System, Please create or change with existing Partner')
            return {'responses': 404, 'status': 'Subject Empty', 'remark': message}

        search_company_id = rec_company.search([('name', '=ilike', rec['company_id'])], limit=1)
        if search_company_id:
            x_company_id = search_company_id.id
        else:
            message = _('Company not Found in XBase System, Please create or change with existing Company')
            return {'responses': 404, 'status': 'Subject Empty', 'remark': message}

        if rec['subject']:
            subject = rec['subject']
        else:
            message = _('Subject is a Mandatory field, Please fill the subject')
            return {'responses': 404, 'status': 'Subject Empty', 'remark': message}
        
        if rec['detail_incident']:
            detail_incident = rec['detail_incident']
        else:
            message = _('Request Text is a Mandatory field, Please fill the Request Text')
            return {'responses': 404, 'status': 'Request Text Empty', 'remark': message}
        
        if rec['subject']:
            vals = []
            now = datetime.now() + relativedelta(hours=7)
            date = datetime.strptime(str(now), "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d")
            time = datetime.strptime(str(now), "%Y-%m-%d %H:%M:%S.%f").strftime("%H:%M:%S")
            time_stamp = date+" "+time
            if type_id == 1:
                vals = {'subject': subject,
                        'request_text': detail_incident,
                        'orf_number': rec['ticket_number'],
                        'location': rec['location'],
                        'service_id': service_id,
                        'category_id': category_id,
                        'type_id': 1,
                        'x_company_id': x_company_id,
                        'partner_id': partner_id,
                        'author_id': contact_id,
                        'sla_user_id': user_id,
                        # 'assign_team_id': assign_team_id,
                        'x_xswift_attachment': rec['attachment'],
                        'stage_id': 2,
                        'impact': '0',
                        'urgency': '0',
                        'priority': '0',
                        'x_is_xswift': True,
                    }
            else:
                message = _('This Endpoint only for Request Type [Incident]')
                return {'responses': 404, 'status': 'Forbidden', 'remark': message}
                
            new_data = request.env['request.request'].sudo().create(vals)
            new = new_data.write({'stage_id': 2})
            args = {'responses': 200, 
                    'ticket_id': new_data.id, 
                    'ticket_name': new_data.name, 
                    'timestamp_submit': time_stamp,
                    'status': 'Successfully Created to XBase', 
                    'remark': '-'}
        else:
            args = {'responses': 500, 
                    'ticket_id': 'Not Found', 
                    'ticket_name': 'Not Found', 
                    'timestamp_submit': 'None',
                    'status': 'Failed', 
                    'remark': 'Failed to create Ticket, Try Again!'}
        return args

    @http.route('/incident_ticket_priority', type='json', auth='user', method='POST')
    def incident_ticket_priority(self, **rec):
        rec_ticket = http.request.env['request.request'].sudo()
        rec_generic_team_member = http.request.env['generic.team.member'].sudo()
        rec_users = http.request.env['res.users'].sudo() 
        
        ticket_id = rec_ticket.search([('orf_number','=', rec['ticket_number'])], limit=1)

        search_generic_team_member_id = rec_generic_team_member.search(['&', ('user_id.login','ilike',rec['email']), ('team_id.active','=',True)], limit=1)
        if search_generic_team_member_id:
            assign_team_id = search_generic_team_member_id.team_id.id
        else:
            message = _('This member not assigned to any Team')
            return {'responses': 404, 'status': 'Member not Found', 'remark': message}

        search_users_id = rec_users.search([('login', 'ilike', rec['email'])], limit=1)
        if search_users_id:
            user_id = search_users_id.id
        else:
            message = _('This user not registered in XBase System, please create or change with existing user')
            return {'responses': 404, 'status': 'User Not Found', 'remark': message}

        impact = ""
        urgency = ""
        if rec['impact']:
            if rec['impact'].lower() == "low":
                impact = "1"
            elif rec['impact'].lower() == "medium":
                impact = "2"
            elif rec['impact'].lower() == "high":
                impact = "3"
            else:
                message = _('Impact Value [%s] Not Found' %(rec['impact']))
                return {'responses': 404, 'status': 'Not Found', 'remark': message}
        else:
            message = _('Impact Value is Empty')
            return {'responses': 404, 'status': 'Not Found', 'remark': message}

        if rec['urgency']:
            if rec['urgency'].lower() == "low":
                urgency = "1"
            elif rec['urgency'].lower() == "medium":
                urgency = "2"
            elif rec['urgency'].lower() == "high":
                urgency = "3"
            else:
                message = _('urgency Value [%s] Not Found' %(rec['urgency']))
                return {'responses': 404, 'status': 'Not Found', 'remark': message}
        else:
            message = _('urgency Value is Empty')
            return {'responses': 404, 'status': 'Not Found', 'remark': message}

        timestamp_submit = datetime.strptime(rec['timestamp_submit'], "%Y-%m-%d %H:%M:%S")
        time_submit = timestamp_submit - relativedelta(hours=7)
        timestamp_assigned = datetime.strptime(rec['timestamp_assigned'], "%Y-%m-%d %H:%M:%S")
        time_assigned = timestamp_assigned - relativedelta(hours=7)
        if ticket_id:
            vals = {'impact': impact,
                    'urgency': urgency,
                    # 'priority': rec['priority'],
                    'user_id': user_id,
                    'assign_team_id': assign_team_id,
                    'x_xswift_submit_time': time_submit,
                    'x_current_date_time': time_assigned,
                    'date_assigned': time_assigned}
            try:
                ticket_id.update(vals)
                classification = ticket_id.write({'stage_id': 3})
                # obj_resolve_time = ticket_id.mapped('sla_control_ids').mapped('sla_rule_id').filtered(lambda r: r.code == 'resolve-time')
                for line in ticket_id.sla_control_ids.filtered(lambda i: i.sla_active == True):
                    for rule_resolve in line.sla_rule_id.mapped('rule_line_ids').filtered(lambda i: i.priority == ticket_id.priority):
                        line.warn_time = rule_resolve.warn_time
                        line.limit_time = rule_resolve.limit_time
            except Exception as exc:
                return {'responses': 400, 'status': 'Forbidden', 'remark': exc}
                
            # response_warn_time = 0
            # response_limit_time = 0
            resolve_warn_date = 0
            resolve_due_date = 0
            warn_date = False
            due_date = False
            # if ticket_id.sla_control_ids:
                # obj_response_time = ticket_id.mapped('sla_control_ids').mapped('sla_rule_id').filtered(lambda r: r.code == 'response-time')
                # for rule_response in obj_response_time.rule_line_ids.filtered(lambda i: i.priority == ticket_id.priority):
                #     response_warn_time = int(rule_response.warn_time * 60)
                #     response_limit_time = int(rule_response.limit_time * 60)
            for sla_ids in ticket_id.sla_control_ids.filtered(lambda i: i.sla_active == True):
                resolve_warn_date = int(sla_ids.warn_time * 60)
                resolve_due_date = int(sla_ids.limit_time * 60)
                warn_date = sla_ids.warn_date + relativedelta(hours=7)
                due_date = sla_ids.limit_date + relativedelta(hours=7)

            now = ticket_id.x_current_date_time
            created_time = ticket_id.x_xswift_submit_time

            actual_time = now - created_time
            minute = divmod(actual_time.seconds, 60)

            # warn_date = created_time + relativedelta(minutes=response_warn_time)
            # due_date = created_time + relativedelta(minutes=response_limit_time)
            # limit_time = response_limit_time

            response_status = "off_target" if minute[0] > resolve_due_date else "on_target"
            if not ticket_id.x_response_status:
                ticket_id.x_response_status = response_status
            
            args = {'responses': 200, 
                    'xbase_ticket_id': ticket_id.id,
                    'xbase_ticket_name': ticket_id.name,
                    'xbase_created_date': ticket_id.x_xswift_submit_time,
                    'xswift_ticket_name': ticket_id.orf_number,
                    'warn_date': warn_date,
                    'due_date': due_date,
                    'response_status': ticket_id.x_response_status,
                    'status': 'Resolved. Successfully Update to Xbase'}
        else:
            dummy_now_str = rec['timestamp_assigned']
            dummy_created_time_str = rec['timestamp_submit']
            dummy_now = datetime.strptime(dummy_now_str, "%Y-%m-%d %H:%M:%S")
            dummy_created_time = datetime.strptime(dummy_created_time_str, "%Y-%m-%d %H:%M:%S")
            dummy_actual_time = dummy_now - dummy_created_time
            dummy_minute = divmod(dummy_actual_time.seconds, 60)

            dummy_warn_date = dummy_created_time + relativedelta(minutes=15)
            dummy_due_date = dummy_created_time + relativedelta(minutes=30)
            dummy_limit_time = 30

            response_status_dummy = "off_target" if dummy_minute[0] > dummy_limit_time else "on_target"
            if not ticket_id.x_response_status:
                ticket_id.x_response_status = response_status_dummy

            args = {'responses': 200, 
                    'xbase_ticket_id': 'Not Found',
                    'xbase_ticket_name': 'Not Found',
                    'xbase_created_date': dummy_created_time_str,
                    'xswift_ticket_name': rec['ticket_number'],
                    'due_date': dummy_due_date,
                    'warn_date': dummy_warn_date,
                    'response_status': ticket_id.x_response_status,
                    'status': 'Resolved. This is Dummy Data because this Ticket Number not Registered in XBASE'}
        return args


    @http.route('/incident_ticket_conclude', type='json', auth='user', method='POST')
    def incident_ticket_conclude(self, **rec):
        rec_ticket = http.request.env['request.request'].sudo()
        rec_generic_team_member = http.request.env['generic.team.member'].sudo()
        rec_users = http.request.env['res.users'].sudo() 
        
        ticket_obj = rec_ticket.search([('orf_number','=', rec['ticket_id'])], limit=1)
        if ticket_obj.stage_id.id == 3:
            ticket_id = ticket_obj
        else:
            message = _('This Incident Ticket status is [%s]. Can only update [Classification] Status' %(ticket_obj.stage_id.name))
            return {'responses': 404, 'status': 'Member not Found', 'remark': message}

        search_generic_team_member_id = rec_generic_team_member.search(['&', ('user_id.login','ilike',rec['email']), ('team_id.active','=',True)], limit=1)
        if search_generic_team_member_id:
            assign_team_id = search_generic_team_member_id.team_id.id
        else:
            message = _('This member not assigned to any Team')
            return {'responses': 404, 'status': 'Member not Found in any Team', 'remark': message}

        search_users_id = rec_users.search([('login', 'ilike', rec['email'])], limit=1)
        if search_users_id:
            user_id = search_users_id.id
        else:
            message = _('This user not registered in XBase System, please create or change with existing user')
            return {'responses': 404, 'status': 'User Not Found', 'remark': message}

        stage_id = False
        if rec['state'].lower() == 'resolved':
            stage_id = 5
        elif rec['state'].lower() == 'rejected':
            stage_id = 6
        else:
            message = _('Only state ["resolved" or "rejected"]')
            return {'responses': 404, 'status': 'State Not Found', 'remark': message}
        
        if ticket_id:
            now = datetime.now() + relativedelta(hours=7)
            date = datetime.strptime(str(now), "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d")
            time = datetime.strptime(str(now), "%Y-%m-%d %H:%M:%S.%f").strftime("%H:%M:%S")
            time_stamp = date+" "+time
            vals = {'x_xswift_submit_time': ticket_id.x_xswift_submit_time if ticket_id.x_xswift_submit_time else rec['timestamp_start'],
                    'x_current_date_time': rec['timestamp_conclude'],
                    'response_text': rec['reason'],
                    'user_id': user_id,
                    'assign_team_id': assign_team_id}
            try:
                update_data = ticket_id.update(vals)
                if ticket_id.stage_id.id == 3 and rec['state'].lower() == 'resolved':
                    # classification = ticket_id.write({'stage_id': 3})
                    progress = ticket_id.write({'stage_id': 4})
                    resolved = ticket_id.write({'stage_id': 5})
                elif ticket_id.stage_id.id == 3 and rec['state'].lower() == 'rejected':
                    # classification = ticket_id.write({'stage_id': 3})
                    rejected = ticket_id.write({'stage_id': 6})
            except Exception as exc:
                return {'responses': 400, 'status': 'Forbidden', 'remark': exc}

            resolve_warn_time = 0
            resolve_limit_time = 0
            if ticket_id.sla_control_ids:

                obj_resolve_time = ticket_id.mapped('sla_control_ids').mapped('sla_rule_id').filtered(lambda r: r.code == 'resolve-time')
                for rule_resolve in obj_resolve_time.rule_line_ids.filtered(lambda i: i.priority == ticket_id.priority):
                    resolve_warn_time += int(rule_resolve.warn_time * 60)
                    resolve_limit_time += int(rule_resolve.limit_time * 60)

            now = ticket_id.x_current_date_time
            created_time = ticket_id.x_xswift_submit_time

            actual_time = now - created_time
            minute = divmod(actual_time.seconds, 60)

            warn_date = created_time + relativedelta(minutes=resolve_warn_time)
            due_date = created_time + relativedelta(minutes=resolve_limit_time)
            limit_time = resolve_limit_time

            if rec['state'].lower() == 'resolved':
                args = {'responses': 200, 
                        'xbase_ticket_id': ticket_id.id,
                        'xbase_ticket_name': ticket_id.name,
                        'xbase_created_date': ticket_id.x_xswift_submit_time,
                        'xswift_ticket_name': ticket_id.orf_number,
                        'due_date': due_date,
                        'warn_date': warn_date,
                        'response_status': "Off Target" if minute[0] > limit_time else "On Target",
                        'status': 'Resolved. Successfully Update to Xbase'}
                return args
            else:
                args = {'responses': 200, 
                        'xbase_ticket_id': ticket_id.id,
                        'xbase_ticket_name': ticket_id.name,
                        'xbase_created_date': ticket_id.x_xswift_submit_time,
                        'xswift_ticket_name': ticket_id.orf_number,
                        'due_date': "",
                        'warn_date': "",
                        'response_status': "",
                        'status': 'Rejected. Successfully Update to Xbase'}
                return args
        else:
            args = {'responses': 404, 
                    'xbase_ticket_id': 'Not Found',
                    'xbase_ticket_name': 'Not Found',
                    'xbase_created_date': 'Not Found',
                    'xswift_ticket_name': 'Not Found',
                    'due_date': 'Not Found',
                    'warn_date': 'Not Found',
                    'response_status': 'Not Found',
                    'status': 'Not Found'}
        return args