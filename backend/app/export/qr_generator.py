"""
MCRDSE Sprint 4 – QR Code Generator Service
============================================
Generates verification QR codes for municipal report audit validation.
Renders PNG images and base64 data URLs containing report ID & SHA256 checksum URLs.
"""

from __future__ import annotations

import base64
import io
import logging

try:
    import qrcode
    from qrcode.image.pil import PilImage
    _QR_AVAILABLE = True
except ImportError:
    _QR_AVAILABLE = False

logger = logging.getLogger("app.export.qr_generator")


class QRCodeGenerator:
    """
    QR Code generation service for audit verification links.
    """

    @staticmethod
    def generate_qr_code(verification_url: str) -> tuple[bytes, str]:
        """
        Generate QR code PNG bytes and base64 data URL from a verification link.

        Parameters
        ----------
        verification_url:
            URL encoded inside the QR matrix.

        Returns
        -------
        tuple[bytes, str]
            (png_bytes, base64_data_url)
        """
        if _QR_AVAILABLE:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=6,
                border=2,
            )
            qr.add_data(verification_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            png_bytes = buf.getvalue()
        else:
            logger.warning("qrcode package not available; generating fallback dummy PNG bytes")
            # Fallback 1x1 transparent PNG
            png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"

        b64_str = base64.b64encode(png_bytes).decode("ascii")
        data_url = f"data:image/png;base64,{b64_str}"

        return png_bytes, data_url
