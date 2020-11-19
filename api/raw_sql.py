from django.db import connection



def get_count_by_month(year):
    COUNT_BY_MONTH = f'''
    SELECT mon, SUM(cnt) FROM (
                              (SELECT extract(month from t1.arrival_date) mon,
                                      COUNT(*) as                         cnt
                               FROM webapp_reservation t1
                               where (extract(year from t1.arrival_date) = {year}
                                  OR extract(year from t1.departure_date) = {year})
                                 AND t1.status = 'active'
                               GROUP BY mon
                               order by mon)
                              UNION
                              (SELECT extract(month from t1.departure_date) mon,
                                      COUNT(*) as                           cnt
                               FROM webapp_reservation t1
                               where (extract(year from t1.departure_date) = {year}
                                 AND extract(month from t1.arrival_date) != extract(month from t1.departure_date))
                                 AND t1.status = 'active'
                               GROUP BY mon
                               order by mon)
                          ) a
    GROUP BY mon
    ORDER BY mon
    '''
    with connection.cursor() as cursor:
        cursor.execute(COUNT_BY_MONTH)
        row = cursor.fetchall()
    return row

def get_count_housing(month, year):
    COUNT_BY_HOUSING_DATE = f'''
    select wh.name, count(res.id), wh.id from webapp_reservation res
            join webapp_guestroom wg on res.room_id = wg.id
            join webapp_housing wh on wg.housing_id = wh.id
            where ((extract(month from res.arrival_date) = {month} and extract(year from res.arrival_date) = {year}) or
                    (extract(month from res.departure_date) = {month} and extract(year from res.departure_date) = {year}))
                    AND res.status = 'active'
    group by 3, 1
    order by 1
'''
    with connection.cursor() as cursor:
        cursor.execute(COUNT_BY_HOUSING_DATE)
        row = cursor.fetchall()
    return row
