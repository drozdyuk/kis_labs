import base64
import logging

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrderSign(models.Model):
    _inherit = "sale.order"

    # ---- Нові поля ----
    digital_signature = fields.Binary(
        string="Цифровий підпис",
        readonly=True,
        copy=False,
        help="RSA-підпис хешу ключових полів документа.",
    )
    signature_date = fields.Datetime(
        string="Дата підпису",
        readonly=True,
        copy=False,
    )
    is_verified = fields.Boolean(
        string="Підпис перевірено",
        default=False,
        readonly=True,
        copy=False,
    )

    # ======================================================
    # Нотифікації через bus.bus (форма оновлюється коректно)
    # ======================================================

    def _notify(self, title, message, notification_type="success", sticky=False):
        """Send a notification via bus so the form still reloads."""
        self.env["bus.bus"]._sendone(
            self.env.user.partner_id,
            "simple_notification",
            {
                "title": title,
                "message": message,
                "type": notification_type,
                "sticky": sticky,
            },
        )

    # ======================================================
    # Допоміжні методи: робота з ключами
    # ======================================================

    def _get_or_create_keys(self):
        """
        Отримує або генерує пару RSA-ключів.
        Ключі зберігаються у системних параметрах Odoo
        (ir.config_parameter), що забезпечує їх персистентність
        між перезапусками сервера.
        """
        ICP = self.env["ir.config_parameter"].sudo()

        private_pem = ICP.get_param("document_sign.private_key")
        public_pem = ICP.get_param("document_sign.public_key")

        if not private_pem or not public_pem:
            # Генерація нової пари ключів (2048 біт)
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )

            # Серіалізація у формат PEM
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ).decode("utf-8")

            public_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("utf-8")

            # Збереження у системних параметрах
            ICP.set_param("document_sign.private_key", private_pem)
            ICP.set_param("document_sign.public_key", public_pem)

            _logger.info("Document Sign: RSA key pair generated and stored.")

        return private_pem, public_pem

    def _load_private_key(self, pem_data):
        """Завантажує закритий ключ із PEM-рядка."""
        return serialization.load_pem_private_key(
            pem_data.encode("utf-8"),
            password=None,
        )

    def _load_public_key(self, pem_data):
        """Завантажує відкритий ключ із PEM-рядка."""
        return serialization.load_pem_public_key(
            pem_data.encode("utf-8"),
        )

    # ======================================================
    # Формування payload — дані, що підписуються
    # ======================================================

    def _get_sign_payload(self):
        """
        Формує рядок із ключових полів документа.
        Саме цей рядок буде хешований і підписаний.
        Якщо будь-яке з цих полів змінити після підпису,
        верифікація виявить розбіжність.
        """
        self.ensure_one()
        payload = (
            f"{self.name or ''}"
            f"|{self.date_order or ''}"
            f"|{self.amount_total or 0.0}"
            f"|{self.partner_id.id or 0}"
        )
        return payload.encode("utf-8")

    # ======================================================
    # Дії (actions): підпис і перевірка
    # ======================================================

    def action_sign_document(self):
        """
        Підписує документ:
        1. Формує payload із ключових полів.
        2. Підписує payload закритим ключем (RSA + SHA-256).
        3. Зберігає підпис у полі digital_signature.
        """
        self.ensure_one()

        if self.digital_signature:
            raise UserError(
                "Документ вже підписано. Для повторного підпису "
                "спочатку скиньте поточний підпис."
            )

        private_pem, _public_pem = self._get_or_create_keys()
        private_key = self._load_private_key(private_pem)

        payload = self._get_sign_payload()

        # Підпис: бібліотека cryptography виконує SHA-256
        # хешування автоматично у межах виклику sign()
        signature = private_key.sign(
            payload,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )

        self.write({
            "digital_signature": base64.b64encode(signature),
            "signature_date": fields.Datetime.now(),
            "is_verified": True,
        })

        self._notify(
            "Підпис створено",
            f"Документ {self.name} успішно підписано.",
        )

    def action_verify_signature(self):
        """
        Перевіряє цифровий підпис:
        1. Формує payload із поточних значень полів.
        2. Розшифровує підпис відкритим ключем.
        3. Порівнює хеші: якщо дані змінилися — верифікація
           провалюється (InvalidSignature).
        """
        self.ensure_one()

        if not self.digital_signature:
            raise UserError("Документ не підписано.")

        _private_pem, public_pem = self._get_or_create_keys()
        public_key = self._load_public_key(public_pem)

        payload = self._get_sign_payload()
        signature = base64.b64decode(self.digital_signature)

        try:
            public_key.verify(
                signature,
                payload,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            self.is_verified = True
            self._notify(
                "Результат перевірки",
                f"Підпис документа {self.name} валідний. "
                "Цілісність даних підтверджено.",
                "success",
                sticky=True,
            )
        except Exception:
            self.is_verified = False
            self._notify(
                "Результат перевірки",
                f"УВАГА! Підпис документа {self.name} НЕВАЛІДНИЙ. "
                "Дані були змінені після підпису!",
                "danger",
                sticky=True,
            )

    def action_reset_signature(self):
        """Скидає підпис для повторного підписання."""
        self.ensure_one()
        self.write({
            "digital_signature": False,
            "signature_date": False,
            "is_verified": False,
        })
