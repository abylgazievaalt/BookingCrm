from django.contrib import admin

# Register your models here.
from image_cropping import ImageCroppingMixin

from webapp.models import GalleryPhoto, Discount, Roominess, TypeOfRoom, ServiceLanding


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


admin.site.register(Discount)
admin.site.register(Roominess)
admin.site.register(TypeOfRoom)
admin.site.register(ServiceLanding)
admin.site.register(Service, ServiceAdmin)
