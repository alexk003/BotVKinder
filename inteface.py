import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from config import acces_token, comunity_token
import core
import data_store
import datetime
import psycopg2
conn = psycopg2.connect(database="postgres", user="postgres", password="*6352a17")
current_year = datetime.datetime.now().year

class BotInterface:

    def __init__(self, token):
        self.bot = vk_api.VkApi(token=token)

    def message_send(self, user_id, message=None, attachment=None):
        self.bot.method('messages.send',
                        {'user_id': user_id,
                         'message': message,
                         'random_id': get_random_id(),
                         'attachment': attachment
                         }
                        )

    def handler(self):
        offset = 0
        longpull = VkLongPoll(self.bot)
        for event in longpull.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                data_store.create_table(conn)
                prof_info = core.tools.get_profile_info(event.user_id)
                city_id = prof_info[0].get('city').get('id')
                birthday = prof_info[0].get('bdate')
                birth_year = birthday.split('.')[2]
                age_from = current_year - int(birth_year) - 5
                age_to = current_year - int(birth_year)
                sex = prof_info[0].get('sex')
                if event.text.lower() == 'привет':
                    self.message_send(event.user_id, 'Добрый день, напишите команду "поиск" чтобы увидеть результат!')
                elif event.text.lower() == 'поиск' or event.text.lower() == 'далее':
                    if sex == 1:
                        sex = 2
                        self.message_send(event.user_id, 'Вы женщина, ищем мужчину, возраст: +- 5 лет :-)')
                    elif sex == 2:
                        self.message_send(event.user_id, 'Вы мужчина, ищем женщину, возраст: +- 5 лет :-)')
                        sex = 1
                    else:
                        sex = int(input('ошибка определения пола, введите Ваш пол:'
                                        ' 1 - если Вы женщина, 2 - если Вы мужчина'))
                    result_prof = core.tools.user_serch(city_id, age_from, age_to, sex, 1, offset)
                    for profile in result_prof:
                        offset += 1
                        id_found = profile.get('id')
                        id_list = data_store.from_db(conn, event.user_id)
                        list_id =[]
                        for x in id_list:
                            list_id.append(x[0])
                        if id_found in list_id:
                            continue
                        else:
                            data_store.to_db(conn, event.user_id, id_found)
                            self.message_send(event.user_id, 'https://vk.com/id' + str(id_found))
                            result_photos_get = core.tools.photos_get(id_found)
                            for photo in result_photos_get:
                                photo_id = photo.get('id')
                                owner_id = photo.get('owner_id')
                                media = 'photo' + str(owner_id) + '_' + str(photo_id)
                                self.message_send(event.user_id, attachment= media)
                    self.message_send(event.user_id, 'Напишите "поиск" или "далее", если хотите продолжить поиск!')
                else:
                    self.message_send(event.user_id, 'извините, пока я знаю только "привет", "поиск", '
                                                     '"далее" и "пока" :-)')


if __name__ == '__main__':
    bot = BotInterface(comunity_token)
    bot.handler()
