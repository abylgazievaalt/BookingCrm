import datetime
import os
import io
from calendar import monthrange

import requests
from django.db.models import Max, Count
from django.db.models.functions import TruncMonth
from .utils import get_full_reservation_sum, get_custom_reservation_sum
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, FileResponse, Http404
from django.utils.decorators import method_decorator
from django.utils.timezone import utc
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from kombu.utils import json
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from rest_framework import viewsets, status, generics, filters
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from collections import OrderedDict, Counter

from rest_framework.views import APIView
import pytz
from datetime import datetime, timedelta, date
from django.utils import timezone
from api.raw_sql import get_count_housing, get_count_by_month
from BookingCrm.settings import BASE_DIR, STATICFILES_DIRS
from webapp.models import Guestroom, Reservation, Service, Housing, Accessories, Comfort, Gallery, \
    Feedback, AboutUs, AboutUsNumbers, Contacts, RoomGallery, Staff, Cleaning, Meal, FeedbackReply, \
    Price, GalleryCategory, Roominess, RoomView, Floor, MainPage, Maid, Manager, SIDE_CHOICES, TypeOfRoom, \
    Administrator, Landing, Payment, MealPrice, SocialNetwork, PAYMENT_TYPE_CHOICES, GalleryPhoto, ServiceLanding
from api.serializers import RoomSerializer, ReservationSerializer, HousingSerializer, FeedbackSerializer, \
    AboutUsSerializer, \
    AboutUsNumberSerializer, ContactSerializer, RoomGallerySerializer, \
    StaffSerializer, MealSerializer, FeedbackReplySerializer, PriceSerializer, \
    GalleryCategorySerializer, \
    RoomListSerializer, AboutInfoSerializer, RoomViewSerializer, FloorSerializer, ReservationCrmSerializer, \
    FullRoomSerializer, PriceListSerializer, MainPageSerializer, MaidSerializer, \
    ManagerSerializer, MainPageCreateSerializer, RoomListHousingSerializer, RoomBriefSerializer, CleaningListSerializer, \
    CleaningDetailSerializer, TypeSerializer, AvailableRoomListSerializer, AdministratorSerializer, \
    StaffCreateSerializer, \
    PaymentSerializer, LandingSerializer, \
    SocialNetworkSerializer, FeedbackCreateSerializer, RoominessListSerializer, RoominessCreateSerializer, \
    AccessoriesListSerializer, \
    AccessoriesCreateSerializer, ServiceListSerializer, ServiceCreateSerializer, ComfortCreateSerializer, \
    ComfortListSerializer, GallerySerializer, GalleryListSerializer, GalleryRetrieveSerializer, GalleryPhotoSerializer, \
    RoominessBriefSerializer, FullRoomSerializer2, CrmRoomListSerializer, ServiceLandingSerializer, \
    ServiceLandingCreateSerializer, MealPriceSerializer
from rest_framework.authentication import TokenAuthentication
import django_filters.rest_framework


AIKOL_LOGO = os.path.join(BASE_DIR, 'aikol.png')


def get_reservation_receipt(request, pk):
    obj = get_object_or_404(Reservation, pk=pk)
    buffer = io.BytesIO()
    canvas = Canvas(buffer)
    pdfmetrics.registerFont(TTFont('Times', os.path.join(STATICFILES_DIRS[0], 'fonts', 'times.ttf')))
    canvas.setFont('Times', 20)
    canvas.drawImage(AIKOL_LOGO, 400, 780, width=122, height=52, mask='auto')
    canvas.drawString(200, 750, "Информация о брони")
    canvas.setFont('Times', 15)
    canvas.drawString(50, 700, f"Дата заезда: {obj.arrival_date.strftime('%d/%m/%Y')}")
    canvas.drawString(50, 675, f"Дата выезда: {obj.departure_date.strftime('%d/%m/%Y')}")
    canvas.drawString(50, 650, f"ФИО: {obj.last_name} {obj.name}")
    canvas.drawString(50, 625, f"Телефон: {obj.phone}")
    canvas.drawString(50, 600, f"Электронная почта: {obj.email}")
    canvas.drawString(50, 575, f"ID брони: {obj.id}")
    canvas.drawString(50, 550, f"Сумма: {obj.total_sum} сом")
    canvas.drawString(50, 525, f"Статус оплаты: {obj.get_payment_status_display()}")
    canvas.showPage()
    canvas.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'Айколь_Бронь_{obj.last_name}_{obj.name}_{datetime.now().strftime("%m/%d/%Y")}.pdf')


@api_view(['GET'])
# @authentication_classes([TokenAuthentication, ])
def get_calendar_filters(request):
    """
      Кол-во броней по месяцам. Параметры в описании.

      year - год указать обязательно {int}

      1. Без ID
      get - list
      """
    def monthdelta(date, delta):
        m, y = (date.month + delta) % 12, date.year + ((date.month) + delta - 1) // 12
        if not m: m = 12
        return date.replace(day=1, month=m, year=y)

    year = int(request.GET.get('year'))
    startDate = timezone.now().replace(day=1, month=1, year=year)

    all_months = [{"month": x, "count": 0} for x in [monthdelta(startDate, x) for x in range(12)]]
    x = 0
    reservations_months = get_count_by_month(year)
    if reservations_months:
        for item in all_months:
            if item['month'].month == int(reservations_months[x][0]):
                item['count'] = int(reservations_months[x][1])
                if len(reservations_months) - 1 == x:
                    break
                x = x + 1

    return JsonResponse({
        'months': list({"month": x['month'].strftime('%d-%m-%Y'), "count": x['count']} for x in all_months)
    })


def has_next_month(reservation, cur_month):
    arrival_month = reservation.arrival_date.month
    departure_month = reservation.departure_date.month
    if arrival_month == departure_month:
        return False
    if departure_month != cur_month:
        return True
    return False


def has_prev_month(reservation, cur_month):
    arrival_month = reservation.arrival_date.month
    departure_month = reservation.departure_date.month
    if arrival_month == departure_month:
        return False
    if arrival_month != cur_month:
        return True
    return False


@api_view(['GET'])
# @authentication_classes([TokenAuthentication, ])

def get_calendar_rooms(request):
    """
    Календарь броней. Параметры в описании.

    year - int
    month - int

    1. Без ID
    get - list
    """
    # housing = request.GET.get('housing')
    month = request.GET.get('month')
    year = request.GET.get('year')

    res = get_count_housing(month, year)
    print(res)
    all_housings = Housing.objects.prefetch_related('floors').order_by('name')
    all_reservations = Reservation.objects.filter(status="active").select_related('room')
    all_guestrooms = Guestroom.objects.select_related('floor')

    result = []
    for housing in all_housings:
        count = 0
        for x in res:
            if housing.name == x[0]:
                count = x[1]
        floors_set = housing.floors.all().order_by('floor')
        floors = []
        for floor in floors_set:
            floors_dict = {}
            rooms_set = all_guestrooms.filter(floor=floor).order_by('number')
            if rooms_set.count() > 0:
                floors_dict['floor'] = floor.floor
                floors.append(floors_dict)
            rooms_list = []
            for room in rooms_set:
                room_dict = {}
                room_dict['room_id'] = room.id
                room_dict['room_number'] = room.number
                room_dict['roominess'] = room.roominess.roominess_name
                room_dict['roominess_number'] = room.roominess.roominess
                room_dict['description'] = room.furniture
                reservations_set = all_reservations.filter(room=room, arrival_date__month=month, arrival_date__year=year)\
                                    .union(all_reservations.filter(room=room, departure_date__month=month, departure_date__year=year))
                reservations = []
                for reservation in reservations_set:
                    reservation_dict = {}
                    reservation_dict['id'] = reservation.id
                    reservation_dict['name'] = str(reservation)
                    reservation_dict['count_of_people'] = reservation.count_of_people
                    arrival_date = reservation.arrival_date
                    if arrival_date.month != int(month):
                        arrival_date = arrival_date.replace(day=1, month=int(month))
                    reservation_dict['arrival_date'] = arrival_date.strftime('%d-%m-%Y')
                    departure_date = reservation.departure_date
                    if departure_date.month != int(month):
                        departure_date = departure_date.replace(day=monthrange(int(year), int(month))[1], month=int(month))
                    reservation_dict['departure_date'] = departure_date.strftime('%d-%m-%Y')
                    # days = (departure_date - arrival_date).days
                    reservation_dict['days'] = (reservation.departure_date - reservation.arrival_date).days
                    reservation_dict['has_next_month'] = has_next_month(reservation, int(month))
                    reservation_dict['has_prev_month'] = has_prev_month(reservation, int(month))
                    try:
                        reservation_dict['morning'] = reservation.meals.get(date=reservation.arrival_date).breakfast
                    except:
                        reservation_dict['morning'] = False
                    reservations.append(reservation_dict)
                if reservations:
                    room_dict['reservations'] = reservations
                rooms_list.append(room_dict)
                floors_dict['rooms'] = rooms_list
        a = {
            "housing": housing.name,
            "count": count
        }
        if floors:
            a['floors'] = floors
        result.append(a)

    return JsonResponse(result, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class PaymentView(View):
    def post(self, request, pk, *args, **kwargs):
        reservation = get_object_or_404(Reservation, pk=pk)
        UTC = pytz.utc
        exporation_date = datetime.now(UTC) + timedelta(hours=10)
        exporation_date = exporation_date.strftime('%Y-%m-%d %H:%M:%S')
        data = {
            "order": f"{ reservation.id }",
            "amount": int(reservation.total_sum),
            "currency": "KGS",
            "description": f"Бронирование номера в пансионате Айкол: {reservation.last_name} {reservation.name}",
            "expires_at": exporation_date,
            "language": "ru",
            "options": {
                "callbacks": {
                    "result_url": "http://176.126.166.151:8080/api/reservation/payment_response",
                    "check_url": "http://176.126.166.151",
                    "cancel_url": "http://176.126.166.151",
                    "success_url": "http://176.126.166.151/booking/success",
                    "failure_url": "http://176.126.166.151/booking/failure",
                    "back_url": "http://176.126.166.151",
                    "capture_url": "http://176.126.166.151"
                }
            }
        }

        response = requests.post("https://api.paybox.money/v4/payments",
                                 json=data,
                                 auth=('528164', 'WANX84ZUCjbMC450'),
                                 headers={'X-Idempotency-Key': f'{ reservation.uuid }'}
                                 )

        data = json.loads(response.content)
        try:
            a = data['status']
            if reservation.payment_url:
                return JsonResponse(data={'payment_url': f'{reservation.payment_url}'})
        except:
            a = data['payment_page_url']
            reservation.payment_url = a
            reservation.save()
            return JsonResponse(data={'payment_url': f'{reservation.payment_url}'})

        return JsonResponse(data={'error': 'Что то пошло не так'})


@method_decorator(csrf_exempt, name='dispatch')
class PaymentResponseView(View):
    @staticmethod
    def post(request):
        data = json.loads(request.body)
        if data['status']['code'] == 'success':
            reservation = get_object_or_404(Reservation, pk=int(data['order']))
            reservation.payment_status = 'fully paid'
            reservation.save()
            a = Payment.objects.get(reservation=reservation)
            a.status = reservation.payment_status
            a.save()
            return HttpResponse(status=200)

        return HttpResponse(data=200)


class Pagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('page_count', self.page.paginator.num_pages),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class PaginationStaff(PageNumberPagination):
    page_size = 9
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('page_count', self.page.paginator.num_pages),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))

class PaginationWithExtra(PageNumberPagination):
    page_size = 4
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data, extra, dates):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('page_count', self.page.paginator.num_pages),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('another', extra),
            ('another_dates', dates)
        ]))


class RoomListPaginationWithExtra(PageNumberPagination):
    page_size = 9
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data, types_list, housings_list, floors_list, roominess_list, sides_list):
        filters = {}
        filters['types'] = types_list
        filters['housings'] = housings_list
        filters['floors'] = floors_list
        filters['roominess'] = roominess_list
        filters['sides'] = sides_list

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('page_count', self.page.paginator.num_pages),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('filters', filters),
        ]))


class CleaningListPaginationWithExtra(PageNumberPagination):
    page_size = 9
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data, types_list, housings_list, floors_list, rooms_list):
        filters = {}
        filters['types'] = types_list
        filters['housings'] = housings_list
        filters['floors'] = floors_list
        filters['rooms'] = rooms_list

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('page_count', self.page.paginator.num_pages),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('filters', filters),
        ]))


class RoomListPagination(PageNumberPagination):
    page_size = 9
    page_size_query_param = 'page_size'
    max_page_size = 9


class PriceListPagination(PageNumberPagination):
    page_size = 9
    page_size_query_param = 'page_size'
    max_page_size = 9

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('page_count', self.page.paginator.num_pages),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
        ]))


class GalleryListPagination(PageNumberPagination):
    page_size = 16
    page_size_query_param = 'page_size'
    max_page_size = 16


class MainPageViewSet(viewsets.ModelViewSet):

    """
    Страница: Главная

    1. Без ID
    get - list
    post - create
    2. C ID
    get - retrieve
    put - update
    delete - delete
    """

    queryset = MainPage.objects.all()
    serializer_class = MainPageSerializer
    lookup_field = 'pk'

    def get_serializer_class(self):
        return MainPageCreateSerializer

    def retrieve(self, request, *args, **kwargs):
        obj = MainPage.objects.first()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        obj = MainPage.objects.first()
        if obj == None:
            obj = MainPage.objects.create()
        serializer = self.get_serializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ServiceLandingViewSet(viewsets.ModelViewSet):
    """
    Сервисы на главном
    1. Без ID
    get - list
    post - create
    """
    queryset = ServiceLanding.objects.exclude(service=None)
    serializer_class = ServiceListSerializer
    lookup_field = 'pk'

    def list(self, request, *args, **kwargs):
        qrs = ServiceLanding.objects.exclude(service=None)\
                    .values('id', 'service__image', 'service__name', 'service__description')
        queryset = self.filter_queryset(qrs)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ServiceLandingSerializer(page, many=True,
                                                  context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ServiceLandingSerializer(queryset, many=True,
                                              context={'request': request})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        for item in request.data['service']:
            service = get_object_or_404(Service, pk=item)
            a = ServiceLanding.objects.create(service=service)
            a.save()
        return Response({"success": True}, status=status.HTTP_201_CREATED)


class RoomViewSet(viewsets.ModelViewSet):

    """
    Страница: Описание номера

    1. Без ID
    get - list
    post - create
    2. C ID
    get - retrieve
    put - update
    delete - delete
    """

    # serializer_class = RoomSerializer
    lookup_field = 'pk'
    pagination_class = Pagination

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return FullRoomSerializer
        return RoomSerializer

    def create(self, request, *args, **kwargs):
        serializer = RoomSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        for i in instance.room_galleries.all():
            if i.image:
                if os.path.isfile(i.image.path):
                    os.remove(i.image.path)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        queryset = Guestroom.objects.select_related('roominess', 'housing', 'floor', 'view') \
            .prefetch_related('accessories', 'comfort', 'service', 'room_galleries')
        filter_fields = {}

        if self.request.GET.get('type'):
            filter_fields['type'] = self.request.GET.get('type')

        if self.request.GET.get('housing'):
            filter_fields['housing'] = self.request.GET.get('housing')

        if self.request.GET.get('floor'):
            filter_fields['floor'] = self.request.GET.get('floor')

        if self.request.GET.get('roominess'):
            filter_fields['roominess_name'] = self.request.GET.get('roominess_name')

        if self.request.GET.get('side'):
            filter_fields['side'] = self.request.GET.get('side')

        if filter_fields:
            queryset = queryset.filter(**filter_fields)

        return queryset


class RoomListViewSet(viewsets.ModelViewSet):

    """
    Страница: Номера. Параметры в описании.

    Параметры:
    type - стандарт, люкс {id}
    housing - корпус (все номера) {id}
    floor - этаж {id}
    roominess - вместимость (одноместные, двухместные) (кол-во мест) {id}
    side - сторона (north, south, west, east) {north, west, east, south}

    1. Без ID
    get - list

    """

    lookup_field = 'pk'
    pagination_class = RoomListPaginationWithExtra

    def get_serializer_class(self):
        if self.action == 'list':
            # if self.request.user.is_authenticated or 'swagger' in self.request.META['PATH_INFO']:
            #     return CrmRoomListSerializer
            # else:
            return RoomListSerializer
        if self.action == 'create' or  'swagger' in self.request.META['PATH_INFO']:
            return FullRoomSerializer
        return RoomListSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        for i in instance.room_galleries.all():
            if i.image:
                if os.path.isfile(i.image.path):
                    os.remove(i.image.path)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def filter_queryset(self, queryset):
        filter_fields = {}

        if self.request.GET.get('type'):
            filter_fields['type'] = self.request.GET.get('type')

        if self.request.GET.get('housing'):
            filter_fields['housing'] = self.request.GET.get('housing')

        if self.request.GET.get('floor'):
            floor_qs = Floor.objects.filter(floor=self.request.GET.get('floor'))
            queryset = queryset.filter(floor__id__in=floor_qs)

        if self.request.GET.get('roominess'):
            filter_fields['roominess__roominess'] = self.request.GET.get('roominess')

        if self.request.GET.get('side'):
            filter_fields['side'] = self.request.GET.get('side')

        if filter_fields:
            queryset = queryset.filter(**filter_fields)

        return queryset

    def get_queryset(self):
        queryset = Guestroom.objects.select_related('roominess',
                                                    'housing',
                                                    'floor',
                                                    'view').prefetch_related('room_galleries')
        inactive_housings = Housing.objects.filter(active=False)
        queryset = queryset.exclude(housing__in=inactive_housings)
        queryset = self.filter_queryset(queryset)

        return queryset

    def get_paginated_response(self, data):
        assert self.paginator is not None
        types_list = []

        housings = Housing.objects.filter(active=True).order_by('name')
        serializer = RoomListHousingSerializer(housings, many=True)
        housings_list = serializer.data

        floors = Floor.objects.all().order_by('floor').values('floor').distinct()
        floors_list = []
        for floor in floors:
            extra_dict = {}
            extra_dict['name'] = floor['floor']
            floors_list.append(extra_dict)

        roominess_set = Roominess.objects.all().order_by('roominess')
        roominess_list = []
        for roominess in roominess_set:
            extra_dict = {}
            extra_dict['id'] = roominess.id
            extra_dict['name'] = roominess.roominess_name
            roominess_list.append(extra_dict)

        sides_list = []
        sides = SIDE_CHOICES
        for side in sides:
            extra_dict = {}
            extra_dict['id'] = side[0]
            extra_dict['name'] = side[1]
            sides_list.append(extra_dict)

        for type in TypeOfRoom.objects.all():
            extra_dict = {}
            extra_dict['id'] = type.id
            extra_dict['name'] = type.type
            types_list.append(extra_dict)

        if self.request.GET.get('type'):
            type = TypeOfRoom.objects.get(id=self.request.GET.get('type'))
            housings = type.housing.all().order_by('name')
            serializer = RoomListHousingSerializer(housings, many=True)
            housings_list = serializer.data

        if self.request.GET.get('housing'):
            floors_list = []
            housing = self.request.GET.get('housing')
            h = Housing.objects.get(id=housing)
            h_floors = h.floors.all().order_by('floor')

            for floor in h_floors:
                extra_dict = {}
                extra_dict['id'] = floor.id
                extra_dict['name'] = floor.floor
                floors_list.append(extra_dict)

        if self.request.GET.get('floor') and self.request.GET.get('housing'):
            housing = self.request.GET.get('housing')
            h = Housing.objects.get(id=housing)
            roominess_list = []
            floor = self.request.GET.get('floor')
            f = Floor.objects.get(housing=housing, floor=floor)
            f_roominess = f.roominess.all().order_by('roominess')
            for roominess in f_roominess:
                extra_dict = {}
                extra_dict['id'] = roominess.id
                extra_dict['name'] = roominess.roominess_name
                roominess_list.append(extra_dict)

        print(roominess_list)
        page = self.paginate_queryset(self.get_queryset())
        serializer = self.get_serializer(page, many=True)
        return self.paginator.get_paginated_response(serializer.data, types_list, housings_list, floors_list,
                                                     roominess_list, sides_list)


class AvailableListViewSet(viewsets.ModelViewSet):

    """
    Страница: Результат. Параметры в описании.

    Параметры:
    arrival_date - дата прибытия {y-m-d}
    departure_date - дата отъезда {y-m-d}
    type - стандарт, люкс (выбрать номер) {id}
    count_of_people - кол-во людей/вместимость (взрослые) {int}
    housing - корпус {id}
    roominess - вместимость (одноместные, двухместные) (тип комнаты) {id}
    side - сторона (north, west, south, east)
    floor - этаж {id}
    view - вид {id}

    1. Без ID
    get - list

    """

    serializer_class = AvailableRoomListSerializer
    lookup_field = 'pk'
    pagination_class = PaginationWithExtra

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        for i in instance.room_galleries.all():
            if i.image:
                if os.path.isfile(i.image.path):
                    os.remove(i.image.path)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def filter_queryset(self, queryset):
        filter_fields = {}

        if self.request.GET.get('type'):
            filter_fields['type'] = self.request.GET.get('type')

        if self.request.GET.get('housing'):
            filter_fields['housing'] = self.request.GET.get('housing')

        if self.request.GET.get('view'):
            filter_fields['view'] = self.request.GET.get('view')

        if self.request.GET.get('floor'):
            floor_qs = Floor.objects.filter(floor = self.request.GET.get('floor'))
            queryset = queryset.filter(floor__id__in=floor_qs)
            print(queryset)

        if self.request.GET.get('side'):
            filter_fields['side'] = self.request.GET.get('side')

        if self.request.GET.get('count_of_people'):
            roominess_value = self.request.GET.get('count_of_people')
            roominess_set = Roominess.objects.filter(roominess__gte=roominess_value)
            queryset = queryset.filter(roominess__id__in=roominess_set).order_by('roominess__roominess')

        if self.request.GET.get('roominess') and not self.request.GET.get('count_of_people'):
            filter_fields['roominess'] = self.request.GET.get('roominess')

        if filter_fields:
            queryset = queryset.filter(**filter_fields)

        return queryset

    def get_queryset(self):
        queryset = Guestroom.objects.select_related('roominess',
                                                    'housing',
                                                    'floor',
                                                    'view').prefetch_related('room_galleries')

        queryset = self.filter_queryset(queryset)

        if self.request.GET.get('arrival_date') and self.request.GET.get('departure_date'):
            arrival_date = datetime.strptime(self.request.GET.get('arrival_date'), '%d-%m-%Y')
            departure_date = datetime.strptime(self.request.GET.get('departure_date'), '%d-%m-%Y')
            reservations_qs = Reservation.objects.filter(status='active', arrival_date__lte= departure_date, departure_date__gte=arrival_date).values('room__id')
            queryset = queryset.exclude(id__in=reservations_qs)
        return queryset

    def get_paginated_response(self, data):
        assert self.paginator is not None
        dates = {}

        queryset = Guestroom.objects.select_related('roominess',
                                                    'housing',
                                                    'floor',
                                                    'view').prefetch_related('room_galleries')
        queryset = self.filter_queryset(queryset)

        if self.request.GET.get('arrival_date') and self.request.GET.get('departure_date'):
            arrival_date_extra = datetime.strptime(self.request.GET.get('arrival_date'), '%d-%m-%Y')
            departure_date_extra = datetime.strptime(self.request.GET.get('departure_date'), '%d-%m-%Y')

            time_diff = departure_date_extra - arrival_date_extra
            arrival_date_extra = departure_date_extra + timedelta(days=1)
            departure_date_extra = arrival_date_extra + time_diff

            reservations_qs = Reservation.objects.filter(status='active', arrival_date__lte=departure_date_extra, departure_date__gte=arrival_date_extra).values('room__id')
            queryset = queryset.exclude(id__in=reservations_qs)

            year = str(arrival_date_extra.year)
            month = arrival_date_extra.month
            day = arrival_date_extra.day

            arrival_date_extra = '-'.join(["{:02d}".format(day), "{:02d}".format(month), year])

            year = str(departure_date_extra.year)
            month = departure_date_extra.month
            day = departure_date_extra.day

            departure_date_extra = '-'.join(["{:02d}".format(day), "{:02d}".format(month), year])

            dates['from_date'] = arrival_date_extra
            dates['to_date'] = departure_date_extra

        else:
            queryset = self.get_queryset()

        queryset = queryset.exclude(pk__in=self.get_queryset())
        queryset = queryset[:5]
        q2 = Guestroom.objects.all()[:3]
        queryset = (queryset | q2).distinct()
        page = self.paginate_queryset(self.get_queryset())
        serializer = self.get_serializer(page, many=True)

        serializer_extra = self.get_serializer(queryset, many=True)

        return self.paginator.get_paginated_response(serializer.data, serializer_extra.data, dates)


class MealViewSet(viewsets.ModelViewSet):
    """
        Календарь питания(CRM)

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
    """
    queryset = Meal.objects.all()
    serializer_class = MealSerializer
    lookup_field = 'pk'


class ReservationViewSet(viewsets.ModelViewSet):
    """
        Страница: Бронирования

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
        """

    queryset = Reservation.objects.all()
    lookup_field = 'pk'
    permission_classes_by_action = {'create': [AllowAny],
                                    'list': [IsAdminUser], }

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.user.is_authenticated or 'swagger' in self.request.META['PATH_INFO']:
            return ReservationCrmSerializer
        else:
            return ReservationSerializer

    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes]


class PaymentTypesView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAdminUser]

    def get(self, request, format=None):
        data = []

        for i in PAYMENT_TYPE_CHOICES:
            dict = {}
            dict['key'] = i[0]
            dict['value'] = i[1]
            data.append(dict)

        return Response(OrderedDict([
            ('types', data)
        ]))


class ServiceViewSet(viewsets.ModelViewSet):
    """
        Страница: Сервис

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
    """

    queryset = Service.objects.all()
    lookup_field = 'pk'
    pagination_class = Pagination

    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            if not self.request.GET.get('page'):
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.image:
            if os.path.isfile(instance.image.path):
                os.remove(instance.image.path)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.action == 'list':
            return ServiceListSerializer
        return ServiceCreateSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

class HousingViewSet(viewsets.ModelViewSet):
    """
        Корпусы

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
    """
    queryset = Housing.objects.all()
    serializer_class = HousingSerializer
    lookup_field = 'pk'

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class AccessoriesViewSet(viewsets.ModelViewSet):
    """
        Принадлежности

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
    """
    queryset = Accessories.objects.all()
    lookup_field = 'pk'

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.image:
            if os.path.isfile(instance.image.path):
                os.remove(instance.image.path)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.action == 'list':
            return AccessoriesListSerializer
        return AccessoriesCreateSerializer


class RoomGalleryViewSet(viewsets.ModelViewSet):
    """
        Фотографии номера

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
    """
    queryset = RoomGallery.objects.all()
    serializer_class = RoomGallerySerializer
    lookup_field = 'pk'


class ComfortViewSet(viewsets.ModelViewSet):
    """
        Главная: Услуги и удобства

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
    """
    queryset = Comfort.objects.all()
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.action == 'list':
            return ComfortListSerializer
        return ComfortCreateSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.image:
            if os.path.isfile(instance.image.path):
                os.remove(instance.image.path)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class GalleryCategoryViewSet(viewsets.ModelViewSet):

    """
    Категории галереи

    1. Без ID
    get - list
    post - create
    2. C ID
    get - retrieve
    put - update
    delete - delete
    """
    queryset = GalleryCategory.objects.all()
    lookup_field = 'pk'
    pagination_class = GalleryListPagination
    serializer_class = GalleryCategorySerializer


class GalleryViewSet(viewsets.ModelViewSet):

    """
    Главная: Прекрасные места нашего пансионата

    1. Без ID
    get - list
    post - create
    2. C ID
    get - retrieve
    put - update
    delete - delete
    """

    queryset = Gallery.objects.all()
    lookup_field = 'pk'
    pagination_class = GalleryListPagination
    serializer_class = GallerySerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return GalleryListSerializer
        # if self.action == 'retrieve':
        #     return GalleryRetrieveSerializer
        return GallerySerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        for i in instance.gallery_photos.all():
            if i.image:
                if os.path.isfile(i.image.path):
                    os.remove(i.image.path)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        # try:
        for item in request.data.getlist('gallery_photos'):
            GalleryPhoto.objects.create(gallery=instance, image=item)
        # except:
        #     pass
        return Response(serializer.data)


class GalleryPhotosViewSet(viewsets.ModelViewSet):
    """
    Все фото в галерее
    2. C ID
    get - retrieve
    put - update
    delete - delete
    """
    queryset = GalleryPhoto.objects.all()
    lookup_field = 'pk'
    pagination_class = GalleryListPagination
    serializer_class = GalleryPhotoSerializer



class FeedbackViewSet(viewsets.ModelViewSet):
    """

        Параметры:
        date_created = dd-mm-yyyy (Дата создания)

        Страница: Отзывы

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
    """
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    lookup_field = 'pk'
    pagination_class = PaginationStaff
    permission_classes_by_action = {'create': [AllowAny],
                                    'list': [IsAdminUser], }

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return FeedbackSerializer
        if self.action == 'destroy':
            return FeedbackSerializer
        return FeedbackCreateSerializer

    def get_queryset(self):
        queryset = self.queryset
        filter_fields = {}
        if self.request.GET.get('date_created'):
            date = datetime.strptime(self.request.GET.get('date_created'), '%d-%m-%Y').date()
            filter_fields['date__date'] = date
        if filter_fields:
            queryset = queryset.filter(**filter_fields)
        return queryset

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]


class AboutUsViewSet(viewsets.ModelViewSet):
    """
        Страница: О нас

        1. Без ID
        get
        put
    """
    queryset = AboutUs.objects.all()
    serializer_class = AboutUsSerializer
    lookup_field = 'pk'

    def update(self, request, *args, **kwargs):
        instance = AboutUs.objects.first()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        instance = AboutUs.objects.first()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MealPriceView(viewsets.ModelViewSet):
    queryset = MealPrice.objects.all()
    serializer_class = MealPriceSerializer
    lookup_field = 'pk'
    permission_classes = [AllowAny]

    def update(self, request, *args, **kwargs):
        instance = MealPrice.objects.first()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        instance = MealPrice.objects.first()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class AboutNumberViewSet(viewsets.ModelViewSet):
    """
        О нас в цифрах

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
    """
    queryset = AboutUsNumbers.objects.all()
    serializer_class = AboutUsNumberSerializer
    lookup_field = 'pk'


class AboutInfoViewSet(viewsets.ModelViewSet):
    """
        Главная: О нас

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
    """

    # queryset = AboutUs.objects.all()
    serializer_class = AboutInfoSerializer
    lookup_field = 'pk'

    def list(self, request, *args, **kwargs):
        instance = AboutUs.objects.first()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ContactsViewSet(viewsets.ModelViewSet):
    """
        Страница: Контакты
        1. Без ID
        get - retrieve
        put - update
    """
    queryset = Contacts.objects.all()
    serializer_class = ContactSerializer
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        obj = Contacts.objects.first()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        obj = Contacts.objects.first()
        if obj == None:
            obj = Contacts.objects.create()
        serializer = self.get_serializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class StaffViewSet(viewsets.ModelViewSet):
    """
        Сотрудники (CRM)
             Дополнительные параметры:
            date_created = Дата создания dd-mm-yyyy

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
    """
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    pagination_class = PaginationStaff
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['last_name', 'first_name', 'middle_name', 'id']
    filter_fields = ['role']
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.action == 'list':
            return StaffSerializer
        if self.action == 'retrieve':
            return StaffSerializer
        if self.action == 'create':
            return StaffCreateSerializer
        if self.action == 'destroy':
            return StaffCreateSerializer
        return StaffSerializer

    def get_queryset(self):
        queryset = self.queryset
        filter_fields = {}
        if self.request.GET.get('date_created'):
            date = datetime.strptime(self.request.GET.get('date_created'), '%d-%m-%Y').date()
            filter_fields['date_created'] = date
        if filter_fields:
            queryset = queryset.filter(**filter_fields)
        return queryset

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class CleaningViewSet(viewsets.ModelViewSet):

    """
    Уборка номеров (CRM)

    Параметры:
    room_type - стандарт, люкс {id}
    housing - корпус (все номера) {id}
    floor - этаж {id}
    roominess - вместимость (одноместные, двухместные) (кол-во мест) {id}
    room - комната {id}


    1. Без ID
    get - list
    post - create
    2. C ID
    get - retrieve
    put - update
    delete - delete
    """

    # serializer_class = CleaningListSerializer
    lookup_field = 'pk'
    authentication_classes = (TokenAuthentication,)
    pagination_class = CleaningListPaginationWithExtra
    permission_classes = [IsAdminUser]
    queryset = Cleaning.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return CleaningListSerializer
        if self.action == 'retrieve':
            return CleaningDetailSerializer
        if self.action == 'create':
            return CleaningDetailSerializer
        if self.action == 'destroy':
            return CleaningDetailSerializer
        return CleaningListSerializer

    def create(self, request, *args, **kwargs):
        serializer = CleaningDetailSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def filter_queryset(self, queryset):
        filter_fields = {}
        if self.request.GET.get('date'):
            filter_fields['date'] = datetime.strptime(self.request.GET.get('date'), '%d-%m-%Y').date()

        if self.request.GET.get('housing'):
            filter_fields['housing'] = self.request.GET.get('housing')

        if self.request.GET.get('floor'):
            filter_fields['floor'] = self.request.GET.get('floor')

        if self.request.GET.get('roominess'):
            filter_fields['room__roominess'] = self.request.GET.get('roominess')

        if self.request.GET.get('room'):
            filter_fields['room'] = self.request.GET.get('room')

        if self.request.GET.get('room_type'):
            filter_fields['room_type'] = self.request.GET.get('room_type')

        if filter_fields:
            queryset = queryset.filter(**filter_fields)

        return queryset

    def get_queryset(self):
        queryset = Cleaning.objects.select_related('room_type',
                                                   'housing',
                                                   'floor',
                                                   'room')
        # inactive_housings = Cleaning.objects.filter(active=False)
        # queryset = queryset.exclude(housing__in=inactive_housings)
        queryset = self.filter_queryset(queryset)

        return queryset

    def get_paginated_response(self, data):
        assert self.paginator is not None

        types_list = []
        housings_list = []
        floors_list = []
        rooms_list = []

        types = TypeOfRoom.objects.all()
        serializer = TypeSerializer(types, many=True)
        types_list = serializer.data

        if self.request.GET.get('type'):
            type = TypeOfRoom.objects.get(id=self.request.GET.get('type'))
            housings = type.housing.all().order_by('name')
            serializer = RoomListHousingSerializer(housings, many=True)
            housings_list = serializer.data

        if self.request.GET.get('housing'):
            housing = Housing.objects.get(id=self.request.GET.get('housing'))
            floors = housing.floors.all().order_by('floor')
            for floor in floors:
                extra_data = {}
                extra_data['id'] = floor.id
                extra_data['name'] = floor.floor
                floors_list.append(extra_data)

        if self.request.GET.get('floor'):
            floor = Floor.objects.get(id=self.request.GET.get('floor'))
            rooms = Guestroom.objects.filter(floor=floor).order_by('housing')
            serializer = RoomBriefSerializer(rooms, many=True)
            rooms_list = serializer.data

        return self.paginator.get_paginated_response(data, types_list, housings_list, floors_list, rooms_list)


class CleaningCreateFilterView(APIView):
    """
    Фильтрация полей для создания уборки. Параметры в описании.

    Параметры:
    housing - корпус {id}
    floor - этаж {id}
    roominess - вместительность {id}

    1. Без ID
    get - list

    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAdminUser]

    def get(self, request, format=None):
        housings_list = []
        floors_list = []
        roominess_list = []
        rooms_list = []
        housing = None
        floor = None

        for housing in Housing.objects.all().order_by('name'):
            extra_dict = {}
            extra_dict['id'] = housing.id
            extra_dict['name'] = housing.name
            housings_list.append(extra_dict)

        if self.request.GET.get('housing'):
            housing = Housing.objects.get(id=self.request.GET.get('housing'))
            floors = housing.floors.all().order_by('floor')
            for floor in floors:
                extra_dict = {}
                extra_dict['id'] = floor.id
                extra_dict['name'] = floor.floor
                floors_list.append(extra_dict)

        if self.request.GET.get('floor'):
            floor = Floor.objects.get(id=self.request.GET.get('floor'))
            roominess_set = floor.roominess.all().order_by('roominess')
            for room in roominess_set:
                extra_dict = {}
                extra_dict['id'] = room.id
                extra_dict['name'] = room.roominess_name
                roominess_list.append(extra_dict)

        if self.request.GET.get('roominess'):
            roominess = Roominess.objects.get(id=self.request.GET.get('roominess'))
            rooms = Guestroom.objects.filter(roominess=roominess, housing=housing, floor=floor).order_by('housing')
            serializer = RoomBriefSerializer(rooms, many=True)
            rooms_list = serializer.data

        data = {}
        data['housings'] = housings_list
        data['floors'] = floors_list
        data['roominess'] = roominess_list
        data['rooms'] = rooms_list

        return Response(OrderedDict([
            ('filters', data)
        ]))


class AvailableFilterView(APIView):
    """
    Фильтрация полей для создания уборки. Параметры в описании.

    Параметры:
    housing - корпус {id}
    floor - этаж {id}
    roominess - вместительность {id}

    1. Без ID
    get - list

    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        types_list = []
        housings_list = []
        floors_list = []
        roominess_list = []
        sides_list = []
        views_list = []

        for type in TypeOfRoom.objects.all():
            extra_dict = {}
            extra_dict['id'] = type.id
            extra_dict['name'] = type.type
            types_list.append(extra_dict)

        for housing in Housing.objects.all().order_by('name'):
            extra_dict = {}
            extra_dict['id'] = housing.id
            extra_dict['name'] = housing.name
            housings_list.append(extra_dict)

        for roominess in Roominess.objects.all().order_by('roominess'):
            extra_dict = {}
            extra_dict['id'] = roominess.id
            extra_dict['name'] = roominess.roominess_name
            roominess_list.append(extra_dict)

        sides = SIDE_CHOICES
        for side in sides:
            extra_dict = {}
            extra_dict['id'] = side[0]
            extra_dict['name'] = side[1]
            sides_list.append(extra_dict)

        floors_unique = Floor.objects.all().values_list('floor', flat=True).distinct()
        for floor in floors_unique:
            extra_dict = {}
            extra_dict['name'] = floor
            floors_list.append(extra_dict)

        for view in RoomView.objects.all():
            extra_dict = {}
            extra_dict['id'] = view.id
            extra_dict['name'] = view.view
            views_list.append(extra_dict)

        data = {}
        data['types'] = types_list
        data['housings'] = housings_list
        data['roominess'] = roominess_list
        data['sides'] = sides_list
        data['floors'] = floors_list
        data['views'] = views_list

        return Response(OrderedDict([
            ('filters', data)
        ]))


class FeedbackReplyViewSet(viewsets.ModelViewSet):

    """
    Обратная связь (CRM)

    1. Без ID
    get - list
    post - create
    2. C ID
    get - retrieve
    put - update
    delete - delete
    """

    serializer_class = FeedbackReplySerializer
    lookup_field = 'pk'
    queryset = FeedbackReply.objects.all()
    authentication_classes = (TokenAuthentication,)
    pagination_class = Pagination
    permission_classes = [IsAdminUser]


class TypeOfRoomViewSet(viewsets.ModelViewSet):

    """
    Обратная связь (CRM)

    1. Без ID
    get - list
    post - create
    2. C ID
    get - retrieve
    put - update
    delete - delete
    """

    serializer_class = TypeSerializer
    lookup_field = 'pk'
    queryset = TypeOfRoom.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = [AllowAny]


class PriceViewSet(viewsets.ModelViewSet):

    """
    Цены (CRM)

    1. Без ID
    get - list
    post - create
    2. C ID
    get - retrieve
    put - update
    delete - delete
    """

    lookup_field = 'pk'
    queryset = Price.objects.all()
    authentication_classes = (TokenAuthentication,)
    pagination_class = PriceListPagination
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        return PriceSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class PriceFilterView(APIView):
    """
    Вычисление итоговой суммы для бронирования. Параметры в описании.

    Параметры:
    room - номер {id}
    arrival_date - дата заезда {d-m-Y}
    departure_date - дата выезда {d-m-Y}
    count_of_people - общее кол-во людей {int}

    1. Без ID
    get - list

    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        roominess = None
        housing = None
        arrival_date = None
        departure_date = None
        room = None
        count_of_people = 0

        if self.request.GET.get('room'):
            room_id = self.request.GET.get('room')
            room = Guestroom.objects.get(id=room_id)
            housing = room.housing
            roominess = room.roominess

        if self.request.GET.get('arrival_date'):
            arrival_date = datetime.strptime(self.request.GET.get('arrival_date'), '%d-%m-%Y').date()

        if self.request.GET.get('departure_date'):
            departure_date = datetime.strptime(self.request.GET.get('departure_date'), '%d-%m-%Y').date()

        if self.request.GET.get('count_of_people'):
            count_of_people = int(self.request.GET.get('count_of_people'))

        sum = get_full_reservation_sum(housing, roominess, arrival_date, departure_date, room, count_of_people)

        return Response(OrderedDict([
            ('total', sum)
        ]))


class CrmPriceFilterView(APIView):
    """
    Вычисление итоговой суммы для бронирования (CRM). Тело запроса в описании.

    {
        "room": 1,
        "arrival_date": "10-09-2020",
        "departure_date": "13-09-2020",
        "count_of_people": 2,
        "discount": 0,
        "meals": [
            {
                "date": "12-09-2020",
                "breakfast": true,
                "lunch": true,
                "dinner": false
            }
        ]
    }

    1. Без ID
    get - list

    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAdminUser]

    def post(self, request, format=None):
        received_json_data = json.loads(request.body)
        room_id = received_json_data['room']
        room = Guestroom.objects.get(id=room_id)
        housing = room.housing
        roominess = room.roominess
        arrival_date = received_json_data['arrival_date']
        departure_date = received_json_data['departure_date']
        count_of_people = received_json_data['count_of_people']
        meals = received_json_data['meals']
        discount = received_json_data['discount']

        arrival_date = datetime.strptime(arrival_date, '%d-%m-%Y').date()
        departure_date = datetime.strptime(departure_date, '%d-%m-%Y').date()

        sum = get_custom_reservation_sum(housing, roominess, arrival_date, departure_date, room, count_of_people, meals, discount)

        return Response(OrderedDict([
            ('total', sum)
        ]))


class PriceCreateFilterView(APIView):
    """
    Фильтры для создания цены. Параметры в описании.

    Параметры:
    room - номер {id}
    arrival_date - дата заезда {d-m-Y}
    departure_date - дата выезда {d-m-Y}
    count_of_people - общее кол-во людей {int}

    1. Без ID
    get - list

    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAdminUser]

    def get(self, request, format=None):
        housings_list = []
        types_list = []
        roominess_list = []
        housing = None

        for housing in Housing.objects.all().order_by('name'):
            extra_dict = {}
            extra_dict['id'] = housing.id
            extra_dict['name'] = housing.name
            housings_list.append(extra_dict)

        if self.request.GET.get('housing'):
            housing = Housing.objects.get(id=self.request.GET.get('housing'))
            types = housing.types.all().order_by('type')
            for type in types:
                extra_dict = {}
                extra_dict['id'] = type.id
                extra_dict['name'] = type.type
                types_list.append(extra_dict)

        if self.request.GET.get('type'):
            type = TypeOfRoom.objects.get(id=self.request.GET.get('type'))
            floors_set = housing.floors.all().order_by('floor')
            for floor in floors_set:
                r_set = floor.roominess.all()
                for r in r_set:
                    extra_dict = {}
                    extra_dict['id'] = r.id
                    extra_dict['name'] = r.roominess_name
                    roominess_list.append(extra_dict)
            roominess_list = {v['id']: v for v in roominess_list}.values()

        data = {}
        data['housings'] = housings_list
        data['types'] = types_list
        data['roomsiness'] = roominess_list

        return Response(OrderedDict([
                ('filters', data)
            ]))


class RoominessViewSet(viewsets.ModelViewSet):

    """
    Вместительность в настройках (одноместные, двухместные и т.д.)

    1. Без ID
    get - list
    post - create
    2. C ID
    get - retrieve
    put - update
    delete - delete
    """

    lookup_field = 'pk'
    ordering = ['roominess']
    queryset = Roominess.objects.all().order_by('roominess')
    authentication_classes = (TokenAuthentication,)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.action == 'list':
            # if self.request.user.is_authenticated:
            #     return RoominessBriefSerializer
            return RoominessListSerializer
        return RoominessCreateSerializer


class PricesTableView(APIView):
    """
    Страница: Цены. Параметры в описании.

    Параметры:
    room_type - {id} по умолчанию стандарт

    1. Без ID
    get - list

    """
    authentication_classes = (TokenAuthentication,)

    def get(self, request, format=None):
        response = {}
        result = []
        roominess_set = Roominess.objects.prefetch_related('prices').reverse().order_by('roominess')
        ps_set = Price.objects.select_related('roominess', 'housing')

        room_type = TypeOfRoom.objects.get(type='Стандарт')
        if (self.request.query_params.get('room_type')):
            room_type = str(self.request.query_params.get('room_type'))
        ps_set = ps_set.filter(room_type=room_type)
        housings = Housing.objects.all()

        for h in housings:
            price = []
            prices_set = ps_set.filter(housing=h).order_by('from_date').values('from_date', 'to_date').distinct()
            for ps in prices_set:
                per_dict = {}
                from_date = '.'.join(["{:02d}".format(ps['from_date'].day), "{:02d}".format(ps['from_date'].month)])
                to_date = '.'.join(["{:02d}".format(ps['to_date'].day), "{:02d}".format(ps['to_date'].month)])
                period = '-'.join([from_date, to_date])
                per_dict['name'] = 'Период'
                per_dict['value'] = period
                per_list = []
                per_list.append(per_dict)
                for rs in roominess_set:
                    rm_dict = {}
                    rm_dict['name'] = rs.roominess_name
                    try:
                        cur_price_obj = ps_set.get(room_type=room_type, housing=h, roominess=rs.roominess,
                                                   from_date=ps['from_date'], to_date=ps['to_date'])
                        rm_dict['value'] = cur_price_obj.price
                    except:
                        rm_dict['value'] = None

                    per_list.append(rm_dict)
                price.append(per_list)
            if prices_set.count()>0:
                result.append({'housing': h.name, 'price': price})

        year = str(ps_set.latest('from_date').from_date.year)
        prices_within_year = ps_set.filter(from_date__year=year)
        min_date = str(prices_within_year.earliest('from_date').from_date)
        max_date = str(prices_within_year.latest('to_date').to_date)

        response['desc'] = 'Стоимость номеров на летний период %s (%s по %s %sг. \n Питание: 600 сом с человека.)' % (
            year, min_date, max_date, year)
        response['result'] = result

        return HttpResponse(content=json.dumps(response),
                            status=status.HTTP_200_OK,
                            content_type='application/json'
                            )


class ReservationPayment(APIView):
    # uuid
    #
    def post(self, request, order_id):
        id = request.data['id']
        total_sum = request.data['total_sum']
        response = {'url': 'url'}
        return JsonResponse(response)


class RoomViewViewSet(viewsets.ModelViewSet):
    """
        Вид (на озеро, на парковку и т.д.)

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
    """
    queryset = RoomView.objects.all()
    serializer_class = RoomViewSerializer
    lookup_field = 'pk'


class FloorViewSet(viewsets.ModelViewSet):
    """
        Этажи

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
    """
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer
    lookup_field = 'pk'


class MaidViewSet(viewsets.ModelViewSet):
    """
        Горничные

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
    """
    queryset = Maid.objects.all()
    serializer_class = MaidSerializer
    lookup_field = 'pk'


class ManagerViewSet(viewsets.ModelViewSet):
    """
        Менеджеры

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
    """
    queryset = Manager.objects.all()
    serializer_class = ManagerSerializer
    lookup_field = 'pk'


class AdministratorViewSet(viewsets.ModelViewSet):
    """
        Администраторы

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
    """
    queryset = Administrator.objects.all()
    serializer_class = AdministratorSerializer
    lookup_field = 'pk'


class RoomCreateFilterView(APIView):
    """
    Фильтрация полей для создания комнаты. Параметры в описании.

    Параметры:
    type - тип комнаты {id}
    housing - корпус {id}
    floor - этаж {id}
    roominess - вместительность {id}


    1. Без ID
    get - list

    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAdminUser]

    def get(self, request, format=None):
        types_list = []
        housings_list = []
        floors_list = []
        roominess_list = []
        sides_list = []

        for type in TypeOfRoom.objects.all():
            extra_dict = {}
            extra_dict['id'] = type.id
            extra_dict['name'] = type.type
            types_list.append(extra_dict)

        if self.request.GET.get('type'):
            type = TypeOfRoom.objects.get(id=self.request.GET.get('type'))
            housings = type.housing.all().order_by('name')
            for housing in housings:
                extra_dict = {}
                extra_dict['id'] = housing.id
                extra_dict['name'] = housing.name
                housings_list.append(extra_dict)

        if self.request.GET.get('housing'):
            housing = Housing.objects.get(id=self.request.GET.get('housing'))
            floors = housing.floors.all().order_by('floor')
            for floor in floors:
                extra_dict = {}
                extra_dict['id'] = floor.id
                extra_dict['name'] = floor.floor
                floors_list.append(extra_dict)

        if self.request.GET.get('floor'):
            floor = Floor.objects.get(id=self.request.GET.get('floor'))
            roominess_set = floor.roominess.all().order_by('roominess')
            for roominess in roominess_set:
                extra_dict = {}
                extra_dict['id'] = roominess.id
                extra_dict['name'] = roominess.roominess_name
                roominess_list.append(extra_dict)

        if self.request.GET.get('roominess'):
            sides = SIDE_CHOICES
            for side in sides:
                extra_dict = {}
                extra_dict['id'] = side[0]
                extra_dict['name'] = side[1]
                sides_list.append(extra_dict)

        data = {}
        data['types'] = types_list
        data['housings'] = housings_list
        data['floors'] = floors_list
        data['roominess'] = roominess_list
        data['sides'] = sides_list
        return Response(OrderedDict([
            ('filters', data)
        ]))


class ReservationPaymentView(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    lookup_field = 'pk'
    pagination_class = PaginationStaff

    def get_queryset(self):
        start_date = self.request.GET.get('date')
        search = self.request.GET.get('search')

        queryset = Payment.objects.all().order_by('-id')

        if start_date:
            date = str(start_date)
            date = date.replace('-', ' ').split()
            month = int(date[1])
            year = int(date[2])
            queryset = queryset.filter(date__month=month, date__year=year)
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)


class LandingViewSet(viewsets.ModelViewSet):
    """
        Главная страница

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
    """
    queryset = Landing.objects.all()
    serializer_class = LandingSerializer
    lookup_field = 'pk'

    def create(self, request, *args, **kwargs):
        if Landing.objects.count() > 0:
            return HttpResponseForbidden()

        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        instance = Landing.objects.first()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)



class SocialNetworkViewSet(viewsets.ModelViewSet):
    """
        Социальные сети

        1. Без ID
        get - list
        post - create
        2. C ID
        get - retrieve
        put - update
        delete - delete
    """
    queryset = SocialNetwork.objects.all()
    serializer_class = SocialNetworkSerializer
    lookup_field = 'pk'

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class GuestroomIsReserved(APIView):
    """
    Проверка существующих броней на данный номер в указанный промежуток. Параметры в описании.

     Параметры:
    room - номер {id}
    arrival_date - дата заезда {d-m-Y}
    departure_date - дата выезда {d-m-Y}

     1. Без ID
     get - list

     """
    authentication_classes = (TokenAuthentication,)
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        arrival_date = None
        departure_date = None

        if self.request.GET.get('room'):
            room = Guestroom.objects.get(id=self.request.GET.get('room'))

        if self.request.GET.get('arrival_date'):
            arrival_date = datetime.strptime(self.request.GET.get('arrival_date'), '%d-%m-%Y') + timedelta(days=1)

        if self.request.GET.get('departure_date'):
            departure_date = datetime.strptime(self.request.GET.get('departure_date'), '%d-%m-%Y') - timedelta(days=1)
        free = True
        reservations = Reservation.objects.filter(status='active', arrival_date__lte=departure_date, departure_date__gte=arrival_date, room=room)
        if reservations:
            free = False

        return Response(OrderedDict([
            ('free', free)
        ]))


class CleaningCreateFilterView(APIView):
    """
    Фильтрация полей для создания уборки. Параметры в описании.

    Параметры:
    housing - корпус {id}
    floor - этаж {id}
    roominess - вместительность {id}

    1. Без ID
    get - list

    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAdminUser]

    def get(self, request, format=None):
        housings_list = []
        floors_list = []
        roominess_list = []
        rooms_list = []
        housing = None
        floor = None

        for housing in Housing.objects.all().order_by('name'):
            extra_dict = {}
            extra_dict['id'] = housing.id
            extra_dict['name'] = housing.name
            housings_list.append(extra_dict)

        if self.request.GET.get('housing'):
            housing = Housing.objects.get(id=self.request.GET.get('housing'))
            floors = housing.floors.all().order_by('floor')
            for floor in floors:
                extra_dict = {}
                extra_dict['id'] = floor.id
                extra_dict['name'] = floor.floor
                floors_list.append(extra_dict)

        if self.request.GET.get('floor'):
            floor = Floor.objects.get(id=self.request.GET.get('floor'))
            roominess_set = floor.roominess.all().order_by('roominess')
            for room in roominess_set:
                extra_dict = {}
                extra_dict['id'] = room.id
                extra_dict['name'] = room.roominess_name
                roominess_list.append(extra_dict)

        if self.request.GET.get('roominess'):
            roominess = Roominess.objects.get(id=self.request.GET.get('roominess'))
            rooms = Guestroom.objects.filter(roominess=roominess, housing=housing, floor=floor).order_by('housing')
            serializer = RoomBriefSerializer(rooms, many=True)
            rooms_list = serializer.data

        data = {}
        data['housings'] = housings_list
        data['floors'] = floors_list
        data['roominess'] = roominess_list
        data['rooms'] = rooms_list

        return Response(OrderedDict([
            ('filters', data)
        ]))


class ChangeRoomDescription(generics.UpdateAPIView):
    """
    Изменение описания комнаты в календаре CRM.

    1. С ID
    get - retrieve

    """
    queryset = Guestroom.objects.all()
    serializer_class = FullRoomSerializer2
