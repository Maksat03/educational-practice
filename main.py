import config

import logging
logging.basicConfig(level=logging.INFO)

from db import DB
from datetime import datetime
from aiogram import Bot, Dispatcher, executor
from aiogram.types import ContentType, Message, CallbackQuery
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, \
						InlineKeyboardMarkup, InlineKeyboardButton

bot = Bot(token=config.token, parse_mode='HTML')
dp = Dispatcher(bot)

customers_db = DB("customers")
dishes_db = DB("dishes")
categories_db = DB("categories")
orders_db = DB("orders")
feedbacks_db = DB("feedbacks")
promotions_db = DB("promotions")

def get_keyboard_markup(buttons):
	markup = ReplyKeyboardMarkup(resize_keyboard=True)
	for i in range(len(buttons) // 2):
		markup.add(KeyboardButton(buttons[i + i]), KeyboardButton(buttons[i + i + 1]))
	for i in range(len(buttons) % 2):
		markup.add(KeyboardButton(buttons[len(buttons) - 1]))
	return markup

def get_inline_keyboard_markup(buttons):
	markup = InlineKeyboardMarkup(resize_keyboard=True)
	for i in range(len(buttons) // 2):
		markup.add(InlineKeyboardButton(text=buttons[i + i][0], callback_data=buttons[i + i][1]), InlineKeyboardButton(text=buttons[i + i + 1][0], callback_data=buttons[i + i + 1][1]))
	for i in range(len(buttons) % 2):
		markup.add(InlineKeyboardButton(text=buttons[len(buttons) - 1][0], callback_data=buttons[len(buttons) - 1][1]))
	return markup

@dp.message_handler(commands=['start'])
async def welcome(msg: Message):
	await msg.answer("Добро пожаловать!", reply_markup=get_keyboard_markup(["👨🏻‍🍳 О нас", "🍽 Меню", "📃История заказов", "🛍Корзина", "🔥Акции", "📨Отзывы"]))
	if not customers_db.get("user_id", ["user_id", msg.from_user.id]):
		customers_db.add(f"{msg.from_user.id}, '', 0, 0, 0, 0, 0")
	else:
		user_info = ["name", "phone_number", "location", "feedback"]
		for i in range(len(user_info)):
			customers_db.update("get_"+user_info[i], 0, ["user_id", msg.from_user.id])

@dp.message_handler(content_types=[ContentType.TEXT, ContentType.CONTACT, ContentType.LOCATION])
async def get_message(msg: Message):
	if msg.chat.type == "private":
		user_info = ["name", "phone_number", "location", "feedback"]
		
		for i in range(len(user_info)):
			if customers_db.get("get_"+user_info[i], ["user_id", msg.from_user.id])[0][0]:
				if user_info[i] == "name":
					customers_db.update("get_name", 0, ["user_id", msg.from_user.id])
					
					if msg.text == "❌ Отмена":
						text = "Отменен"
						markup = get_keyboard_markup(["👨🏻‍🍳 О нас", "🍽 Меню", "📃История заказов", "🛍Корзина", "🔥Акции", "📨Отзывы"])
					else:
						text = "📱Введите Ваш телефон или отправьте свой контакт"
						markup = ReplyKeyboardMarkup(resize_keyboard=True)
						markup.add(KeyboardButton(text='📱Отправить контакт', request_contact=True))
						markup.add(KeyboardButton(text='❌ Отмена'))

						customers_db.update("name", msg.text, ["user_id", msg.from_user.id])
						customers_db.update("get_phone_number", 1, ["user_id", msg.from_user.id])

					await msg.answer(text, reply_markup=markup)

				elif user_info[i] == "phone_number":
					customers_db.update("get_phone_number", 0, ["user_id", msg.from_user.id])
					
					if msg.text == "❌ Отмена":
						text = "Отменен"
						markup = get_keyboard_markup(["👨🏻‍🍳 О нас", "🍽 Меню", "📃История заказов", "🛍Корзина", "🔥Акции", "📨Отзывы"])
					else:
						text = 'Куда доставить заказ?\n\nВы можете нажать на кнопку "📍 Отправить локацию" или написать адрес вручную.\n\nЕсли вы находитесь в заведении, можете написать номер стола'
						markup = ReplyKeyboardMarkup(resize_keyboard=True)
						markup.add(KeyboardButton(text='📍 Отправить локацию', request_location=True))
						markup.add(KeyboardButton(text='❌ Отмена'))

						if msg.text:
							phone_number = msg.text
						else:
							phone_number = msg.contact.phone_number

						customers_db.update("phone_number", phone_number, ["user_id", msg.from_user.id])
						customers_db.update("get_location", 1, ["user_id", msg.from_user.id])

					await msg.answer(text, reply_markup=markup)

				elif user_info[i] == "location":
					customers_db.update("get_location", 0, ["user_id", msg.from_user.id])
					
					if msg.text == "❌ Отмена":
						text = "Отменен"
						markup = get_keyboard_markup(["👨🏻‍🍳 О нас", "🍽 Меню", "📃История заказов", "🛍Корзина", "🔥Акции", "📨Отзывы"])
					else:
						await msg.answer("Отлично! Осталось подтвердить заказ!", reply_markup=get_keyboard_markup(["❌ Отмена"]))
						text = ''
						price = 0
						
						orders = orders_db.get("*", ["user_id", msg.from_user.id])
						for order in orders:
							if order[4] == 0:
								text += f'📥 Ваш заказ с индексом {order[0]}:\n\n'
								dishes = order[3].split(";")
								for i in range(len(dishes) - 1):
									splitted_data = dishes[i].split(",")
									ind = int(splitted_data[0][3:])
									count = int(splitted_data[1][6:])
									dish_name = dishes_db.get("name", ["id", ind])[0][0]
									dish_price = dishes_db.get("price", ["id", ind])[0][0]
									text += f"{i + 1}. {dish_name}\n{count} x {dish_price} тг. = {count*dish_price} тг.\n\n"
									price += count * dish_price

						if msg.text:
							location = msg.text
						else:
							location = msg.location

						phone_number = customers_db.get("phone_number", ["user_id", msg.from_user.id])[0][0]
						text += f"💵 Итого: {price} тг.\n📱 Hомер: {phone_number}\n📍 Адрес доставки: {location}"

						markup = get_inline_keyboard_markup([["✅ Подтвердить", "confirm_order"]])

					await msg.answer(text, reply_markup=markup)

				elif user_info[i] == "feedback":
					customers_db.update("get_feedback", 0, ["user_id", msg.from_user.id])

					if msg.text == "❌ Отмена":
						text = "Отменен"
						markup = get_keyboard_markup(["👨🏻‍🍳 О нас", "🍽 Меню", "📃История заказов", "🛍Корзина", "🔥Акции", "📨Отзывы"])
					else:
						text = "Укажите Вашу оценку!"
						markup = InlineKeyboardMarkup(
							inline_keyboard = [
								[InlineKeyboardButton(text="⭐️", callback_data="stars1")],
								[InlineKeyboardButton(text="⭐️"*2, callback_data="stars2")],
								[InlineKeyboardButton(text="⭐️"*3, callback_data="stars3")],
								[InlineKeyboardButton(text="⭐️"*4, callback_data="stars4")],
								[InlineKeyboardButton(text="⭐️"*5, callback_data="stars5")]
							]
						)

						feedbacks = feedbacks_db.get("*", ["user_id", msg.from_user.id])
						for feedback in feedbacks:
							if feedback[6] == 0:
								feedbacks_db.update("feedback", msg.text, ["id", feedback[0]])
								break

					await msg.answer(text, reply_markup=markup)

				else:
					pass

				break

		else:
			if msg.text == "🍽 Меню" or msg.text == "🍴В меню":
				categories = categories_db.get("*", ["parent_category", ""])
				for i in range(len(categories)):
					categories[i] = [categories[i][1], "ctgr_"+str(categories[i][0])]
				await msg.answer("Выберите раздел, чтобы вывести список блюд", reply_markup=get_keyboard_markup(["🏠 Начало", "🛍Корзина", "🍴В меню"]))
				await msg.answer("Меню:", reply_markup=get_inline_keyboard_markup(categories))
			elif msg.text == "🏠 Начало":
				await msg.answer(msg.text, reply_markup=get_keyboard_markup(["👨🏻‍🍳 О нас", "🍽 Меню", "📃История заказов", "🛍Корзина", "🔥Акции", "📨Отзывы"]))
			elif msg.text == "🛍Корзина":
				await msg.answer("Корзина:", reply_markup=get_keyboard_markup(["🏠 Начало", "🍴В меню"]))
				orders = orders_db.get("*", ["user_id", msg.from_user.id])
			
				for i in range(len(orders)):
					if orders[i][4] == 0:
						dishes = orders[i][3].split(";")
						if len(dishes) == 1:
							await msg.answer("Корзина пуста :(")
							break
						else:
							first_dish = dishes_db.get("*", ["id", int(dishes[0].split(",")[0][3:])])[0]
							price = first_dish[4] * int(dishes[0].split(",")[1][6:])
							
							inline_markup = InlineKeyboardMarkup(
								inline_keyboard=[
									[
										InlineKeyboardButton(text='🔻1', callback_data=f'dish_in_basket-=1,ind:{first_dish[0]}'),
										InlineKeyboardButton(text=f'{dishes[0].split(",")[1][6:]} шт.', callback_data='nothing'),
										InlineKeyboardButton(text='🔺1', callback_data=f'dish_in_basket+=1,ind:{first_dish[0]}')
									],
									[
										InlineKeyboardButton(text='🔻5', callback_data=f'dish_in_basket-=5,ind:{first_dish[0]}'),
										InlineKeyboardButton(text='🔺5', callback_data=f'dish_in_basket+=5,ind:{first_dish[0]}')
									],
									[
										InlineKeyboardButton(text='❌', callback_data=f'delete dish_in_basket,ind:{first_dish[0]}')
									]
								]
							)

							if len(dishes) > 2:
								inline_markup.add(
									InlineKeyboardButton(text=f"1 из {len(dishes)-1}", callback_data="nothing"),
									InlineKeyboardButton(text="➡️", callback_data="next_dish_in_basket:1")
								)
								for i in range(1, len(dishes) - 1):
									dish = dishes_db.get("*", ["id", int(dishes[i].split(",")[0][3:])])[0]
									price += dish[4] * int(dishes[i].split(",")[1][6:])

							inline_markup.add(InlineKeyboardButton(text=f"✅ Заказ на {price} тг. Оформить?", callback_data="checkout"))

							desc = "\n\n<i>" + first_dish[3] + "</i>\n\n"
							if first_dish[3] == "":
								desc = "\n"

							await msg.answer(f"<b>{first_dish[2]}</b>{desc}<a href='{first_dish[5]}'> </a>Цена: {first_dish[4]} тг.", reply_markup=inline_markup)
							break
				else:
					await msg.answer("Корзина пуста :(")
			
			elif msg.text == "📃История заказов":
				orders = orders_db.get("*", ["user_id", msg.from_user.id])
				for i in range(len(orders)):
					if orders[i][4] == 0:
						del orders[i]

				if len(orders) == 0:
					text = "📃 История заказов:\n\nК сожалению, в Вашей истории нет оформленных заказов! :("
					inline_markup = None
				else:
					text = "📃 История заказов:"
					inline_markup = InlineKeyboardMarkup()

					for i, order in enumerate(orders):
						inline_markup.add(InlineKeyboardButton(text = order[2], callback_data = f"history_of_orders;{order[2]}"))
						if i == 4:
							break

					inline_markup.add(
						InlineKeyboardButton(text = "◀️", callback_data = "nothing"),
						InlineKeyboardButton(text = "▶️", callback_data = "page_of_history_of_orders:5:0")
					)

				await msg.answer(text, reply_markup=inline_markup)

			elif msg.text == "📨Отзывы":
				feedbacks = feedbacks_db.get("*", ["confirm", 1])
				
				if len(feedbacks) == 0:
					await msg.answer("Отзывов пока нет", reply_markup=get_keyboard_markup(["📝 Добавить отзыв", "🏠 Начало"]))
				else:
					await msg.answer(feedbacks[0][2] + f" ({feedbacks[0][3]})\n" + ("⭐️"*feedbacks[0][4]) + "\n" + feedbacks[0][5], reply_markup=get_keyboard_markup(["📝 Добавить отзыв", "🏠 Начало"]))

					stop = len(feedbacks)
					more = False
					
					if stop > 5:
						stop = 4
						more = True

					for i in range(1, stop):
						await msg.answer(feedbacks[i][2] + f" ({feedbacks[i][3]})\n" + ("⭐️"*feedbacks[i][4]) + "\n" + feedbacks[i][5])

					if more:
						await msg.answer(feedbacks[4][2] + f" ({feedbacks[4][3]})\n" + ("⭐️"*feedbacks[4][4]) + "\n" + feedbacks[4][5], reply_markup=get_inline_keyboard_markup([["Еще", "more_feedbacks:5"]]))

			elif msg.text == "📝 Добавить отзыв":
				customers_db.update("get_feedback", 1, ["user_id", msg.from_user.id])
				feedbacks = feedbacks_db.get("confirm", ["username", msg.from_user.first_name])

				for feedback in feedbacks:
					if feedback[0] == 0:
						break
				else:
					feedbacks_db.add(f"{msg.from_user.id}, '{msg.from_user.first_name}', '', 0, '', 0")

				await msg.answer("📝 Добавление отзыва:\nПожалуйста, введите текст Вашего отзыва:", reply_markup=get_keyboard_markup(["❌ Отмена"]))

			elif msg.text == "🔥Акции":
				promotions_db.cursor.execute("SELECT * FROM promotions")
				promotions = promotions_db.cursor.fetchall()

				if len(promotions) == 0:
					await msg.answer("Акции нету")
				else:
					for promotion in promotions:
						await msg.answer("<b>" + promotion[0] + f"</b><a href='{promotion[2]}'> </a>\n<i>" + promotion[1] + "</i>")

			elif msg.text == "👨🏻‍🍳 О нас":
				await msg.answer(config.about_us)
			elif msg.text == "❌ Отмена":
				await msg.answer("Отменен", reply_markup=get_keyboard_markup(["👨🏻‍🍳 О нас", "🍽 Меню", "📃История заказов", "🛍Корзина", "🔥Акции", "📨Отзывы"]))
			else:
				await msg.answer("I don't know how to answer this", reply_markup=get_keyboard_markup(["👨🏻‍🍳 О нас", "🍽 Меню", "📃История заказов", "🛍Корзина", "🔥Акции", "📨Отзывы"]))

def get_dishes_markup(ind, var, orders, dish_ind):
	inline_markup = None
	
	if var:
		splitted_data = orders[ind][3].split(";")
		for i in range(len(splitted_data)):
			if f"id:{dish_ind}," in splitted_data[i]:
				count = int(splitted_data[i].split(",")[1][6:])
				inline_markup = InlineKeyboardMarkup(
					inline_keyboard=[
						[
							InlineKeyboardButton(text='🔻1', callback_data=f'dish-=1,ind:{dish_ind}'),
							InlineKeyboardButton(text=f'{count} шт.', callback_data='nothing'),
							InlineKeyboardButton(text='🔺1', callback_data=f'dish+=1,ind:{dish_ind}')
						],
						[
							InlineKeyboardButton(text='🔻5', callback_data=f'dish-=5,ind:{dish_ind}'),
							InlineKeyboardButton(text='🔺5', callback_data=f'dish+=5,ind:{dish_ind}')
						],
						[
							InlineKeyboardButton(text='❌', callback_data=f'del dish,ind:{dish_ind}')
						]
					]
				)
				break
		else:
			inline_markup = get_inline_keyboard_markup([["В корзину", "in_garbage_"+str(dish_ind)]])
	else:						
		inline_markup = get_inline_keyboard_markup([["В корзину", "in_garbage_"+str(dish_ind)]])

	return inline_markup

@dp.callback_query_handler()
async def inline_echo(call: CallbackQuery):
	if call.message:
		if call.data.startswith("ctgr_"):
			selected_ctgr_ind = int(call.data[5:])
			selected_ctgr = categories_db.get("name", ["id", selected_ctgr_ind])[0][0]

			categories = categories_db.get("*", ["parent_category", selected_ctgr])
			for i in range(len(categories)):
				categories[i] = [categories[i][1], "ctgr_"+str(categories[i][0])]

			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=selected_ctgr+":", reply_markup=get_inline_keyboard_markup(categories))

			if len(categories) == 0:
				dishes = dishes_db.get("*", ["category", selected_ctgr])
				orders = orders_db.get("*", ["user_id", call.message.chat.id])
				ind = 0
				var = False
				
				for i in range(len(orders)):
					if orders[i][4] == 0:
						ind = i
						var = True
						break

				if len(dishes) > 5:
					for i in range(4):
						desc = "\n\n<i>" + dishes[i][3] + "</i>\n\n"
						
						if dishes[i][3] == "":
							desc = "\n"
						
						await call.message.answer(
							f"<b>{dishes[i][2]}</b>{desc}<a href='{dishes[i][5]}'> </a>Цена: {dishes[i][4]} тг.", 
							reply_markup=get_dishes_markup(ind, var, orders, dishes[i][0])
						)
					
					inline_markup = get_dishes_markup(ind, var, orders, dishes[4][0])
					inline_markup.add(InlineKeyboardButton(text="Еще", callback_data=f"more_dishes:{selected_ctgr_ind};5"))
					
					desc = "\n\n<i>" + dishes[4][3] + "</i>\n\n"
					if dishes[4][3] == "":
						desc = "\n"

					await call.message.answer(
						f"<b>{dishes[4][2]}</b>{desc}<a href='{dishes[4][5]}'> </a>Цена: {dishes[4][4]} тг.",
						reply_markup=inline_markup
					)
				else:
					for i in range(len(dishes)):
						desc = "\n\n<i>" + dishes[i][3] + "</i>\n\n"
						
						if dishes[i][3] == "":
							desc = "\n"
						
						await call.message.answer(
							f"<b>{dishes[i][2]}</b>{desc}<a href='{dishes[i][5]}'> </a>Цена: {dishes[i][4]} тг.", 
							reply_markup=get_dishes_markup(ind, var, orders, dishes[i][0])
						)

		elif call.data.startswith("more_dishes:"):
			markup = call.message.reply_markup["inline_keyboard"]
			
			if len(markup) == 2:
				markup = get_inline_keyboard_markup([[markup[0][0]["text"], markup[0][0]["callback_data"]]])
			else:
				markup = InlineKeyboardMarkup(
					inline_keyboard=[
						[
							InlineKeyboardButton(text='🔻1', callback_data=markup[0][0]["callback_data"]),
							InlineKeyboardButton(text=markup[0][1]['text'], callback_data='nothing'),
							InlineKeyboardButton(text='🔺1', callback_data=markup[0][2]["callback_data"])
						],
						[
							InlineKeyboardButton(text='🔻5', callback_data=markup[1][0]["callback_data"]),
							InlineKeyboardButton(text='🔺5', callback_data=markup[1][1]["callback_data"])
						],
						[
							InlineKeyboardButton(text='❌', callback_data=markup[2][0]["callback_data"])
						]
					]
				)

			callback_data = call.data.split(":")[1].split(";")
			selected_ctgr_ind = int(callback_data[0])
			start = int(callback_data[1])
			ctgr = categories_db.get("name", ["id", selected_ctgr_ind])[0][0]
			dishes = dishes_db.get("*", ["category", ctgr])
			orders = orders_db.get("*", ["user_id", call.message.chat.id])
			index = 0
			var = False

			desc = "\n\n<i>" + dishes[start - 1][3] + "</i>\n\n"
			if dishes[start - 1][3] == "":
				desc = "\n"

			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
				text=f"<b>{dishes[start - 1][2]}</b>{desc}<a href='{dishes[start - 1][5]}'> </a>Цена: {dishes[start - 1][4]} тг.", reply_markup=markup)
			
			for i in range(len(orders)):
				if orders[i][4] == 0:
					index = i
					var = True
					break
			
			if len(dishes) - start > 5:
				for i in range(start, start + 4):
					desc = "\n\n<i>" + dishes[i][3] + "</i>\n\n"
						
					if dishes[i][3] == "":
						desc = "\n"
					
					await call.message.answer(
						f"<b>{dishes[i][2]}</b>{desc}<a href='{dishes[i][5]}'> </a>Цена: {dishes[i][4]} тг.", 
						reply_markup=get_dishes_markup(index, var, orders, dishes[i][0])
					)
				
				inline_markup = get_dishes_markup(index, var, orders, dishes[start+4][0])
				inline_markup.add(InlineKeyboardButton(text="Еще", callback_data=f"more_dishes:{selected_ctgr_ind};{start+5}"))
				
				desc = "\n\n<i>" + dishes[start + 4][3] + "</i>\n\n"
				if dishes[start + 4][3] == "":
					desc = "\n"

				await call.message.answer(
					f"<b>{dishes[start + 4][2]}</b>{desc}<a href='{dishes[start + 4][5]}'> </a>Цена: {dishes[start + 4][4]} тг.",
					reply_markup=inline_markup
				)
			else:
				for i in range(start, len(dishes)):
					desc = "\n\n<i>" + dishes[i][3] + "</i>\n\n"
						
					if dishes[i][3] == "":
						desc = "\n"
					
					await call.message.answer(
						f"<b>{dishes[i][2]}</b>{desc}<a href='{dishes[i][5]}'> </a>Цена: {dishes[i][4]} тг.", 
						reply_markup=get_dishes_markup(index, var, orders, dishes[i][0])
					)

		elif call.data.startswith("in_garbage_"):
			dish_ind = call.data[11:]
			orders = orders_db.get("*", ["user_id", call.message.chat.id])
			for i in range(len(orders)):
				if orders[i][4] == 0:
					order = orders[i][3]
					order += f"id:{dish_ind},count:1;"
					orders_db.update("dishes", order, ["id", orders[i][0]])
					break
			else:
				orders_db.add(f"{call.message.chat.id}, '', 'id:{dish_ind},count:1;', 0")

			inline_markup = InlineKeyboardMarkup(
				inline_keyboard=[
					[
						InlineKeyboardButton(text='🔻1', callback_data=f'dish-=1,ind:{dish_ind}'),
						InlineKeyboardButton(text='1 шт.', callback_data='nothing'),
						InlineKeyboardButton(text='🔺1', callback_data=f'dish+=1,ind:{dish_ind}')
					],
					[
						InlineKeyboardButton(text='🔻5', callback_data=f'dish-=5,ind:{dish_ind}'),
						InlineKeyboardButton(text='🔺5', callback_data=f'dish+=5,ind:{dish_ind}')
					],
					[
						InlineKeyboardButton(text='❌', callback_data=f'del dish,ind:{dish_ind}')
					]
				]
			)

			markup = call.message.reply_markup["inline_keyboard"]
			if len(markup) == 2:
				inline_markup.add(InlineKeyboardButton(text=markup[1][0]['text'], callback_data=markup[1][0]['callback_data']))

			dish = dishes_db.get("*", ["id", dish_ind])[0]
			desc = "\n\n<i>" + dish[3] + "</i>\n\n"
			if dish[3] == "":
				desc = "\n"

			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
				text=f"<b>{dish[2]}</b>{desc}<a href='{dish[5]}'> </a>Цена: {dish[4]} тг.", reply_markup=inline_markup)

		elif call.data.startswith("dish-=") or call.data.startswith("dish+="):
			dish_ind = call.data.split(",")[1][4:]
			orders = orders_db.get("*", ["user_id", call.message.chat.id])
			var = False
			count = 0

			for i in range(len(orders)):
				if orders[i][4] == 0:
					dishes = orders[i][3].split(";")
					for j in range(len(dishes)):
						if dishes[j].startswith(f"id:{dish_ind}"):
							current_count = int(dishes[j].split(":")[2])
							count = current_count
							if "+=1" in call.data:
								count += 1
							elif "-=1" in call.data:
								count -= 1
							elif "+=5" in call.data:
								count += 5
							else:
								count -= 5
							if count <= 0 and current_count == 1:
								var = True
							if count <= 0:
								count = 1
							dishes[j] = f"id:{dish_ind},count:{count}"
							break
					dishes = ";".join(dishes)
					orders_db.update("dishes", dishes, ["id", orders[i][0]])
					break

			if not var:
				inline_markup = InlineKeyboardMarkup(
					inline_keyboard=[
						[
							InlineKeyboardButton(text='🔻1', callback_data=f'dish-=1,ind:{dish_ind}'),
							InlineKeyboardButton(text=f'{count} шт.', callback_data='nothing'),
							InlineKeyboardButton(text='🔺1', callback_data=f'dish+=1,ind:{dish_ind}')
						],
						[
							InlineKeyboardButton(text='🔻5', callback_data=f'dish-=5,ind:{dish_ind}'),
							InlineKeyboardButton(text='🔺5', callback_data=f'dish+=5,ind:{dish_ind}')
						],
						[
							InlineKeyboardButton(text='❌', callback_data=f'del dish,ind:{dish_ind}')
						]
					]
				)

				markup = call.message.reply_markup["inline_keyboard"]
				if len(markup) == 4:
					inline_markup.add(InlineKeyboardButton(text=markup[3][0]['text'], callback_data=markup[3][0]['callback_data']))

				dish = dishes_db.get("*", ["id", dish_ind])[0]
				desc = "\n\n<i>" + dish[3] + "</i>\n\n"
				if dish[3] == "":
					desc = "\n"

				await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
					text=f"<b>{dish[2]}</b>{desc}<a href='{dish[5]}'> </a>Цена: {dish[4]} тг.", reply_markup=inline_markup)

		elif call.data.startswith("del dish"):
			dish_ind = call.data.split(",")[1][4:]
			orders = orders_db.get("*", ["user_id", call.message.chat.id])

			for i in range(len(orders)):
				if orders[i][4] == 0:
					dishes = orders[i][3].split(";")
					for j in range(len(dishes)):
						if dishes[j].startswith(f"id:{dish_ind}"):
							del dishes[j]
							break
					dishes = ";".join(dishes)
					orders_db.update("dishes", dishes, ["id", orders[i][0]])
					break

			inline_markup = get_inline_keyboard_markup([["В корзину", "in_garbage_"+str(dish_ind)]])
			markup = call.message.reply_markup["inline_keyboard"]
			if len(markup) == 4:
				inline_markup.add(InlineKeyboardButton(text=markup[3][0]['text'], callback_data=markup[3][0]['callback_data']))

			dish = dishes_db.get("*", ["id", dish_ind])[0]
			desc = "\n\n<i>" + dish[3] + "</i>\n\n"
			if dish[3] == "":
				desc = "\n"

			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
				text=f"<b>{dish[2]}</b>{desc}<a href='{dish[5]}'> </a>Цена: {dish[4]} тг.", reply_markup=inline_markup)

		elif call.data.startswith("dish_in_basket-=") or call.data.startswith("dish_in_basket+="):
			dish_ind = int(call.data.split(",")[1][4:])
			orders = orders_db.get("*", ["user_id", call.message.chat.id])
			dishes = None
			var = False
			count = 0

			for i in range(len(orders)):
				if orders[i][4] == 0:
					dishes = orders[i][3].split(";")
					for j in range(len(dishes)):
						if dishes[j].startswith(f"id:{dish_ind}"):
							current_count = int(dishes[j].split(":")[2])
							count = current_count
							if "+=1" in call.data:
								count += 1
							elif "-=1" in call.data:
								count -= 1
							elif "+=5" in call.data:
								count += 5
							else:
								count -= 5
							if count <= 0 and current_count == 1:
								var = True
							if count <= 0:
								count = 1
							dishes[j] = f"id:{dish_ind},count:{count}"
							break
					dishes = ";".join(dishes)
					orders_db.update("dishes", dishes, ["id", orders[i][0]])
					break

			if not var:
				inline_markup = InlineKeyboardMarkup(
					inline_keyboard=[
						[
							InlineKeyboardButton(text='🔻1', callback_data=f'dish_in_basket-=1,ind:{dish_ind}'),
							InlineKeyboardButton(text=f'{count} шт.', callback_data='nothing'),
							InlineKeyboardButton(text='🔺1', callback_data=f'dish_in_basket+=1,ind:{dish_ind}')
						],
						[
							InlineKeyboardButton(text='🔻5', callback_data=f'dish_in_basket-=5,ind:{dish_ind}'),
							InlineKeyboardButton(text='🔺5', callback_data=f'dish_in_basket+=5,ind:{dish_ind}')
						],
						[
							InlineKeyboardButton(text='❌', callback_data=f'delete dish_in_basket,ind:{dish_ind}')
						]
					]
				)

				markup = call.message.reply_markup["inline_keyboard"]
				if len(markup) == 5:
					if len(markup[3]) == 2:
						inline_markup.add(
							InlineKeyboardButton(text=markup[3][0]['text'], callback_data=markup[3][0]['callback_data']),
							InlineKeyboardButton(text=markup[3][1]['text'], callback_data=markup[3][1]['callback_data'])
						)
					else:
						inline_markup.add(
							InlineKeyboardButton(text=markup[3][0]['text'], callback_data=markup[3][0]['callback_data']),
							InlineKeyboardButton(text=markup[3][1]['text'], callback_data=markup[3][1]['callback_data']),
							InlineKeyboardButton(text=markup[3][2]['text'], callback_data=markup[3][2]['callback_data'])
						)

				price = 0
				dishes = dishes.split(";")
				for i in range(len(dishes) - 1):
					dish_data = dishes[i].split(",")
					price += dishes_db.get("price", ["id", dish_data[0][3:]])[0][0] * int(dish_data[1][6:])

				inline_markup.add(
					InlineKeyboardButton(text=f"✅ Заказ на {price} тг. Оформить?", callback_data="checkout")
				)

				dish = dishes_db.get("*", ["id", dish_ind])[0]
				desc = "\n\n<i>" + dish[3] + "</i>\n\n"
				if dish[3] == "":
					desc = "\n"

				await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
					text=f"<b>{dish[2]}</b>{desc}<a href='{dish[5]}'> </a>Цена: {dish[4]} тг.", reply_markup=inline_markup)

		elif call.data.startswith("delete dish_in_basket"):
			dish_ind = call.data.split(",")[1][4:]
			orders = orders_db.get("*", ["user_id", call.message.chat.id])
			dishes = None

			for i in range(len(orders)):
				if orders[i][4] == 0:
					dishes = orders[i][3].split(";")
					for j in range(len(dishes)):
						if dishes[j].startswith(f"id:{dish_ind}"):
							del dishes[j]
							break
					dishes = ";".join(dishes)
					orders_db.update("dishes", dishes, ["id", orders[i][0]])
					break

			markup = call.message.reply_markup["inline_keyboard"]
			if len(markup) == 5:
				ind = 0
				for i in range(len(markup[3])):
					if " из " in markup[3][i]['text']:
						ind = i

				dishes = dishes.split(";")
				count = markup[3][ind]['text'].split(" из ")
				remainder = int(count[1]) - 1
				if remainder == 1:
					dishes = dishes[0].split(",")
					dish = dishes_db.get("*", ["id", int(dishes[0][3:])])[0]
					
					desc = "\n\n<i>" + dish[3] + "</i>\n\n"
					if dish[3] == "":
						desc = "\n"
					
					text = f"<b>{dish[2]}</b>{desc}<a href='{dish[5]}'> </a>Цена: {dish[4]} тг."
					price = dish[4] * int(dishes[1][6:])
					inline_markup = InlineKeyboardMarkup(
						inline_keyboard=[
							[
								InlineKeyboardButton(text='🔻1', callback_data=f'dish_in_basket-=1,ind:{dishes[0][3:]}'),
								InlineKeyboardButton(text=f'{dishes[1][6:]} шт.', callback_data='nothing'),
								InlineKeyboardButton(text='🔺1', callback_data=f'dish_in_basket+=1,ind:{dishes[0][3:]}')
							],
							[
								InlineKeyboardButton(text='🔻5', callback_data=f'dish_in_basket-=5,ind:{dishes[0][3:]}'),
								InlineKeyboardButton(text='🔺5', callback_data=f'dish_in_basket+=5,ind:{dishes[0][3:]}')
							],
							[
								InlineKeyboardButton(text='❌', callback_data=f'delete dish_in_basket,ind:{dishes[0][3:]}')
							],
							[
								InlineKeyboardButton(text=f"✅ Заказ на {price} тг. Оформить?", callback_data="checkout")
							]
						]
					)
				else:
					ind = int(count[0]) - 1 - 1
					if ind == -1:
						ind = 0

					dish_data = dishes[ind].split(",")
					dish = dishes_db.get("*", ["id", dish_data[0][3:]])[0]

					desc = "\n\n<i>" + dish[3] + "</i>\n\n"
					if dish[3] == "":
						desc = "\n"
					
					text = f"<b>{dish[2]}</b>{desc}<a href='{dish[5]}'> </a>Цена: {dish[4]} тг."
					inline_markup = InlineKeyboardMarkup(
						inline_keyboard=[
							[
								InlineKeyboardButton(text='🔻1', callback_data=f'dish_in_basket-=1,ind:{dish_data[0][3:]}'),
								InlineKeyboardButton(text=f'{dish_data[1][6:]} шт.', callback_data='nothing'),
								InlineKeyboardButton(text='🔺1', callback_data=f'dish_in_basket+=1,ind:{dish_data[0][3:]}')
							],
							[
								InlineKeyboardButton(text='🔻5', callback_data=f'dish_in_basket-=5,ind:{dish_data[0][3:]}'),
								InlineKeyboardButton(text='🔺5', callback_data=f'dish_in_basket+=5,ind:{dish_data[0][3:]}')
							],
							[
								InlineKeyboardButton(text='❌', callback_data=f'delete dish_in_basket,ind:{dish_data[0][3:]}')
							]
						]
					)

					if ind == 0:
						inline_markup.add(
							InlineKeyboardButton(text=f"1 из {len(dishes)-1}", callback_data="nothing"),
							InlineKeyboardButton(text="➡️", callback_data="next_dish_in_basket:1")
						)
					elif ind + 1 == len(dishes) - 1:
						inline_markup.add(
							InlineKeyboardButton(text="⬅️", callback_data=f"previous_dish_in_basket:{len(dishes)-1-1-1}"),
							InlineKeyboardButton(text=f"{len(dishes)-1} из {len(dishes)-1}", callback_data="nothing")
						)
					else:
						inline_markup.add(
							InlineKeyboardButton(text="⬅️", callback_data=f"previous_dish_in_basket:{ind-1}"),
							InlineKeyboardButton(text=f"{ind+1} из {len(dishes)-1}", callback_data="nothing"),
							InlineKeyboardButton(text="➡️", callback_data=f"next_dish_in_basket:{ind+1}")
						)

					price = 0
					for i in range(len(dishes) - 1):
						dish_data = dishes[i].split(",")
						price += dishes_db.get("price", ["id", dish_data[0][3:]])[0][0] * int(dish_data[1][6:])

					inline_markup.add(InlineKeyboardButton(text=f"✅ Заказ на {price} тг. Оформить?", callback_data="checkout"))

			else:
				text = "Корзина пуста :("
				inline_markup = None

			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=inline_markup)

		elif call.data.startswith("next_dish_in_basket") or call.data.startswith("previous_dish_in_basket"):
			orders = orders_db.get("*", ['user_id', call.message.chat.id])
			ind = int(call.data.split(":")[1])
			ind_of_expected_dish = 0
			dishes = None
			count = None

			for i in range(len(orders)):
				if orders[i][4] == 0:
					dishes = orders[i][3].split(";")
					dish_info = dishes[ind].split(",")
					ind_of_expected_dish = int(dish_info[0][3:])
					count = int(dish_info[1][6:])
					break

			dish_info = dishes_db.get("*", ["id", ind_of_expected_dish])[0]

			desc = "\n\n<i>" + dish_info[3] + "</i>\n\n"
			if dish_info[3] == "":
				desc = "\n"
			
			text = f"<b>{dish_info[2]}</b>{desc}<a href='{dish_info[5]}'> </a>Цена: {dish_info[4]} тг."
			inline_markup = InlineKeyboardMarkup(
				inline_keyboard=[
					[
						InlineKeyboardButton(text='🔻1', callback_data=f'dish_in_basket-=1,ind:{ind_of_expected_dish}'),
						InlineKeyboardButton(text=f'{count} шт.', callback_data='nothing'),
						InlineKeyboardButton(text='🔺1', callback_data=f'dish_in_basket+=1,ind:{ind_of_expected_dish}')
					],
					[
						InlineKeyboardButton(text='🔻5', callback_data=f'dish_in_basket-=5,ind:{ind_of_expected_dish}'),
						InlineKeyboardButton(text='🔺5', callback_data=f'dish_in_basket+=5,ind:{ind_of_expected_dish}')
					],
					[
						InlineKeyboardButton(text='❌', callback_data=f'delete dish_in_basket,ind:{ind_of_expected_dish}')
					]
				]
			)

			if len(dishes) - 1 == ind + 1:
				inline_markup.add(
					InlineKeyboardButton(text="⬅️", callback_data=f"previous_dish_in_basket:{len(dishes)-1-1-1}"),
					InlineKeyboardButton(text=f"{len(dishes)-1} из {len(dishes)-1}", callback_data="nothing")
				)
			elif ind == 0:
				inline_markup.add(
					InlineKeyboardButton(text=f"1 из {len(dishes)-1}", callback_data="nothing"),
					InlineKeyboardButton(text="➡️", callback_data="next_dish_in_basket:1")
				)
			else:
				inline_markup.add(
					InlineKeyboardButton(text="⬅️", callback_data=f"previous_dish_in_basket:{ind-1}"),
					InlineKeyboardButton(text=f"{ind+1} из {len(dishes)-1}", callback_data="nothing"),
					InlineKeyboardButton(text="➡️", callback_data=f"next_dish_in_basket:{ind+1}")
				)

			markup = call.message.reply_markup["inline_keyboard"]
			inline_markup.add(InlineKeyboardButton(text=markup[len(markup)-1][0]['text'], callback_data=markup[len(markup)-1][0]['callback_data']))

			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=inline_markup)

		elif call.data == "checkout":
			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Оформление заказа:", reply_markup=None)
			await bot.send_message(call.message.chat.id, "-----", reply_markup=get_keyboard_markup(["❌ Отмена"]))
			await bot.send_message(call.message.chat.id, f"Ваше имя {call.message.chat.first_name}?", reply_markup=get_inline_keyboard_markup([["✅ Да", "name_yes"], ["❌ Нет", "name_no"]]))

		elif call.data == "name_yes":
			customers_db.update("name", call.message.chat.first_name, ["user_id", call.message.chat.id])
			customers_db.update("get_phone_number", 1, ["user_id", call.message.chat.id])
			
			markup = ReplyKeyboardMarkup(resize_keyboard=True)
			markup.add(KeyboardButton(text='📱Отправить контакт', request_contact=True))
			markup.add(KeyboardButton(text='❌ Отмена'))

			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text, reply_markup=None)
			await bot.send_message(call.message.chat.id, "📱Введите Ваш телефон или отправьте свой контакт", reply_markup=markup)

		elif call.data == "name_no":
			customers_db.update("get_name", 1, ["user_id", call.message.chat.id])
			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Введите ваше имя:", reply_markup=None)

		elif call.data == "confirm_order":
			orders = orders_db.get("*", ["user_id", call.message.chat.id])
			order_ind = 0
			
			for i in range(len(orders)):
				if orders[i][4] == 0:
					order_ind = orders[i][0]
					break

			date = str(datetime.now())[:16]
			orders_db.update("confirm", 1, ["id", order_ind])
			orders_db.update("date", date, ["id", order_ind])
			orders_db.update("dishes", call.message.text, ["id", order_ind])

			msg_text = call.message.text.split('\n')
			msg_text[0] = f"Новый заказ с индексом: {order_ind}\nКлиент: {customers_db.get('name', ['user_id', call.message.chat.id])[0][0]}\nЗаказал: {date}"
			msg_text = "\n".join(msg_text)

			await bot.send_message("838318362", msg_text, reply_markup=get_inline_keyboard_markup([["✅ Принят заказ", f"accept_order:{call.message.chat.id}"]]))
			
			msg_text = msg_text.split("\n📍 Адрес доставки: ")
			if "latitude" in msg_text[1] and "longitude" in msg_text[1]:
				location = msg_text[1].split(",")
				latitude = float(location[0].split(": ")[1])
				longitude = float(location[1].split(": ")[1][:-1])
				await bot.send_location("838318362", latitude, longitude)

			text = "Благодарим вас что заказываете у нас🤗\n✅ Заказ успешно отправлен, ждем когда оператор примет его"
			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=None)
			await call.message.answer("🔊 Я буду сообщать вам о всех действиях оператора", reply_markup=get_keyboard_markup(["👨🏻‍🍳 О нас", "🍽 Меню", "📃История заказов", "🛍Корзина", "🔥Акции", "📨Отзывы"]))
			await call.answer(text="✅ Заказ успешно отправлен", show_alert=True)

		elif call.data.startswith("accept_order:"):
			text = '📥 Ваш заказ с индексом {ind} готовится 👨‍🍳'.format(ind = call.message.text.split("\n")[0][24:])
			await bot.send_message(call.data.split(":")[1], text)
			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text, reply_markup=get_inline_keyboard_markup([["🚗 Oтправить заказ", f"send_order:{call.data.split(':')[1]}"]]))

		elif call.data.startswith("send_order:"):
			text = '📥 Ваш заказ с индексом {ind} передан курьеру 🚗'.format(ind = call.message.text.split("\n")[0][24:])
			await bot.send_message(call.data.split(":")[1], text)
			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text, reply_markup=get_inline_keyboard_markup([["✅ Завершить заказ", f"complete_order:{call.data.split(':')[1]}"]]))

		elif call.data.startswith("complete_order"):
			text = '📥 Ваш заказ с индексом {ind} доставлен ✅\n\nПриятного аппетита 😘\nБлагодарим вас что заказываете у нас🤗'.format(ind = call.message.text.split("\n")[0][24:])
			await bot.send_message(call.data.split(":")[1], text)
			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text, reply_markup=get_inline_keyboard_markup([["✅ Заказ завершен", "nothing"]]))

		elif call.data.startswith("history_of_orders;"):
			date = call.data.split(";")[1]
			orders = orders_db.get("*", ["user_id", call.message.chat.id])

			for i in range(len(orders)):
				if orders[i][4] == 1 and orders[i][2] == date:
					order = orders[i][3]
					await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=order, reply_markup=None)
					break

		elif call.data.startswith("page_of_history_of_orders:"):
			start = int(call.data.split(":")[1])
			current = int(call.data.split(":")[2])
			
			if start == current:
				pass
			else:
				orders = orders_db.get("*", ["user_id", call.message.chat.id])
				inline_markup = InlineKeyboardMarkup()

				for i in range(len(orders)):
					if orders[i][4] == 0:
						del orders[i]

				for i in range(start, len(orders)):
					inline_markup.add(InlineKeyboardButton(text = orders[i][2], callback_data = f"history_of_orders;{orders[i][2]}"))
					if i == start + 4:
						break

				start_5 = start - 5
				if start_5 < 0:
					start_5 = 0

				inline_markup.add(
					InlineKeyboardButton(text = "◀️", callback_data = f"page_of_history_of_orders:{start_5}:{start}"),
					InlineKeyboardButton(text = "▶️", callback_data = f"page_of_history_of_orders:{start + 5}:{start}")
				)

				await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="📃 История заказов:", reply_markup=inline_markup)

		elif call.data.startswith("more_feedbacks:"):
			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text, reply_markup=None)
			
			feedbacks = feedbacks_db.get("*", ["confirm", 1])
			start = int(call.data.split(":")[1])
			stop = len(feedbacks)
			more = False
			
			if stop - start > 5:
				stop = start + 4
				more = True

			for i in range(start, stop):
				await call.message.answer(feedbacks[i][2] + f" ({feedbacks[i][3]})\n" + ("⭐️"*feedbacks[i][4]) + "\n" + feedbacks[i][5])

			if more:
				await call.message.answer(feedbacks[start + 4][2] + f" ({feedbacks[start + 4][3]})\n" + ("⭐️"*feedbacks[start + 4][4]) + "\n" + feedbacks[start + 4][5], reply_markup=get_inline_keyboard_markup([["Еще", f"more_feedbacks:{start+5}"]]))

		elif call.data.startswith("stars"):
			stars = int(call.data[5:])
			date = str(datetime.now())[:16]
			feedbacks = feedbacks_db.get("*", ['user_id', call.message.chat.id])

			for feedback in feedbacks:
				if feedback[6] == 0:
					feedbacks_db.update("stars", stars, ["id", feedback[0]])
					feedbacks_db.update("date", date, ["id", feedback[0]])
					feedbacks_db.update("confirm", 1, ["id", feedback[0]])
					break

			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Вас отзыв успешно принят!", reply_markup=None)
			await call.message.answer("Спасибо за отзыв!", reply_markup=get_keyboard_markup(["👨🏻‍🍳 О нас", "🍽 Меню", "📃История заказов", "🛍Корзина", "🔥Акции", "📨Отзывы"]))

		else:
			pass

if __name__ == "__main__":
	executor.start_polling(dp, skip_updates=True)
	# 838318362
