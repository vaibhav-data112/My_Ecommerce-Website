import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_order_confirmation(order_id, user_name, user_email, items, total, shipping_address, payment_method='razorpay'):
    """Send order confirmation email. Silently skipped if MAIL_SERVER not configured."""
    smtp_host = os.environ.get('MAIL_SERVER', '').strip()
    smtp_user = os.environ.get('MAIL_USERNAME', '').strip()
    smtp_pass = os.environ.get('MAIL_PASSWORD', '').strip()
    smtp_port = int(os.environ.get('MAIL_PORT', '587'))
    mail_from = os.environ.get('MAIL_FROM', smtp_user).strip()

    if not all([smtp_host, smtp_user, smtp_pass, user_email]):
        return  # email not configured — skip silently

    payment_note = (
        'Pay on delivery when your order arrives.'
        if payment_method == 'cod'
        else 'Payment received via Razorpay.'
    )

    rows = ''.join(
        f"<tr><td style='padding:8px;border-bottom:1px solid #eee'>{i['name']}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee;text-align:center'>{i['quantity']}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee;text-align:right'>₹{i['price'] * i['quantity']:.2f}</td></tr>"
        for i in items
    )

    body = f"""
<html><body style="font-family:Inter,sans-serif;color:#1C1C1A;background:#FAFAF7;margin:0;padding:0">
<div style="max-width:520px;margin:32px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(44,62,40,0.10)">
  <div style="background:#2D6A4F;padding:28px 32px">
    <h1 style="font-family:Georgia,serif;color:#fff;margin:0;font-size:24px">🌶️ Karvii Spices</h1>
    <p style="color:#B7D5C4;margin:6px 0 0;font-size:14px">Order Confirmed!</p>
  </div>
  <div style="padding:28px 32px">
    <p style="margin:0 0 16px">Hi <strong>{user_name}</strong>,</p>
    <p style="margin:0 0 20px;color:#6B6B5E">Thank you for your order! Here's your order summary:</p>
    <div style="background:#F4F1EB;border-radius:8px;padding:12px 16px;margin-bottom:20px">
      <strong style="color:#2D6A4F">Order #{order_id}</strong>
    </div>
    <table style="width:100%;border-collapse:collapse;margin-bottom:16px">
      <tr style="background:#2D6A4F;color:#fff">
        <th style="padding:8px;text-align:left;font-size:13px">Product</th>
        <th style="padding:8px;text-align:center;font-size:13px">Qty</th>
        <th style="padding:8px;text-align:right;font-size:13px">Price</th>
      </tr>
      {rows}
    </table>
    <div style="text-align:right;font-size:18px;font-weight:700;color:#2D6A4F;margin-bottom:20px">
      Total: ₹{total:.2f}
    </div>
    <div style="background:#F4F1EB;border-radius:8px;padding:14px 16px;margin-bottom:16px">
      <div style="font-size:12px;color:#6B6B5E;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.05em">Delivery Address</div>
      <div style="font-size:14px">{shipping_address}</div>
    </div>
    <div style="background:#FDEBD0;border-radius:8px;padding:12px 16px;margin-bottom:20px;font-size:13px;color:#B84A06">
      💳 {payment_note}
    </div>
    <p style="font-size:13px;color:#6B6B5E;margin:0 0 8px">
      📦 Expected delivery: <strong>3–5 business days</strong>
    </p>
    <p style="font-size:13px;color:#6B6B5E;margin:0">
      Questions? Reply to this email or visit our <a href="https://karvii.in/contact" style="color:#2D6A4F">Contact page</a>.
    </p>
  </div>
  <div style="background:#F4F1EB;padding:16px 32px;text-align:center">
    <p style="font-size:12px;color:#6B6B5E;margin:0">Karvii Spices — Pure Spices, Authentic Flavours</p>
  </div>
</div>
</body></html>
"""

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Order Confirmed — Karvii Spices Order #{order_id}"
    msg['From']    = f"Karvii Spices <{mail_from}>"
    msg['To']      = user_email
    msg.attach(MIMEText(body, 'html', 'utf-8'))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(mail_from, [user_email], msg.as_string())
    except Exception:
        pass  # never let email failure break an order
