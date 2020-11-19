import uuid as uuid
from asgiref.sync import async_to_sync
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db import models
from channels.layers import get_channel_layer

# Create your models here.
from django.db.models import Min
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.safestring import mark_safe
from image_cropping import ImageRatioField

from BookingCrm.local_settings import EMAIL_HOST_USER

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

ROLE_CHOICES = (
    ('administrator', 'Администратор'),
    ('manager', 'Менеджер'),
    ('maid', 'Горничная')
)

FEEDBACK_STATUS_CHOICES = (
    ('N', 'Не просмотрено'),
    ('P', 'Просмотрено'),
)

CLEANING_STATUS_CHOICES = (
    ('waiting', 'Ожидание'),
    ('in process', 'В процессе'),
    ('done', 'Завершен')
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


class AboutUs(models.Model):
    image = models.ImageField(upload_to='about_us_images/', null=True, blank=True, verbose_name='Картинка')
    cropping = ImageRatioField('image', '1170x440')
    description = models.TextField('Краткое описание')
    full_description = models.TextField('Полное описание', default='')

    class Meta:
        verbose_name = 'О нас'
        verbose_name_plural = 'О нас'

    def image_tag(self):
        return mark_safe('<img src="/uploads/%s" style="max-width:200px;"/>' % (self.image))

    image_tag.short_description = 'Фото для баннера'
    image_tag.allow_tags = True

    def __str__(self):
        return 'О нас'

    def save(self, *args, **kwargs):
        if not self.pk and AboutUs.objects.exists():
            raise ValidationError('There is can be only one AboutUs instance')
        return super(AboutUs, self).save(*args, **kwargs)


class AboutUsNumbers(models.Model):
    # fk = models.ForeignKey('webapp.AboutUs', on_delete=models.CASCADE, related_name='quantities', null=True, blank=True)
    quantity = models.CharField('Цифры', max_length=200)
    description = models.CharField('Описание', max_length=200, null=True, blank=True)

    class Meta:
        verbose_name = 'В цифрах'
        verbose_name_plural = 'В цифрах'

    def __str__(self):
        return "%s %s" % (self.quantity, self.description)


class Phone(models.Model):
    phone = models.CharField('Телефон', max_length=200)
    contacts = models.ForeignKey('webapp.Contacts', null=True, on_delete=models.CASCADE, related_name='phones', verbose_name='Контакты')

    class Meta:
        verbose_name = 'Телефон'
        verbose_name_plural = 'Телефоны'


class MainPage(models.Model):
    heading = models.CharField('Заголовок', max_length=30, default='')
    background = models.ImageField('Изображение',  upload_to='main_page_images/', null=True)
    video = models.FileField('Видео', upload_to='video/', null=True)
    cropping = ImageRatioField('background', '1366x620')
    darkening = models.BooleanField('Сделать затемнение изображения', default=True)
    show_video = models.BooleanField('Показывать видео', default=True)

    class Meta:
        verbose_name = 'Главная страница'
        verbose_name_plural = 'Главная страница'

    def background_tag(self):
        return mark_safe('<img src="/uploads/%s" style="max-width:200px;"/>' % (self.background))

    background_tag.short_description = 'Изображение'
    background_tag.allow_tags = True

    def __str__(self):
        return self.heading


class Contacts(models.Model):
    address = models.CharField('Адрес', max_length=200)
    email = models.EmailField('Email', max_length=200, unique=True)
    phone = models.CharField('Телефон 1', max_length=200, blank=True, null=True)
    phone2 = models.CharField('Телефон 2', max_length=200, blank=True, null=True)

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'

    def __str__(self):
        return 'Контакты'


class SocialNetwork(models.Model):
    name = models.CharField('Заголовок', null=True, blank=True, max_length=400)
    link = models.CharField('Ссылка', null=True, blank=True, max_length=400)
    icon = models.FileField('Иконка', upload_to='social_images/', null=True)

    class Meta:
        verbose_name = 'Социальная сеть'
        verbose_name_plural = 'Социальные сети'

    def image_tag(self):
        return mark_safe('<img src="/uploads/%s" style="max-width:200px;"/>' % (self.icon))

    image_tag.short_description = 'Иконка'
    image_tag.allow_tags = True

    def __str__(self):
        return self.name


class Manager(models.Model):
    fk = models.ForeignKey('webapp.Staff', null=True, on_delete=models.CASCADE, related_name='managers', verbose_name='Сотрудник')

    class Meta:
        verbose_name = 'Менеджер'
        verbose_name_plural = 'Менеджеры'

    def __str__(self):
        return f'{self.fk}'

    def delete(self):
        self.delete_reverse()
        super(Manager, self).delete()

    @receiver(post_delete, sender='webapp.Manager')
    def delete_reverse(sender, **kwargs):
        try:
            if kwargs['instance'].fk:
                kwargs['instance'].fk.delete()
        except:
            pass


class Maid(models.Model):
    fk = models.ForeignKey('webapp.Staff', null=True, on_delete=models.CASCADE, related_name='maids', verbose_name='Сотрудник')

    class Meta:
        verbose_name = 'Горничная'
        verbose_name_plural = 'Горничные'

    def __str__(self):
        return f'{self.fk}'

    @receiver(post_delete, sender='webapp.Maid')
    def delete_reverse(sender, **kwargs):
        try:
            if kwargs['instance'].fk:
                kwargs['instance'].fk.delete()
        except:
            pass

    def delete(self):
        self.delete_reverse()
        super(Maid, self).delete()


class Administrator(models.Model):
    fk = models.ForeignKey('webapp.Staff', null=True, on_delete=models.CASCADE, related_name='admins', verbose_name='Сотрудник')

    class Meta:
        verbose_name = 'Администратор'
        verbose_name_plural = 'Администраторы'

    def __str__(self):
        return f'{self.fk}'

    @receiver(post_delete, sender='webapp.Administrator')
    def delete_reverse(sender, **kwargs):
        try:
            if kwargs['instance'].fk:
                kwargs['instance'].fk.delete()
        except:
            pass

    def delete(self):
        self.delete_reverse()
        super(Administrator, self).delete()


class Cleaning(models.Model):
    room_type = models.ForeignKey('webapp.TypeOfRoom', on_delete=models.CASCADE, related_name='cleaning', verbose_name='Тип номера',
                             null=True)
    housing = models.ForeignKey('webapp.Housing', null=True, on_delete=models.CASCADE, related_name='cleaning', verbose_name='Корпус', blank=True)
    floor = models.ForeignKey('webapp.Floor', null=True, on_delete=models.CASCADE, related_name='cleaning', verbose_name='Этаж', blank=True)
    room = models.ForeignKey('webapp.Guestroom', null=True, on_delete=models.CASCADE, related_name='cleaning', verbose_name='Номер')
    maids = models.ManyToManyField('webapp.Maid', related_name='cleaning', verbose_name='Горничная')
    status = models.CharField('Статус', max_length=10, choices=CLEANING_STATUS_CHOICES, default='waiting')
    date = models.DateField('Дата')
    start_time = models.TimeField('Начало')
    end_time = models.TimeField('Конец', null=True, blank=True)

    class Meta:
        verbose_name = 'Уборка номера'
        verbose_name_plural = 'Уборка номеров'
        ordering = ('-id',)

    def __str__(self):
        return '%s' % (self.room)

    def save(self, *args, **kwargs):
        if self.status == 'done':
            time = timezone.now().time()
            h = time.hour
            m = time.minute
            s = time.second
            self.end_time = f'{h:02d}:{m:02d}:{s:02d}'
        try:
            self.room_type = self.room.type
        except:
            self.room_type = None
        super(Cleaning, self).save(*args, **kwargs)


class Staff(models.Model):
    role = models.CharField(choices=ROLE_CHOICES, default='administrator', max_length=50, verbose_name='Должность')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    first_name = models.CharField(max_length=50, verbose_name='Имя')
    middle_name = models.CharField(max_length=50, verbose_name='Отчество')
    date_created = models.DateField('Дата добавления', null=True, auto_now_add=True)

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Все сотрудники'
        ordering = ('-id',)

    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)

    def save(self, *args, **kwargs):
        if self.pk is None or self.role is None:
            super(Staff, self).save(*args, **kwargs)
            if self.role == 'manager':
                Manager.objects.create(fk = self)
            elif self.role == 'maid':
                Maid.objects.create(fk = self)
            elif self.role == 'administrator':
                Administrator.objects.create(fk = self)
        else:
            super(Staff, self).save(*args, **kwargs)


class Feedback(models.Model):
    name = models.CharField('Имя', max_length=200)
    last_name = models.CharField('Фамилия', max_length=200, default='')
    email = models.EmailField('Электроная почта', max_length=200)
    phone = models.CharField('Телефонный номер', max_length=200)
    comment = models.TextField('Комментарий')
    status = models.CharField('Статус', max_length=1, choices=FEEDBACK_STATUS_CHOICES, default = 'N')
    date = models.DateTimeField('Дата отправки заявки', null=True, auto_now_add=True)
    is_replied = models.BooleanField('Ответили', default=False, blank=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Обратная связь'
        ordering = ('-id',)

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        ret = super().save(*args, **kwargs)
        feedbacks_request = Feedback.objects.filter(status='N').count() - 1
        async_to_sync(send_notification)(feedbacks_request)
        return ret


class FeedbackReply(models.Model):
    feedback = models.ForeignKey('webapp.Feedback', on_delete=models.CASCADE, related_name='replies',
                                 null=True, verbose_name='Отзыв')
    subject = models.CharField('Тема', max_length=200, default='')
    message = models.TextField('Ответ')
    attachment = models.FileField('Прикрепить файл', blank=True)

    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответить'

    def __str__(self):
        return '%s' % self.id

    def send_mail(self):
        to_email = self.feedback.email
        a = self.feedback
        a.is_replied = True
        a.save()
        from_email = EMAIL_HOST_USER
        connection = get_connection()
        self.subject = 'AIKOL: reply <%s>' % self.feedback.name
        mail = EmailMultiAlternatives(self.subject, self.message, from_email, [to_email], connection=connection)

        if self.attachment:
            mail.attach_file('uploads/' + str(self.attachment))
        ret = mail.send()

    def save(self, *args, **kwargs):
        feedback = self.feedback
        feedback.status = 'P'
        feedback.save()
        super(FeedbackReply, self).save(*args, **kwargs)
        self.send_mail()


class RoomView(models.Model):
    view = models.CharField('Вид', max_length=200, default='')

    class Meta:
        verbose_name = 'Вид'
        verbose_name_plural = 'Виды'

    def __str__(self):
        return self.view


class Floor(models.Model):
    floor = models.SmallIntegerField('Этаж')
    housing = models.ForeignKey('webapp.Housing', null=True, on_delete=models.CASCADE, related_name='floors', verbose_name='Корпус')
    roominess = models.ManyToManyField('webapp.Roominess', related_name='roominess_floor', verbose_name='Вместительность')

    class Meta:
        verbose_name = 'Этаж'
        verbose_name_plural = 'Этажи'

    def __str__(self):
        return "%s-%s" % (self.housing, self.floor)


class MealPrice(models.Model):
    breakfast = models.IntegerField('Завтрак', null=True)
    lunch = models.IntegerField('Обед', null=True)
    dinner = models.IntegerField('Ужин', null=True)

    class Meta:
        verbose_name = 'Цены за питание'
        verbose_name_plural = 'Цены за питание'

    def __str__(self):
        return "Завтрак: %s, обед: %s, ужин: %s" % (self.breakfast, self.lunch, self.dinner)


class Restriction(models.Model):
    text = models.CharField('Текст', max_length=100)
    image = models.FileField(upload_to='restrictions_images/', null=True, blank=True, verbose_name='Иконка')

    class Meta:
        verbose_name = 'Запрещено'
        verbose_name_plural = 'Запрещено'

    def image_tag(self):
        return mark_safe('<img src="/uploads/%s" style="max-width:200px;"/>' % (self.image))

    image_tag.short_description = 'Иконка'
    image_tag.allow_tags = True

    def __str__(self):
        return self.text


class Landing(models.Model):
    main_page = models.ForeignKey('webapp.MainPage', null=True, on_delete=models.CASCADE, related_name='landing', verbose_name='Главная')
    roominess = models.ManyToManyField('webapp.Roominess', related_name='landing_roominess', verbose_name='Типы номеров')
    about = models.ForeignKey('webapp.AboutUs', null=True, on_delete=models.CASCADE, related_name='landing', verbose_name='О нас')
    about_numbers = models.ManyToManyField('webapp.AboutUsNumbers', related_name='landing_numbers', verbose_name='В цифрах')
    service = models.ManyToManyField('webapp.Service', related_name='landing_service', verbose_name='Сервис')
    galleries = models.ManyToManyField('webapp.GalleryCategory', related_name='landing_galleries', verbose_name='Галерея')
    contact = models.ForeignKey('webapp.Contacts',  null=True, on_delete=models.CASCADE, related_name='landing', verbose_name='Контакты')
    social = models.ManyToManyField('webapp.SocialNetwork', related_name='landing_social', verbose_name='Социальные сети')
    longitude = models.CharField('Долгота', max_length=50, default='')
    latitude = models.CharField('Широта', max_length=50, default='')
    date_created = models.DateField('Дата', null=True, auto_now_add=True)

    class Meta:
        verbose_name = 'Главная страница'
        verbose_name_plural = 'Главная страница'

    def __str__(self):
        return 'Главная страница'
