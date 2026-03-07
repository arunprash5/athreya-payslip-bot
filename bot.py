import os
import csv

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors

BOT_TOKEN = os.environ["BOT_TOKEN"]

EMPLOYEE, MONTH = range(2)


# -----------------------------
# Load employees
# -----------------------------
def load_employees():
    employees = []
    with open("employees.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            employees.append(row)
    return employees


# -----------------------------
# Page background
# -----------------------------
def draw_background(canvas, doc):
    canvas.setFillColorRGB(0.93, 0.97, 1)
    canvas.rect(0, 0, A4[0], A4[1], fill=1)


# -----------------------------
# Generate payslip PDF
# -----------------------------
def generate_payslip(emp, month):

    filename = f"{emp['name']}_{month}_payslip.pdf"

    elements = []

    header_style = ParagraphStyle(
        "header",
        fontSize=20,
        textColor=colors.HexColor("#1F4E79"),
        alignment=0,
        spaceAfter=10,
    )

    normal_style = ParagraphStyle(
        "normal",
        fontSize=10,
        alignment=0,
        spaceAfter=4,
    )

    title_style = ParagraphStyle(
        "title",
        fontSize=14,
        textColor=colors.HexColor("#1F4E79"),
        alignment=0,
        spaceAfter=10,
    )

    logo = ""

    if os.path.exists("athreya.jpg"):
        logo = Image("athreya.jpg", width=120, height=60)

    header = Table(
        [[Paragraph("<b>Athreya Dental Clinic</b>", header_style), logo]],
        colWidths=[380, 150],
    )

    header.setStyle(
        TableStyle(
            [
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    elements.append(header)

    elements.append(Spacer(1, 8))

    address = Paragraph(
        "1st floor, Natesh Apartments, No.28/2<br/>"
        "Velachery Bypass Rd, near Kotak Mahindra Bank<br/>"
        "Venkateswara Nagar, Velachery<br/>"
        "Chennai, Tamil Nadu 600042<br/><br/>"
        "Phone: 078100 28515<br/><br/>"
        "Website: https://www.athreyadentalclinic.com/",
        normal_style,
    )

    elements.append(address)

    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"<b>Payslip – {month}</b>", title_style))

    elements.append(Spacer(1, 10))

    employee_table = Table(
        [
            ["Employee Name", emp["name"]],
            ["Designation", emp["designation"]],
            ["Employee ID", emp["id"]],
        ],
        colWidths=[200, 330],
    )

    employee_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8F1FB")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )

    elements.append(employee_table)

    elements.append(Spacer(1, 25))

    salary_table = Table(
        [
            ["Earnings", "Amount"],
            ["Basic Salary", f"Rs. {emp['salary']}"],
            ["Deductions", "Rs. 0"],
            ["Net Pay", f"Rs. {emp['salary']}"],
        ],
        colWidths=[330, 200],
    )

    salary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8F1FB")),
            ]
        )
    )

    elements.append(salary_table)

    elements.append(Spacer(1, 40))

    footer = Paragraph(
        "This is a computer generated payslip and does not require signature.",
        normal_style,
    )

    elements.append(footer)

    pdf = SimpleDocTemplate(filename, pagesize=A4)

    pdf.build(elements, onFirstPage=draw_background, onLaterPages=draw_background)

    return filename


# -----------------------------
# Start payslip flow
# -----------------------------
async def start_payslip(update: Update, context: ContextTypes.DEFAULT_TYPE):

    employees = load_employees()

    names = [[emp["name"]] for emp in employees]

    reply_markup = ReplyKeyboardMarkup(names, resize_keyboard=True)

    await update.message.reply_text(
        "Select Employee", reply_markup=reply_markup
    )

    return EMPLOYEE


# -----------------------------
# Employee selected
# -----------------------------
async def employee_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["employee"] = update.message.text.strip()

    months = [
        ["January", "February", "March"],
        ["April", "May", "June"],
        ["July", "August", "September"],
        ["October", "November", "December"],
    ]

    reply_markup = ReplyKeyboardMarkup(months, resize_keyboard=True)

    await update.message.reply_text(
        "Select Month", reply_markup=reply_markup
    )

    return MONTH


# -----------------------------
# Month selected
# -----------------------------
async def month_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):

    month = update.message.text.strip()

    employees = load_employees()

    emp = None

    for e in employees:
        if e["name"].strip() == context.user_data["employee"]:
            emp = e
            break

    if emp is None:
        await update.message.reply_text("Employee not found.")
        return ConversationHandler.END

    filename = generate_payslip(emp, month)

    await update.message.reply_document(open(filename, "rb"))

    return ConversationHandler.END


# -----------------------------
# Bot setup
# -----------------------------
app = ApplicationBuilder().token(BOT_TOKEN).build()

conv = ConversationHandler(
    entry_points=[CommandHandler("payslip", start_payslip)],
    states={
        EMPLOYEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, employee_selected)],
        MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, month_selected)],
    },
    fallbacks=[],
)

app.add_handler(conv)

app.run_polling()
