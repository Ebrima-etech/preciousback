import hashlib
import hmac
import requests
from decouple import config
import logging

logger = logging.getLogger(__name__)

MODEMPAY_API_BASE = 'https://api.modempay.com/v1'


class ModemPayError(Exception):
    pass


def create_payment_intent(
    *,
    amount,
    currency,
    customer_email='',
    customer_name='',
    customer_phone='',
    return_url,
    cancel_url,
    metadata=None
):
    """Create a payment intent with ModemPay/Wave"""
    api_key = config('MODEMPAY_API_KEY', default='')

    if not api_key:
        raise ModemPayError('ModemPay API key not configured')

    fields = {
        'amount': round(float(amount)),
        'currency': currency,
        'return_url': return_url,
        'cancel_url': cancel_url,
    }

    if customer_email:
        fields['customer_email'] = customer_email
    if customer_name:
        fields['customer_name'] = customer_name
    if customer_phone:
        fields['customer_phone'] = customer_phone
    if metadata:
        fields['metadata'] = metadata

    try:
        resp = requests.post(
            f'{MODEMPAY_API_BASE}/payments',
            json={'data': fields},
            headers={
                'Authorization': f'Bearer {api_key}',
                'User-Agent': 'PreciousPlastic/1.0',
            },
            timeout=15,
        )

        if not resp.ok:
            error_msg = resp.json().get('message', 'Failed to create payment')
            logger.error(f'ModemPay error: {error_msg}')
            raise ModemPayError(f'ModemPay: {error_msg}')

        data = resp.json().get('data', {})
        if not data.get('payment_link'):
            raise ModemPayError('No payment link returned from ModemPay')

        return data
    except requests.RequestException as e:
        logger.error(f'ModemPay request error: {str(e)}')
        raise ModemPayError(f'Payment service error: {str(e)}')


def verify_webhook_signature(payload_bytes: bytes, signature_header: str) -> bool:
    """Verify webhook signature from ModemPay"""
    secret = config('MODEMPAY_WEBHOOK_SECRET', default='')

    if not secret:
        logger.warning('ModemPay webhook secret not configured')
        return False

    try:
        expected = hmac.new(
            secret.encode(),
            payload_bytes,
            hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(expected, signature_header)
    except Exception as e:
        logger.error(f'Webhook signature verification error: {str(e)}')
        return False
