# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
import logging

from odoo import api, fields, models
from odoo.tools import is_html_empty, split_every
from odoo.tools.misc import str2bool

_logger = logging.getLogger(__name__)


class MailTemplate(models.Model):
    _inherit = "mail.template"

    operating_unit_id = fields.Many2one("operating.unit", string="Operating Unit")

    def send_mail(
        self,
        res_id,
        force_send=False,
        raise_exception=False,
        email_values=None,
        email_layout_xmlid=False,
    ):
        # Include in the email values the alias domain ID of the current OU if any
        email_values = email_values or {}
        if self.operating_unit_id and self.operating_unit_id.alias_domain_id:
            email_values["record_alias_domain_id"] = (
                self.operating_unit_id.alias_domain_id.id,
            )
        return super().send_mail(
            res_id,
            force_send=force_send,
            raise_exception=raise_exception,
            email_values=email_values,
            email_layout_xmlid=email_layout_xmlid,
        )

    def _is_operating_unit_use_mail_server_enabled(self):
        """Return whether operating unit outgoing mail server routing is enabled."""
        self.ensure_one()
        return str2bool(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("mail_operating_unit.operating_unit_use_mail_server", False)
        )

    def _get_operating_unit_mail_server(self, record):
        """Return the operating unit outgoing mail server.

        If the record has ``operating_unit_id`` and that operating unit has
        a configured outgoing mail server, use it.
        If the record has ``operating_unit_ids`` and all operating units
        share the same outgoing mail server, use that server.
        Otherwise return `False`.
        """
        record.ensure_one()
        if "operating_unit_id" in record and record.operating_unit_id:
            if mail_server := record.operating_unit_id.mail_server_id:
                return mail_server
            return False
        if "operating_unit_ids" in record and record.operating_unit_ids:
            if mail_servers := record.operating_unit_ids.mapped("mail_server_id"):
                if len(mail_servers) == 1:
                    return mail_servers
        return False

    def _get_operating_unit_label(self, record):
        """Return operating unit label for logging purposes.

        Examples:
        - ``Operating Unit A`` for ``operating_unit_id``;
        - ``Operating Unit A, Operating Unit B`` for ``operating_unit_ids``;
        - ``no operating unit`` when no OU is set on the record.
        """
        record.ensure_one()
        if "operating_unit_id" in record and record.operating_unit_id:
            return record.operating_unit_id.display_name
        if "operating_unit_ids" in record and record.operating_unit_ids:
            return ", ".join(record.operating_unit_ids.mapped("display_name"))
        return "no operating unit"

    # ruff: noqa: C901
    @api.returns("self", lambda value: value.ids)
    def send_mail_batch(
        self,
        res_ids,
        force_send=False,
        raise_exception=False,
        email_values=None,
        email_layout_xmlid=False,
    ):
        # OVERRIDE: to allow routing outgoing mail server from the operating unit.
        # If ``mail_server_id`` is explicitly set on the template
        # it has the highest priority and operating unit based routing is skipped.
        # If not and the routing from operating unit feature is enabled,
        # attempt to resolve an outgoing mail server from the record's operating unit.
        # Otherwise, fallback to the standard behavior.
        # The code is inspired from standard ``mail_template.send_mail_batch``,
        # but adapted to handle the operating unit based routing.
        self.ensure_one()
        self._send_check_access(res_ids)
        sending_email_layout_xmlid = email_layout_xmlid or self.email_layout_xmlid

        mails_sudo = self.env["mail.mail"].sudo()
        batch_size = (
            int(self.env["ir.config_parameter"].sudo().get_param("mail.batch_size"))
            or 50
        )  # be sure to not have 0, as otherwise no iteration is done
        RecordModel = self.env[self.model].with_prefetch(res_ids)
        record_ir_model = self.env["ir.model"]._get(self.model)
        # OVERRIDE START
        use_ou_mail_server = self._is_operating_unit_use_mail_server_enabled()
        if not use_ou_mail_server:
            _logger.info(
                "mail_operating_unit: outgoing mail server routing is disabled"
            )
        # OVERRIDE END
        for res_ids_chunk in split_every(batch_size, res_ids):
            res_ids_values = self._generate_template(
                res_ids_chunk,
                (
                    "attachment_ids",
                    "auto_delete",
                    "body_html",
                    "email_cc",
                    "email_from",
                    "email_to",
                    "mail_server_id",
                    "model",
                    "partner_to",
                    "reply_to",
                    "report_template_ids",
                    "res_id",
                    "scheduled_date",
                    "subject",
                ),
            )
            values_list = [res_ids_values[res_id] for res_id in res_ids_chunk]

            # get record in batch to use the prefetch
            records = RecordModel.browse(res_ids_chunk)
            attachments_list = []

            # lang and company is used for rendering layout
            res_ids_langs, res_ids_companies = {}, {}
            if sending_email_layout_xmlid:
                if self.lang:
                    res_ids_langs = self._render_lang(res_ids_chunk)
                res_ids_companies = records._mail_get_companies(
                    default=self.env.company
                )

            for record in records:
                values = res_ids_values[record.id]
                values["recipient_ids"] = [
                    (4, pid) for pid in (values.get("partner_ids") or [])
                ]
                values["attachment_ids"] = [
                    (4, aid) for aid in (values.get("attachment_ids") or [])
                ]
                values.update(email_values or {})

                # OVERRIDE START
                # Keep template priority.
                # ``mail_server_id`` is already generated from the template in
                # ``_generate_template_static_values()``. If present, do not
                # override it with operating unit based logic.
                if values.get("mail_server_id"):
                    _logger.info(
                        "mail_operating_unit: keeping template mail server %s "
                        "for template %s(%s) and record %s(%s)",
                        values["mail_server_id"],
                        self.name,
                        self.id,
                        record._name,
                        record.id,
                    )
                elif use_ou_mail_server:
                    operating_unit_label = self._get_operating_unit_label(record)
                    mail_server = self._get_operating_unit_mail_server(record)
                    if mail_server:
                        values["mail_server_id"] = mail_server.id
                        _logger.info(
                            "mail_operating_unit: using operating unit "
                            "mail server %s (%s) from OU [%s] for record %s(%s)",
                            mail_server.display_name,
                            mail_server.id,
                            operating_unit_label,
                            record._name,
                            record.id,
                        )
                    else:
                        _logger.info(
                            "mail_operating_unit: no operating unit mail server "
                            "resolved from OU [%s] for record %s(%s), "
                            "falling back to default behavior",
                            operating_unit_label,
                            record._name,
                            record.id,
                        )
                # OVERRIDE END
                # delegate attachments after creation due to ACL check
                attachments_list.append(values.pop("attachments", []))

                # add a protection against void email_from
                if "email_from" in values and not values.get("email_from"):
                    values.pop("email_from")

                # encapsulate body
                if not sending_email_layout_xmlid:
                    values["body"] = values["body_html"]
                    continue

                lang = res_ids_langs.get(record.id) or False
                company = res_ids_companies.get(record.id) or self.env.company
                model_lang = (
                    record_ir_model.with_context(lang=lang) if lang else record_ir_model
                )

                template_ctx = {
                    # message
                    "message": self.env["mail.message"]
                    .sudo()
                    .new(
                        dict(body=values["body_html"], record_name=record.display_name)
                    ),
                    "subtype": self.env["mail.message.subtype"].sudo(),
                    # record
                    "model_description": model_lang.display_name,
                    "record": record,
                    "record_name": False,
                    "subtitles": False,
                    # user / environment
                    "company": company,
                    "email_add_signature": False,
                    "signature": "",
                    "website_url": "",
                    # tools
                    "is_html_empty": is_html_empty,
                }
                body = model_lang.env["ir.qweb"]._render(
                    sending_email_layout_xmlid,
                    template_ctx,
                    minimal_qcontext=True,
                    raise_if_not_found=False,
                )
                if not body:
                    _logger.warning(
                        "QWeb template %s not found when "
                        "sending template %s. Sending without layout.",
                        sending_email_layout_xmlid,
                        self.name,
                    )
                    body = values["body_html"]

                values["body_html"] = self.env[
                    "mail.render.mixin"
                ]._replace_local_links(body)
                values["body"] = values["body_html"]

            mails = self.env["mail.mail"].sudo().create(values_list)

            # manage attachments
            for mail, attachments in zip(mails, attachments_list, strict=False):
                if attachments:
                    attachments_values = [
                        (
                            0,
                            0,
                            {
                                "name": name,
                                "datas": datas,
                                "type": "binary",
                                "res_model": "mail.message",
                                "res_id": mail.mail_message_id.id,
                            },
                        )
                        for (name, datas) in attachments
                    ]
                    mail.with_context(default_type=None).write(
                        {"attachment_ids": attachments_values}
                    )

            mails_sudo += mails

        if force_send:
            mails_sudo.send(raise_exception=raise_exception)
        return mails_sudo
