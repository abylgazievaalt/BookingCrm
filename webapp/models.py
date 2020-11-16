import uuid as uuid
from asgiref.sync import async_to_sync
from django.db import models
from channels.layers import get_channel_layer

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

CLIENT_TYPE_CHOICES = (
    ('individual', 'Физ. лицо'),
    ('entity', 'Организация')
)

PAYMENT_TYPE_CHOICES = (
    ('offline', 'офис'),
    ('online', 'онлайн'),
)

PAYMENT_STATUS_CHOICES = (
    ('not paid', 'Не оплачено'),
    ('fully paid', 'Оплачено полностью'),
    ('partially paid', 'Оплачено частично'),
)

RESERVATION_STATUS_CHOICES = (
    ('active', 'Активный'),
    ('not paid', 'Клиент не внес оплату'),
    ('date changed', 'Клиент поменял дату'),
    ('other', 'Другая причина')
)

async def send_notification(feedbacks_request):
    channel_layer = get_channel_layer()
    await channel_layer.group_send("notification_group", {
        "type": "notify",
        "content": {
                    "feedbacks_request": feedbacks_request,
                   },
    })


class Discount(models.Model):
    discount = models.IntegerField('Скидка', default=0, null=True)

    class Meta:
        verbose_name = 'Скидка'
        verbose_name_plural = 'Скидки'

    def __str__(self):
        return '%s%%' %(self.discount) or ''


class Meal(models.Model):
    date = models.DateField('Дата')
    breakfast = models.BooleanField('Завтрак', default=True)
    lunch = models.BooleanField('Обед', default=True)
    dinner = models.BooleanField('Ужин', default=True)
    reservation = models.ForeignKey('Reservation',on_delete=models.CASCADE, related_name='meals',
                                    verbose_name='Бронь номера', null=True)

    class Meta:
        verbose_name = 'Питание'
        verbose_name_plural = 'Питание'

    def __str__(self):
        return '%s %s %s' % (self.breakfast, self.lunch, self.dinner)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        reservation = Reservation.objects.get(id=self.reservation.id)
        reservation.save()

    def delete(self):
        reservation = Reservation.objects.get(id=self.reservation.id)
        super(Meal, self).delete()
        reservation.save()


class Reservation(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    client_type = models.CharField('Тип клиента', max_length=10, choices=CLIENT_TYPE_CHOICES, default='individual')
    room = models.ForeignKey('webapp.Guestroom', on_delete=models.CASCADE, null=True, related_name='reservations', verbose_name='Номер')
    arrival_date = models.DateField('Дата заезда')
    departure_date = models.DateField('Дата выезда')
    count_calendar = models.PositiveSmallIntegerField('Количество людей с питанием', default=0)
    count_of_people = models.PositiveSmallIntegerField('Общее кол-во людей')
    name = models.CharField('Имя', max_length=100)
    last_name = models.CharField('Фамилия', max_length=100)
    phone = models.CharField('Номер телефона', max_length=100)
    email = models.EmailField('Электроная почта', max_length=200, unique=False)
    comment = models.TextField('Комментарий', default='', blank=True)
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPE_CHOICES, default=PAYMENT_TYPE_CHOICES[0][0],
                                    verbose_name='Тип оплаты')
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_CHOICES[0][0],
                                      verbose_name='Статус оплаты')
    total_sum = models.PositiveIntegerField('Итоговая сумма', default=0)
    discount = models.IntegerField('Скидка', default=0, null=True)
    status = models.CharField(max_length=12, choices=RESERVATION_STATUS_CHOICES, default='active', verbose_name='Статус')
    payment_url = models.CharField('Ссылка на оплату', max_length=1000, blank=True, null=True)

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'

    def __str__(self):
        return self.name or ""

    # def get_total_sum(self):
    #     meals = None
    #     meals_sum = 0
    #     sum = 0
    #
    #     try:
    #         meals = Meal.objects.filter(reservation=self)
    #     except:
    #         pass
    #
    #     arrival = datetime.datetime.strptime(str(self.arrival_date), '%Y-%m-%d')
    #     departure = datetime.datetime.strptime(str(self.departure_date), '%Y-%m-%d')
    #     delta_days = (departure - arrival).days
    #
    #     try:
    #         prices = MealPrice.objects.first()
    #         total_per_day = prices.breakfast + prices.lunch + prices.dinner
    #         meals_sum =  total_per_day * delta_days * self.count_of_people
    #
    #         if meals:
    #             custom_meals_sum = 0
    #             for item in self.meals.all():
    #                 custom_meals_sum += self.count_of_people * item.get_cost_per_person()
    #
    #             meals_sum -= meals.count() * total_per_day * self.count_of_people
    #             meals_sum += custom_meals_sum
    #     except:
    #         meals_sum = 0
    #
    #     try:
    #         room_price = Price.objects.get(room_type=self.room.type, roominess=self.room.roominess,
    #                                         from_date__lte=self.departure_date, to_date__gte=self.arrival_date,
    #                                         housing=self.room.housing).price
    #     except:
    #         room_price = self.room.default_price
    #
    #     sum = delta_days * room_price + meals_sum
    #     if self.discount is not None:
    #         sum -= sum *(self.discount.discount / 100.0)
    #     return round(sum)

    def save(self, *args, **kwargs):
        self.room.status = 'Забронировано'
        reservation_request = 'Новая бронь'
        # self.total_sum = self.get_total_sum()
        super().save(*args, **kwargs)
        name = f'{self.name[0]}. {self.last_name}'
        try:
            Payment.objects.get(reservation=self)
        except:
            Payment.objects.create(
                reservation=self, name=name, total_sum=self.total_sum,
                payment_type=self.payment_type, status='not paid'
            )
        if self.pk is None:
            async_to_sync(send_notification)(reservation_request)


class Payment(models.Model):
    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
        ordering = ('-id',)

    reservation = models.OneToOneField(Reservation, verbose_name='Бронь', on_delete=models.CASCADE, related_name='payment')
    date = models.DateTimeField('Дата', auto_now_add=True, null=True)
    name = models.CharField('ФИО', max_length=256)
    total_sum = models.PositiveIntegerField('Итоговая сумма', default=0)
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPE_CHOICES, default=PAYMENT_TYPE_CHOICES[0][0],
                                    verbose_name='Способ оплаты')
    status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_CHOICES[0][0],
                                    verbose_name='Тип оплаты')

    def __str__(self):
        return f'{self.name} | {self.total_sum} | {self.date}'


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

