To configure this module, you need to:

- Assign an *Alias Domain* to each Operating Unit that should use a specific email domain.
- Assign an *Operating Unit* to an Email Template when emails sent from that template must use the alias domain of that operating unit.
- Optionally assign an *Outgoing Mail Server* to an Operating Unit when emails should be routed through a specific SMTP server.
- Enable *Use operating unit outgoing mail server* in *General Settings* if outgoing mail servers should be selected automatically from the Operating Unit.

When no operating unit is defined on the template or on the target record, the standard Odoo alias domain behavior is applied.

When the outgoing mail server feature is disabled, or when no unambiguous Operating Unit mail server can be determined, the standard Odoo outgoing mail server selection is applied.
