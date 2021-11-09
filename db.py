import sqlite3

class DB:
	def __init__(self, table):
		self.table = table
		self.conn = sqlite3.connect("db.db")
		self.cursor = self.conn.cursor()
		columns = {
			"customers":
				"""
				user_id				INTEGER,
				name				TEXT,
				phone_number		INTEGER,
				get_name			BOOLEAN,
				get_phone_number	BOOLEAN,
				get_location		BOOLEAN,
				get_feedback		BOOLEAN
				""",
			"dishes":
				"""
				id 				INTEGER PRIMARY KEY,
				category		TEXT,
				name			TEXT,
				description		TEXT,
				price			INTEGER,
				img				TEXT
				""",
			"categories":
				"""
				id 				INTEGER PRIMARY KEY,
				name			TEXT,
				parent_category TEXT
				""",
			"orders":
				"""
				id 			INTEGER PRIMARY KEY,
				user_id 	INTEGER,
				date 		TEXT,
				dishes		TEXT,
				confirm		BOOLEAN
				""",
			"feedbacks":
				"""
				id 			INTEGER PRIMARY KEY,
				user_id		INTEGER,
				username	TEXT,
				date		TEXT,
				stars		INTEGER,
				feedback 	TEXT,
				confirm		BOOLEAN
				""",
			"promotions":
				"""
				name 			TEXT,
				description 	TEXT,
				img 			TEXT
				"""
		}
		self.columns = columns[self.table]
		self.cursor.execute("CREATE TABLE IF NOT EXISTS {table} ({columns})".format(table=self.table, columns=self.columns))

	def reset(self):
		self.cursor.execute(f"DROP TABLE IF EXISTS '{self.table}'")
		self.cursor.execute("CREATE TABLE IF NOT EXISTS {table} ({columns})".format(table=self.table, columns=self.columns))

	def add(self, data):
		if self.table == "dishes":
			self.cursor.execute("INSERT INTO {table} (category, name, description, price, img) VALUES ({data})".format(table=self.table, data=data))
		elif self.table == "categories":
			self.cursor.execute("INSERT INTO {table} (name, parent_category) VALUES ({data})".format(table=self.table, data=data))
		elif self.table == "orders":
			self.cursor.execute("INSERT INTO {table} (user_id, date, dishes, confirm) VALUES ({data})".format(table=self.table, data=data))
		elif self.table == "feedbacks":
			self.cursor.execute("INSERT INTO {table} (user_id, username, date, stars, feedback, confirm) VALUES ({data})".format(table=self.table, data=data))
		else:
			self.cursor.execute(f"INSERT INTO {self.table} VALUES ({data})")
		self.conn.commit()

	def get(self, item, where):
		self.cursor.execute(f"SELECT {item} FROM {self.table} WHERE {where[0]} = '{where[1]}'")
		return self.cursor.fetchall()

	def update(self, item, value, where):
		self.cursor.execute(f"UPDATE {self.table} SET {item} = '{value}' WHERE {where[0]} = '{where[1]}'")
		self.conn.commit()

	def delete(self, where):
		self.cursor.execute(f"DELETE FROM {self.table} WHERE {where[0]} = '{where[1]}'")
		self.conn.commit()
