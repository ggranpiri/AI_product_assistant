import logging

def log(update):
    from bot.utils.data_time import get_date
    if update.message:
        user = update.message.from_user
        text = update.message.text
        print(f'{get_date()} - {user.first_name} {user.last_name} (id {user.id}) написал: "{text}"')
    elif update.callback_query:
        query = update.callback_query
        user = query.from_user
        action = query.data
        print(f'{get_date()} - {user.first_name} (id {user.id}) нажал кнопку: "{action}"')


logging.getLogger("httpx").setLevel(logging.WARNING)