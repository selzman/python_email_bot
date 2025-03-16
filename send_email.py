import asyncio
import base64
import os
import smtplib
import tempfile
from email.mime.image import MIMEImage
from pyromod import listen
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid
from jinja2 import Environment, FileSystemLoader
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import create_engine, Column, Integer, String, BLOB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///email.db')
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


class Photos(Base):
    __tablename__ = 'photos'
    id = Column(Integer, primary_key=True)
    photo = Column(BLOB)


class Messages(Base):
    __tablename__ = 'text'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    message = Column(String)


Base.metadata.create_all(engine)

if not os.path.exists('emails.txt'):
    with open('emails.txt', 'w') as file:
        file.write('')
else:
    pass

user_data = {}



# ////////////////////////////////////////////////





api_id = 123456789
api_hash = "api hash"
bot_token = "bot_token"


EMAIL_USER = 'example@gmail.com'
EMAIL_PASSWORD = "password"
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

MAIN_ADMINS = [1234567]
ADMINS = []



# ///////////////////////////////////////////






app = Client(
    "my_bot",
    api_id=api_id, api_hash=api_hash,
    bot_token=bot_token
)



ADD_TEXT = False
ADD_EMAIL = False
ADD_PHOTO = False
LAGHV_ADD_ADMIN = False
running = True
canceled = False
pause_event = asyncio.Event()

template_path = 'template.html'
with open(template_path, 'r', encoding='utf-8') as file:
    template_content = file.read()


@app.on_message(filters.command(["start"]))
async def Home(Client, message):
    chat_id = message.chat.id
    for admin in MAIN_ADMINS or ADMINS:

        if chat_id == admin:
            inline_buttons = [
                [InlineKeyboardButton(" ارسال ایمیل 📧", callback_data="send_email"), ],
                [InlineKeyboardButton('  ادمین ها 🫂', callback_data='manage_admins_part')],
                [InlineKeyboardButton("تعداد ایمیل ها 📊", callback_data="email_count"),
                 InlineKeyboardButton("اضافه کردن ایمیل 📢", callback_data="add_email"),
                 ],
                [InlineKeyboardButton("اضافه عکس 🖼", callback_data="add_photo"),
                 InlineKeyboardButton("حذف عکس 📥", callback_data="delete_photo"),
                 ],
                [InlineKeyboardButton("اضافه متن ✏", callback_data="add_text"),
                 InlineKeyboardButton(" حذف متن 📥", callback_data="delete_text"), ],
                [InlineKeyboardButton('حذف ایمیل ها 🗑', callback_data="delete_emails"), ],

            ]
            inline_keyboard = InlineKeyboardMarkup(inline_buttons)
            name = await app.get_users(chat_id)

            msg = f'''
             سلام  {name.first_name}  به ربات ایمیل مارکتینگ خوش امدید.
            
            '''
            await app.send_message(chat_id, text=msg, reply_markup=inline_keyboard)

        else:
            await app.send_message(chat_id, text='''
            برای خرید ربات ایمیل مارکتینگ و اطلاع از جزئیات ان با ایدی زیر در ارتباط باشید. 
            
            @netmm_suport
            ''')


# admin part
@app.on_callback_query(filters.regex("manage_admins_part"))
async def manage_admins_part(client, query):
    chat_id = query.message.chat.id
    btns = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("حذف ادمین 🙅", callback_data="delete_admin"), ],
            [InlineKeyboardButton("اضافه کردن ادمین🧑‍🦱", callback_data="add_admin_part"), ],
            #  [ InlineKeyboardButton( "لیست ادمین ها 👭 ",callback_data="admins_list"), ],
            [InlineKeyboardButton("بازگشت ", callback_data="back_to_admin"), ],

        ]
    )

    try:
        await app.edit_message_text(chat_id, query.message.id, "بخش مدیریت ادمین ربات", reply_markup=btns)
    except:
        await app.send_message(chat_id, "بخش مدیریت ادمین ربات", reply_markup=btns)


@app.on_callback_query(filters.regex("add_admin_part"))
async def delete_admin_query(client, query):
    global LAGHV_ADD_ADMIN
    LAGHV_ADD_ADMIN = True
    chat_id = query.message.chat.id
    await app.delete_messages(chat_id, query.message.id)
    chat = query.message.chat
    inline_buttons = [
        [InlineKeyboardButton("بازگشت", callback_data="back_to_admin")],
    ]
    inline_keyboard = InlineKeyboardMarkup(inline_buttons)

    new_admin = await chat.ask(f'''
 لطفا یوزر ایدی کاربر مورد نظر را برای اضافه کردن به ادمین بفرستید،اگر یوزر ایدی خود یا کاربران را نمیدانید از ربات زیر استفاده کنید.

 @userinfobot

    ''', reply_markup=inline_keyboard)

    if LAGHV_ADD_ADMIN:
        try:
            get_data_admin = await app.get_users(int(new_admin.text))
            btns = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("اره خودشه", callback_data=f"set_admin_success_{get_data_admin.id}"),
                     InlineKeyboardButton("نه این نیست", callback_data="dont_set_admin"), ]])
            await app.send_message(chat_id=chat_id, text=f'''
        ایا کاربر با اطلاعات زیر را تایید میکنید؟

    نام : {get_data_admin.first_name}

    یوزر نیم : @{get_data_admin.username}

    ''', reply_markup=btns)

        except:
            await app.send_message(chat_id=chat_id, text="متاسفانه ایدی اشتباه فرستادی ❌")

    else:
        pass


@app.on_callback_query(filters.regex(r"set_admin_success_\w+"))
async def set_admin_success(client, query):
    chat_id = query.message.chat.id
    admin_user_id = query.data.split("_")[-1]
    try:
        ADMINS.append(int(admin_user_id))
        await app.edit_message_text(chat_id, query.message.id, "ادمین با موفقیت اضافه شد.🙂")
    except:
        await app.edit_message_text(chat_id, query.message.id, "خطایی رخ داده لطفاً با برنامه نویس تماس بگیر.❌")


@app.on_callback_query(filters.regex("dont_set_admin"))
async def dont_set_admin(client, query):
    chat_id = query.message.chat.id
    await app.delete_messages(chat_id, query.message.id)
    return await back_to_admin(Client, query)


@app.on_callback_query(filters.regex("delete_admin"))
async def delete_admin_query(client, query):
    chat_id = query.message.chat.id

    inline_keyboard = []

    for admin_id in ADMINS:
        admin = await app.get_users(admin_id)
        button_text = f"{admin.first_name} ({admin.username})"
        button = InlineKeyboardButton(text=button_text, callback_data=f"admin_{admin_id}")
        inline_keyboard.append([button])

    back_btn = InlineKeyboardButton(text='بازگشت', callback_data="back_to_admin")
    inline_keyboard.append([back_btn])

    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    await app.edit_message_text(chat_id=chat_id, message_id=query.message.id,
                                text="برای حذف ادمین روی کاربر مورد نظر کلیک کنید", reply_markup=reply_markup)


@app.on_callback_query(filters.regex(r"admin_\w+"))
async def cart_callback_handler(client, query):
    chat_id = query.message.chat.id
    user_id_of_admin = query.data.split("_")[1]

    for admin in ADMINS:
        try:
            ADMINS.remove(int(user_id_of_admin))
        except:
            pass
    await app.answer_callback_query(query.id, text="ادمین با موفقیت حذف شد ✅", show_alert=True)

    inline_keyboard = []

    for admin_id in ADMINS:
        admin = await app.get_users(admin_id)
        button_text = f"{admin.first_name} \t ({admin.username})"
        button = InlineKeyboardButton(text=button_text, callback_data=f"admin_{admin_id}")
        inline_keyboard.append([button])
    back_btn = InlineKeyboardButton(text='بازگشت', callback_data="back_to_admin")

    inline_keyboard.append([back_btn])

    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    await app.edit_message_text(chat_id, query.message.id,
                                text="برای حذف کردن ادمین روی اسم و نام کاربری آن کلیک کنید😁",
                                reply_markup=reply_markup)


# photo part
@app.on_callback_query(filters.regex("add_photo"))
async def add_text(Client, query):
    global ADD_PHOTO
    ADD_PHOTO = True
    chat_id = query.message.chat.id

    chat = query.message.chat
    inline_buttons = [
        [InlineKeyboardButton("بازگشت", callback_data="back_to_admin")],
    ]
    inline_keyboard = InlineKeyboardMarkup(inline_buttons)
    await app.delete_messages(chat_id, query.message.id)
    msg = await chat.ask(text='عکس خود را برای ذخیره ارسال کنید 😁', reply_markup=inline_keyboard)
    if ADD_PHOTO:
        try:
            down_photo_path = await app.download_media(msg.photo)
            with open(down_photo_path, 'rb') as file:
                photo_data = file.read()

            new_photo = Photos(photo=photo_data)
            session.add(new_photo)
            session.commit()

            await app.send_message(chat_id, text='عکس با موفقیت اظافه شد.')
        except Exception as e:
            print(e)
            ADD_PHOTO = False
            await app.send_message(chat_id, text='خطا')

    else:
        pass


@app.on_callback_query(filters.regex("delete_photo"))
async def delete_text(Client, query):
    chat_id = query.message.chat.id

    photos = session.query(Photos).all()

    if photos:
        for photo in photos:
            id = photo.id
            photo_data = photo.photo
            button_text = f" حذف عکس {id} "
            callback_data = f"photo_delete_{id}"

            # Write binary data to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_file.write(photo_data)
                temp_file_path = temp_file.name

            try:
                await app.send_photo(
                    chat_id=chat_id,
                    photo=temp_file_path,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(button_text, callback_data=callback_data)]]
                    )
                )
            finally:
                # Remove the temporary file after sending the photo
                os.remove(temp_file_path)
    else:
        await query.answer('عکسی وجود ندارد.', show_alert=True)


@app.on_callback_query(filters.regex(r"photo_delete_\w+"))
async def message_delete(client, query):
    photo_id = query.data.split("_")[-1]
    chat_id = query.message.chat.id

    try:
        photo_to_delete = session.query(Photos).filter(Photos.id == photo_id).one_or_none()
        session.delete(photo_to_delete)
        session.commit()
        await query.answer('عکس با موفقیت حذف شد.', show_alert=True)
        await app.delete_messages(chat_id, query.message.id)
    except:
        await query.answer('خطا', show_alert=True)


# text part
@app.on_callback_query(filters.regex("add_text"))
async def add_text(Client, query):
    global ADD_TEXT
    ADD_TEXT = True
    chat_id = query.message.chat.id
    await app.delete_messages(chat_id, query.message.id)

    chat = query.message.chat
    inline_buttons = [
        [InlineKeyboardButton("بازگشت", callback_data="back_to_admin")],
    ]
    inline_keyboard = InlineKeyboardMarkup(inline_buttons)

    try:
        await app.send_message(chat_id, text='برای لغو از دکمه بازگشت استفاده کنید.', reply_markup=inline_keyboard)

        if ADD_TEXT:
            title_msg = await chat.ask(text='عنوان متن  خود را برای ذخیره ارسال کنید 🙂')
            if not ADD_TEXT:  # Check if the process was cancelled
                return
            msg = await chat.ask(text='پیام خود را برای ذخیره ارسال کنید 😁')
            if not ADD_TEXT:  # Check if the process was cancelled
                return

            new_messsage = Messages(message=msg.text, title=title_msg.text)
            session.add(new_messsage)
            session.commit()

            await app.send_message(chat_id, text='پیام با موفقیت اظافه شد.')

    except Exception as e:
        print(e)
        await app.send_message(chat_id, text=' خطا')

@app.on_callback_query(filters.regex("delete_text"))
async def delete_text(Client, query):
    chat_id = query.message.chat.id

    texts = session.query(Messages).all()
    inline_buttons = []
    try:
        for text in texts:
            id = text.id
            message = text.message
            title = text.title
            button_text = f" title :{title} \n message: {message}"
            callback_data = f"message_delete_{id}"
            inline_buttons.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

        inline_buttons.append([InlineKeyboardButton("بازگشت", callback_data="back_to_admin")])

        inline_keyboard = InlineKeyboardMarkup(inline_buttons)

        try:
            await app.edit_message_text(chat_id, query.message.id, text="برای حذف متن روی آن کلیک کنید",
                                        reply_markup=inline_keyboard)
        except Exception as e:
            print(e)
            await app.delete_messages(chat_id, query.message.id)
            await app.send_message(chat_id, text="برای حذف متن روی آن کلیک کنید", reply_markup=inline_keyboard)
    except:
        pass

@app.on_callback_query(filters.regex(r"message_delete_\w+"))
async def message_delete(client, query):
    chat_id = query.message.chat.id
    message_to_delete = query.data.split("_")[-1]

    try:
        msg_to_delete = session.query(Messages).filter(Messages.id == message_to_delete).one_or_none()

        session.delete(msg_to_delete)
        session.commit()
    except:
        await app.send_message(chat_id, text=' خطا')

    texts = session.query(Messages).all()
    inline_buttons = []

    for text in texts:
        id = text.id
        message = text.message
        title = text.title
        button_text = f" title :{title} \n message: {message}"
        callback_data = f"message_delete_{id}"
        inline_buttons.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    inline_buttons.append([InlineKeyboardButton("بازگشت", callback_data="back_to_admin")])

    inline_keyboard = InlineKeyboardMarkup(inline_buttons)

    try:
        await app.edit_message_text(chat_id, query.message.id, text="برای حذف متن روی آن کلیک کنید",
                                    reply_markup=inline_keyboard)
    except Exception as e:
        await app.delete_messages(chat_id, query.message.id)
        await app.send_message(chat_id, text="برای حذف متن روی آن کلیک کنید", reply_markup=inline_keyboard)


# email part
@app.on_callback_query(filters.regex("delete_emails"))
async def delete_emails(Client, query):
    with open('emails.txt', 'w') as existing_file:
        existing_file.write('')
    await app.answer_callback_query(
        query.id,
        text="همه ایمیل ها پاک شد.",
        show_alert=True
    )


@app.on_callback_query(filters.regex("add_email"))
async def add_email(Client, query):
    global ADD_EMAIL
    ADD_EMAIL = True
    chat_id = query.message.chat.id
    chat = query.message.chat
    inline_buttons = [
        [InlineKeyboardButton("بازگشت", callback_data="back_to_admin")],
    ]
    inline_keyboard = InlineKeyboardMarkup(inline_buttons)
    await app.delete_messages(chat_id, query.message.id)
    msg = await chat.ask(text='فایل txt ایمیل خود را بفرستید.  ', reply_markup=inline_keyboard)
    if ADD_EMAIL:
        try:
            file_path = await app.download_media(msg.document.file_id, msg.document.file_name)
            with open(file_path, 'r') as downloaded_file:
                downloaded_content = downloaded_file.read()

            with open('emails.txt', 'a') as existing_file:
                existing_file.write('\n')
                existing_file.write(downloaded_content)
            await app.send_message(chat_id, text='ایمیل ها با موفقیت اظافه شد.')

        except:
            await app.send_message(chat_id, text='خطا')


    else:
        pass


@app.on_callback_query(filters.regex("email_count"))
async def email_count(Client, query):
    try:
        with open('emails.txt', 'r') as file:
            lines = file.readlines()
            line_count = len(lines)
            word_count = sum(len(line.split()) for line in lines)
        await query.answer(f' تعداد ایمیل ها  {word_count} ', show_alert=True)
    except:
        await query.answer('خطلا', show_alert=True)





def b64encode(value):
    return base64.b64encode(value).decode('utf-8')


# Set up Jinja2 environment
current_dir = os.path.dirname(__file__)
template_dir = current_dir
env = Environment(loader=FileSystemLoader(template_dir))
env.filters['b64encode'] = b64encode

# Load the HTML template
template = env.get_template('template.html')


# @app.on_callback_query(filters.regex("send_email"))
# async def email_count(Client, query):
#     global running, canceled, pause_event
#     chat_id = query.message.chat.id
#     running = True
#     canceled = False
#     pause_event.set()
#     inline_buttons = [
#         [InlineKeyboardButton("توقف", callback_data="stop")],
#         [InlineKeyboardButton("از سر گیری", callback_data="resume")],
#         [InlineKeyboardButton("لغو کردن", callback_data="cancel")],
#     ]
#     inline_keyboard = InlineKeyboardMarkup(inline_buttons)
#
#     # Query the database for messages and photos
#     allMessages = session.query(Messages).all()
#     allPhotos = session.query(Photos).all()
#
#     # Generate unique CIDs for each photo and prepare the context for the template
#     photos_with_cid = [{'id': photo.id, 'photo': photo.photo, 'cid': make_msgid()[1:-1]} for photo in allPhotos]
#     context = {
#         'messages': allMessages,
#         'photos': photos_with_cid
#     }
#
#     try:
#         sent_message = await app.send_message(chat_id, text='فرستادن ایمیل شروع شد : 0', reply_markup=inline_keyboard)
#
#         # Open the email file and process its content
#         with open('emails.txt', 'r') as file:
#             lines = file.readlines()
#
#             for count, line in enumerate(lines, start=1):
#                 await pause_event.wait()
#                 if not running or canceled:
#                     break
#
#                 try:
#                     msg = MIMEMultipart()
#                     msg['From'] = EMAIL_USER
#                     msg['To'] = line.strip()
#                     msg['Subject'] = 'Test Email with Messages and Photos'
#
#                     to_email = line.strip()
#
#                     # Render HTML content with context data
#                     html_content = template.render(context)
#
#                     msg_alternative = MIMEMultipart('alternative')
#                     msg.attach(msg_alternative)
#                     msg_alternative.attach(MIMEText(html_content, 'html'))
#
#                     # Attach each photo with the corresponding CID
#                     for photo in photos_with_cid:
#                         image = MIMEImage(photo['photo'], name=f'image_{photo["id"]}.jpg')
#                         image.add_header('Content-ID', f'<{photo["cid"]}>')
#                         msg.attach(image)
#
#                     with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
#                         server.starttls()
#                         server.login(EMAIL_USER, EMAIL_PASSWORD)
#                         server.sendmail(EMAIL_USER, to_email, msg.as_string())
#
#                     await sent_message.edit_text(f"فرستادن ایمیل شروع شد : {count}", reply_markup=inline_keyboard)
#                 except Exception as e:
#                     print(e)
#                     pass
#
#             if canceled:
#                 await app.send_message(chat_id, text='ارسال پیام لغو شد.')
#             elif running:
#                 await app.send_message(chat_id, text='به همه ایمیل‌ها پیام فرستاده شد.')
#             else:
#                 await app.send_message(chat_id, text='پروسه متوقف شد.')
#     except Exception as e:
#         print(e)
#         pass
#
#




@app.on_callback_query(filters.regex("send_email"))
async def email_count(Client, query):
    global running, canceled, pause_event
    chat_id = query.message.chat.id
    running = True
    canceled = False
    pause_event.set()
    inline_buttons = [
        [InlineKeyboardButton("توقف", callback_data="stop")],
        [InlineKeyboardButton("از سر گیری", callback_data="resume")],
        [InlineKeyboardButton("لغو کردن", callback_data="cancel")],
        [InlineKeyboardButton("بازگشت ", callback_data="back_to_admin")],
    ]
    inline_keyboard = InlineKeyboardMarkup(inline_buttons)

    allMessages = session.query(Messages).all()
    allPhotos = session.query(Photos).all()

    photos_with_cid = [{'id': photo.id,
                        'photo': photo.photo,
                        'cid': make_msgid()[1:-1],
                        'title': message.title,
                        'message': message.message} for
                       photo, message in zip(allPhotos, allMessages)]
    context = {
        'photos': photos_with_cid
    }

    try:
        # sent_message = await app.send_message(chat_id, text='فرستادن ایمیل شروع شد : 0', reply_markup=inline_keyboard)
        sent_message = await app.edit_message_text(chat_id,query.message.id, text='فرستادن ایمیل شروع شد : 0', reply_markup=inline_keyboard)

        with open('emails.txt', 'r+') as file:
            lines = file.readlines()

            # Render HTML content with context data outside the loop
            html_content = template.render(context)

            for count, line in enumerate(lines, start=1):
                await pause_event.wait()
                if not running or canceled:
                    break

                try:
                    msg = MIMEMultipart()
                    msg['From'] = EMAIL_USER
                    msg['To'] = line.strip()
                    msg['Subject'] = 'Test Email with Messages and Photos'

                    to_email = line.strip()

                    msg_alternative = MIMEMultipart('alternative')
                    msg.attach(msg_alternative)
                    msg_alternative.attach(MIMEText(html_content, 'html'))

                    # Attach each photo with the corresponding CID
                    for photo in photos_with_cid:
                        image = MIMEImage(photo['photo'], name=f'image_{photo["id"]}.jpg')
                        image.add_header('Content-ID', f'<{photo["cid"]}>')
                        msg.attach(image)

                    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                        server.starttls()
                        server.login(EMAIL_USER, EMAIL_PASSWORD)
                        server.sendmail(EMAIL_USER, to_email, msg.as_string())

                    await sent_message.edit_text(f"فرستادن ایمیل شروع شد : {count}", reply_markup=inline_keyboard)
                except Exception as e:
                    print(e)
                    pass

                file.seek(0)
                file.writelines(lines[1:])
                file.truncate()
                lines = lines[1:]


            if canceled:
                await app.send_message(chat_id, text='ارسال پیام لغو شد.')
            elif running:
                await app.send_message(chat_id, text='به همه ایمیل‌ها پیام فرستاده شد.')
            else:
                await app.send_message(chat_id, text='پروسه متوقف شد.')
    except Exception as e:
        print(e)
        await query.answer('ایمیلی برای ارسال وجود ندارد.',show_alert=True)


@app.on_callback_query(filters.regex("cancel"))
async def cancel_timer(client, callback_query):
    global running, canceled, pause_event
    running = False
    canceled = True
    pause_event.clear()
    await callback_query.answer("فرستادن پیام لغو شد.")
    await callback_query.message.edit_reply_markup(None)


@app.on_callback_query(filters.regex("stop"))
async def stop_timer(client, callback_query):
    global running, pause_event
    running = False
    pause_event.clear()
    await callback_query.answer("پروسه متوقف شد.")


@app.on_callback_query(filters.regex("resume"))
async def resume_timer(client, callback_query):
    global running, pause_event
    running = True
    pause_event.set()  # Set the event to resume the loop
    await callback_query.answer(" در حال ارسال پیام ...")


# back button
@app.on_callback_query(filters.regex("back_to_admin"))
async def back_to_admin(Client, query):
    global ADD_TEXT
    global ADD_EMAIL
    global ADD_PHOTO
    global LAGHV_ADD_ADMIN
    global running, canceled, pause_event
    ADD_TEXT = False
    ADD_EMAIL = False
    ADD_PHOTO = False
    LAGHV_ADD_ADMIN = False
    running = False
    canceled = True
    pause_event.clear()
    chat_id = query.message.chat.id
    await app.delete_messages(chat_id, query.message.id)
    await Home(Client, query.message)


if __name__ == '__main__':
    app.run()
