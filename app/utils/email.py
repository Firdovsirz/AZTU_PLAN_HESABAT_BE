import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader

def send_html_email(recipient_email: str, recipient_name: str):
    sender_email = "firdovsirz@gmail.com"
    sender_password = "txjf wgkx mqdi fban"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    env = Environment(loader=FileSystemLoader("templates/email"))
    template = env.get_template("registration_email.html")
    html_content = template.render(name=recipient_name)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Qeydiyyat təsdiqi"
    msg["From"] = sender_email
    msg["To"] = recipient_email

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        return True
    except Exception as e:
        print("Email error:", e)
        return False