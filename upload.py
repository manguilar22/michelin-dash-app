import psycopg2
import pandas as pd


def upload_to_db(db_config):
	records = pd.read_csv('./michelin_my_maps.csv').to_dict('records')
	try:
		connection = psycopg2.connect(**db_config)
		cursor = connection.cursor()
		print(f'connected to db: {dir(cursor)}')
		
		print(records[0].keys())

		insert_query = """
		INSERT INTO restaurants (name, address, location, price, cuisine, longitude, latitude, phone_number, url, website_url, award, green_star, facilities_and_services, description) 
		VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
		"""

		for record in records:
			name = record['Name']
			address = record['Address']
			location = record['Location']
			price = record['Price']
			cuisine = record['Cuisine']
			lon = float(record['Longitude'])
			lat = float(record['Latitude'])
			phone = str(record['PhoneNumber'])
			url = record['Url']
			web_url = record['WebsiteUrl']
			award = record['Award']
			stars = record['GreenStar']
			services = record['FacilitiesAndServices']
			desc = record['Description']
			
			
			try:
				cursor.execute(insert_query, (name, address,location,price,cuisine,lon,lat,phone,url,web_url,award,stars,services,desc,))
				connection.commit()
			except Exception as err:
				print(f'{name} - {err}')
	except Exception as err:
		print(err)
	finally:
		cursor.close()
		connection.close()
