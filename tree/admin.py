from django.contrib import admin
from django.utils.html import format_html
from .models import Person, Relationship, Invitation, FamilyProfile


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display  = ('full_name', 'birth_date', 'birth_place', 'occupation', 'is_deceased', 'photo_preview')
    list_filter   = ('gender', 'death_date')
    search_fields = ('first_name', 'last_name', 'birth_name', 'birth_place', 'occupation')
    readonly_fields = ('created_at', 'updated_at', 'photo_preview')
    fieldsets = (
        ('Name', {'fields': ('first_name', 'last_name', 'birth_name', 'gender')}),
        ('Geburt', {'fields': ('birth_date', 'birth_year_only', 'birth_place')}),
        ('Tod', {'fields': ('death_date', 'death_place'), 'classes': ('collapse',)}),
        ('Weiteres', {'fields': ('occupation', 'notes', 'photo', 'photo_preview')}),
        ('Account', {'fields': ('user',), 'classes': ('collapse',)}),
        ('Metadaten', {'fields': ('created_by', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="height:50px;border-radius:50%"/>', obj.photo.url)
        return '–'
    photo_preview.short_description = 'Vorschau'


@admin.register(Relationship)
class RelationshipAdmin(admin.ModelAdmin):
    list_display  = ('from_person', 'relation_type', 'to_person', 'note')
    list_filter   = ('relation_type',)
    search_fields = ('from_person__first_name', 'from_person__last_name',
                     'to_person__first_name', 'to_person__last_name')
    autocomplete_fields = ['from_person', 'to_person']


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display  = ('email', 'invited_by', 'created_at', 'expires_at', 'used', 'used_by')
    list_filter   = ('used',)
    readonly_fields = ('token', 'created_at', 'used_at', 'used_by')


@admin.register(FamilyProfile)
class FamilyProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter  = ('role',)


admin.site.site_header = 'FamilyTree Administration'
admin.site.site_title  = 'FamilyTree Admin'
admin.site.index_title = 'Familien-Stammbaum verwalten'
