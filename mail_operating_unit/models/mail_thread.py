from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _message_compute_author(
        self, author_id=None, email_from=None, raise_on_email=True
    ):
        alias_domain_id = self.env.context.get("record_alias_domain_id")
        if alias_domain_id:
            email_from = (
                self.env["mail.alias.domain"].browse(alias_domain_id).default_from_email
            )
        return super()._message_compute_author(
            author_id=author_id, email_from=email_from, raise_on_email=raise_on_email
        )
