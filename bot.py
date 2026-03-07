import os
import csv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('DejaVuSans','DejaVuSans.ttf'))

BOT_TOKEN = os.environ["BOT_TOKEN"]


def get_employee(name):
    with open("employees.csv", newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["name"].lower() == name.lower():
                return row
    return None


def generate_payslip(emp, month):

    filename = f"{emp['name']}_{month}_payslip.pdf"

    styles = getSampleStyleSheet()
    elements = []

    if os.path.exists("logo.png"):
        logo = Image("logo.png", width=140, height=70)
        elements.append(logo)

    elements.append(Spacer(1,10))

    elements.append(Paragraph("<b>Athreya Dental Clinic</b>", styles['Title']))

    elements.append(Paragraph(
        "1st floor, Natesh Apartments, No.28/2, Velachery Bypass Rd,<br/>"
        "near Kotak Mahindra Bank, Venkateswara Nagar,<br/>"
        "Velachery, Chennai, Tamil Nadu 600042",
        styles['Normal']
    ))

    elements.append(Paragraph("Phone: 078100 28515", styles['Normal']))
    elements.append(Paragraph("Website: https://www.athreyadentalclinic.com/", styles['Normal']))

    elements.append(Spacer(1,20))

    elements.append(Paragraph(f"<b>Payslip – {month}</b>", styles['Heading2']))

    elements.append(Spacer(1,20))

    employee_data = [
        ["Employee Name", emp["name"]],
        ["Designation", emp["designation"]],
        ["Employee ID", emp["id"]],
    ]

    employee_table = Table(employee_data, colWidths=[200,300])

    employee_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,-1),colors.lightgrey),
        ("GRID",(0,0),(-1,-1),1,colors.grey)
    ]))

    elements.append(employee_table)

    elements.append(Spacer(1,30))

    salary_data = [
        ["Earnings","Amount"],
        ["Basic Salary", f"₹ {emp['salary']}"],
        ["Deductions","₹ 0"],
        ["Net Pay", f"₹ {emp['salary']}"]
    ]

    salary_table = Table(salary_data, colWidths=[300,200])

    salary_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#2E86C1")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),1,colors.grey),
        ("BACKGROUND",(0,-1),(-1,-1),colors.lightgrey)
    ]))

    elements.append(salary_table)

    pdf = SimpleDocTemplate(filename, pagesize=A4)
    pdf.build(elements)

    return filename


async def payslip(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /payslip name month")
        return

    name = context.args[0]
    month = context.args[1]

    emp = get_employee(name)

    if not emp:
        await update.message.reply_text("Employee not found")
        return

    filename = generate_payslip(emp, month)

    await update.message.reply_document(open(filename,"rb"))


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("payslip", payslip))

app.run_polling()
