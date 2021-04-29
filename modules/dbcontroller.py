import sqlite3
import os
import traceback
import datetime

DB_PATH = "./modules/SQLite/desko.db"


#============================================================================================| DECORATOR
def connection_session_db(function_to_decorate):											#|
		def the_wrapper_around_the_original_function(params):								#|
			conn = sqlite3.connect(DB_PATH)													#|
			cursor = conn.cursor()															#|
			ret = function_to_decorate(cursor, params)										#|
			cursor.close()																	#|
			conn.commit()																	#|
			conn.close()																	#|
			return ret																		#|
		return the_wrapper_around_the_original_function										#|
#============================================================================================|

@connection_session_db	# CHECK IMAGE IN DB
def check_kc_model_inDB(cursor , params):
	inspected_kc = params['current_kc']
	sql = "SELECT * FROM WHEELS_MODELS WHERE kc_id LIKE {}".format(inspected_kc)
	cursor.execute(sql)
	response = cursor.fetchone() # or use fetchone()
	if response is None:
		return False
	else:
		return True


@connection_session_db	# READ IMAGE FROM DB
def read_image_kc_FromDB(cursor , params):
	read_kc = params['current_kc']
	sql = "SELECT * FROM WHEELS_MODELS WHERE kc_id LIKE {}".format(read_kc)
	cursor.execute(sql)
	response = cursor.fetchone() # or use fetchone()
	if response is None:
		return False
	else:
		binary_frame = response[1]
		#img = cv2.imdecode(np.fromstring(readed_blob, dtype=np.uint8), cv2.IMREAD_COLOR)
		return binary_frame

@connection_session_db	# READ IMAGE FROM DB
def read_nipel_roi_polygons_FromDB(cursor , params):
	read_kc = params['current_kc']
	sql = "SELECT * FROM WHEELS_MODELS WHERE kc_id LIKE {}".format(read_kc)
	cursor.execute(sql)
	response = cursor.fetchone() # or use fetchone()
	if response is None:
		return False
	else:
		nipel_roi_polygons = response[4]
		#img = cv2.imdecode(np.fromstring(readed_blob, dtype=np.uint8), cv2.IMREAD_COLOR)
		return nipel_roi_polygons


@connection_session_db	# READ SETTINGS FROM DB
def read_settings_FromDB(cursor , params):
	setting = params['setting']
	sql = "SELECT {} FROM SETTINGS".format(setting)
	cursor.execute(sql)
	response = cursor.fetchone() # or use fetchone()
	if response is None:
		return False
	else:
		return response[0]


@connection_session_db	# UPDATE SETTINGS FROM DB
def update_settings_FromDB(cursor , params):
	try:
		#table = params['table']
		setting = params['setting']
		value = params['value']
		#sql = "UPDATE {} SET {} = '{}'".format(table, setting, value)
		sql = "UPDATE SETTINGS SET {} = '{}'".format(setting, value)
		cursor.execute(sql)
		#print('done!')
	except:
		print('error!')
		print(traceback.format_exc())


@connection_session_db	# UPDATE SETTINGS FROM DB
def update_wheel_FromDB(cursor , params):
	try:
		setting = params['setting']
		value = params['value']
		current_kc = params['current_kc']
		#sql = "UPDATE {} SET {} = '{}'".format(table, setting, value)
		if setting == 'photo':
			#sql = "UPDATE WHEELS_MODELS SET {} = '{}' WHERE kc_id LIKE {}".format(setting, str(value), current_kc)
			sql = '''UPDATE WHEELS_MODELS SET (photo) = ? WHERE kc_id = ?'''
			data_tuple = (value, current_kc)
			cursor.execute(sql, data_tuple)
			print('done!')
		else:
			sql = "UPDATE WHEELS_MODELS SET {} = '{}' WHERE kc_id LIKE {}".format(setting, value, current_kc)
			cursor.execute(sql)
			print('done!')
	except:
		print('error!')
		print(traceback.format_exc())


@connection_session_db	# UPDATE SETTINGS FROM DB
def add_wheel_inDB(cursor , params):
	try:
		now = datetime.datetime.now()
		kc_id = params['current_kc']
		photo = params['lockedFrameReady']
		center_x = 0
		center_y = 0
		nipel_roi_polygons = params['nipel_roi_polygons']
		date = now.strftime("%Y-%m-%d %H:%M")
		sql = """ INSERT INTO WHEELS_MODELS
			(kc_id, photo, center_x, center_y, nipel_roi_polygons, date) VALUES (?, ?, ?, ?, ?, ?)"""
		data_tuple = (kc_id, photo, center_x, center_y, nipel_roi_polygons, date)
		cursor.execute(sql, data_tuple)
		print('done!')
	except:
		print('error!')
		print(traceback.format_exc())
	# except sqlite3.Error as error:
	# 	print("Failed to insert blob data into sqlite table", error)
	# finally:
	# 	if (sqliteConnection):
	# 		sqliteConnection.close()
	# 		print("the sqlite connection is closed")







# @connection_session_db
# def add_NewBatch_ToDB(cursor, batchID, complete_labeled, images_count):
# 	insertPacket = [(batchID, complete_labeled, images_count)]
# 	cursor.executemany("INSERT INTO BATCHES VALUES (?,?,?)", insertPacket)

# @connection_session_db
# def read_batches_list_FromDB(cursor, batchID, complete_labeled, images_count):
# 	sql = "SELECT * FROM BATCHES"
# 	cursor.execute(sql)
# 	response = cursor.fetchall() # or use fetchone()
# 	return response

# @connection_session_db
# def read_single_batch_info_FromDB(cursor, batchID, complete_labeled, images_count):
# 	sql = "SELECT * FROM BATCHES WHERE UUID LIKE '{}'".format(batchID) 
# 	cursor.execute(sql)
# 	response = cursor.fetchone() # or use fetchone()
# 	return response

# @connection_session_db_classes
# def add_Class_ToDB(cursor, batchID, addedClass):
# 	insertPacket = [(batchID, addedClass)]
# 	cursor.executemany("INSERT INTO SEGMENTATION_CLASSES VALUES (?,?)", insertPacket)

# @connection_session_db_classes
# def read_Classes_FromDB(cursor, batchID, addedClass):
# 	sql = "SELECT * FROM SEGMENTATION_CLASSES WHERE BATCH_UUID LIKE '{}'".format(batchID)
# 	cursor.execute(sql)
# 	response = cursor.fetchall() # or use fetchone()
# 	return response

# @connection_session_db
# def set_ImportedBatch_as_Labeled(cursor, batchID, complete_labeled, images_count):
# 	sql = "UPDATE BATCHES SET COMPLETE_LABELED = 1 WHERE UUID LIKE '{}'".format(batchID) 
# 	cursor.execute(sql)
# 	return True

# @connection_session_db_settings
# def read_settings_FromDB(cursor, parametr, action):
# 	sql = "SELECT '{}' FROM SETTINGS".format(parametr)
# 	cursor.execute(sql)
# 	response = cursor.fetchone() # or use fetchone()
# 	return response

#================================================================================================================================================#
# def convertToBinaryData(filename):
# 	#Convert digital data to binary format
# 	with open(filename, 'rb') as file:
# 		blobData = file.read()
# 	return blobData

# def insertBLOB(kc_id, photo, center_x, center_y, nipel_roi_polygons, date):
# 	try:
# 		sqliteConnection = sqlite3.connect('wheelsdatabase.db')
# 		cursor = sqliteConnection.cursor()
# 		print("Connected to SQLite")
# 		sqlite_insert_blob_query = """ INSERT INTO WHEELS_MODELS
# 								  (kc_id, photo, center_x, center_y, nipel_roi_polygons, date) VALUES (?, ?, ?, ?, ?, ?)"""

# 		empPhoto = convertToBinaryData(photo)
# 		#resume = convertToBinaryData(resumeFile)
# 		# Convert data into tuple format
# 		data_tuple = (kc_id, empPhoto, center_x, center_y, nipel_roi_polygons, date)
# 		cursor.execute(sqlite_insert_blob_query, data_tuple)
# 		sqliteConnection.commit()
# 		print("Image and file inserted successfully as a BLOB into a table")
# 		cursor.close()

# 	except sqlite3.Error as error:
# 		print("Failed to insert blob data into sqlite table", error)
# 	finally:
# 		if (sqliteConnection):
# 			sqliteConnection.close()
# 			print("the sqlite connection is closed")

# #insertBLOB(123, "test.png", 50, 50, 'blabla', '13.05.2020')
# #insertBLOB(2, "David", "E:\pynative\Python\photos\david.jpg", "E:\pynative\Python\photos\david_resume.txt")

# def my_own_func_write(kc_id, photo, center_x, center_y, nipel_roi_polygons, date):
# 	frame = cv2.imread(photo, 0) # 0 - bw, 1 - color
# 	_,enc = cv2.imencode(".png",frame)
# 	#rgb = Image.fromarray(frame, mode=None)


# 	sqliteConnection = sqlite3.connect('wheelsdatabase.db')
# 	cursor = sqliteConnection.cursor()
# 	print("Connected to SQLite")
# 	sqlite_insert_blob_query = """ INSERT INTO WHEELS_MODELS(kc_id, photo, center_x, center_y, nipel_roi_polygons, date) VALUES (?, ?, ?, ?, ?, ?)"""

# 	data_tuple = (kc_id, enc, center_x, center_y, nipel_roi_polygons, date)
# 	cursor.execute(sqlite_insert_blob_query, data_tuple)
# 	sqliteConnection.commit()
# 	print("Image and file inserted successfully as a BLOB into a table")
# 	cursor.close()

# #my_own_func_write(126, "test1.png", 50, 50, 'blabla', '13.05.2020')


# def my_readBlobData(empId):
# 	try:
# 		sqliteConnection = sqlite3.connect('wheelsdatabase.db')
# 		cursor = sqliteConnection.cursor()
# 		print("Connected to SQLite")

# 		#sql_fetch_blob_query = """SELECT * from new_employee where id = ?"""
# 		sql = "SELECT * FROM WHEELS_MODELS WHERE kc_id LIKE '{}'".format(empId)
# 		cursor.execute(sql)
# 		#cursor.execute(sql_fetch_blob_query, (empId,))
# 		record = cursor.fetchone()
		
# 		readed_blob = record[1]
# 		#print()
# 		img = cv2.imdecode(np.fromstring(readed_blob, dtype=np.uint8), cv2.IMREAD_COLOR)
# 		cv2.imwrite('output2.png', img)

# 		cursor.close()

# 	except sqlite3.Error as error:
# 		print("Failed to read blob data from sqlite table", error)
# 	finally:
# 		if (sqliteConnection):
# 			sqliteConnection.close()
# 			print("sqlite connection is closed")


#my_readBlobData(126)
	