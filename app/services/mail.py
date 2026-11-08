"""Outgoing e-mail via SMTP. Without MAIL_HOST, mails are written to the log (development)."""
import smtplib
import ssl
from email.message import EmailMessage

from flask import current_app, render_template

# Tests read sent mails from here instead of a real mailbox.
outbox: list[EmailMessage] = []


def send_mail(to: str, subject: str, template: str, **context) -> bool:
    """Render templates/emails/<template>.txt and send it. Returns False if sending failed."""
    cfg = current_app.config
    body = render_template(f"emails/{template}.txt", **context)

    msg = EmailMessage()
    msg["Subject"] = f"{subject} – {cfg['SITE_NAME']}"
    msg["From"] = cfg["MAIL_FROM"]
    msg["To"] = to
    msg.set_content(body)

    if current_app.testing:
        outbox.append(msg)
        return True
    if not cfg["MAIL_HOST"]:
        current_app.logger.info("E-mail NOT sent (MAIL_HOST empty)\nTo: %s\nSubject: %s\n\n%s",
                                to, msg["Subject"], body)
        return True

    try:
        context_ssl = ssl.create_default_context()
        if cfg["MAIL_PORT"] == 465:
            smtp = smtplib.SMTP_SSL(cfg["MAIL_HOST"], cfg["MAIL_PORT"], context=context_ssl, timeout=15)
        else:
            smtp = smtplib.SMTP(cfg["MAIL_HOST"], cfg["MAIL_PORT"], timeout=15)
            if cfg["MAIL_USE_TLS"]:
                smtp.starttls(context=context_ssl)
        with smtp:
            if cfg["MAIL_USERNAME"]:
                smtp.login(cfg["MAIL_USERNAME"], cfg["MAIL_PASSWORD"])
            smtp.send_message(msg)
        return True
    except (smtplib.SMTPException, OSError):
        current_app.logger.exception("Could not send e-mail to %s (%s)", to, template)
        return False
