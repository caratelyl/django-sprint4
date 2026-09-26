from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count
from django.utils import timezone

from constants import FIELD_MAX_LENGTH, COMMENT_STR_MAX_LENGTH


User = get_user_model()


class PostQuerySet(models.QuerySet):
    def with_related(self):
        return self.select_related('author', 'category', 'location')

    def published(self):
        return self.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
        )

    def with_comment_count(self):
        return self.annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')


class PublishedModel(models.Model):
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.',
    )
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        abstract = True


class TitleModel(models.Model):
    """Абстрактная модель для добавления поля title и метода __str__."""
    
    title = models.CharField(
        max_length=FIELD_MAX_LENGTH,
        verbose_name='Заголовок',
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.title


class Category(PublishedModel, TitleModel):
    description = models.TextField(verbose_name='Описание')
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        help_text=(
            'Идентификатор страницы для URL; разрешены символы латиницы, '
            'цифры, дефис и подчёркивание.'
        ),
    )

    class Meta(PublishedModel.Meta):
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'
        ordering = ('title',)


class Location(PublishedModel):
    name = models.CharField(
        max_length=FIELD_MAX_LENGTH,
        verbose_name='Название места'
    )

    class Meta(PublishedModel.Meta):
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Post(PublishedModel, TitleModel):
    objects = PostQuerySet.as_manager()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
        related_name='posts',
    )
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем — '
            'можно делать отложенные публикации.'
        ),
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Местоположение',
        related_name='posts',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория',
        related_name='posts',
    )
    image = models.ImageField(
        'Изображение',
        upload_to='post_images/',
        blank=True,
    )

    class Meta(PublishedModel.Meta):
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('pub_date',)


class Comment(models.Model):
    text = models.TextField('Текст комментария')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Публикация',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария',
    )
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('created_at',)

    def __str__(self):
        return self.text[:COMMENT_STR_MAX_LENGTH]
