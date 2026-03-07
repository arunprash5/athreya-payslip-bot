import os
import csv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# REGISTER FONT (for ₹ symbol)
pdfmetrics.registerFont(TTFont('DejaVuSans','DejaVuSans.ttf'))

BOT_TOKEN = os.environ["8689608357:AAGRJcJE5R0pJ97KU07scK0f-2EE8FIV9L8"]

def get_employee(name):
    with open("employees.csv", newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["name"].lower() == name.lower():
                return row
    return None


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

    filename = f"{name}_{month}_payslip.pdf"

    c = canvas.Canvas(filename)

    # SET FONT
    c.setFont("DejaVuSans", 12)

    # HEADER
    c.drawString(200,800,"ATHREYA DENTAL CLINIC")
    c.drawString(200,780,f"Payslip - {month}")

    # EMPLOYEE DETAILS
    c.drawString(100,720,f"Employee Name: {emp['name']}")
    c.drawString(100,700,f"Designation: {emp['designation']}")
    c.drawString(100,680,f"Employee ID: {emp['id']}")

    # SALARY SECTION
    c.drawString(100,640,"Earnings")
    c.drawString(100,620,f"Basic Salary: ₹ {emp['salary']}")

    c.drawString(100,580,f"Net Pay: ₹ {emp['salary']}")

    c.save()

    await update.message.reply_document(open(filename,"rb"))


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("payslip", payslip))

app.run_polling()
