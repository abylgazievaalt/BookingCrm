from django.urls import path, include
from rest_framework import routers

from .views import RoomViewSet, ReservationViewSet, ServiceViewSet, HousingViewSet, AccessoriesViewSet, \
    ContactsViewSet, FeedbackViewSet, AboutUsViewSet, AboutNumberViewSet, ComfortViewSet, \
    RoomGalleryViewSet, StaffViewSet, MealViewSet, FeedbackReplyViewSet, \
    PriceViewSet, GalleryCategoryViewSet, RoominessViewSet \
    , RoomListViewSet, AboutInfoViewSet, PricesTableView, RoomViewViewSet, FloorViewSet, AvailableListViewSet, \
    CleaningViewSet, MainPageViewSet, ReservationPayment, PaymentView, MaidViewSet, ManagerViewSet, \
    PriceCreateFilterView, CleaningCreateFilterView, RoomCreateFilterView, AdministratorViewSet, ReservationPaymentView, \
    PaymentResponseView, \
    LandingViewSet, PriceFilterView, AvailableFilterView, get_calendar_filters, SocialNetworkViewSet, PaymentTypesView, \
    GuestroomIsReserved, GalleryViewSet, GalleryPhotosViewSet, get_calendar_rooms, get_reservation_receipt, \
    ChangeRoomDescription, TypeOfRoomViewSet, CrmPriceFilterView, ServiceLandingViewSet, MealPriceView

app_name = 'api'


urlpatterns = [
    path('mealPrice', MealPriceView.as_view({'get': 'list', 'put': 'update'})),
    path('available/', AvailableListViewSet.as_view({'get': 'list'})),
    path('available/filter', AvailableFilterView.as_view()),

    path('room/filter', RoomCreateFilterView.as_view()),
    path('room/', RoomListViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('room_is_free/', GuestroomIsReserved.as_view()),
    path('room/<int:pk>/', RoomViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch':'partial_update', 'delete': 'destroy'})),

    path('meal/', MealViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('meal/<int:pk>/', MealViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('reservation/', ReservationViewSet.as_view({'post': 'create', 'get': 'list'})),
    path('reservation/<int:pk>/', ReservationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch':'partial_update', 'delete': 'destroy'})),
    path('reservation/payment/<int:pk>/', PaymentView.as_view(), name='payment'),
    path('reservation/payment_response', PaymentResponseView.as_view(), name='payment_response'),

    path('roominess/', RoominessViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('roominess/<int:pk>/', RoominessViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('service/', ServiceViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('service_landing/', ServiceLandingViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('service_landing/<int:pk>/', ServiceLandingViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),

    path('service/<int:pk>/', ServiceViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('housing/', HousingViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('housing/<int:pk>/', HousingViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('accessories/', AccessoriesViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('accessories/<int:pk>/', AccessoriesViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('room/photos/', RoomGalleryViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('room/photos/<int:pk>/', RoomGalleryViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('contact/', ContactsViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
    # path('contact/<int:pk>/', ContactsViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('gallery/', GalleryViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('gallery/<int:pk>/', GalleryViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    # path('gallery_photos', GalleryPhotosViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('gallery_photos/<int:pk>/', GalleryPhotosViewSet.as_view({'delete': 'destroy'})),

    path('gallery_category/', GalleryCategoryViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('gallery_category/<int:pk>/', GalleryCategoryViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('feedback/', FeedbackViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('feedback/<int:pk>/', FeedbackViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch':'partial_update', 'delete': 'destroy'})),

    path('reply/', FeedbackReplyViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('reply/<int:pk>/', FeedbackReplyViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('main/', MainPageViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
    # path('main/<int:pk>/', MainPageViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('social/', SocialNetworkViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('social/<int:pk>/', SocialNetworkViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),

    path('about/', AboutUsViewSet.as_view({'get': 'list', 'put': 'update'})),
    path('info/', AboutInfoViewSet.as_view({'get': 'list', 'post': 'create'})),
    # path('about/<int:pk>/', AboutUsViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),

    path('about/numbers/', AboutNumberViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('about/numbers/<int:pk>/', AboutNumberViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('price/filter/', PriceCreateFilterView.as_view()),
    path('price/count/', PriceFilterView.as_view()),
    path('price/custom_count/', CrmPriceFilterView.as_view()),
    path('price/', PriceViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('price/<int:pk>/', PriceViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('prices/', PricesTableView.as_view()),

    path('comfort/', ComfortViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('comfort/<int:pk>/', ComfortViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('maid/', MaidViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('maid/<int:pk>/', MaidViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('manager/', ManagerViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('manager/<int:pk>/', ManagerViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('administrator/', AdministratorViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('administrator/<int:pk>/', AdministratorViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('staff/', StaffViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('staff/<int:pk>/', StaffViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('room_types/', TypeOfRoomViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('room_types/', StaffViewSet.as_view({'get': 'list', 'post': 'create'})),

    path('cleaning/filter', CleaningCreateFilterView.as_view()),
    path('cleaning/', CleaningViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('cleaning/<int:pk>/', CleaningViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch':'partial_update', 'delete': 'destroy'})),

    path('roomview/', RoomViewViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('roomview/<int:pk>/', RoomViewViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('floor/', FloorViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('floor/<int:pk>/', FloorViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('landing/', LandingViewSet.as_view({'get': 'list'})),

    path('pay/<int:order_id>/', ReservationPayment.as_view()),

    path('get_calendar_filters/', get_calendar_filters, name='get_calendar_filters'),
    path('get_calendar_reservations/', get_calendar_rooms, name='get_calendar_rooms'),

    path('change_room_description/<int:pk>/', ChangeRoomDescription.as_view(), name='change_room_description'),

    path('payment_types', PaymentTypesView.as_view()),
    path('payments/', ReservationPaymentView.as_view({'get': 'list'})),
    path('payments/<int:pk>/', ReservationPaymentView.as_view({'get': 'retrieve', 'put': 'update'})),
    path('reservation/receipt/<int:pk>/', get_reservation_receipt, name='reservation_receipt'),
]
