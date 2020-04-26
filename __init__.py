import logging

from telegram import (Bot, ReplyKeyboardMarkup, ReplyKeyboardRemove)

from telegram.ext import (Updater, CommandHandler, MessageHandler, MessageHandler,
                          Filters, ConversationHandler, CallbackQueryHandler)

from SQLbase import (DB, Create, Insert, Queries, Upgrade, Delete)

from datetime import datetime

from bitmexHandler import BitmexRefChecker, BitmexParser

from config import (TG_TOKEN, main_keyboard, ref_keyboard, ref_link, balance_choice_keyboard,
                    withdraw_keyboard, cashout_keyboard, withdraw_via_keyboard, wallet_keyboard,
                    read_wallet_keyboard, confirm_output_keyboard, back_to_main_keyboard,
                    admin_id1, admin_id2, admin_id3, admin_keyboard, admin_clearing_keyboard,
                    withdraw_via_code_keyboard, bonuses_keyboard, list_bonuses_keyboard,
                    hello_bonus_keyboard, chat_id1, chat_id2, back_keyboard,
                    cashback_choice_keyboard, exchanges_keyboard, cashback_bitmex_keyboard,
                    cashback_bitmex_confirmation_keyboard,
                    number_of_rvb_for_one_referral, first_menu_keyboard,
                    link_to_instruction, rvb_for_hello_bonus,
                    about_us_keyboard, minimum_cashout_wallet_btc, minimum_cashout_exchange_btc,
                    balance_choice_keyboard_with_exist_withdraw)

from dateutil.tz import tzutc

# Enable logging
logging.basicConfig (format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

logger = logging.getLogger (__name__)

FIRST_MAIN, MAIN = range (2)

REF, GET_REF_LINK = range (2, 4)

BALANCE, WITHDRAW, WALLET, READ_WALLET, EXCHANGE, \
EXCHANGE_AMOUNT, ACTION_CONFIRMATION, CONFIRMED, DENIED, \
WITHDRAW_ID, NAME_EXCHANGE, YOBIT, COINSBIT, LIVECOIN = range (4, 18)

BONUSES, LIST_BONUSES, HELLO_BONUS, CHECK_HELLO_BONUS = range (18, 22)

CASHBACK, EXCHANGES, CB_CONFIRMATION, CB_BITMEX, ID_BITMEX, ID_PROCESSING, \
SECRET_BITMEX, CONFIRM_BITMEX = range (22, 30)

ABOUT_US = range (30, 31)
ADMIN, CLEARING = range (31, 33)


# common functions
def conversion_from_satoshi_to_btc(amount_satoshi):
    try:
        amount_btc = float ('{:.8f}'.format (amount_satoshi / 100000000))
    except:
        return 0
    return amount_btc


def token_balance_update(update):
    DB.start()
    tg_id = update.message.from_user.id
    old_num_referrals_with_hb = Queries.get_num_referrals_from_db(tg_id)
    current_num_referrals_with_hb = Queries.get_current_num_referrals_with_hello_bonus(tg_id)
    delta_num_referrals_with_hb = current_num_referrals_with_hb - old_num_referrals_with_hb

    if delta_num_referrals_with_hb > 0:
        delta_balance_rvb = delta_num_referrals_with_hb * number_of_rvb_for_one_referral
        Upgrade.increase_balance_rvb(tg_id, delta_balance_rvb)
        Upgrade.increase_balance_rvb_for_referrals(tg_id, delta_balance_rvb)
        Upgrade.rewrite_num_referrals(tg_id, current_num_referrals_with_hb)
    DB.stop()


def back_to_main(update, context):
    return start (update, context)


# MAIN beginning
def start(update, context):
    tg_id = update.message.from_user.id
    words = update.message.text.split ()
    DB.start ()
    if not Queries.user_exist(tg_id):
        username = update.message.from_user.link
        id_inviter = None
        if len (words) == 2 and int (words[1]) != tg_id:
            id_inviter = int (words[1])
        Insert.add_user(tg_id, id_inviter, username=username)

        DB.stop ()
        update.message.reply_text ("<b>ReverseBTC</b> – сервис, позволяющий возвращать "
                                   "часть торговой комиссии со сделок на криптовалютных биржах.\n\n"
                                   "Краткий <a href='https://medium.com/@reversebtc/%D0%BA%D1%80%D0%B0%D1%82%D0%BA%D0"
                                   "%B8%D0%B9-%D0%B3%D0%B0%D0%B9%D0%B4-%D0%BF%D0%BE-%D1%81%D0%B5%D1%80%D0%B2%D"
                                   "0%B8%D1%81%D1%83-reversebtc-4b49322d4e4e?post"
                                   "PublishedType=initial'> гайд </a> по использованию сервиса\n\n"
                                   "<b>Продолжая использование сервиса, вы подтверждаете, что вы ознакомились "
                                   "с полым содержанием Пользовательского соглашения, а также "
                                   "согласны со всеми условиями и требованиями, которые в нём упоминаются.</b>",
                                   parse_mode="HTML",
                                   reply_markup=ReplyKeyboardMarkup (first_menu_keyboard,
                                                                     resize_keyboard=True),
                                   disable_web_page_preview=True)

        return FIRST_MAIN

    update.message.reply_text ('Приветствуем вас в главном меню сервиса *reverseBTC*!',
                               parse_mode="Markdown",
                               reply_markup=ReplyKeyboardMarkup (main_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    return MAIN


def first_main_terms_of_use(update, context):
    doc = open('terms_of_use.docx', 'rb')
    update.message.reply_document(doc)
    return FIRST_MAIN
# MAIN ending


# REF beginning
def ref_choice(update, context):
    token_balance_update(update)
    DB.start ()
    tg_id = update.message.from_user.id
    ref_message = 'Мы предоставляем выгодную партнерскую программу: ' \
                  'за каждого реферала, получившего приветственный бонус, ' \
                  'вам будет начислено *{num_for_one} RVB*! \n\n' \
                  '*Всего рефералов: *{num_ref}\n' \
                  '*Рефералов, получивших приветственный бонус: *{num_ref_with_hello_bonus}\n' \
                  '*Начислено за рефералов: *{balance_rvb} RVB\n' \
                  ''.format (num_for_one=number_of_rvb_for_one_referral,
                             num_ref=Queries.get_current_num_referrals(tg_id),
                             num_ref_with_hello_bonus=Queries.get_current_num_referrals_with_hello_bonus (tg_id),
                             balance_rvb=Queries.get_balance_rvb_for_referrals(tg_id))

    update.message.reply_text (ref_message,
                               parse_mode="Markdown",
                               reply_markup=ReplyKeyboardMarkup (ref_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    DB.stop ()

    return REF


def get_referral_link(update, context):
    update.message.reply_text ('*Ваша партнёрская ссылка*', parse_mode="Markdown")
    tg_id = update.message.from_user.id
    update.message.reply_text ('{ref_link}'.format (ref_link=ref_link.format (tg_id)),
                               parse_mode="Markdown",
                               reply_markup=ReplyKeyboardMarkup (back_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    return GET_REF_LINK
# REF ending


# BONUSES beginning
def bonuses_choice(update, context):
    bonuses_message = "Бонусы - это уникальная возможность " \
                      "бесплатно получить криптовалюту *RVB*, " \
                      "потратив немного своего времени!"
    update.message.reply_text (bonuses_message,
                               parse_mode="Markdown",
                               reply_markup=ReplyKeyboardMarkup (bonuses_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    return BONUSES


def list_bonuses(update, context):
    update.message.reply_text ("Пожалуйста, выберите на клавиатуре один из бонусов",
                               reply_markup=ReplyKeyboardMarkup (list_bonuses_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    return LIST_BONUSES


def hello_bonus(update, context):
    tg_id = update.message.from_user.id
    DB.start ()
    if not Queries.received_hello_bonus (tg_id):
        hello_bonus_message = "Вы выбрали Приветственный бонус! " \
                              "После получения бонуса на ваш баланс " \
                              "будет автоматически начислено *{num} RVB*. " \
                              "Для получения бонуса необходимо подписаться " \
                              "на наши каналы:\n\n" \
                              "1. @reversebtc - *Новости нашего проекта*\n\n" \
                              "2. @reversebtc\_news - *Новости из мира криптовалют*".format (num=rvb_for_hello_bonus)
        update.message.reply_text (hello_bonus_message,
                                   parse_mode="Markdown",
                                   reply_markup=ReplyKeyboardMarkup (hello_bonus_keyboard,
                                                                     resize_keyboard=True,
                                                                     one_time_keyboard=True))
    else:
        update.message.reply_text ("Извините, но вы уже получили Приветственный бонус!",
                                   reply_markup=ReplyKeyboardMarkup (back_keyboard,
                                                                     resize_keyboard=True,
                                                                     one_time_keyboard=True))
    DB.stop ()
    return HELLO_BONUS


def check_hello_bonus(update, context):
    global is_first, is_second
    tg_id = update.message.from_user.id
    bot = Bot (TG_TOKEN)
    try:
        is_first = False
        is_second = False
        first = bot.get_chat_member(chat_id1, tg_id).status
        second = bot.get_chat_member (chat_id2, tg_id).status
        if first == "member" or first == "administrator" or first == "creator":
            is_first = True
        if second == "member" or second == "administrator" or second == "creator":
            is_second = True
    except:
        pass

    if is_first and is_second:
        DB.start()
        Upgrade.set_to_true_received_hello_bonus(tg_id)
        Upgrade.increase_balance_rvb (tg_id, rvb_for_hello_bonus)
        DB.stop ()
        check_message = "Поздравляем! Вы выполнили все условия! " \
                        "На ваш баланс начислено *{num} RVB*" \
                        "".format (num=rvb_for_hello_bonus)
        update.message.reply_text(check_message, parse_mode="Markdown")
        return back_to_list_bonuses(update, context)

    update.message.reply_text ("Извините, но вы выполнили не все условия!",
                               parse_mode="Markdown",
                               reply_markup=ReplyKeyboardMarkup (back_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))

    return CHECK_HELLO_BONUS


def back_to_bonuses_choice(update, context):
    return bonuses_choice (update, context)


def back_to_list_bonuses(update, context):
    return list_bonuses (update, context)


def back_to_hello_bonus(update, context):
    return hello_bonus (update, context)
# BONUSES ending


# BALANCE beginning
def find_free_balance_btc(update):
    DB.start ()
    tg_id = update.message.from_user.id
    full_balance = Queries.get_balance_satoshi (tg_id)
    sum_active_cashouts_btc = Queries.sum_active_cashouts (tg_id)
    if sum_active_cashouts_btc == None:
        sum_active_cashouts_btc = 0
    free_balance_satoshi = full_balance - sum_active_cashouts_btc * 100000000
    DB.stop ()
    return free_balance_satoshi / 100000000


def balance_choice(update, context):
    token_balance_update(update)
    free_balance_btc = find_free_balance_btc(update)
    DB.start()
    tg_id = update.message.from_user.id
    balance_out = Queries.sum_active_cashouts(tg_id)
    if balance_out == None:
        balance_out = 0
    balance_message = '*У вас*: {rvb_balance} RVB\n' \
                      '*Свободный баланс*: {balance} BTC\n' \
                      '*Баланс на вывод*: {balance_out} BTC'.format (rvb_balance=Queries.get_balance_rvb(tg_id),
                                                                     balance=format (free_balance_btc, ".8f"),
                                                                     balance_out=balance_out)
    if Queries.get_sum_all_cashouts(tg_id) != None:
        update.message.reply_text (balance_message,
                                   parse_mode="Markdown",
                                   reply_markup=ReplyKeyboardMarkup (balance_choice_keyboard_with_exist_withdraw,
                                                                     resize_keyboard=True,
                                                                     one_time_keyboard=True))
    else:
        update.message.reply_text (balance_message,
                                   parse_mode="Markdown",
                                   reply_markup=ReplyKeyboardMarkup (balance_choice_keyboard,
                                                                     resize_keyboard=True,
                                                                     one_time_keyboard=True))
    DB.stop ()
    return BALANCE


def withdraw(update, context):
    update.message.reply_text ('Пожалуйста, выберите способ вывода',
                               parse_mode="Markdown",
                               reply_markup=ReplyKeyboardMarkup (withdraw_keyboard,
                                                                 resize_keyboard=True))
    return WITHDRAW


def withdraw_list_for_user(update, context):
    tg_id = update.message.from_user.id
    DB.start()
    if  Queries.get_sum_all_cashouts(tg_id) == None:
        DB.stop()
        return balance_choice(update, context)

    list_cashouts = Queries.get_list_all_cashouts(tg_id)
    withdraw_message = ""
    for item in list_cashouts:
        withdraw_message += "*Тип вывода*: {}\n" \
                            "*Количество средств на вывод*: {} BTC\n" \
                            "*Статус заявки*: {}\n\n".format(item[0], item[1], item[2])
    update.message.reply_text(withdraw_message,
                              parse_mode="Markdown")
    DB.stop()
    return balance_choice(update, context)


def is_positive_number(string):
    try:
        if float (string) > 0:
            return True
    except ValueError:
        return False
    return False


def withdraw_via_wallet(update, context):
    token_balance_update(update)
    free_balance_btc = find_free_balance_btc(update)
    balance_message = '*Свободный баланс*: {balance} BTC\n' \
                      '*Минимальная сумма вывода* ' \
                      ': {min_cashout} BTC.\n' \
                      'Пожалуйста, введите сумму, ' \
                      'которую вы хотели бы вывести'.format (balance=format (free_balance_btc, ".8f"),
                                                             min_cashout=minimum_cashout_wallet_btc)
    update.message.reply_text (balance_message,
                               parse_mode="Markdown",
                               reply_markup=ReplyKeyboardMarkup (withdraw_via_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    return WALLET


def via_wallet_confirmation(update, context):
    update.message.reply_text ("Происходит обработка запроса",
                               reply_markup=ReplyKeyboardMarkup (withdraw_via_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    tg_id = update.message.from_user.id
    splited = update.message.text.split ()
    free_balance_btc = find_free_balance_btc(update)
    if len (splited) == 1 and is_positive_number (splited[0]) and float (splited[0]) >= minimum_cashout_wallet_btc:
        wallet_amount = float (splited[0])
        if wallet_amount > free_balance_btc:
            update.message.reply_text ("Извините, на вашем счёте недостаточно средств!")
            return withdraw (update, context)
        else:
            update.message.reply_text ("Заявка почти сформирована. Пожалуйста, введите теперь свой биткоин кошелек")
            DB.start ()
            username = Queries.get_username(tg_id)
            withdraw_id = Insert.add_withdraw (tg_id, wallet_amount, "wallet", username)
            context.user_data[WITHDRAW_ID] = withdraw_id
            DB.stop ()
            return READ_WALLET
    else:
        update.message.reply_text ("Извините, но вы ввели некорректные данные!")
        return withdraw (update, context)


def read_wallet(update, context):
    DB.start ()
    withdraw_id = context.user_data[WITHDRAW_ID]
    amount_out = Queries.amount_withdraw (withdraw_id)
    splited = update.message.text.split()
    btc_wallet = splited[0]
    Upgrade.add_btc_wallet_to_withdraw(withdraw_id, btc_wallet)
    DB.stop ()
    confirm_message = "Пожалуйста, перепроверьте введенные данные! " \
                      "Учтите, отменить это действие будет невозможно!\n\n" \
                      "Вы хотите вывести: {amount_withdraw} BTC\n" \
                      "На кошелёк: {btc_wallet}".format (amount_withdraw=amount_out,
                                                         btc_wallet=btc_wallet)
    update.message.reply_text (confirm_message,
                               parse_mode="Markdown",
                               reply_markup=ReplyKeyboardMarkup (confirm_output_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    return ACTION_CONFIRMATION


def cashout_confirmed(update, context):
    update.message.reply_text ("Ваша заявка на вывод была создана! "
                               "Обычно заявки обрабатываются не более 24 часов с момента её создания. "
                               "Если вам не пришли средства в течение 24 часов, "
                               "пожалуйста, напишите в нашу службу поддержки!",
                               parse_mode="Markdown",
                               reply_markup=ReplyKeyboardMarkup (back_to_main_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    return CONFIRMED


def cashout_denied(update, context):
    tg_id = update.message.from_user.id
    DB.start()
    Delete.del_last_withdraw_user(tg_id)
    DB.stop ()
    update.message.reply_text ("Вы отменили свою заявку на вывод.\n",
                               parse_mode="Markdown",
                               reply_markup=ReplyKeyboardMarkup (back_to_main_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    return DENIED


def withdraw_via_code(update, context):
    token_balance_update(update)
    free_balance_btc = find_free_balance_btc(update)
    withdraw_via_code_message = "Вы выбрали вывод с помощью кода. " \
                                "Обратите внимание, что для вывода с помощью кода " \
                                "вам необохдимо иметь Telegram юзернейм. Например: [@ivan_ivanov]\n" \
                                "Иначе при попытке вывести средства, вы получите сообщение об ошибке.\n" \
                                "Также настоятельно рекомендуем вам не менять юзернейм, " \
                                "пока происходят все проверки и передача вам вашего кода! " \
                                "В противном случае вы рискуете тем, что код до вас не дойдёт! \n" \
                                "За потерю средств в этом случае мы ответственности не несём! \n\n" \
                                "*Свободный баланс*: {free_balance} BTC\n\n" \
                                "*Минимальная сумма вывода*: {min_cashout} BTC\n\n" \
                                "Пожалуйста, выберите биржу".format (free_balance=format (free_balance_btc, ".8f"),
                                                                     min_cashout=minimum_cashout_exchange_btc)

    update.message.reply_text (withdraw_via_code_message,
                               parse_mode="Markdown",
                               reply_markup=ReplyKeyboardMarkup (withdraw_via_code_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    return EXCHANGE


def yobit(update, context):
    context.user_data[NAME_EXCHANGE] = YOBIT
    return exchange_read_amount (update, context)


def coinsbit(update, context):
    context.user_data[NAME_EXCHANGE] = COINSBIT
    return exchange_read_amount (update, context)


def livecoin(update, context):
    context.user_data[NAME_EXCHANGE] = LIVECOIN
    return exchange_read_amount (update, context)


def exchange_read_amount(update, context):
    free_balance_btc = find_free_balance_btc(update)
    balance_message = 'Пожалуйста, введите сумму, которую вы хотели бы вывести. \n' \
                      '*Ваш свободный баланс составляет*: {balance} BTC\n' \
                      '*Минимальная сумма вывода на биржу составляет*: {min_cashout} BTC. \n' \
                      'Пожалуйста, введите сумму!'.format (balance=format (free_balance_btc, ".8f"),
                                                           min_cashout=minimum_cashout_exchange_btc)

    update.message.reply_text (balance_message,
                               parse_mode="Markdown",
                               reply_markup=ReplyKeyboardMarkup (withdraw_via_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    return EXCHANGE_AMOUNT


def exchange_amount_confirmation(update, context):
    update.message.reply_text ("Происходит обработка запроса",
                               reply_markup=ReplyKeyboardMarkup (withdraw_via_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    DB.start ()
    tg_id = update.message.from_user.id
    amount = update.message.text
    DB.stop ()
    free_balance_btc = find_free_balance_btc(update)
    if is_positive_number (amount) and float (amount) >= minimum_cashout_exchange_btc:
        wallet_amount = float (amount)
        if wallet_amount > free_balance_btc:
            update.message.reply_text ("Извините, на вашем счёте недостаточно средств!")
            return withdraw (update, context)
        else:
            username = update.message.from_user.username
            if username == None:
                update.message.reply_text ("Извините, но у вас нет юзернейма! "
                                           "Пожалуйста, добавьте Telegram юзернейм "
                                           "и попробуйте снова",
                                           parse_mode="Markdown",
                                           reply_markup=ReplyKeyboardMarkup (back_to_main_keyboard,
                                                                             resize_keyboard=True,
                                                                             one_time_keyboard=True))
                return DENIED

            update.message.reply_text ("Заявка почти сформирована. Вам осталось лишь сверить введенные данные")
            DB.start ()

            name_exchange = "-"
            exchange_id = context.user_data.get (NAME_EXCHANGE)
            del context.user_data[NAME_EXCHANGE]

            if exchange_id == COINSBIT:
                name_exchange = "Coinsbit"
            elif exchange_id == LIVECOIN:
                name_exchange = "Livecoin"
            elif exchange_id == YOBIT:
                name_exchange = "Yobit"

            Insert.add_withdraw (tg_id, wallet_amount, name_exchange, username)
            DB.stop ()
            confirm_message = "*Вы хотите вывести*: {amount_withdraw} BTC\n" \
                              "*Кодом на биржу*: {name_exchange} \n" \
                              "*Код придёт на*: @{username} \n" \
                              "Отменить это действие будет невозможно!" \
                              "".format (amount_withdraw=wallet_amount,
                                         name_exchange=name_exchange,
                                         username=username)

            update.message.reply_text (confirm_message,
                                       parse_mode="Markdown",
                                       reply_markup=ReplyKeyboardMarkup (confirm_output_keyboard,
                                                                         resize_keyboard=True,
                                                                         one_time_keyboard=True))

            return ACTION_CONFIRMATION
    else:
        update.message.reply_text ("Извините, но вы ввели некорректные данные")
        return withdraw (update, context)


def back_to_balance(update, context):
    return balance_choice (update, context)


def back_to_withdraw_with_delete_last(update, context):
    tg_id = update.message.from_user.id
    DB.start ()
    Delete.del_last_withdraw_user(tg_id)
    DB.stop ()
    return withdraw (update, context)

def back_to_withdraw_without_delete_last(update, context):
    return withdraw (update, context)
# BALANCE ending


# CASHBACK beginning
def confirm_bitmex(update, context):
    try:
        api_key = context.user_data[ID_BITMEX]
        api_secret = context.user_data[SECRET_BITMEX]
        del context.user_data[ID_BITMEX]
        del context.user_data[SECRET_BITMEX]
        current_date = datetime.now (tz=tzutc ())
        conf_message = "Извините, но похоже, что вы не наш реферал, " \
                       "попробуйте ввести данные снова! " \
                       "Если проблема повторилась, " \
                       "пожалуйста, обратитесь в службу поддержки!"
        brc = BitmexRefChecker (api_key, api_secret)
        id_bitmex = brc.get_id ()
        DB.start ()
        if id_bitmex == None:
            conf_message = "Извините, но нам не удалось подключиться к Bitmex. " \
                           "Попробуйте ввести данные снова\n\n" \
                           "Если проблема повторилась, " \
                           "пожалуйста, обратитесь в службу поддержки!"
        elif Queries.check_id_bitmex(id_bitmex):
            conf_message = "Извините, но этот аккаунт Bitmex уже зарегистрирован!"
        elif brc.is_referral ():
            conf_message = "Поздравляем! Теперь вы участвуете в программе кешбека. " \
                           "Начисления на баланс производятся каждые 48 часов."
            tg_id = update.message.from_user.id
            exchange_id = Queries.get_bitmex_exchange_id ()
            email = None
            Insert.add_record (tg_id, exchange_id, email, api_key, api_secret, current_date, id_bitmex)
        DB.stop ()

        update.message.reply_text (conf_message,
                                   parse_mode="Markdown",
                                   reply_markup=ReplyKeyboardMarkup (back_keyboard,
                                                                     resize_keyboard=True,
                                                                     one_time_keyboard=True))
    except:
        update.message.reply_text ("Извините, но вы не ввели Secret или ID",
                                   parse_mode="Markdown",
                                   reply_markup=ReplyKeyboardMarkup (back_keyboard,
                                                                     resize_keyboard=True,
                                                                     one_time_keyboard=True))

    return CONFIRM_BITMEX


def cashback_choice(update, context):
    cashback_message = "Мы предоставляем пользователям нашего сервиса уникальную возможность – " \
                       "регистрируйтесь на биржах по нашим реферальным ссылкам и получайте кешбек " \
                       "в размере 80% от реферальных комиссионных. " \
                       "Политика некоторых бирж, например Bitmex, позволяет иметь несколько биржевых аккаунтов. " \
                       "Это значит, что даже если вы были зарегистрированы на Bitmex прежде, " \
                       "у вас всё равно есть возможность создать новый аккаунт и получать кешбек от нашего бота."


    update.message.reply_text (cashback_message,
                               parse_mode="Markdown",
                               reply_markup=ReplyKeyboardMarkup (cashback_choice_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    return CASHBACK

def exchanges(update, context):
    exchanges_message = "Пожалуйста, выберите биржу, на которой хотите получать кешбэк"
    update.message.reply_text (exchanges_message,
                               parse_mode="Markdown",
                               reply_markup=ReplyKeyboardMarkup (exchanges_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    return EXCHANGES


def cashback_bitmex_confirmation(update, context):
    cb_conf = "<a href='https://www.bitmex.com/app/terms'>Условия предоставления услуг биржи Bitmex</a> \n" \
              "разрешают регистрацию и использование нескольких учетных записей одним лицом. " \
              "Это значит, что вы имеете право на регистрацию нового аккаунта и использование его в любых целях, " \
              "в том числе и для получения кешбэка. " \
              "Для получения кешбэка зарегистрируйте аккаунт по нашей реферальной ссылке \n" \
              "https://www.bitmex.com/register/9m1ZRQ \n" \
              "затем нажмите на кнопку ниже"

    update.message.reply_text (cb_conf,
                               parse_mode="HTML",
                               reply_markup=ReplyKeyboardMarkup (cashback_bitmex_confirmation_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    return CB_CONFIRMATION


def cashback_bitmex(update, context):
    cb_bx_message = "Для отслеживания вашего торгового оборота нам потребуется API " \
                    "без права на торговлю и вывод средств. \n" \
                    "<a href='{link}'>Инструкция как получить API</a>\n" \
                    "".format (link=link_to_instruction)
    update.message.reply_text (cb_bx_message,
                               parse_mode="HTML",
                               reply_markup=ReplyKeyboardMarkup (cashback_bitmex_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True),
                               disable_web_page_preview=True)
    return CB_BITMEX


def starting_add_new_api(update, context):
    id_message = "Пожалуйста, введите ID"
    update.message.reply_text (id_message,
                               parse_mode="Markdown",
                               reply_markup=ReplyKeyboardMarkup (back_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    return ID_BITMEX


def id_bitmex_processing(update, context):
    splited_text = update.message.text.split()
    if len (splited_text) != 1 or len(splited_text[0]) != 24:
        return back_to_bitmex(update, context, 'id')

    context.user_data[ID_BITMEX] = splited_text[0]
    message = "вам осталось ввести лишь Secret!"
    update.message.reply_text (message,
                               parse_mode="Markdown",
                               reply_markup=ReplyKeyboardMarkup (back_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True))
    return ID_PROCESSING


def secret_bitmex_processing(update, context):
    splited_text = update.message.text.split()
    if len (splited_text) != 1 or len(splited_text[0]) != 48:
        return back_to_bitmex(update, context, 'secret')
    context.user_data[SECRET_BITMEX] = splited_text[0]
    message = "Пожалуйста, ожидайте! Мы обрабатываем ваш запрос!"
    update.message.reply_text(message)
    return confirm_bitmex(update, context)


def back_to_cashback(update, context):
    return cashback_choice (update, context)


def back_to_exchanges(update, context):
    return exchanges (update, context)


def back_to_bitmex(update, context, where_did_it_come_from=''):
    if where_did_it_come_from == 'secret':
        update.message.reply_text ("Вы ввели некорректный SECRET! Пожалуйста, перепроверьте данные и "
                                   "попробуйте ввести их снова.\n\n"
                                   "Если ошибка повторилась, пожалуйста, "
                                   "обратитесь в службу поддержки")
    if where_did_it_come_from == 'id':
        update.message.reply_text ("Вы ввели некорректное ID! Пожалуйста, перепроверьте данные и "
                                   "попробуйте ввести их снова.\n\n" 
                                   "Если ошибка повторилась, пожалуйста, "
                                   "обратитесь в службу поддержки")
    return cashback_bitmex (update, context)
# CASHBACK ending


# ABOUT US beginning
def about_us_choice(update, context):

    about_us_message = '<b>ReverseBTC</b> – сервис, позволяющий возвращать часть торговой комиссии. \n\n' \
                       'Краткий <a href="https://medium.com/@reversebtc/%D0%BA%D1%80%D0%B0%D1%82' \
                       '%D0%BA%D0%B8%D0%B9-%D0%B3%D0%B0%D0%B9%D0%B4-%D0%BF%D0%BE-' \
                       '%D1%81%D0%B5%D1%80%D0%B2%D0%B8%D1%81%D1%83-reversebtc-4b49322d4e4e?' \
                       'postPublishedType=initial">гайд</a>' \
                       ' по использованию \n\n' \
                       '<b>Новости проекта:</b> @reversebtc \n' \
                       '<b>Чат проекта:</b> @reversebtc_chat \n' \
                       '<b>Новости из мира криптовалют:</b> @reversebtc_news \n' \
                       '<b>Поддержка:</b> @reversebtc_admin' \

    update.message.reply_text (about_us_message,
                               parse_mode="HTML",
                               reply_markup=ReplyKeyboardMarkup (about_us_keyboard,
                                                                 resize_keyboard=True,
                                                                 one_time_keyboard=True),
                               disable_web_page_preview=True)
    return ABOUT_US


def terms_of_use_from_about_us(update, context):
    doc = open ('terms_of_use.docx', 'rb')
    update.message.reply_document (doc,
                                   reply_markup=ReplyKeyboardMarkup (about_us_keyboard,
                                                                     resize_keyboard=True,
                                                                     one_time_keyboard=True)
                                   )
    return ABOUT_US
# ABOUT US ending


# ADMIN beginning
def admin(update, context):
    tg_id = update.message.from_user.id
    if tg_id == admin_id1 or tg_id == admin_id2 or tg_id == admin_id3:
        doc = open ('bot_base.db', 'rb')
        update.message.reply_document (doc)
        update.message.reply_text ("Здравствуйте, Повелитель.\n"
                                   "Вы что-то хотели?",
                                   reply_markup=ReplyKeyboardMarkup (admin_keyboard,
                                                                     resize_keyboard=True))
        return ADMIN
    else:
        return start (update, context)


def admin_upgrade_balances(update, context):
    DB.start ()
    records = Queries.get_bitmex_records ()
    DB.stop ()
    for item in records:
        ps = BitmexParser (item[0], item[1])
        ps.parse ()

    update.message.reply_text ("Готово")
    return ADMIN


def list_out(update, context):
    DB.start ()
    wd = Queries.print_withdraws ()
    sum = 0
    for item in wd:
        # need to output withdraw_id first and status last
        if item[-1] != "transferred":
            result = "{num_deal}\n" \
                     "tg_id: {tg_id}\n" \
                     "cashout size: {amount} BTC\n" \
                     "address BTC wallet: {btc_wallet}\n" \
                     "username: {username}\n" \
                     "type cashout: {type}".format(num_deal=str(item[0]),
                                                   tg_id=str(item[1]),
                                                   amount=str(item[2]),
                                                   btc_wallet=str(item[3]),
                                                   username=str(item[4]),
                                                   type=str(item[5]))
            update.message.reply_text(result,
                                      disable_web_page_preview=True)
            sum += 1
    DB.stop ()
    update.message.reply_text ("Босс, клиенты есть, их всего {} \n"
                               "Чтобы удалить сообщение нажмите реплай месседж "
                               "и введите на клавиатуре букву 'д'".format (sum),
                               parse_mode="MarkdownV2",
                               reply_markup=ReplyKeyboardMarkup (admin_clearing_keyboard,
                                                                 resize_keyboard=True))
    return CLEARING


def change_status_withdraw(update, context):
    what_should_be_done = update.message.text
    if what_should_be_done != 'д':
        return list_out (update, context)
    what_is_in_this_message = update.message.reply_to_message.text.split()
    withdraw_id = what_is_in_this_message[0]
    DB.start ()
    amount_withdraw_btc = Queries.amount_withdraw (withdraw_id)
    tg_id = Queries.user_from_withdraw (withdraw_id)
    new_balance_satoshi = Queries.get_balance_satoshi (tg_id) - amount_withdraw_btc * 100000000
    Upgrade.change_balance_satoshi(tg_id, new_balance_satoshi)
    Upgrade.change_status_withdraw_request(withdraw_id, status="transferred")
    DB.stop()
    return list_out (update, context)
# ADMIN ending


# MAIN begining
def main():
    updater = Updater (TG_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    ref_handler = ConversationHandler (
        entry_points=[MessageHandler (Filters.regex ('^Рефералы$'), ref_choice)],
        states={
            REF: [MessageHandler (Filters.regex ('^Назад$'), back_to_main),
                  MessageHandler (Filters.regex ('^Получить реферальную ссылку$'), get_referral_link)],
            GET_REF_LINK: [MessageHandler (Filters.regex ('^Назад$'), back_to_main)]
        },
        fallbacks={},
        map_to_parent={
            MAIN: MAIN
        }
    )

    balance_handler = ConversationHandler (
        entry_points=[MessageHandler (Filters.regex ('^Баланс$'), balance_choice)],
        states={
            BALANCE: [MessageHandler (Filters.regex ('^Назад$'), back_to_main),
                      MessageHandler (Filters.regex ('^История выводов$'), withdraw_list_for_user),
                      MessageHandler (Filters.regex ('^Вывести$'), withdraw)],

            WITHDRAW: [MessageHandler (Filters.regex ('^Назад$'), back_to_balance),
                       MessageHandler (Filters.regex ('^На биткоин кошелёк$'), withdraw_via_wallet),
                       MessageHandler (Filters.regex ('^Кодом на биржу$'), withdraw_via_code)],

            WALLET: [MessageHandler (Filters.regex ('^Назад$'), back_to_withdraw_without_delete_last),
                     MessageHandler (Filters.text, via_wallet_confirmation)],

            READ_WALLET: [MessageHandler (Filters.regex ('^Назад$'), back_to_withdraw_with_delete_last),
                          MessageHandler (Filters.text, read_wallet)],

            EXCHANGE: [MessageHandler (Filters.regex ('^Назад$'), back_to_withdraw_without_delete_last),
                       MessageHandler (Filters.regex ('^Yobit$'), yobit),
                       MessageHandler (Filters.regex ('^Coinsbit$'), coinsbit),
                       MessageHandler (Filters.regex ('^Livecoin$'), livecoin)],

            EXCHANGE_AMOUNT: [MessageHandler (Filters.regex ('^Назад$'), back_to_withdraw_without_delete_last),
                              MessageHandler (Filters.text, exchange_amount_confirmation)],

            ACTION_CONFIRMATION: [MessageHandler (Filters.regex ('^Нет$'), cashout_denied),
                                  MessageHandler (Filters.regex ('^Да$'), cashout_confirmed)],

            CONFIRMED: [MessageHandler (Filters.regex ('^Вернуться на главную$'), start)],

            DENIED: [MessageHandler (Filters.regex ('^Вернуться на главную$'), start)],
        },
        fallbacks={},
        map_to_parent={
            MAIN: MAIN
        }
    )

    bonuses_handler = ConversationHandler (
        entry_points=[MessageHandler (Filters.regex ('^Бонусы$'), bonuses_choice),
                      MessageHandler (Filters.regex ('^Получить приветственный бонус!$'), hello_bonus)],
        states={
            BONUSES: [MessageHandler (Filters.regex ('^Назад$'), back_to_main),
                      MessageHandler (Filters.regex ('^Список бонусов$'), list_bonuses)],

            LIST_BONUSES: [MessageHandler (Filters.regex ('^Назад$'), back_to_bonuses_choice),
                           MessageHandler (Filters.regex ('^Приветственный бонус$'), hello_bonus)],

            HELLO_BONUS: [MessageHandler (Filters.regex ('^Назад$'), back_to_list_bonuses),
                          MessageHandler (Filters.regex ('^Я выполнил условия! Получить бонус$'), check_hello_bonus)],

            CHECK_HELLO_BONUS: [MessageHandler (Filters.regex ('^Назад$'), back_to_list_bonuses),
                                MessageHandler (Filters.regex ('^Вернуться на главную$'), back_to_main)],
        },
        fallbacks={},
        map_to_parent={
            MAIN: MAIN
        }
    )

    cashback_handler = ConversationHandler (
        entry_points=[MessageHandler (Filters.regex ('^Кешбэк сервис$'), cashback_choice)],

        states={
            CASHBACK: [MessageHandler (Filters.regex ('^Назад$'), back_to_main),
                       MessageHandler (Filters.regex ('^Список доступных бирж$'), exchanges)],

            EXCHANGES: [MessageHandler (Filters.regex ('^Назад$'), back_to_cashback),
                        MessageHandler (Filters.regex ('^Bitmex$'), cashback_bitmex_confirmation)],

            CB_CONFIRMATION: [MessageHandler (Filters.regex ('^Назад$'), back_to_exchanges),
                              MessageHandler (Filters.regex ('^Зарегистрировал$'), cashback_bitmex)],

            CB_BITMEX: [MessageHandler (Filters.regex ('^Назад$'), back_to_exchanges),
                        MessageHandler (Filters.regex ('^Добавить свой API в базу$'), starting_add_new_api)],

            ID_BITMEX: [MessageHandler (Filters.regex ('^Назад$'), back_to_bitmex),
                        MessageHandler (Filters.text, id_bitmex_processing)],

            ID_PROCESSING: [MessageHandler (Filters.regex ('^Назад$'), back_to_bitmex),
                            MessageHandler (Filters.text, secret_bitmex_processing)],

            CONFIRM_BITMEX: [MessageHandler (Filters.regex ('^Назад$'), back_to_bitmex)],
        },
        fallbacks={},
        map_to_parent={
            MAIN: MAIN
        }
    )

    admin_handler = ConversationHandler (
        entry_points=[CommandHandler ('admin', admin)],
        states={
            ADMIN: [MessageHandler (Filters.regex ('^Назад$'), back_to_main),
                    MessageHandler (Filters.regex ('^Список на вывод$'), list_out),
                    MessageHandler (Filters.regex ('^Обновить балансы$'), admin_upgrade_balances)],

            CLEARING: [MessageHandler (Filters.reply, change_status_withdraw),
                       MessageHandler (Filters.regex ('^Назад$'), back_to_main)]
        },
        fallbacks={},
        map_to_parent={
            MAIN: MAIN
        }
    )

    about_us_handler = ConversationHandler (
        entry_points=[MessageHandler (Filters.regex ('^О проекте$'), about_us_choice)],
        states={
            ABOUT_US: [MessageHandler (Filters.regex ('^Назад$'), back_to_main),
                       MessageHandler (Filters.regex ('^Пользовательское соглашение$'), terms_of_use_from_about_us)]
        },
        fallbacks={},
        map_to_parent={
            MAIN: MAIN
        }
    )

    conv_handler = ConversationHandler (
        entry_points=[CommandHandler ('start', start)],
        states={
            FIRST_MAIN: [bonuses_handler,
                         MessageHandler (Filters.regex ('^Пропустить бонус$'), start),
                         MessageHandler (Filters.regex ('^Пользовательское соглашение$'), first_main_terms_of_use)],

            MAIN: [CommandHandler ('start', start),
                   ref_handler, balance_handler, cashback_handler,
                   admin_handler, about_us_handler, bonuses_handler],

        },
        fallbacks={},
    )

    dp.add_handler (conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle ()


if __name__ == '__main__':
    main ()
