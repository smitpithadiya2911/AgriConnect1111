import random
import string
from io import BytesIO
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from xhtml2pdf import pisa
from django.core.files.base import ContentFile

def generate_otp(length=6):
    """Generates a random N-digit OTP code."""
    return ''.join(random.choices(string.digits, k=length))

def send_html_email(subject, template_name, context, recipient_list, attachment_content=None, attachment_filename=None):
    """
    Renders an HTML template and sends it via email.
    Can optionally attach a file (e.g. PDF).
    """
    html_content = render_to_string(template_name, context)
    
    # We create plain text fallback as well, but mainly send HTML
    msg = EmailMessage(
        subject,
        html_content,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list
    )
    msg.content_subtype = "html"  # Main content is now text/html

    if attachment_content and attachment_filename:
        msg.attach(attachment_filename, attachment_content, 'application/pdf')

    try:
        result = msg.send()
        return result
    except Exception as e:
        print(f"\n{'='*50}\nEMAIL FAILED TO SEND: {e}\n{'='*50}")
        print(f"TO: {recipient_list}")
        print(f"SUBJECT: {subject}")
        if context and 'otp_code' in context:
            print(f"** OTP CODE: {context['otp_code']} **")
        print(f"{'='*50}\n")
        return False

def generate_invoice_pdf(order):
    """
    Generates a PDF invoice for the given order and returns the raw PDF bytes.
    Also saves it to the order.invoice_pdf field.
    """
    template_path = 'emails/invoice_template.html'
    context = {'order': order, 'items': order.items.all()}
    html = render_to_string(template_path, context)
    
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        pdf_bytes = result.getvalue()
        # Save to the order object directly
        filename = f"Invoice_AG_{order.id}.pdf"
        order.invoice_pdf.save(filename, ContentFile(pdf_bytes), save=True)
        return pdf_bytes
    return None
