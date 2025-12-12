import base64
import logging
from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, service):
        self.service = service
        self.template_content = self._load_template()

    def _load_template(self) -> str:
        """Reads the HTML file into memory."""
        if not Config.TEMPLATE_FILE.exists():
            raise FileNotFoundError(f"Template not found at {Config.TEMPLATE_FILE}")
        with open(Config.TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            return f.read()

    def send_email(self, to_email: str, name: str, cert_data: bytes, cert_name: str):
        msg = MIMEMultipart('mixed')
        msg['To'] = to_email
        msg['Subject'] ="Appreciation & Certificate of Ambassadorship – CodeQuest 3rd Edition"


        msg_related = MIMEMultipart('related')
        msg.attach(msg_related)

        # Inject variables into the HTML template
        # We use .format() to replace {name} and {form_link} in the HTML file
        try:
            filled_html = self.template_content.format(
                name=name,
                form_link=Config.FORM_LINK
            )
        except KeyError as e:
            logger.error(f"Template error: Missing placeholder {e} in HTML file.")
            filled_html = self.template_content # Fallback to raw template if error

        msg_related.attach(MIMEText(filled_html, 'html'))

        # Inline Signature
        if Config.SIGNATURE_IMAGE_PATH.exists():
            with open(Config.SIGNATURE_IMAGE_PATH, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-ID', '<sig_img>')
                img.add_header('Content-Disposition', 'inline')
                msg_related.attach(img)
        else:
            logger.warning(f"Signature {Config.SIGNATURE_IMAGE_PATH} not found.")

        # Attachment
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(cert_data)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{cert_name}"')
        msg.attach(part)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        self.service.users().messages().send(userId="me", body={"raw": raw}).execute()