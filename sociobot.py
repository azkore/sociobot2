import config
import logging
from telegram import *
from telegram.ext import *
from lib import *
from conversationhandler import azConversationHandler
from poll import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


START, GENDER, AGE, CITY, INFO = range(5)


def update_users(bot, update):
    user=update.message.from_user
    sql("insert or replace into users values (?, ?, ?, ?, strftime('%s', 'now'));",
            (user.id, user.first_name, user.last_name, user.username))

def active(bot, update, args):
    if(not args):
        args=['24h']
    if(len(args)<2):
        args.append('')
    active=get_soctypes(args[1], to_seconds(args[0]))
    bot.sendMessage(chat_id=update.message.chat_id, text=active, parse_mode=ParseMode.HTML)

def my(bot, update, args):
    message = update.message
    user=update.message.from_user

    if(not args):
        options = ', '.join(select("poll", "polls"))
        reply = "Возможные варианты: {}".format(options)
    else:
        poll = args[0]
        data = ' '.join(args[1:])
        reply = add_data(user.id, poll, data)

    bot.sendMessage(message.chat_id, reply, reply_to_message_id = message.message_id)

def add_data(uid, poll, data):
        maxlen = sql("select maxlen from polls where poll=?", (poll,))[0][0]
        data = data[:maxlen] if len(data) > maxlen else data
        data = data[0].upper() + data[1:]
        sql("delete from pollsdata where poll=? and uid=?", (poll, uid))
        sql("insert into pollsdata (uid, poll, data) values (?, ?, ?)",
                (uid, poll, data))
        return "ok"

def get_user_data(bot, update, args):
    message = update.message
    user=update.message.from_user

    if(not args):
        return

    reply = '\n'.join(select("users.firstname||':'|| group_concat(' '||pollsdata.poll || ' - ' || pollsdata.data)",
            "pollsdata, users where lower(users.firstname) like '%'||lower(?||'%') and users.uid=pollsdata.uid group by users.firstname",
            (args[0],) ))

    bot.sendMessage(message.chat_id, reply, reply_to_message_id = message.message_id)

def get_data(bot, update, args):
    message = update.message
    user=update.message.from_user

    if(not args):
        options = ', '.join(select("poll", "polls"))
        reply = "Возможные варианты: {}".format(options)
    else:
        poll = args[0]
        if(poll=="info"):
            return

        reply = '\n'.join(select(
            "data || '(' || count(firstname) || ')' || ': ' || group_concat(firstname)",
                "(select users.firstname as firstname, pollsdata.data"
                " from users, pollsdata where users.uid=pollsdata.uid and pollsdata.poll=?)"
                " group by data order by count(firstname) desc",
                (poll, ) ))


    bot.sendMessage(message.chat_id, reply, reply_to_message_id = message.message_id)

def find(bot, update, args):
    message = update.message
    user=update.message.from_user

    if(not args):
        return
    if(len(args[0])<3):
        reply = "нужно, как минимум, 3 символа"
    else:
        reply = '\n'.join(select("users.firstname|| ': ' || pollsdata.poll || ' - '|| pollsdata.data",
            "users, pollsdata where lower(data) like lower('%'||?||'%') and users.uid=pollsdata.uid", (' '.join(args),) ))

    bot.sendMessage(message.chat_id, reply, reply_to_message_id = message.message_id)

def find_age(bot, update, args):
    message = update.message
    user=update.message.from_user

    if(not args):
        return
    try:
        (min, max) = args[0].split('-')
    except:
        min = args[0]
        max = args[0]
    if(not min):
        min=0
    if(not max):
        max=100
    reply = '\n'.join(select("users.firstname|| ': ' || pollsdata.data",
        "pollsdata, users where poll='age' and cast(data as decimal)>=? and cast(data as decimal)<=?"
        " and users.uid=pollsdata.uid", (int(min), int(max)) ))

    bot.sendMessage(message.chat_id, reply, reply_to_message_id = message.message_id)

def ask(bot, update, args):
    message = update.message
    if(message.reply_to_message):
        message=message.reply_to_message
    user = message.from_user

    bot.conv_handler.conversations[ (message.chat_id, user.id) ] = GENDER

    print("ask CONVERSATIONS ", str(bot.conv_handler.conversations))
    reply_keyboard = [['М', 'Ж']]

    bot.sendMessage(message.chat_id,
                    text='Привет! Ответь, пожалуйста, на несколько вопросов.'
                         'Выбери /cancel чтобы не отвечать.\n\n'
                         'Какого ты пола?',
                    reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective = True),
                    reply_to_message_id = message.message_id)

    return GENDER

def gender(bot, update):
    print("gender CONVERSATIONS ", str(bot.conv_handler.conversations))
    user = update.message.from_user
    gender=update.message.text
    logger.info("Gender of %s: %s" % (user.first_name, gender))
    add_data(user.id, 'gender', gender)
    bot.sendMessage(update.message.chat_id, text='Сколько тебе лет?'
                                                 '( /skip, чтобы пропустить.)',
                                                 reply_to_message_id = update.message.message_id,
                                                 reply_markup=ForceReply(selective=True))
    return AGE

'''
#def photo(bot, update):
   user = update.message.from_user
    photo_file = bot.getFile(update.message.photo[-1].file_id)
    photo_file.download('user_photo.jpg')
    logger.info("Photo of %s: %s" % (user.first_name, 'user_photo.jpg'))
    bot.sendMessage(update.message.chat_id, text='Gorgeous! Now, send me your location please, '
                                                 'or send /skip if you don\'t want to.')

    return LOCATION
'''
'''
def skip_photo(bot, update):
    user = update.message.from_user
    logger.info("User %s did not send a photo." % user.first_name)
    bot.sendMessage(update.message.chat_id, text='I bet you look great! Now, send me your '
                                                 'location please, or send /skip.')

    return LOCATION


def location(bot, update):
    user = update.message.from_user
    user_location = update.message.location
    logger.info("Location of %s: %f / %f"
                % (user.first_name, user_location.latitude, user_location.longitude))
    bot.sendMessage(update.message.chat_id, text='Maybe I can visit you sometime! '
                                                 'At last, tell me something about yourself.')

    return BIO


def skip_location(bot, update):
    user = update.message.from_user
    logger.info("User %s did not send a location." % user.first_name)
    bot.sendMessage(update.message.chat_id, text='You seem a bit paranoid! '
                                                 'At last, tell me something about yourself.')

    return BIO
'''
def city(bot, update):
    user = update.message.from_user
    logger.info("City of %s: %s"
                % (user.first_name, update.message.text))
    add_data(user.id, 'city', update.message.text)
    bot.sendMessage(update.message.chat_id, text='Прекрасно. '
                                                 'Напиши что-нибудь о себе.'
                                                 '( /skip, чтобы пропустить.)',
                                                 reply_to_message_id = update.message.message_id,
                                                 reply_markup=ForceReply(selective=True))

    return INFO


def skip_city(bot, update):
    user = update.message.from_user
    logger.info("User %s did not send a location." % user.first_name)
    bot.sendMessage(update.message.chat_id, text='ok '
                                                 'Напиши что-нибудь о себе.'
                                                 '( /skip, чтобы пропустить.)',
                                                 reply_to_message_id = update.message.message_id,
                                                 reply_markup=ForceReply(selective=True))

    return INFO

def age(bot, update):
    user = update.message.from_user
    logger.info("Age of %s: %s"
                % (user.first_name, update.message.text))
    add_data(user.id, 'age', update.message.text)
    bot.sendMessage(update.message.chat_id,
                    text='Отлично! Какой ближайший к тебе город? '
                         '( /skip, чтобы пропустить.)',
                         reply_to_message_id = update.message.message_id,
                         reply_markup=ForceReply(selective=True))

    return CITY


def skip_age(bot, update):
    user = update.message.from_user
    logger.info("User %s did not send an age." % user.first_name)
    bot.sendMessage(update.message.chat_id,
                    text='Отлично! Какой ближайший к тебе город? '
                         '( /skip, чтобы пропустить.)',
                         reply_to_message_id = update.message.message_id,
                         reply_markup=ForceReply(selective=True))

    return CITY

def info(bot, update):
    user = update.message.from_user
    logger.info("Bio of %s: %s" % (user.first_name, update.message.text))
    add_data(user.id, 'info', update.message.text)
    bot.sendMessage(update.message.chat_id,
                    text='Спасибо!', reply_to_message_id = update.message.message_id, reply_markup=ReplyKeyboardHide(selective=True))

    return ConversationHandler.END

def skip_info(bot, update):
    user = update.message.from_user
    logger.info("User %s did not send an info." % user.first_name)
    bot.sendMessage(update.message.chat_id, text='ok',
                                                 reply_to_message_id = update.message.message_id,
                                                 reply_markup=ReplyKeyboardHide(selective=True))
    return ConversationHandler.END

def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation." % user.first_name)
    bot.sendMessage(update.message.chat_id,
                    text='ок. пропускаем вопросы.', reply_to_message_id = update.message.message_id,  reply_markup=ReplyKeyboardHide(selective=True))

    return ConversationHandler.END


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    sbot=Bot(token=config.token)
    updater = Updater(bot=sbot)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler([lambda m: True], update_users), 1)
    dispatcher.add_handler(CommandHandler('active', active, pass_args=True))
    dispatcher.add_handler(CommandHandler('my', my, pass_args=True))
    dispatcher.add_handler(CommandHandler('get', get_data, pass_args=True))
    dispatcher.add_handler(CommandHandler('sh', get_user_data, pass_args=True))
    dispatcher.add_handler(CommandHandler('search', find, pass_args=True))
    dispatcher.add_handler(CommandHandler('find', find, pass_args=True))
    dispatcher.add_handler(CommandHandler('ask', ask, pass_args=True))
    dispatcher.add_handler(CommandHandler('age', find_age, pass_args=True))

    sbot.conv_handler = azConversationHandler(
        entry_points=[CommandHandler('ask1', ask)],

        states={
            GENDER: [RegexHandler('^(М|Ж)$', gender)],
            AGE: [MessageHandler([Filters.text], age), CommandHandler('skip', skip_age)],

            CITY: [MessageHandler([Filters.text], city),
                       CommandHandler('skip', skip_city)],

            INFO: [MessageHandler([Filters.text], info),
                CommandHandler('skip', skip_info)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )


    dispatcher.add_handler(sbot.conv_handler)

    dispatcher.add_error_handler(error)

    updater.start_polling()

if __name__ == '__main__':
    main()
