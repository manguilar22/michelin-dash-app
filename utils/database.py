from psycopg2 import sql

import psycopg2, psycopg2.extras
import logging

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger(__file__)

def get_locations(config, location_type):
    if location_type == 'country':
        with psycopg2.connect(**config) as db:
            with db.cursor() as cursor:
                cursor.execute('SELECT DISTINCT (location) FROM restaurants')
                result = cursor.fetchall()
                records = set()
                for record in result:
                    string = record[0].split(',', 2)
                    if len(string) == 1:
                        records.add(string[0].strip())
                    else:
                        records.add(string[1].strip())
                return list(records)
    else:
        with psycopg2.connect(**config) as db:
            with db.cursor() as cursor:
                cursor.execute('SELECT DISTINCT (location) FROM restaurants')
                result = cursor.fetchall()
                data = [x[0] for x in result]
                return data


def get_restaurant_features(config, location_type, location_value):
    with psycopg2.connect(**config) as db:
        with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            if location_type == 'country':
                sql_statement = 'SELECT * FROM restaurants WHERE location ~ \'{}\''.format(location_value)
                cursor.execute(sql_statement)
                result = cursor.fetchall()

                award = set([x['award'] for x in result])
                price = set([x['price'] for x in result])
            else:
                sql_statement = 'SELECT * FROM restaurants WHERE location = \'{}\''.format(location_value)
                cursor.execute(sql_statement)
                result = cursor.fetchall()

                award = set([x['award'] for x in result])
                price = set([x['price'] for x in result])

    return price, award


def get_restaurants(config, location_type, locations_value, prices, awards):
    if location_type == 'country':
        sql_statement = 'SELECT * FROM restaurants WHERE location ~ \'{}\''.format(locations_value)
    else:
        sql_statement = 'SELECT * FROM restaurants WHERE location = \'{}\''.format(locations_value)

    if prices and awards:
        prices_condition = ','.join([f'\'{x}\'' for x in prices])
        awards_condition = ','.join([f'\'{x}\'' for x in awards])
        predicate = f'price IN ({prices_condition}) AND award IN ({awards_condition})'
        sql_statement = f'{sql_statement} AND {predicate}'
    elif prices:
        prices_condition = ','.join([f'\'{x}\'' for x in prices])
        sql_statement = f'{sql_statement} AND price IN ({prices_condition})'
    elif awards:
        awards_condition = ','.join([f'\'{x}\'' for x in awards])
        sql_statement = f'{sql_statement} AND award IN ({awards_condition})'

    with psycopg2.connect(**config) as db:
        with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(sql_statement)
            records = cursor.fetchall()
            logger.info(f'location_type = {location_type} prices = {prices} awards = {awards} size = {len(records)} value = {locations_value} sql = {sql_statement}')
            return records, sql_statement
