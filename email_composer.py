import base64
import logging
from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config


class EmailService:
    """Handles constructing and sending emails."""


    def __init__(self, service):
        self.service = service

    def _build_html_body(self, name: str) -> str:
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
          <p>Hi {name},</p>
          <p>Thank you for being part of CodeQuest 3.0.</p>
          <p>You’ve completed this edition, and we’re happy to award you your official participation certificate.</p>
          <p><strong>Please find your certificate attached.</strong></p>
          <p>Feedback: <a href="{Config.FORM_LINK}">Click here</a></p>
          <p>The CodeQuest Team</p>
          <br>
          <img src="cid:sig_img" alt="Signature" style="width:100%; max-width:500px;">
        </body>
        </html>
        """

    def send_email(self, to_email: str, name: str, cert_data: bytes, cert_name: str):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        logger = logging.getLogger(__name__)

        msg = MIMEMultipart('mixed')
        msg['To'] = to_email
        msg['Subject'] = "Your CodeQuest 3.0 Certificate"

        # Related part (HTML + Inline Images)
        msg_related = MIMEMultipart('related')
        msg.attach(msg_related)
        msg_related.attach(MIMEText(self._build_html_body(name), 'html'))

        # Inline Signature
        if Config.SIGNATURE_IMAGE_PATH.exists():
            with open(Config.SIGNATURE_IMAGE_PATH, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-ID', '<sig_img>')
                img.add_header('Content-Disposition', 'inline')
                msg_related.attach(img)
        else:
            logger.warning("Signature image not found. Sending without it.")

        # Attachment
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(cert_data)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{cert_name}"')
        msg.attach(part)

        # Send
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        self.service.users().messages().send(userId="me", body={"raw": raw}).execute()