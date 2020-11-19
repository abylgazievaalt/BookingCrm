from datetime import date, timedelta

from webapp.models import Price, MealPrice


def get_month_date(month):
    month = int(month)
    if month == 1:
        date1 = date(1, 1, 2020)


def get_room_sum(rdelta, housing, roominess, arrival_date, departure_date, room):
    price_qs = Price.objects.filter(housing=housing, roominess=roominess, from_date__lte=arrival_date,
                                    to_date__gte=arrival_date) | \
               Price.objects.filter(housing=housing, roominess=roominess, from_date__lte=departure_date,
                                    to_date__gte=departure_date) | \
               Price.objects.filter(housing=housing, roominess=roominess, from_date__gte=arrival_date,
                                    to_date__lte=departure_date)
    sum = 0
    if price_qs.count() > 1:
        price_qs = price_qs.order_by('from_date')
        from_dates = []

        for price in price_qs:
            if price.from_date >= arrival_date and price.from_date <= departure_date:
                from_dates.append(price.from_date)

        price_prev = price_qs.first()
        for date in from_dates:
            delta = date - arrival_date
            price_price = price_prev.price
            sum += delta.days * price_price
            arrival_date = date
            price_prev = price_qs.get(from_date=date)

        delta = departure_date - from_dates[-1]
        sum += delta.days * price_prev.price
    elif price_qs.count() == 1:
        price = price_qs.first().price * rdelta.days
        sum += price
    else:
        price = room.default_price * rdelta.days
        sum += price
    return sum


def get_full_reservation_sum(housing, roominess, arrival_date, departure_date, room, count_of_people):
    arrival_date_2 = arrival_date
    rdelta = departure_date - arrival_date_2
    sum = get_room_sum(rdelta, housing, roominess, arrival_date, departure_date, room)
    prices = MealPrice.objects.first()

    days = (departure_date - arrival_date).days
    meal_cost_per_person = prices.dinner
    for i in range(days - 1):
        meal_cost_per_person += prices.breakfast + prices.lunch + prices.dinner
    meal_cost_per_person += prices.breakfast + prices.lunch
    sum += meal_cost_per_person * count_of_people
    return sum


def get_cost_per_person(breakfast, lunch, dinner):
    sum = 0
    if breakfast == True or breakfast == 'true':
        sum += MealPrice.objects.first().breakfast
    if lunch == True or lunch == 'true':
        sum += MealPrice.objects.first().lunch
    if dinner == True or dinner == 'true':
        sum += MealPrice.objects.first().dinner
    return sum


def get_custom_reservation_sum(housing, roominess, arrival_date, departure_date, room, count_of_people, meals, discount):
    arrival_date_2 = arrival_date
    rdelta = departure_date - arrival_date_2
    sum = get_room_sum(rdelta, housing, roominess, arrival_date, departure_date, room)
    meals_sum = 0
    for item in meals:
        meals_sum += count_of_people * get_cost_per_person(item['breakfast'], item['lunch'], item['dinner'])
    sum += meals_sum
    sum -= sum * (int(discount) / 100.0)
    return round(sum)
