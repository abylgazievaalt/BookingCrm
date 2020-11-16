from django.db import models

# Create your models here.
from django.utils.safestring import mark_safe
from image_cropping import ImageRatioField


class Discount(models.Model):
    discount = models.IntegerField('Скидка', default=0, null=True)

    class Meta:
        verbose_name = 'Скидка'
        verbose_name_plural = 'Скидки'

    def __str__(self):
        return '%s%%' %(self.discount) or ''


class Roominess(models.Model):
    roominess = models.PositiveSmallIntegerField('Вместительность номера(число)', default=0, blank=True)
    roominess_name = models.CharField('Вместительность номера', max_length=200)
    price_from = models.PositiveIntegerField('Цены от', default=0)
    image = models.ImageField(upload_to='roominess_images', null=True, blank=True, verbose_name='Фото')
    cropping = ImageRatioField('image', '220x180')
    date_created = models.DateField('Дата', null=True, auto_now_add=True)

    class Meta:
        verbose_name = 'Вместительность номера'
        verbose_name_plural = 'Вместительность номеров'
        ordering = ('-id',)

    def __str__(self):
        return f'{self.roominess_name}' or ''

    def image_tag(self):
        return mark_safe('<img src="/uploads/%s" style="max-width:200px;"/>' % (self.image))

    image_tag.short_description = 'Фото'
    image_tag.allow_tags = True


class TypeOfRoom(models.Model):
    type = models.CharField('Тип номера', max_length=50, default='')

    class Meta:
        verbose_name = 'Тип номера'
        verbose_name_plural = 'Типы номеров'
        ordering = ('-id',)

    def __str__(self):
        return self.type


class Housing(models.Model):
    name = models.CharField('Название корпуса', max_length=200)
    types = models.ManyToManyField('webapp.TypeOfRoom', related_name='housing', verbose_name='Типы номеров')
    distance = models.CharField('До озера', max_length=50, default='')
    active = models.BooleanField('Активный', default=True)
    longitude = models.CharField('Долгота', max_length=50, default='')
    latitude = models.CharField('Широта', max_length=50, default='')

    class Meta:
        ordering = ('name',)
        verbose_name = 'Корпус'
        verbose_name_plural = 'Корпусы'

    def __str__(self):
        return self.name


class Accessories(models.Model):
    name = models.CharField('Принадлежность', max_length=200)
    image = models.FileField(upload_to='accessories_images/', null=True, blank=True, verbose_name='Иконка')
    date_created = models.DateField('Дата', null=True, auto_now_add=True)

    class Meta:
        verbose_name = 'Принадлежность'
        verbose_name_plural = 'Принадлежности'
        ordering = ('-id',)

    def image_tag(self):
        return mark_safe('<img src="/uploads/%s" style="max-width:200px;"/>' % (self.image))

    image_tag.short_description = 'Иконка'
    image_tag.allow_tags = True

    def __str__(self):
        return self.name


class RoomGallery(models.Model):
    room = models.ForeignKey('webapp.Guestroom', on_delete=models.CASCADE, related_name='room_galleries', verbose_name='Комната')
    image = models.ImageField(upload_to='room_images/', null=True, blank=True, verbose_name='Фото')
    cropping = ImageRatioField('image', '770x410')

    class Meta:
        verbose_name = 'Фото'
        verbose_name_plural = 'Фото'

    def image_tag(self):
        return mark_safe('<img src="/uploads/%s" style="max-width:200px;"/>' % (self.image))

    image_tag.short_description = 'Фото'
    image_tag.allow_tags = True


class Comfort(models.Model):
    name = models.CharField('Название', max_length=200)
    image = models.FileField(upload_to='comfort_images/', null=True, blank=True, verbose_name='Иконка')
    date_created = models.DateField('Дата', null=True, auto_now_add=True)

    class Meta:
        verbose_name = 'Услуги и удобства'
        verbose_name_plural = 'Услуги и удобства'
        ordering = ('-id',)

    def image_tag(self):
        return mark_safe('<img src="/uploads/%s" style="max-width:200px;"/>' % (self.image))

    image_tag.short_description = 'Иконка'
    image_tag.allow_tags = True

    def __str__(self):
        return self.name


class GalleryCategory(models.Model):
    name = models.CharField('Название достопримечательности', max_length=200)
    date_created = models.DateField('Дата', null=True, auto_now_add=True)

    class Meta:
        verbose_name = 'Категория галереи'
        verbose_name_plural = 'Категории галереи'

    def __str__(self):
        return f'{self.name}'


class Gallery(models.Model):
    name = models.CharField('Название', max_length=128, blank=True, null=True)
    image = models.ImageField(upload_to='attr_images/', null=True, blank=True, verbose_name='Фото')
    cropping = ImageRatioField('image', '270x240')

    class Meta:
        verbose_name = 'Галерея'
        verbose_name_plural = 'Галерея'
        ordering = ('-id',)

    def __str__(self):
        return self.name

    def image_tag(self):
        return mark_safe('<img src="/uploads/%s" style="max-width:200px;"/>' % (self.image))

    image_tag.short_description = 'Фото'
    image_tag.allow_tags = True


class GalleryPhoto(models.Model):
    gallery = models.ForeignKey('webapp.Gallery', on_delete=models.CASCADE, related_name='gallery_photos',
                                 null=True, blank=True, verbose_name='Галерея')
    image = models.ImageField(upload_to='gallery_images', null=True, blank=True, verbose_name='Фото')

    class Meta:
        verbose_name = 'Фотография'
        verbose_name_plural = 'Фотографии'

    def __str__(self):
        return self.gallery.name

    def image_tag(self):
        return mark_safe('<img src="/uploads/%s" style="max-width:200px;"/>' % (self.image))

    image_tag.short_description = 'Фото'
    image_tag.allow_tags = True


class Service(models.Model):
    name = models.CharField('Название сервиса', max_length=200)
    description = models.TextField('Описание сервиса')
    image = models.FileField(upload_to='service_images/', null=True, blank=True, verbose_name='Иконка')
    date_created = models.DateField('Дата', auto_now_add=True, null=True)

    class Meta:
        verbose_name = 'Сервис'
        verbose_name_plural = 'Сервис'
        ordering = ('-id',)

    def image_tag(self):
        return mark_safe('<img src="/uploads/%s" style="max-width:200px;"/>' % (self.image))

    image_tag.short_description = 'Иконка'
    image_tag.allow_tags = True

    def __str__(self):
        return self.name


class ServiceLanding(models.Model):
    class Meta:
        verbose_name = 'Сервис на главном'
        ordering = ['id']

    service = models.ForeignKey('webapp.Service', models.CASCADE, null=True)

    def __str__(self):
        return self.service


