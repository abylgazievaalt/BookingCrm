from datetime import timedelta

from dateutil.rrule import rrule, MONTHLY
from django.db.models import Min
from drf_writable_nested import WritableNestedModelSerializer, NestedUpdateMixin

from api.utils import get_full_reservation_sum, get_custom_reservation_sum
from webapp.models import Guestroom, Reservation, Service, Housing, Accessories, Comfort, \
    Gallery, SIDE_CHOICES, \
    Feedback, AboutUs, AboutUsNumbers, Contacts, RoomGallery, Maid, Manager, Staff, Cleaning, Meal, FeedbackReply, \
    Price, GalleryCategory, Roominess, Phone, RoomView, Floor, MainPage, TypeOfRoom, Restriction, Payment, Landing, \
    SocialNetwork, GalleryPhoto, ServiceLanding, MealPrice
from rest_framework import serializers
import os
from rest_auth.models import TokenModel


class TokenSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = TokenModel
        fields = ('key',  'username')

    @staticmethod
    def get_username(obj):
        user = obj.user
        return user.username


def diff_months(d1, d2):
    months = [dt.strftime("%m") for dt in rrule(MONTHLY, dtstart=d1, until=d2)]
    return months


class RoomGallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomGallery
        fields = ('id', 'image', 'room_id')


class MaidSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    class Meta:
        model = Maid
        fields = ('id', 'first_name', 'last_name')

    def get_first_name(self, obj):
        return obj.fk.first_name

    def get_last_name(self, obj):
        return obj.fk.last_name


class ManagerSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    class Meta:
        model = Manager
        fields = ('id', 'first_name', 'last_name')

    def get_first_name(self, obj):
        return obj.fk.first_name

    def get_last_name(self, obj):
        return obj.fk.last_name


class AdministratorSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    class Meta:
        model = Maid
        fields = ('id', 'first_name', 'last_name')

    def get_first_name(self, obj):
        return obj.fk.first_name

    def get_last_name(self, obj):
        return obj.fk.last_name


class AccessoriesListSerializer(serializers.ModelSerializer):
    date_created = serializers.DateField(format='%d-%m-%Y')
    class Meta:
        model = Accessories
        fields = ('id', 'name', 'image', 'date_created')


class AccessoriesCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Accessories
        fields = ('id', 'name', 'image')


class ComfortListSerializer(serializers.ModelSerializer):
    date_created = serializers.DateField(format='%d-%m-%Y')
    class Meta:
        model = Comfort
        fields = ('id', 'name', 'image', 'date_created')


class ComfortCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comfort
        fields = ('id', 'name', 'image')


class ServiceListSerializer(serializers.ModelSerializer):
    image = serializers.FileField(max_length=None, use_url=True)

    class Meta:
        model = Service
        fields = ('id', 'name', 'description', 'image')


class ServiceLandingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceLanding
        fields = ('service',)


class ServiceLandingSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='service__name')
    image = serializers.SerializerMethodField()
    description = serializers.CharField(source='service__description')

    class Meta:
        model = ServiceLanding
        fields = ('id', 'name', 'description', 'image')

    def get_image(self, obj):
        request = self.context['request']
        image = None
        try:
            image = f'{request.scheme}://{request.META["HTTP_HOST"]}/uploads/{obj["service__image"]}'
        except:
            pass
        return image


class ServiceCreateSerializer(serializers.ModelSerializer):
    image = serializers.FileField(max_length=None, use_url=True, required=False)

    class Meta:
        model = Service
        fields = ('id', 'name', 'description', 'image')
        # optional_fields = ['name', 'description']


class RestrictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restriction
        fields = ('id', 'text', 'image')


class RoomSerializer(serializers.ModelSerializer):
    housing_name = serializers.SerializerMethodField()
    room_galleries = RoomGallerySerializer(many=True, read_only=True)
    accessories_list = serializers.SerializerMethodField()
    comforts_list = serializers.SerializerMethodField()
    services_list = serializers.SerializerMethodField()
    # restrictions_list = serializers.SerializerMethodField()
    roominess_name = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    month = serializers.SerializerMethodField()
    type_name = serializers.SerializerMethodField()
    floor_name = serializers.SerializerMethodField()
    unique_number = serializers.SerializerMethodField()
    view_name = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    side_name = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()

    class Meta:
        model = Guestroom
        fields = ('id', 'distance', 'unique_number', 'type', 'type_name', 'roominess', 'roominess_name', 'housing', 'housing_name',
                  'view', 'view_name', 'beds_count', 'floor', 'floor_name', 'description', 'side', 'side_name', 'size',
                  'room_galleries', 'accessories', 'accessories_list', 'comfort', 'comforts_list',
                  'service', 'services_list', 'price', 'month', 'longitude', 'latitude')

    def get_longitude(self, obj):
        try:
            return obj.housing.longitude
        except:
            return None

    def get_latitude(self, obj):
        try:
            return obj.housing.latitude
        except:
            return None

    def get_side_name(self, obj):
        try:
            ind = 0
            if obj.side == 'north':
                ind = 0
            elif obj.side == 'south':
                ind = 1
            elif obj.side == 'west':
                ind = 2
            elif obj.side == 'east':
                ind = 3
            return SIDE_CHOICES[ind][1]
        except:
            return None

    def get_view_name(self, obj):
        try:
            return obj.view.view
        except:
            return None

    def get_type_name(self, obj):
        try:
            return obj.type.type
        except:
            return None

    def get_distance(self, obj):
        try:
            return "До озера %s" % obj.housing.distance
        except:
            return None

    def get_view_name(self, obj):
        try:
            return obj.view.view
        except:
            return None

    def get_unique_number(self, obj):
        try:
            return str(obj)
        except:
            return None

    def get_floor_name(self, obj):
        try:
            return obj.floor.floor
        except:
            return None

    def get_accessories_list(self, obj):
        request = self.context['request']
        serializer = AccessoriesCreateSerializer(many=True, instance=obj.accessories)
        for item in serializer.data:
            item['image'] = f'{request.scheme}://{request.META["HTTP_HOST"]}{item["image"]}'
        return serializer.data

    def get_comforts_list(self, obj):
        request = self.context['request']
        serializer = ComfortCreateSerializer(many=True, instance=obj.comfort)
        for item in serializer.data:
            item['image'] = f'{request.scheme}://{request.META["HTTP_HOST"]}{item["image"]}'
        return serializer.data

    def get_services_list(self, obj):
        request = self.context['request']
        serializer = ServiceCreateSerializer(many=True, instance=obj.service)
        for item in serializer.data:
            item['image'] = f'{request.scheme}://{request.META["HTTP_HOST"]}{item["image"]}'
        return serializer.data

    def get_price(self, obj):
        return obj.get_price()

    def get_month(self, obj):
        try:
            price = Price.objects.filter(room_type=obj.type, roominess=obj.roominess, housing=obj.housing).order_by('price')[0]
            months = diff_months(price.from_date, price.to_date)
        except:
            return None

    # def create(self, validated_data):
    #     gallery = self.context['request'].data.getlist('room_galleries')
    #     accessories = validated_data.pop('accessories')
    #     comfort = validated_data.pop('comfort')
    #     service = validated_data.pop('service')
    #     new_room = Guestroom.objects.create(**validated_data)
    #     new_room.accessories.add(*accessories)
    #     new_room.comfort.add(*comfort)
    #     new_room.service.add(*service)
    #
    #     for i in gallery:
    #         new_room.room_galleries.create(image=i)
    #     return new_room

    def get_housing_name(self, obj):
        try:
            return obj.housing.name
        except:
            return None

    def get_roominess_name(self, obj):
        try:
            return obj.roominess.roominess_name
        except:
            return None


class FullRoomSerializer(WritableNestedModelSerializer):
    housing_name = serializers.SerializerMethodField()
    room_galleries = RoomGallerySerializer(many=True, read_only=True)
    accessories_list = serializers.SerializerMethodField()
    comforts_list = serializers.SerializerMethodField()
    services_list = serializers.SerializerMethodField()
    # restrictions_list = serializers.SerializerMethodField()
    roominess_name = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    # month = serializers.SerializerMethodField()
    floor_name = serializers.SerializerMethodField()
    unique_number = serializers.SerializerMethodField()
    type_name = serializers.SerializerMethodField()
    housing_name = serializers.SerializerMethodField()
    view_name = serializers.SerializerMethodField()
    side_name = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()

    class Meta:
        model = Guestroom
        fields = ('id', 'unique_number', 'number', 'type', 'type_name', 'roominess', 'roominess_name', 'housing', 'beds_count',
                  'housing_name', 'view', 'view_name', 'housing_name', 'floor', 'floor_name', 'description',
                  'side', 'side_name', 'size', 'image', 'room_galleries', 'accessories', 'accessories_list', 'comfort', 'comforts_list',
                  'service', 'services_list', 'price', 'default_price', 'longitude',
                  'latitude')

    def get_longitude(self, obj):
        try:
            return obj.housing.longitude
        except:
            return None

    def get_latitude(self, obj):
        try:
            return obj.housing.latitude
        except:
            return None

    def get_side_name(self, obj):
        try:
            ind = 0
            if obj.side == 'north':
                ind = 0
            elif obj.side == 'south':
                ind = 1
            elif obj.side == 'west':
                ind = 2
            elif obj.side == 'east':
                ind = 3
            return SIDE_CHOICES[ind][1]
        except:
            return None

    def get_view_name(self, obj):
        try:
            return obj.view.view
        except:
            return None

    def get_type_name(self, obj):
        try:
            return obj.type.type
        except:
            return None

    def get_unique_number(self, obj):
        try:
            return str(obj)
        except:
            return None

    def get_floor_name(self, obj):
        try:
            return obj.floor.floor
        except:
            return None

    def get_accessories_list(self, obj):
        request = self.context['request']
        serializer = AccessoriesCreateSerializer(many=True, instance=obj.accessories)
        for item in serializer.data:
            item['image'] = f'{request.scheme}://{request.META["HTTP_HOST"]}{item["image"]}'
        return serializer.data

    def get_comforts_list(self, obj):
        request = self.context['request']
        serializer = ComfortCreateSerializer(many=True, instance=obj.comfort)
        for item in serializer.data:
            item['image'] = f'{request.scheme}://{request.META["HTTP_HOST"]}{item["image"]}'
        return serializer.data

    def get_services_list(self, obj):
        request = self.context['request']
        serializer = ServiceCreateSerializer(many=True, instance=obj.service)
        for item in serializer.data:
            item['image'] = f'{request.scheme}://{request.META["HTTP_HOST"]}{item["image"]}'
        return serializer.data

    def get_price(self, obj):
        try:
            return obj.get_price()
        except:
            return None

    # def get_month(self, obj):
    #     try:
    #         price = Price.objects.filter(room_type=obj.type, roominess=obj.roominess, housing=obj.housing).order_by('price')[0]
    #         months = diff_months(price.from_date, price.to_date)
    #     except:
    #         return None

    def get_housing_name(self, obj):
        try:
            return obj.housing.name
        except:
            return None

    def get_roominess_name(self, obj):
        try:
            return obj.roominess.roominess_name
        except:
            return None

    def create(self, validated_data):
        gallery = self.context['request'].data.getlist('room_galleries')
        accessories = validated_data.pop('accessories')
        comfort = validated_data.pop('comfort')
        service = validated_data.pop('service')
        new_room = Guestroom.objects.create(**validated_data)
        new_room.accessories.add(*accessories)
        new_room.comfort.add(*comfort)
        new_room.service.add(*service)
        for i in gallery:
            new_room.room_galleries.create(image=i)
        return new_room

    def update(self, instance, validated_data):
        instance.number = validated_data.get('number', instance.number)
        instance.type = validated_data.get('type', instance.type)
        instance.roominess = validated_data.get('roominess', instance.roominess)
        instance.housing = validated_data.get('housing', instance.housing)
        instance.view = validated_data.get('view', instance.view)
        instance.beds_count = validated_data.get('beds_count', instance.beds_count)
        instance.floor = validated_data.get('floor', instance.floor)
        instance.description = validated_data.get('description', instance.description)
        instance.side = validated_data.get('side', instance.side)
        instance.size = validated_data.get('size', instance.size)
        instance.default_price = validated_data.get('default_price', instance.default_price)

        if self.context['request'].data.get('image'):
            if instance.image:
                if os.path.isfile(instance.image.path):
                    os.remove(instance.image.path)
        instance.image.delete()
        instance.image = self.context['request'].data.get('image')

        if self.context['request'].data.getlist('room_galleries'):
            for i in instance.room_galleries.all():
                if i.image:
                    if os.path.isfile(i.image.path):
                        os.remove(i.image.path)
            instance.room_galleries.all().delete()
            for i in self.context['request'].data.getlist('room_galleries'):
                instance.room_galleries.create(image=i, room=instance)

        if validated_data.get('accessories'):
            print(validated_data.get('accessories'))
            instance.accessories.clear()
            accessories = validated_data.pop('accessories')
            for item in accessories:
                instance.accessories.add(item)
        else:
            # instance.accessories.clear()xx
            instance.save()
        if validated_data.get('comfort'):
            instance.comfort.clear()
            comforts = validated_data.pop('comfort')
            for item in comforts:
                instance.comfort.add(item)
        else:
            # instance.comfort.clear()
            instance.save()
        if validated_data.get('service'):
            instance.service.clear()
            services = validated_data.pop('service')
            for item in services:
                instance.service.add(item)
        else:
            # instance.service.clear()
            instance.save()
        return instance


class FullRoomSerializer2(WritableNestedModelSerializer):
    class Meta:
        model = Guestroom
        fields = ('id', 'furniture',)

    def update(self, instance, validated_data):
        furniture = validated_data.get('furniture')
        instance.furniture = furniture
        instance.save()
        return instance


class RoomBriefSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Guestroom
        fields = ('id', 'name',)

    def get_name(self, obj):
        return str(obj)


class RoomListSerializer(serializers.ModelSerializer):
    housing_name = serializers.SerializerMethodField()
    roominess_name = serializers.SerializerMethodField()
    room_galleries = RoomGallerySerializer(many=True, read_only=True)
    price = serializers.SerializerMethodField()
    unique_number = serializers.SerializerMethodField()
    floor_name = serializers.SerializerMethodField()
    type_name = serializers.SerializerMethodField()
    side_name = serializers.SerializerMethodField()

    class Meta:
        model = Guestroom
        fields = ('id', 'unique_number', 'type', 'type_name', 'roominess', 'roominess_name', 'housing', 'housing_name', 'size',
                'beds_count', 'side', 'side_name', 'floor', 'floor_name', 'room_galleries', 'price')

    def get_side_name(self, obj):
        try:
            ind = 0
            if obj.side == 'north':
                ind = 0
            elif obj.side == 'south':
                ind = 1
            elif obj.side == 'west':
                ind = 2
            elif obj.side == 'east':
                ind = 3
            return SIDE_CHOICES[ind][1]
        except:
            return None

    def get_floor_name(self, obj):
        try:
            return obj.floor.floor
        except:
            return None

    def get_type_name(self, obj):
        try:
            return obj.type.type
        except:
            return None

    def get_unique_number(self, obj):
        try:
            return str(obj)
        except:
            return None

    def get_price(self, obj):
        try:
            return obj.get_price()
        except:
            return None

    def get_housing_name(self, obj):
        try:
         return obj.housing.name
        except:
            return None

    def get_roominess_name(self, obj):
        try:
            return obj.roominess.roominess_name
        except:
            return None


class CrmRoomListSerializer(serializers.ModelSerializer):
    housing_name = serializers.SerializerMethodField()
    roominess_name = serializers.SerializerMethodField()
    # room_galleries = RoomGallerySerializer(many=True, read_only=True)
    price = serializers.SerializerMethodField()
    unique_number = serializers.SerializerMethodField()
    floor_name = serializers.SerializerMethodField()
    type_name = serializers.SerializerMethodField()
    side_name = serializers.SerializerMethodField()

    class Meta:
        model = Guestroom
        fields = ('id', 'unique_number', 'type', 'type_name', 'roominess', 'roominess_name', 'housing', 'housing_name', 'size',
                'beds_count', 'side', 'side_name', 'floor', 'floor_name', 'image', 'price')

    def get_side_name(self, obj):
        try:
            ind = 0
            if obj.side == 'north':
                ind = 0
            elif obj.side == 'south':
                ind = 1
            elif obj.side == 'west':
                ind = 2
            elif obj.side == 'east':
                ind = 3
            return SIDE_CHOICES[ind][1]
        except:
            return None

    def get_floor_name(self, obj):
        try:
            return obj.floor.floor
        except:
            return None

    def get_type_name(self, obj):
        try:
            return obj.type.type
        except:
            return None

    def get_unique_number(self, obj):
        try:
            return str(obj)
        except:
            return None

    def get_price(self, obj):
        try:
            return obj.get_price()
        except:
            return None

    def get_housing_name(self, obj):
        try:
         return obj.housing.name
        except:
            return None

    def get_roominess_name(self, obj):
        try:
            return obj.roominess.roominess_name
        except:
            return None


class AvailableRoomListSerializer(serializers.ModelSerializer):
    housing_name = serializers.SerializerMethodField()
    roominess_name = serializers.SerializerMethodField()
    room_galleries = RoomGallerySerializer(many=True, read_only=True)
    price = serializers.SerializerMethodField()
    floor_name = serializers.SerializerMethodField()
    type_name = serializers.SerializerMethodField()
    side_name = serializers.SerializerMethodField()

    class Meta:
        model = Guestroom
        fields = ('id', 'type_name', 'roominess_name', 'housing_name', 'size',
                'beds_count', 'side_name', 'floor_name', 'room_galleries', 'price')

    def get_side_name(self, obj):
        try:
            ind = 0
            if obj.side == 'north':
                ind = 0
            elif obj.side == 'south':
                ind = 1
            elif obj.side == 'west':
                ind = 2
            elif obj.side == 'east':
                ind = 3
            return SIDE_CHOICES[ind][1]
        except:
            return None

    def get_floor_name(self, obj):
        try:
            return obj.floor.floor
        except:
            return None

    def get_type_name(self, obj):
        try:
            return obj.type.type
        except:
            return None

    def get_price(self, obj):
        try:
            return obj.get_price()
        except:
            return None

    def get_housing_name(self, obj):
        try:
         return obj.housing.name
        except:
            return None

    def get_roominess_name(self, obj):
        try:
            return obj.roominess.roominess_name
        except:
            return None


class MealSerializer(serializers.ModelSerializer):
    date = serializers.DateField(format='%d-%m-%Y')

    class Meta:
        model = Meal
        fields = ('date', 'breakfast', 'lunch', 'dinner')


class ReservationSerializer(serializers.ModelSerializer):
    room = RoomSerializer
    arrival_date = serializers.DateField(input_formats=['%d-%m-%Y', ], format='%d-%m-%Y')
    departure_date = serializers.DateField(input_formats=['%d-%m-%Y', ], format='%d-%m-%Y')

    class Meta:
        model = Reservation
        fields = ('id', 'uuid', 'room', 'arrival_date', 'departure_date', 'count_of_people', 'name', 'last_name',
                  'phone', 'email', 'comment', 'payment_type', 'total_sum', )
        read_only_fields = ('total_sum',)

    def create(self, validated_data):
        arrival_date = validated_data.get('arrival_date')
        departure_date = validated_data.get('departure_date')
        room = validated_data.get('room')
        reservations = Reservation.objects.filter(status='active', arrival_date__lte=departure_date - timedelta(days=1),
                                                  departure_date__gte=arrival_date + timedelta(days=1), room=room)
        if reservations:
            raise serializers.ValidationError('Номер уже забронирован')

        if arrival_date >= departure_date:
            raise serializers.ValidationError("Дата выезда должна быть после даты заезда")
        instance = Reservation.objects.create(**validated_data)

        days = (departure_date - arrival_date).days

        date_date = arrival_date + timedelta(1)
        Meal.objects.create(reservation=instance, date=arrival_date, breakfast=False, lunch=False, dinner=True)
        for i in range(days - 1):
            Meal.objects.create(reservation=instance, date=date_date, breakfast=True, lunch=True, dinner=True)
            date_date = arrival_date + timedelta(days=1)
        Meal.objects.create(reservation=instance, date=departure_date, breakfast=True, lunch=True, dinner=False)

        # room = Guestroom.objects.get(id=room)
        housing = room.housing
        roominess = room.roominess
        count_of_people = validated_data.get('count_of_people')
        sum = get_full_reservation_sum(housing, roominess, arrival_date, departure_date, room, count_of_people)
        instance.total_sum = sum
        instance.count_calendar = count_of_people
        instance.save()
        return instance


class ReservationPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ('id', 'uuid', 'payment_type', 'total_sum', )
        read_only_fields = ('total_sum',)


class ReservationCrmSerializer(WritableNestedModelSerializer):
    room = RoomSerializer
    meals = MealSerializer(many=True, required=False)
    arrival_date = serializers.DateField(input_formats=['%d-%m-%Y', ], format='%d-%m-%Y')
    departure_date = serializers.DateField(input_formats=['%d-%m-%Y', ], format='%d-%m-%Y')

    class Meta:
        model = Reservation
        fields = ('id', 'client_type', 'room', 'count_calendar', 'arrival_date', 'departure_date', 'count_of_people', 'name', 'last_name',
                  'phone', 'email', 'payment_type', 'payment_status', 'total_sum', 'meals', 'status', 'discount')

    def create(self, validated_data):
        arrival_date = validated_data.get('arrival_date')
        departure_date = validated_data.get('departure_date')
        room = validated_data.get('room')
        discount = validated_data.get('discount')
        reservations = Reservation.objects.filter(status='active', arrival_date__lte=departure_date - timedelta(days=1),
                                                  departure_date__gte=arrival_date + timedelta(days=1), room__id=room.id)
        if reservations.count() > 0:
            raise serializers.ValidationError('Номер уже забронирован')

        if arrival_date >= departure_date:
            raise serializers.ValidationError("Дата выезда должна быть после даты заезда")
        try:
            meals = validated_data.pop('meals')
        except:
            meals = dict()
        instance = Reservation.objects.create(**validated_data)
        for item in meals:
            Meal.objects.create(**item, reservation=instance)

        housing = room.housing
        roominess = room.roominess
        count_calendar = validated_data.get('count_calendar')
        sum = get_custom_reservation_sum(housing, roominess, arrival_date, departure_date, room, count_calendar, meals, discount)
        instance.total_sum = sum
        instance.save()
        return instance

    def update(self, instance, validated_data):
        arrival_date = instance.arrival_date
        departure_date = instance.departure_date
        count_calendar = instance.count_calendar
        discount = instance.discount
        meals = instance.meals.values()

        update_price = False
        if validated_data.get("arrival_date") and not validated_data.get("departure_date"):
            update_price = True
            arrival_date = validated_data.get("arrival_date")
            if arrival_date >= instance.departure_date:
                raise serializers.ValidationError('Дата заезда должна быть раньше даты выезда')
        if validated_data.get("departure_date") and not validated_data.get("arrival_date"):
            update_price = True
            departure_date = validated_data.get("departure_date")
            if departure_date <= instance.arrival_date:
                raise serializers.ValidationError('Дата выезда должна быть позже даты заезда')
        if validated_data.get("departure_date") and validated_data.get("arrival_date"):
            update_price = True
            arrival_date = validated_data.get("arrival_date")
            departure_date = validated_data.get("departure_date")
            if departure_date <= arrival_date:
                raise serializers.ValidationError('Дата выезда должна быть позже даты заезда')

        if validated_data.get('meals'):
            update_price = True
            meals = validated_data.get('meals')
        if validated_data.get('count_calendar'):
            update_price = True
            count_calendar = validated_data.get('count_calendar')
        if validated_data.get('discount'):
            update_price = True
            discount = validated_data.get('discount')

        relations, reverse_relations = self._extract_relations(validated_data)

        # Create or update direct relations (foreign key, one-to-one)
        self.update_or_create_direct_relations(
            validated_data,
            relations,
        )

        # Update instance
        instance = super(NestedUpdateMixin, self).update(
            instance,
            validated_data,
        )
        self.update_or_create_reverse_relations(instance, reverse_relations)
        self.delete_reverse_relations_if_need(instance, reverse_relations)

        if update_price:
            room = instance.room
            housing = room.housing
            roominess = room.roominess
            sum = get_custom_reservation_sum(housing, roominess, arrival_date, departure_date, room, count_calendar, meals, discount)
            instance.total_sum = sum
            instance.save()
        return instance


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeOfRoom
        exclude =[]


class RoominessListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roominess
        fields = ('id', 'roominess', 'roominess_name', 'image', 'price_from')


class RoominessBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roominess
        fields = ('id', 'roominess_name', 'price_from')


class RoominessCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roominess
        exclude = ['cropping', 'date_created']


class RoomListHousingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Housing
        fields = ('id', 'name')


class GalleryCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryCategory
        fields = ('id', 'name')


class GalleryPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryPhoto
        fields = ('id', 'gallery', 'image')


class GallerySerializer(serializers.ModelSerializer):
    gallery_photos = GalleryPhotoSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = Gallery
        fields = ('id', 'name', 'image', 'gallery_photos')


class GalleryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gallery
        fields = ('id', 'name', 'image')


class GalleryRetrieveSerializer(WritableNestedModelSerializer):
    photos_list = GalleryPhotoSerializer(source='gallery_photos', many=True)

    class Meta:
        model = Gallery
        fields = ('id', 'name', 'photos_list')


class FeedbackSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format='%d-%m-%Y')

    class Meta:
        model = Feedback
        fields = ('id', 'name', 'last_name', 'email', 'phone', 'comment', 'date', 'is_replied')


class FeedbackCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Feedback
        fields = ('id', 'name', 'last_name', 'email', 'phone', 'comment',)


class AboutUsNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutUsNumbers
        fields = ('id', 'quantity', 'description')


class AboutInfoNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutUsNumbers
        fields = ('id', 'quantity', 'description')


class AboutInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutUs
        fields = ('id', 'description', 'full_description',)


class MealPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealPrice
        fields = ('breakfast', 'lunch', 'dinner',)


class AboutUsSerializer(WritableNestedModelSerializer):

    class Meta:
        model = AboutUs
        fields = ('id', 'image', 'description', 'full_description', )

    def update(self, instance, validated_data):
        try:
            instance.description = validated_data.pop('description')
        except:
            pass
        try:
            instance.full_description = validated_data.pop('full_description')
        except:
            pass
        try:
            image = self.context['request'].data.get('image')
            if image:
                if os.path.isfile(instance.image.path):
                    os.remove(instance.image.path)
                instance.image = image
        except:
            pass

        instance.save()
        return instance


class PhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phone
        exclude = []


class PhoneBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phone
        exclude = ['contacts']


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contacts
        fields = ('id', 'address', 'phone', 'phone2', 'email')


class SocialNetworkSerializer(serializers.ModelSerializer):
    icon = serializers.FileField()
    class Meta:
        model = SocialNetwork
        fields = ('id', 'name', 'link', 'icon',)


class StaffSerializer(serializers.ModelSerializer):
    date_created = serializers.DateField(format='%d-%m-%Y')

    class Meta:
        model = Staff
        fields = ('id', 'role', 'first_name', 'last_name', 'middle_name', 'date_created')


class StaffCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Staff
        fields = ('id', 'role', 'first_name', 'last_name', 'middle_name',)


class CleaningStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ('id', 'first_name', 'last_name', )


class CleaningMaidSerializer(serializers.ModelSerializer):
    fk = CleaningStaffSerializer(many=False, read_only=False)

    class Meta:
        model = Maid
        fields = ('fk',)


class MainPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainPage
        fields = ('id', 'heading', 'background', 'show_video')


class MainPageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainPage
        fields = ('heading', 'background', 'darkening', 'video', 'show_video')


class CleaningListSerializer(serializers.ModelSerializer):
    maids_list = serializers.SerializerMethodField()
    number = serializers.SerializerMethodField()
    housing_name = serializers.SerializerMethodField()
    room_type = serializers.SerializerMethodField()
    date = serializers.DateField(format='%d-%m-%Y')
    start_time = serializers.TimeField(format='%I:%M')
    end_time = serializers.TimeField(format='%I:%M')

    class Meta:
        model = Cleaning
        fields = ('id', 'room_type', 'room', 'number', 'housing', 'housing_name', 'floor', 'maids', 'maids_list',
                  'status', 'date', 'start_time', 'end_time')

    def get_room_type(self, obj):
        try:
            return obj.room_type.type
        except:
            return None

    def get_number(self, obj):
        try:
            return obj.room.number
        except:
            return None

    def get_housing_name(self, obj):
        try:
            return obj.room.housing.name
        except:
            return None

    def get_maids_list(self, obj):
        try:
            request = self.context['request']
            serializer = CleaningMaidSerializer(many=True, instance=obj.maids)
            return serializer.data
        except:
            return None


class CleaningDetailSerializer(serializers.ModelSerializer):
    maids_list = serializers.SerializerMethodField()
    room_number = serializers.SerializerMethodField()
    housing_name = serializers.SerializerMethodField()
    room_type_name = serializers.SerializerMethodField()
    date = serializers.DateField(format='%d-%m-%Y')
    start_time = serializers.TimeField(format='%I:%M')
    end_time = serializers.TimeField(format='%I:%M')

    class Meta:
        model = Cleaning
        fields = ('id', 'room', 'room_number', 'room_type', 'room_type_name', 'housing', 'housing_name', 'floor', 'maids', 'maids_list',
                  'status', 'date', 'start_time', 'end_time')

    def get_room_type_name(self, obj):
        try:
            return obj.room.type.type
        except:
            return None

    def get_room_number(self, obj):
        try:
            return obj.room.number
        except:
            return None

    def get_housing_name(self, obj):
        try:
            return obj.room.housing.name
        except:
            return None

    def get_maids_list(self, obj):
        try:
            request = self.context['request']
            serializer = CleaningMaidSerializer(many=True, instance=obj.maids)
            return serializer.data
        except:
            return None

    # def create(self, validated_data):
    #     room_type = validated_data.get('room_type')
    #     return Cleaning.objects.create(room_type=room_type, **validated_data)


class FeedbackReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackReply
        exclude = ('subject', )

    def create(self, validated_data):
        feedback = FeedbackReply.objects.create(**validated_data)
        feedback.send_mail()
        return feedback


class PriceSerializer(serializers.ModelSerializer):
    room_type_name = serializers.SerializerMethodField()
    roominess_name = serializers.SerializerMethodField()
    housing_name = serializers.SerializerMethodField()
    from_date = serializers.DateField(format='%d-%m-%Y')
    to_date = serializers.DateField(format='%d-%m-%Y')

    class Meta:
        model = Price
        fields = ('id', 'room_type', 'room_type_name', 'roominess', 'roominess_name',
                  'housing', 'housing_name', 'from_date', 'to_date', 'price')

    def get_room_type_name(self, obj):
        try:
            return obj.room_type.type
        except:
            return None

    def get_housing_name(self, obj):
        try:
            return obj.housing.name
        except:
            return None

    def get_roominess_name(self, obj):
        try:
            return obj.roominess.roominess_name
        except:
            return None


class PriceListSerializer(serializers.ModelSerializer):
    roominess_name = serializers.SerializerMethodField()
    housing_name = serializers.SerializerMethodField()
    period = serializers.SerializerMethodField()

    class Meta:
        model = Price
        fields = ('id', 'housing_name', 'roominess_name', 'period')

    def get_housing_name(self, obj):
        try:
            return obj.housing.name
        except:
            return None

    def get_period(self, obj):
        from_date = '.'.join(["{:02d}".format(obj.from_date.day), "{:02d}".format(obj.from_date.month)])
        to_date = '.'.join(["{:02d}".format(obj.to_date.day), "{:02d}".format(obj.to_date.month)])
        period = '-'.join([from_date, to_date])
        return period

    def get_roominess_name(self, obj):
        try:
            return obj.roominess.roominess_name
        except:
            return None


class RoomViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomView
        exclude = []


class FloorSerializer(WritableNestedModelSerializer):
    roominess_list = serializers.SerializerMethodField()

    class Meta:
        model = Floor
        fields = ('id', 'floor', 'housing', 'roominess', 'roominess_list')

    def get_roominess_list(self, obj):
        serializer = RoominessBriefSerializer(many=True, instance=obj.roominess)
        return serializer.data


class HousingSerializer(WritableNestedModelSerializer):
    floors = FloorSerializer(many=True, required=False)

    class Meta:
        model = Housing
        fields = ('id', 'name', 'types', 'floors', 'distance', 'active', 'longitude', 'latitude')


class PaymentSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format='%d-%m-%Y %H:%M', read_only=True)
    class Meta:
        model = Payment
        fields = ('id', 'date', 'payment_type',
                  'name', 'total_sum', 'status', 'reservation')
        read_only_fields = ('id', 'date', 'payment_type', 'name', 'total_sum', 'reservation')


class LandingSerializer(WritableNestedModelSerializer):
    main_page = MainPageSerializer()
    about = AboutInfoSerializer()
    about_numbers = AboutUsNumberSerializer(many=True)
    social = SocialNetworkSerializer(many=True)
    contact = ContactSerializer()
    galleries = GalleryCategorySerializer(many=True)
    roominess = RoominessCreateSerializer(many=True)
    service = ServiceListSerializer(many=True)

    class Meta:
        model = Landing
        exclude = ['id', ]


class LandingCreateSerializer(WritableNestedModelSerializer):

    class Meta:
        model = Landing
        fields = '__all__'
