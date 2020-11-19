# Generated by Django 2.2 on 2020-11-19 08:53

from django.db import migrations, models
import django.db.models.deletion
import image_cropping.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AboutUs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, null=True, upload_to='about_us_images/', verbose_name='Картинка')),
                ('cropping', image_cropping.fields.ImageRatioField('image', '1170x440', adapt_rotation=False, allow_fullsize=False, free_crop=False, help_text=None, hide_image_field=False, size_warning=False, verbose_name='cropping')),
                ('description', models.TextField(verbose_name='Краткое описание')),
                ('full_description', models.TextField(default='', verbose_name='Полное описание')),
            ],
            options={
                'verbose_name': 'О нас',
                'verbose_name_plural': 'О нас',
            },
        ),
        migrations.CreateModel(
            name='AboutUsNumbers',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.CharField(max_length=200, verbose_name='Цифры')),
                ('description', models.CharField(blank=True, max_length=200, null=True, verbose_name='Описание')),
            ],
            options={
                'verbose_name': 'В цифрах',
                'verbose_name_plural': 'В цифрах',
            },
        ),
        migrations.CreateModel(
            name='Contacts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=200, verbose_name='Адрес')),
                ('email', models.EmailField(max_length=200, unique=True, verbose_name='Email')),
                ('phone', models.CharField(blank=True, max_length=200, null=True, verbose_name='Телефон 1')),
                ('phone2', models.CharField(blank=True, max_length=200, null=True, verbose_name='Телефон 2')),
            ],
            options={
                'verbose_name': 'Контакт',
                'verbose_name_plural': 'Контакты',
            },
        ),
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Имя')),
                ('last_name', models.CharField(default='', max_length=200, verbose_name='Фамилия')),
                ('email', models.EmailField(max_length=200, verbose_name='Электроная почта')),
                ('phone', models.CharField(max_length=200, verbose_name='Телефонный номер')),
                ('comment', models.TextField(verbose_name='Комментарий')),
                ('status', models.CharField(choices=[('N', 'Не просмотрено'), ('P', 'Просмотрено')], default='N', max_length=1, verbose_name='Статус')),
                ('date', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Дата отправки заявки')),
                ('is_replied', models.BooleanField(blank=True, default=False, verbose_name='Ответили')),
            ],
            options={
                'verbose_name': 'Отзыв',
                'verbose_name_plural': 'Обратная связь',
                'ordering': ('-id',),
            },
        ),
        migrations.CreateModel(
            name='MainPage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('heading', models.CharField(default='', max_length=30, verbose_name='Заголовок')),
                ('background', models.ImageField(null=True, upload_to='main_page_images/', verbose_name='Изображение')),
                ('video', models.FileField(null=True, upload_to='video/', verbose_name='Видео')),
                ('cropping', image_cropping.fields.ImageRatioField('background', '1366x620', adapt_rotation=False, allow_fullsize=False, free_crop=False, help_text=None, hide_image_field=False, size_warning=False, verbose_name='cropping')),
                ('darkening', models.BooleanField(default=True, verbose_name='Сделать затемнение изображения')),
                ('show_video', models.BooleanField(default=True, verbose_name='Показывать видео')),
            ],
            options={
                'verbose_name': 'Главная страница',
                'verbose_name_plural': 'Главная страница',
            },
        ),
        migrations.CreateModel(
            name='MealPrice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('breakfast', models.IntegerField(null=True, verbose_name='Завтрак')),
                ('lunch', models.IntegerField(null=True, verbose_name='Обед')),
                ('dinner', models.IntegerField(null=True, verbose_name='Ужин')),
            ],
            options={
                'verbose_name': 'Цены за питание',
                'verbose_name_plural': 'Цены за питание',
            },
        ),
        migrations.CreateModel(
            name='Restriction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=100, verbose_name='Текст')),
                ('image', models.FileField(blank=True, null=True, upload_to='restrictions_images/', verbose_name='Иконка')),
            ],
            options={
                'verbose_name': 'Запрещено',
                'verbose_name_plural': 'Запрещено',
            },
        ),
        migrations.CreateModel(
            name='RoomView',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('view', models.CharField(default='', max_length=200, verbose_name='Вид')),
            ],
            options={
                'verbose_name': 'Вид',
                'verbose_name_plural': 'Виды',
            },
        ),
        migrations.CreateModel(
            name='SocialNetwork',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=400, null=True, verbose_name='Заголовок')),
                ('link', models.CharField(blank=True, max_length=400, null=True, verbose_name='Ссылка')),
                ('icon', models.FileField(null=True, upload_to='social_images/', verbose_name='Иконка')),
            ],
            options={
                'verbose_name': 'Социальная сеть',
                'verbose_name_plural': 'Социальные сети',
            },
        ),
        migrations.CreateModel(
            name='Staff',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('administrator', 'Администратор'), ('manager', 'Менеджер'), ('maid', 'Горничная')], default='administrator', max_length=50, verbose_name='Должность')),
                ('last_name', models.CharField(max_length=50, verbose_name='Фамилия')),
                ('first_name', models.CharField(max_length=50, verbose_name='Имя')),
                ('middle_name', models.CharField(max_length=50, verbose_name='Отчество')),
                ('date_created', models.DateField(auto_now_add=True, null=True, verbose_name='Дата добавления')),
            ],
            options={
                'verbose_name': 'Сотрудник',
                'verbose_name_plural': 'Все сотрудники',
                'ordering': ('-id',),
            },
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('client_type', models.CharField(choices=[('individual', 'Физ. лицо'), ('entity', 'Организация')], default='individual', max_length=10, verbose_name='Тип клиента')),
                ('arrival_date', models.DateField(verbose_name='Дата заезда')),
                ('departure_date', models.DateField(verbose_name='Дата выезда')),
                ('count_calendar', models.PositiveSmallIntegerField(default=0, verbose_name='Количество людей с питанием')),
                ('count_of_people', models.PositiveSmallIntegerField(verbose_name='Общее кол-во людей')),
                ('name', models.CharField(max_length=100, verbose_name='Имя')),
                ('last_name', models.CharField(max_length=100, verbose_name='Фамилия')),
                ('phone', models.CharField(max_length=100, verbose_name='Номер телефона')),
                ('email', models.EmailField(max_length=200, verbose_name='Электроная почта')),
                ('comment', models.TextField(blank=True, default='', verbose_name='Комментарий')),
                ('payment_type', models.CharField(choices=[('offline', 'офис'), ('online', 'онлайн')], default='offline', max_length=50, verbose_name='Тип оплаты')),
                ('payment_status', models.CharField(choices=[('not paid', 'Не оплачено'), ('fully paid', 'Оплачено полностью'), ('partially paid', 'Оплачено частично')], default='not paid', max_length=50, verbose_name='Статус оплаты')),
                ('total_sum', models.PositiveIntegerField(default=0, verbose_name='Итоговая сумма')),
                ('discount', models.IntegerField(default=0, null=True, verbose_name='Скидка')),
                ('status', models.CharField(choices=[('active', 'Активный'), ('not paid', 'Клиент не внес оплату'), ('date changed', 'Клиент поменял дату'), ('other', 'Другая причина')], default='active', max_length=12, verbose_name='Статус')),
                ('payment_url', models.CharField(blank=True, max_length=1000, null=True, verbose_name='Ссылка на оплату')),
                ('room', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='webapp.Guestroom', verbose_name='Номер')),
            ],
            options={
                'verbose_name': 'Бронирование',
                'verbose_name_plural': 'Бронирования',
            },
        ),
        migrations.CreateModel(
            name='Phone',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(max_length=200, verbose_name='Телефон')),
                ('contacts', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='phones', to='webapp.Contacts', verbose_name='Контакты')),
            ],
            options={
                'verbose_name': 'Телефон',
                'verbose_name_plural': 'Телефоны',
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Дата')),
                ('name', models.CharField(max_length=256, verbose_name='ФИО')),
                ('total_sum', models.PositiveIntegerField(default=0, verbose_name='Итоговая сумма')),
                ('payment_type', models.CharField(choices=[('offline', 'офис'), ('online', 'онлайн')], default='offline', max_length=50, verbose_name='Способ оплаты')),
                ('status', models.CharField(choices=[('not paid', 'Не оплачено'), ('fully paid', 'Оплачено полностью'), ('partially paid', 'Оплачено частично')], default='not paid', max_length=50, verbose_name='Тип оплаты')),
                ('reservation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payment', to='webapp.Reservation', verbose_name='Бронь')),
            ],
            options={
                'verbose_name': 'Платеж',
                'verbose_name_plural': 'Платежи',
                'ordering': ('-id',),
            },
        ),
        migrations.CreateModel(
            name='Meal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Дата')),
                ('breakfast', models.BooleanField(default=True, verbose_name='Завтрак')),
                ('lunch', models.BooleanField(default=True, verbose_name='Обед')),
                ('dinner', models.BooleanField(default=True, verbose_name='Ужин')),
                ('reservation', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='meals', to='webapp.Reservation', verbose_name='Бронь номера')),
            ],
            options={
                'verbose_name': 'Питание',
                'verbose_name_plural': 'Питание',
            },
        ),
        migrations.CreateModel(
            name='Manager',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fk', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='managers', to='webapp.Staff', verbose_name='Сотрудник')),
            ],
            options={
                'verbose_name': 'Менеджер',
                'verbose_name_plural': 'Менеджеры',
            },
        ),
        migrations.CreateModel(
            name='Maid',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fk', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='maids', to='webapp.Staff', verbose_name='Сотрудник')),
            ],
            options={
                'verbose_name': 'Горничная',
                'verbose_name_plural': 'Горничные',
            },
        ),
        migrations.CreateModel(
            name='Landing',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('longitude', models.CharField(default='', max_length=50, verbose_name='Долгота')),
                ('latitude', models.CharField(default='', max_length=50, verbose_name='Широта')),
                ('date_created', models.DateField(auto_now_add=True, null=True, verbose_name='Дата')),
                ('about', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='landing', to='webapp.AboutUs', verbose_name='О нас')),
                ('about_numbers', models.ManyToManyField(related_name='landing_numbers', to='webapp.AboutUsNumbers', verbose_name='В цифрах')),
                ('contact', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='landing', to='webapp.Contacts', verbose_name='Контакты')),
                ('galleries', models.ManyToManyField(related_name='landing_galleries', to='webapp.GalleryCategory', verbose_name='Галерея')),
                ('main_page', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='landing', to='webapp.MainPage', verbose_name='Главная')),
                ('roominess', models.ManyToManyField(related_name='landing_roominess', to='webapp.Roominess', verbose_name='Типы номеров')),
                ('service', models.ManyToManyField(related_name='landing_service', to='webapp.Service', verbose_name='Сервис')),
                ('social', models.ManyToManyField(related_name='landing_social', to='webapp.SocialNetwork', verbose_name='Социальные сети')),
            ],
            options={
                'verbose_name': 'Главная страница',
                'verbose_name_plural': 'Главная страница',
            },
        ),
        migrations.CreateModel(
            name='Floor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('floor', models.SmallIntegerField(verbose_name='Этаж')),
                ('housing', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='floors', to='webapp.Housing', verbose_name='Корпус')),
                ('roominess', models.ManyToManyField(related_name='roominess_floor', to='webapp.Roominess', verbose_name='Вместительность')),
            ],
            options={
                'verbose_name': 'Этаж',
                'verbose_name_plural': 'Этажи',
            },
        ),
        migrations.CreateModel(
            name='FeedbackReply',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(default='', max_length=200, verbose_name='Тема')),
                ('message', models.TextField(verbose_name='Ответ')),
                ('attachment', models.FileField(blank=True, upload_to='', verbose_name='Прикрепить файл')),
                ('feedback', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='webapp.Feedback', verbose_name='Отзыв')),
            ],
            options={
                'verbose_name': 'Ответ',
                'verbose_name_plural': 'Ответить',
            },
        ),
        migrations.CreateModel(
            name='Cleaning',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('waiting', 'Ожидание'), ('in process', 'В процессе'), ('done', 'Завершен')], default='waiting', max_length=10, verbose_name='Статус')),
                ('date', models.DateField(verbose_name='Дата')),
                ('start_time', models.TimeField(verbose_name='Начало')),
                ('end_time', models.TimeField(blank=True, null=True, verbose_name='Конец')),
                ('floor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cleaning', to='webapp.Floor', verbose_name='Этаж')),
                ('housing', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cleaning', to='webapp.Housing', verbose_name='Корпус')),
                ('maids', models.ManyToManyField(related_name='cleaning', to='webapp.Maid', verbose_name='Горничная')),
                ('room', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cleaning', to='webapp.Guestroom', verbose_name='Номер')),
                ('room_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cleaning', to='webapp.TypeOfRoom', verbose_name='Тип номера')),
            ],
            options={
                'verbose_name': 'Уборка номера',
                'verbose_name_plural': 'Уборка номеров',
                'ordering': ('-id',),
            },
        ),
        migrations.CreateModel(
            name='Administrator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fk', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='admins', to='webapp.Staff', verbose_name='Сотрудник')),
            ],
            options={
                'verbose_name': 'Администратор',
                'verbose_name_plural': 'Администраторы',
            },
        ),
        migrations.AddField(
            model_name='guestroom',
            name='floor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rooms', to='webapp.Floor', verbose_name='Этаж'),
        ),
    ]
