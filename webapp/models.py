from django.db import models

# Create your models here.
from django.db.models import Min
from django.utils.safestring import mark_safe
from image_cropping import ImageRatioField


SIDE_CHOICES = (
    ('north', 'Север'),
    ('south', 'Юг'),
    ('west', 'Запад'),
    ('east', 'Восток'),
)


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


class Guestroom(models.Model):
    number = models.PositiveSmallIntegerField('Номер комнаты', null=True)
    roominess = models.ForeignKey('webapp.Roominess', on_delete=models.CASCADE, related_name='rooms',
                             verbose_name='Вмещаемость', null=True)
    type = models.ForeignKey('webapp.TypeOfRoom', on_delete=models.CASCADE, related_name='rooms', verbose_name='Тип', null=True)
    housing = models.ForeignKey('webapp.Housing', on_delete=models.CASCADE, related_name='rooms', verbose_name='Корпус', null=True)
    beds_count = models.PositiveSmallIntegerField('Количество кроватей', default=0)
    size = models.SmallIntegerField('Размер комнаты', null=True, blank=True)
    #floor = models.ForeignKey('webapp.Floor', on_delete=models.CASCADE, related_name='rooms', verbose_name='Этаж', null=True)
    description = models.TextField('Описание', null=True)
    furniture = models.CharField(max_length=256, default='', verbose_name='Мебель', null=True)
    side = models.CharField(max_length=50, choices=SIDE_CHOICES, default=SIDE_CHOICES[0][0],
                            verbose_name='Сторона', null=True)
    default_price = models.IntegerField('Цена по умолчанию', default=0,
                                        help_text='Если в базе нет цен на период, указанный в брони, использовать эту цену для подсчета итоговой суммы.')
    accessories = models.ManyToManyField('webapp.Accessories', blank=True, related_name='room_accessories', verbose_name='Принадлежности')
    comfort = models.ManyToManyField('webapp.Comfort', blank=True, related_name='room_comforts', verbose_name='Услуги и удобства')
    service = models.ManyToManyField('webapp.Service', blank=True, related_name='room_services', verbose_name='Сервис')
    # restrictions = models.ManyToManyField('webapp.Restriction', blank=True, related_name='room_restrictions', verbose_name='Запрещено')
    #view = models.ForeignKey('webapp.RoomView', on_delete=models.CASCADE, related_name='rooms', verbose_name='Вид', null=True)
    image = models.ImageField(upload_to='room_main_images', null=True, blank=True, verbose_name='Фоновая картинка', help_text='Будет показана первой, что увидит пользователь')
    cropping = ImageRatioField('image', '370x240')

    class Meta:
        verbose_name = 'Номер'
        verbose_name_plural = 'Номера'
        ordering = ('-id',)

    def image_tag(self):
        return mark_safe('<img src="/uploads/%s" style="max-width:200px;"/>' % (self.image))

    image_tag.short_description = 'Главное фото комнаты'
    image_tag.allow_tags = True

    def __str__(self):
        return "%s-%s" % (self.housing, self.number)

    def get_price(self):
        price = Price.objects.filter(room_type=self.type, roominess=self.roominess, housing=self.housing).aggregate(Min('price'))
        if price['price__min'] is None:
            return self.default_price
        return price['price__min']


class Price(models.Model):
    room_type = models.ForeignKey('webapp.TypeOfRoom', on_delete=models.CASCADE, related_name='price', verbose_name='Тип номера',
                             null=True)
    roominess = models.ForeignKey('webapp.Roominess', on_delete=models.CASCADE, related_name='prices', verbose_name='Вместительность', null=True)
    housing = models.ForeignKey('webapp.Housing', on_delete=models.CASCADE, related_name='prices', verbose_name='Корпус', null=True)
    from_date = models.DateField('С')
    to_date = models.DateField('До')
    price = models.PositiveIntegerField('Цена')

    class Meta:
        verbose_name = 'Цена'
        verbose_name_plural = 'Цены'
        ordering = ('-id',)

    def __str__(self):
        return '%s' %(self.price) or ''

