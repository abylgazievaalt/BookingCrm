from django.contrib import admin
from django.contrib.auth.models import Group
from webapp.models import Accessories, Comfort, Guestroom, Housing, Gallery, Service, AboutUs, \
    AboutUsNumbers, Reservation, RoomGallery, Feedback, Staff, Maid, Manager, Cleaning, Meal, FeedbackReply, Discount, \
    GalleryCategory, Price, Roominess, Contacts, Phone, RoomView, Floor, MealPrice, MainPage, TypeOfRoom, Restriction, \
    Administrator, Payment, Landing, SocialNetwork, GalleryPhoto, ServiceLanding

from image_cropping import ImageCroppingMixin
from webapp.models import GalleryPhoto, Discount, Roominess, TypeOfRoom, ServiceLanding, Service


def custom_titled_filter(title):
    class Wrapper(admin.FieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = admin.FieldListFilter.create(*args, **kwargs)
            instance.title = title
            return instance
    return Wrapper

class GalleryPhotoInlineAdmin(ImageCroppingMixin, admin.StackedInline):
    model = GalleryPhoto
    extra = 0
    fields = ('image', 'image_tag')
    readonly_fields = ('image_tag',)


class GalleryAdmin(ImageCroppingMixin, admin.ModelAdmin):
    fields = ('name', 'image', 'image_tag')
    readonly_fields = ('image_tag',)
    inlines = [
        GalleryPhotoInlineAdmin,
    ]

    def save_model(self, request, obj, form, change):
        obj.save()

        for afile in request.FILES.getlist('photos_multiple'):
            GalleryPhoto.objects.create(gallery=obj, image=afile)


class ServiceAdmin(admin.ModelAdmin):
    fields = ('name', 'description', 'image', 'image_tag',)
    readonly_fields = ('image_tag',)
    list_display = ('name', 'description',)


class AboutUsPage(admin.ModelAdmin):
    fields = ('image', 'image_tag', 'description', 'full_description' )
    readonly_fields = ('image_tag',)

    def has_add_permission(self, request):
        if self.model.objects.count() > 0:
            return False
        else:
            return True


class PhoneInlineAdmin(admin.StackedInline):
    model = Phone
    extra = 0


class ContactsAdmin(ImageCroppingMixin, admin.ModelAdmin):
    fields = ('address', 'email', 'background')

    inlines = [
        PhoneInlineAdmin,
    ]

    def has_add_permission(self, request):
        if self.model.objects.count() > 0:
            return False
        else:
            return True


class MealInlineAdmin(admin.StackedInline):
    model = Meal
    extra = 0


class ReservationAdmin(admin.ModelAdmin):
    inlines = [
        MealInlineAdmin,
    ]
    exclude = ('payment_url',)
    list_display = ('room', 'name', 'last_name', 'payment_type', 'payment_status', 'arrival_date', 'departure_date')
    list_filter = ('room', 'payment_status',)


class FeedbackReplyInlineAdmin(admin.StackedInline):
    model = FeedbackReply
    extra = 1
    max_num = 1


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'name', 'email', 'phone', 'comment', 'status',)
    list_filter = ('date',)

    inlines = [
        FeedbackReplyInlineAdmin,
    ]

class CleaningAdmin(admin.ModelAdmin):
    list_display = ('room', 'get_maids', 'status', 'date', 'start_time', 'end_time')
    list_filter = ('date', 'housing', 'room', 'floor')
    readonly_fields = ('room_type', 'housing', 'floor')

    def get_fields(self, request, obj=None):
        fields = list(super(CleaningAdmin, self).get_fields(request, obj))
        exclude_set = set()
        if not obj:  # obj will be None on the add page, and something on change pages
            exclude_set.add('room_type')
            exclude_set.add('housing')
            exclude_set.add('floor')
        return [f for f in fields if f not in exclude_set]

    def get_maids(self, obj):
        return ",\n".join([(m.fk.first_name + ' ' + m.fk.last_name) for m in obj.maids.all()])
    get_maids.short_description = 'Горничные'


class PriceAdmin(admin.ModelAdmin):
    list_display = ('id', 'room_type', 'roominess', 'housing', 'from_date', 'to_date', 'price')
    list_filter = ('room_type', 'roominess')


class AccessoriesAdmin(admin.ModelAdmin):
    fields = ('name','image', 'image_tag',)
    readonly_fields = ('image_tag',)
    list_display = ('name',)


class ComfortAdmin(admin.ModelAdmin):
    fields = ('name', 'image', 'image_tag',)
    readonly_fields = ('image_tag',)
    list_display = ('name',)


class RestrictionAdmin(admin.ModelAdmin):
    fields = ('text', 'image', 'image_tag',)
    readonly_fields = ('image_tag',)
    list_display = ('text',)


class StaffAdmin(admin.ModelAdmin):
    list_display = ('id', 'last_name', 'first_name', 'middle_name', 'role', 'date_created', )
    list_filter = ('role', 'date_created')


class MealPriceAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if self.model.objects.count() > 0:
            return False
        else:
            return True


class RoomGalleryInlineAdmin(ImageCroppingMixin, admin.StackedInline):
    model = RoomGallery
    extra = 0
    fields = ('image', 'image_tag')
    readonly_fields = ('image_tag',)


class MainPageAdmin(ImageCroppingMixin, admin.ModelAdmin):
    model = RoomGallery
    fields = ('heading', 'background', 'background_tag', 'darkening')
    readonly_fields = ('background_tag',)

    def has_add_permission(self, request):
        if self.model.objects.count() > 0:
            return False
        else:
            return True


class GuestroomAdmin(ImageCroppingMixin, admin.ModelAdmin):
    fields = ('type', 'number', 'housing', 'roominess', 'size', 'floor', 'view', 'beds_count', 'furniture', 'side', 'default_price',
              'description', 'accessories', 'comfort', 'service', 'image', 'image_tag')
    readonly_fields = ('image_tag',)
    list_display = ('__str__', 'type', 'size', 'floor', 'beds_count', 'side', )
    list_filter = ('type', 'roominess', 'housing')
    inlines = [
        RoomGalleryInlineAdmin,
    ]


class FloorInlineAdmin(admin.StackedInline):
    model = Floor
    extra=2


class HousingAdmin(admin.ModelAdmin):
    inlines = [
        FloorInlineAdmin,
    ]


admin.site.register(Guestroom, GuestroomAdmin)
admin.site.register(AboutUs, AboutUsPage)
admin.site.register(Housing, HousingAdmin)
admin.site.register(Phone)
admin.site.register(Reservation, ReservationAdmin)
admin.site.register(Comfort, ComfortAdmin)
admin.site.register(Accessories, AccessoriesAdmin)
admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(Staff, StaffAdmin)
admin.site.register(Maid)
admin.site.register(Manager)
admin.site.register(Administrator)
admin.site.register(Cleaning, CleaningAdmin)
admin.site.register(MealPrice, MealPriceAdmin)
# admin.site.register(FeedbackReply)
admin.site.register(GalleryCategory)
admin.site.register(Price, PriceAdmin)
admin.site.register(Gallery, GalleryAdmin)
# admin.site.register(RoomGallery, RoomGalleryAdmin)
# admin.site.register(Gallery)
admin.site.register(RoomView)
admin.site.register(MainPage, MainPageAdmin)
admin.site.register(Floor)
admin.site.register(Contacts, ContactsAdmin)
admin.site.register(Landing)
admin.site.register(AboutUsNumbers)
admin.site.register(SocialNetwork)
admin.site.register(GalleryPhoto)
admin.site.register(Restriction, RestrictionAdmin)
admin.site.unregister(Group)
admin.site.register(Payment)
admin.site.register(Discount)
admin.site.register(Roominess)
admin.site.register(TypeOfRoom)
admin.site.register(ServiceLanding)
admin.site.register(Service, ServiceAdmin)
