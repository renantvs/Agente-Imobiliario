from loguru import logger
from app.core.config import settings


def send_email(to: str, subject: str, body_html: str) -> bool:
    """
    Envia e-mail via Gmail API OAuth2.
    Retorna False enquanto GMAIL_SENDER não estiver configurado.

    Para ativar:
    1. Criar projeto no Google Cloud Console
    2. Habilitar Gmail API
    3. Criar credenciais OAuth2 e baixar credentials.json
    4. Executar o fluxo de autorização para gerar token.json
    5. Descomentar o bloco abaixo e instalar google-api-python-client

    # from google.oauth2.credentials import Credentials
    # from google.auth.transport.requests import Request
    # from googleapiclient.discovery import build
    # import base64
    # from email.mime.text import MIMEText
    # from email.mime.multipart import MIMEMultipart
    #
    # SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    #
    # def _get_gmail_service():
    #     creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    #     if not creds or not creds.valid:
    #         if creds and creds.expired and creds.refresh_token:
    #             creds.refresh(Request())
    #     return build("gmail", "v1", credentials=creds)
    #
    # service = _get_gmail_service()
    # msg = MIMEMultipart("alternative")
    # msg["Subject"] = subject
    # msg["From"] = settings.GMAIL_SENDER
    # msg["To"] = to
    # part = MIMEText(body_html, "html")
    # msg.attach(part)
    # raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    # service.users().messages().send(userId="me", body={"raw": raw}).execute()
    # return True
    """
    if not settings.GMAIL_SENDER:
        logger.warning(
            "Gmail não configurado. E-mail não enviado. "
            "Defina GMAIL_SENDER no .env para ativar."
        )
        return False

    try:
        # Placeholder para quando Gmail estiver ativado
        logger.info(f"Email preparado | to={to} | subject={subject}")
        return True
    except Exception as e:
        logger.error(f"send_email error | to={to} | {e}")
        return False
