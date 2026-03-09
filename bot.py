import os
import csv
import datetime

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
SELECT_YEAR,
CUSTOM_YEAR,
SELECT_MONTH,
ASK_VARIABLE,
VAR_AMOUNT,
VAR_DESC,
ASK_LOP,
LOP_AMOUNT,
LOP_DESC,
)=range(10)


def load_employees():
    employees=[]
    with open("employees.csv") as f:
        reader=csv.DictReader(f)
        for r in reader:
            employees.append(r)
    return employees


def draw_background(canvas,doc):
    canvas.setFillColorRGB(0.93,0.97,1)
    canvas.rect(0,0,A4[0],A4[1],fill=1)


def generate_payslip(emp,data):

    filename=f"{emp['name']}_{data['month']}_{data['year']}.pdf"

    fixed=int(emp["salary"])
    variable=int(data.get("variable_amount",0))
    lop=int(data.get("lop_amount",0))

    net=fixed+variable-lop

    elements=[]

    header_style=ParagraphStyle(
        "header",
        fontSize=20,
        textColor=colors.HexColor("#1F4E79"),
        spaceAfter=10
    )

    normal_style=ParagraphStyle(
        "normal",
        fontSize=10,
        spaceAfter=4
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

    elements.append(Spacer(1,10))

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

    elements.append(
        Paragraph(
            f"<b>Payslip – {data['month']} {data['year']}</b>",
            title_style
        )
    )

    emp_table=Table(
        [
            ["Employee Name",emp["name"]],
            ["Designation",emp["designation"]],
            ["Date of Joining",emp["doj"]],
            ["PAN",emp["pan"]],
            ["Employee ID",emp["id"]],
        ],
        colWidths=[220,320]
    )

    emp_table.setStyle(
        TableStyle([
            ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#E8F1FB")),
            ("GRID",(0,0),(-1,-1),0.5,colors.grey)
        ])
    )

    elements.append(emp_table)
    elements.append(Spacer(1,25))

    rows=[
        ["Component","Amount"],
        ["Fixed Salary",f"Rs. {fixed}"]
    ]

    if variable>0:
        label="Variable Pay"
        if data.get("variable_desc"):
            label+=f" ({data['variable_desc']})"
        rows.append([label,f"Rs. {variable}"])

    if lop>0:
        label="Loss of Pay"
        if data.get("lop_desc"):
            label+=f" ({data['lop_desc']})"
        rows.append([label,f"Rs. {lop}"])

    rows.append(["Net Salary",f"Rs. {net}"])

    salary_table=Table(rows,colWidths=[340,200])

    salary_table.setStyle(
        TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1F4E79")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("GRID",(0,0),(-1,-1),0.5,colors.grey),
            ("BACKGROUND",(0,-1),(-1,-1),colors.HexColor("#E8F1FB")),
        ])
    )

    elements.append(salary_table)

    elements.append(Spacer(1,50))

    if os.path.exists("Gemini_Generated_Image_2ziuv52ziuv52ziu.png"):

        sig=Image(
            "Gemini_Generated_Image_2ziuv52ziuv52ziu.png",
            width=120,
            height=60
        )

        sig_table=Table(
            [["",sig],
             ["","Authorized Signatory"],
             ["","Athreya Dental Clinic"]],
            colWidths=[380,160]
        )

        sig_table.setStyle(
            TableStyle([
                ("ALIGN",(1,0),(1,0),"RIGHT"),
                ("ALIGN",(1,1),(1,2),"CENTER"),
            ])
        )

        elements.append(sig_table)

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

    current=datetime.datetime.now().year
    previous=current-1

    keyboard=[
        [str(current)],
        [str(previous)],
        ["Custom"]
    ]

    await update.message.reply_text(
        "Select Year",
        reply_markup=ReplyKeyboardMarkup(keyboard,resize_keyboard=True)
    )

    return SELECT_YEAR


async def year(update:Update,context:ContextTypes.DEFAULT_TYPE):

    y=update.message.text

    if y=="Custom":
        await update.message.reply_text("Enter Year (e.g. 2024)")
        return CUSTOM_YEAR

    context.user_data["year"]=y
    return await ask_month(update,context)


async def custom_year(update:Update,context:ContextTypes.DEFAULT_TYPE):

    context.user_data["year"]=update.message.text
    return await ask_month(update,context)


async def ask_month(update,context):

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
        return VAR_AMOUNT

    context.user_data["variable_amount"]=0

    await update.message.reply_text(
        "Any Loss of Pay?",
        reply_markup=ReplyKeyboardMarkup([["Yes","No"]],resize_keyboard=True)
    )

    return ASK_LOP


async def var_amount(update,context):
    context.user_data["variable_amount"]=update.message.text
    await update.message.reply_text("Enter Variable Pay Description or type none")
    return VAR_DESC


async def var_desc(update,context):

    if update.message.text.lower()!="none":
        context.user_data["variable_desc"]=update.message.text

    await update.message.reply_text(
        "Any Loss of Pay?",
        reply_markup=ReplyKeyboardMarkup([["Yes","No"]],resize_keyboard=True)
    )

    return ASK_LOP


async def ask_lop(update,context):

    if update.message.text=="Yes":
        await update.message.reply_text("Enter Loss of Pay Amount")
        return LOP_AMOUNT

    context.user_data["lop_amount"]=0
    return await generate(update,context)


async def lop_amount(update,context):
    context.user_data["lop_amount"]=update.message.text
    await update.message.reply_text("Enter Loss of Pay Description or type none")
    return LOP_DESC


async def lop_desc(update,context):

    if update.message.text.lower()!="none":
        context.user_data["lop_desc"]=update.message.text

    return await generate(update,context)


async def generate(update,context):

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
        SELECT_YEAR:[MessageHandler(filters.TEXT & ~filters.COMMAND,year)],
        CUSTOM_YEAR:[MessageHandler(filters.TEXT & ~filters.COMMAND,custom_year)],
        SELECT_MONTH:[MessageHandler(filters.TEXT & ~filters.COMMAND,month)],
        ASK_VARIABLE:[MessageHandler(filters.TEXT & ~filters.COMMAND,ask_variable)],
        VAR_AMOUNT:[MessageHandler(filters.TEXT & ~filters.COMMAND,var_amount)],
        VAR_DESC:[MessageHandler(filters.TEXT & ~filters.COMMAND,var_desc)],
        ASK_LOP:[MessageHandler(filters.TEXT & ~filters.COMMAND,ask_lop)],
        LOP_AMOUNT:[MessageHandler(filters.TEXT & ~filters.COMMAND,lop_amount)],
        LOP_DESC:[MessageHandler(filters.TEXT & ~filters.COMMAND,lop_desc)],
    },
    fallbacks=[]
)

app.add_handler(conv)

app.run_polling()
