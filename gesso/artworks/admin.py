from datetime import timedelta

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import action, display

from gesso.artworks.forms import ArtworkAdminForm, HomePageForm
from gesso.artworks.image_manager import PENDING, ImageManager
from gesso.artworks.models import Artwork, ArtworkImage, ArtworkStatus
from gesso.commerce.forms import SaleForm
from gesso.commerce.services import record_sale


class ArtworkImages(ImageManager):
    model = ArtworkImage
    fields = (('alt', 'Alt text'), ('caption', 'Caption'), ('is_process', 'Studio / process photo'))
    name = 'artworks_artworkimage'
    prefix = '<str:key>/images/'

    def owner(self, key):
        if key == PENDING:
            return {'artwork': None}
        if not key.isdigit():
            raise Http404
        return {'artwork': get_object_or_404(Artwork, pk=key)}

    def allowed(self, request, key):
        if key == PENDING:
            return self.model_admin.has_add_permission(request)
        return super().allowed(request, key)

    def before_upload(self):
        for image in ArtworkImage.objects.filter(artwork=None, created_at__lt=timezone.now() - timedelta(days=1)):
            image.delete_files()
            image.delete()


@admin.register(Artwork)
class ArtworkAdmin(ModelAdmin):
    form = ArtworkAdminForm
    list_display = ('thumbnail', 'title', 'year', 'status_label', 'is_published', 'featured_order')
    list_display_links = ('thumbnail', 'title')
    list_filter = ('is_published', 'status')
    search_fields = ('title', 'medium')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('images_manager', 'home_page')
    actions_detail = ('record_sale',)
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'year', 'medium', 'height_cm', 'width_cm', 'framing', 'description')}),
        ('Images', {'fields': ('images_manager',)}),
        ('Sale', {'fields': ('status', 'price')}),
        ('On the site', {'fields': ('is_published', 'home_page')}),
    )

    def get_urls(self):
        home_page = path('home-page/', self.admin_site.admin_view(self.home_page_view), name='artworks_homepage')
        return [home_page, *ArtworkImages(self).urls(), *super().get_urls()]

    def home_page_view(self, request):
        if not self.has_change_permission(request):
            raise PermissionDenied
        form = HomePageForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, 'Home page saved.')
            return redirect('admin:artworks_homepage')
        photos = (
            ArtworkImage.objects.filter(is_process=True, artwork__is_published=True)
            .select_related('artwork')
            .order_by(F('home_position').asc(nulls_last=True), 'artwork__title', 'position')
        )
        selected = {int(pk) for pk in form['studio'].value() or []}
        context = {
            **self.admin_site.each_context(request),
            'title': 'Home page',
            'form': form,
            'photos': photos,
            'selected': selected,
        }
        return TemplateResponse(request, 'admin/artworks/home_page.html', context)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('images')

    def save_model(self, request, obj, form, change):
        if not obj.is_published:
            obj.featured_order = None
        super().save_model(request, obj, form, change)
        form.attach_pending_images(obj)

    def view_on_site(self, obj):
        return obj.get_absolute_url() if obj.is_published else None

    @display(description='')
    def images_manager(self, obj):
        return ArtworkImages(self).render(str(obj.pk) if obj and obj.pk else PENDING)

    @display(description='Home page')
    def home_page(self, obj):
        spot = obj.get_featured_order_display() if obj and obj.featured_order else 'Not featured'
        return format_html(
            '{} · <a href="{}" class="text-primary-600 underline">Choose on the Home page page</a>',
            spot,
            reverse('admin:artworks_homepage'),
        )

    @display(description='')
    def thumbnail(self, obj):
        if not obj.thumbnail_url:
            return ''
        return format_html('<img src="{}" alt="" style="height:48px;width:48px;object-fit:cover">', obj.thumbnail_url)

    @display(description='Status', ordering='status', label={'Available': 'success', 'Reserved': 'warning', 'Sold': 'info'})
    def status_label(self, obj):
        return obj.display_status

    def has_record_sale_permission(self, request, object_id=None):
        return object_id is not None and Artwork.objects.filter(pk=object_id).exclude(status=ArtworkStatus.SOLD).exists()

    @action(description='Record a sale', url_path='record-sale', icon='sell', permissions=['record_sale'])
    def record_sale(self, request, object_id):
        artwork = get_object_or_404(Artwork, pk=object_id)
        form = SaleForm(request.POST or None, price_pence=artwork.price_pence)
        if form.is_valid():
            data = form.cleaned_data
            order = record_sale(artwork, price_pence=int(data.pop('price') * 100), **data)
            self.message_user(request, f'{artwork} recorded as sold.')
            return redirect('admin:commerce_order_change', order.pk)
        context = {
            **self.admin_site.each_context(request),
            'title': f'Record a sale of {artwork}',
            'intro': 'For works sold at an exhibition or privately. The work is marked sold and the sale appears under Orders.',
            'form': form,
            'submit_label': 'Record sale',
            'back_url': reverse('admin:artworks_artwork_change', args=[object_id]),
        }
        return TemplateResponse(request, 'admin/action_form.html', context)
