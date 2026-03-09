import os
import csv

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
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

(
SELECT_EMPLOYEE,
SELECT_MONTH,
ASK_VARIABLE,
ENTER_VARIABLE_AMOUNT,
ENTER_VARIABLE_DESC,
ASK_LOP,
ENTER_LOP_AMOUNT,
ENTER_LOP_DESC,
) = range(8)


def load_employees():
    employees = []
    with open("employees.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            employees.append(row)
    return employees


def draw_background(canvas, doc):
    canvas.setFillColorRGB(0.93,0.97,1)
    canvas.rect(0,0,A4[0],A4[1],fill=1)


def generate_payslip(emp,data):

    filename=f"{emp['name']}_{data['month']}.pdf"

    fixed=int(emp["salary"])
    variable=int(data.get("variable_amount",0))
    lop=int(data.get("lop_amount",0))

    net=fixed+variable-lop

    elements=[]

    header_style=ParagraphStyle(
        "header",
        fontSize=20,
        textColor=colors.HexColor("#1F4E79"),
        spaceAfter=6
    )

    normal_style=ParagraphStyle(
        "normal",
        fontSize=10,
        spaceAfter=3
    )

    title_style=ParagraphStyle(
        "title",
        fontSize=14,
        textColor=colors.HexColor("#1F4E79"),
        spaceAfter=10
    )

    logo=""
    if os.path.exists("athreya.jpg"):
        logo=Image("athreya.jpg",width=110,height=55)

    header=Table(
        [[Paragraph("<b>Athreya Dental Clinic</b>",header_style),logo]],
        colWidths=[420,120]
    )

    header.setStyle(
        TableStyle([
            ("ALIGN",(1,0),(1,0),"RIGHT")
        ])
    )

    elements.append(header)
    elements.append(Spacer(1,6))

    address=Paragraph(
        "1st floor, Natesh Apartments, No.28/2<br/>"
        "Velachery Bypass Rd, near Kotak Mahindra Bank<br/>"
        "Venkateswara Nagar, Velachery<br/>"
        "Chennai, Tamil Nadu 600042<br/><br/>"
        "Phone: 078100 28515<br/><br/>"
        "Website: https://www.athreyadentalclinic.com/",
        normal_style
    )

    elements.append(address)
    elements.append(Spacer(1,20))

    elements.append(Paragraph(f"<b>Payslip – {data['month']}</b>",title_style))

    employee_table=Table(
        [
            ["Employee Name",emp["name"]],
            ["Designation",emp["designation"]],
            ["Date of Joining",emp["doj"]],
            ["PAN",emp["pan"]],
            ["Employee ID",emp["id"]],
        ],
        colWidths=[220,320]
    )

    employee_table.setStyle(
        TableStyle([
            ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#E8F1FB")),
            ("GRID",(0,0),(-1,-1),0.5,colors.grey),
        ])
    )

    elements.append(employee_table)
    elements.append(Spacer(1,25))

    salary_rows=[
        ["Component","Amount"],
        ["Fixed Salary",f"Rs. {fixed}"]
    ]

    if variable>0:
        label="Variable Pay"
        if data.get("variable_desc"):
            label+=f" ({data['variable_desc']})"
        salary_rows.append([label,f"Rs. {variable}"])

    if lop>0:
        label="Loss of Pay"
        if data.get("lop_desc"):
            label+=f" ({data['lop_desc']})"
        salary_rows.append([label,f"Rs. {lop}"])

    salary_rows.append(["Net Salary",f"Rs. {net}"])

    salary_table=Table(
        salary_rows,
        colWidths=[340,200]
    )

    salary_table.setStyle(
        TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1F4E79")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("GRID",(0,0),(-1,-1),0.5,colors.grey),
            ("BACKGROUND",(0,-1),(-1,-1),colors.HexColor("#E8F1FB")),
        ])
    )

    elements.append(salary_table)

    pdf=SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=30,
        rightMargin=30,
        topMargin=25,
        bottomMargin=25
    )

    pdf.build(elements,onFirstPage=draw_background)

    return filename


async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    employees=load_employees()

    keyboard=[[e["name"]] for e in employees]

    await update.message.reply_text(
        "Select Employee",
        reply_markup=ReplyKeyboardMarkup(keyboard,resize_keyboard=True)
    )

    return SELECT_EMPLOYEE


async def employee(update:Update,context:ContextTypes.DEFAULT_TYPE):

    context.user_data["employee"]=update.message.text.strip()

    months=[
        ["January","February","March"],
        ["April","May","June"],
        ["July","August","September"],
        ["October","November","December"]
    ]

    await update.message.reply_text(
        "Select Month",
        reply_markup=ReplyKeyboardMarkup(months,resize_keyboard=True)
    )

    return SELECT_MONTH


async def month(update:Update,context:ContextTypes.DEFAULT_TYPE):

    context.user_data["month"]=update.message.text

    await update.message.reply_text(
        "Any Variable Pay / Incentive?",
        reply_markup=ReplyKeyboardMarkup([["Yes","No"]],resize_keyboard=True)
    )

    return ASK_VARIABLE


async def ask_variable(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if update.message.text=="Yes":
        await update.message.reply_text("Enter Variable Pay Amount")
        return ENTER_VARIABLE_AMOUNT
    else:
        context.user_data["variable_amount"]=0
        await update.message.reply_text(
            "Any Loss of Pay?",
            reply_markup=ReplyKeyboardMarkup([["Yes","No"]],resize_keyboard=True)
        )
        return ASK_LOP


async def variable_amount(update:Update,context:ContextTypes.DEFAULT_TYPE):

    context.user_data["variable_amount"]=update.message.text
    await update.message.reply_text("Enter Variable Pay Description (or type none)")
    return ENTER_VARIABLE_DESC


async def variable_desc(update:Update,context:ContextTypes.DEFAULT_TYPE):

    desc=update.message.text
    if desc.lower()!="none":
        context.user_data["variable_desc"]=desc

    await update.message.reply_text(
        "Any Loss of Pay?",
        reply_markup=ReplyKeyboardMarkup([["Yes","No"]],resize_keyboard=True)
    )

    return ASK_LOP


async def ask_lop(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if update.message.text=="Yes":
        await update.message.reply_text("Enter Loss of Pay Amount")
        return ENTER_LOP_AMOUNT
    else:
        context.user_data["lop_amount"]=0
        return await generate(update,context)


async def lop_amount(update:Update,context:ContextTypes.DEFAULT_TYPE):

    context.user_data["lop_amount"]=update.message.text
    await update.message.reply_text("Enter Loss of Pay Description (or type none)")
    return ENTER_LOP_DESC


async def lop_desc(update:Update,context:ContextTypes.DEFAULT_TYPE):

    desc=update.message.text
    if desc.lower()!="none":
        context.user_data["lop_desc"]=desc

    return await generate(update,context)


async def generate(update:Update,context:ContextTypes.DEFAULT_TYPE):

    employees=load_employees()

    emp=None

    for e in employees:
        if e["name"]==context.user_data["employee"]:
            emp=e
            break

    filename=generate_payslip(emp,context.user_data)

    await update.message.reply_document(
        open(filename,"rb"),
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


app=ApplicationBuilder().token(BOT_TOKEN).build()

conv=ConversationHandler(
    entry_points=[CommandHandler("payslip",start)],
    states={
        SELECT_EMPLOYEE:[MessageHandler(filters.TEXT & ~filters.COMMAND,employee)],
        SELECT_MONTH:[MessageHandler(filters.TEXT & ~filters.COMMAND,month)],
        ASK_VARIABLE:[MessageHandler(filters.TEXT & ~filters.COMMAND,ask_variable)],
        ENTER_VARIABLE_AMOUNT:[MessageHandler(filters.TEXT & ~filters.COMMAND,variable_amount)],
        ENTER_VARIABLE_DESC:[MessageHandler(filters.TEXT & ~filters.COMMAND,variable_desc)],
        ASK_LOP:[MessageHandler(filters.TEXT & ~filters.COMMAND,ask_lop)],
        ENTER_LOP_AMOUNT:[MessageHandler(filters.TEXT & ~filters.COMMAND,lop_amount)],
        ENTER_LOP_DESC:[MessageHandler(filters.TEXT & ~filters.COMMAND,lop_desc)],
    },
    fallbacks=[]
)

app.add_handler(conv)

app.run_polling()
