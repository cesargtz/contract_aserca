# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from openerp.exceptions import ValidationError

class ContractAserca(models.Model):
    _name = 'contract.aserca'
    _rec_name = 'name_producer_related'

    main_contract = fields.Many2one('purchase.order')
    name_producer_related = fields.Many2one('res.partner', "Productor")
    quantity_tons = fields.Float('Toneladas', digits=(12, 4))

    @api.multi
    @api.onchange('main_contract','quantity_tons')
    def onchange_tons(self):
        if self.quantity_tons > 0:
            tons_contract = self.main_contract.tons
            if tons_contract > 0:
                pass
            else:
                return {
                        'warning': {
                            'title': "El contrato es de 0 toneladas",
                            'message': "Favor de agregar las toneladas del contrato",
                        }
                    }

class ContractAsercaInherit(models.Model):
    _inherit = 'purchase.order'

    contract_aserca_ids = fields.One2many('contract.aserca', 'main_contract')
    ticket_partner_relations = fields.One2many('ticket.relation', 'main_contract')

    @api.multi
    def write(self, vals):
        res = super(ContractAsercaInherit, self).write(vals)
        tons_aserca = 0
        for i in self.contract_aserca_ids:
            tons_aserca += i.quantity_tons
        if tons_aserca > self.tons:
            raise exceptions.ValidationError("Las toneldas de los productores son mayores a las del contrato.")
        return res



class TicketPartnerRelation(models.Model):
    _name = 'ticket.relation'

    name = fields.Char()
    main_contract = fields.Many2one('purchase.order')
    ticket = fields.Many2one('truck.reception')
    partner_related = fields.Many2one('contract.aserca', domain="[('main_contract','=', main_contract)]")
    quantity = fields.Float(digits=(12, 4))
    bolet_relation = fields.Many2one('ticket.relation')


    @api.onchange('ticket')
    def _onchange_ticket(self):
        tickets = len(self.env['ticket.relation'].search([('ticket','=',self.ticket.id)]))
        if tickets > 0:
            self.name = str(self.ticket.name) + "/" + str(chr(97 + tickets)) #97 -> a
        else:
            self.name = str(self.ticket.name) + "/a"

    @api.multi
    def separate_ticket(self):
        self.ensure_one()
        try:
            form_id = self.env['ir.model.data'].get_object_reference('ticket_relation', 'ticket_relation_form_view')[1]
        except ValueError:
            form_id = False

        ctx = dict()
        ctx.update({
            'default_main_contract': self.main_contract.id,
            'default_ticket': self.ticket.id,
            'default_bolet_relation': self.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ticket.relation',
            'views': [(form_id, 'form')],
            'view_id': form_id,
            #'target': 'new',
            'context': ctx,
        }

    @api.onchange('quantity')
    def _on_change_qty(self):
        tikets = self.env['ticket.relation'].search([('ticket','=',self.ticket.id)])
        total_tickets = self.quantity
        for ticket in tikets:
            total_tickets += ticket.quantity
        if total_tickets > self.ticket.raw_kilos / 1000:
            pass
            # raise exceptions.ValidationError("Las toneldas son mayores al ticket de camión.")

    @api.model
    def create(self, vals):
        res = super(TicketPartnerRelation, self).create(vals)
        if 'bolet_relation' in vals:
            bolet = self.env['ticket.relation'].search([('id','=',vals['bolet_relation'])])
            if vals['quantity'] >= bolet.quantity:
                raise exceptions.ValidationError("Estas tratando de sacar una cantidad mayor de tonaledas de la boleta.")
            else:
                tons_up = bolet.quantity - vals['quantity']
                bolet.write({'quantity': tons_up})
        return res
    
    # @api.model cuando se agrega un nuevo elemento el la vista de lista editable
    # def default_get(self,fields):
    #     res = super(TicketPartnerRelation, self).default_get(fields)
        # self.test_get()
        # last_rec = self.search([], order='id desc', limit=1)
        # if last_rec:
        #     res.update({'name':last_rec.name})
        # return res



class TruckReceptionRelatedPartner(models.Model):
    _inherit = 'truck.reception'

    @api.multi
    def fun_transfer(self):
        res = super(TruckReceptionRelatedPartner, self).fun_transfer()
        # code inyect
        if self.contract_id.state == 'purchase':
            partners = self.env['contract.aserca'].search([('main_contract','=',self.contract_id.id)], order='id')
            if len(partners) > 0:
                for partner in partners:
                    ticket_partners = self.env['ticket.relation'].search([('partner_related','=', partner.id)])
                    tons = 0
                    for ticket in ticket_partners:
                        tons += ticket.quantity
                    if tons < partner.quantity_tons:
                        print("Entro para crear")
                        self.create_ticket_relation(self.name,self.contract_id.id, self.id,self.raw_kilos, partner.id)
                        return res
                self.create_ticket_relation(self.name,self.contract_id.id, self.id,self.raw_kilos,'')
        return res
        
    def create_ticket_relation(self,name,contract,ticket,qty,partner):
        self.env['ticket.relation'].create({
                    'name':  str(name) + "/a",
                    'main_contract': contract,
                    'ticket': ticket,
                    'quantity': qty / 1000,
                    'partner_related':partner,

            })