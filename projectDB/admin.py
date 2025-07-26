from django.contrib import admin
from .models import Usuario, VehicleUser, BidParticipation, BidFormat, UserLoginRecord, FCMToken
from django.utils.html import format_html

try:
    admin.site.unregister(Usuario)
except admin.sites.NotRegistered:
    pass

class VehicleUserInline(admin.TabularInline):
    model = VehicleUser
    extra = 0
    readonly_fields = ('photoVehicle_thumbnail',)

    def photoVehicle_thumbnail(self, obj):
        if obj.photoVehicle:
            return format_html('<img src="{}" width="50" height="50" />', obj.photoVehicle.url)
        return "Sin imagen"

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    inlines = [VehicleUserInline]

class VehicleAdmin(admin.ModelAdmin):
    list_display = ('id', 'ownerName', 'typeCar', 'brandCar', 'vehicleId', 'photoVehicle_thumbnail')

    def photoVehicle_thumbnail(self, obj):
        if obj.photoVehicle:
            return format_html('<img src="{}" width="50" height="50" />', obj.photoVehicle.url)
        return "Sin imagen"

admin.site.register(VehicleUser, VehicleAdmin)

@admin.register(BidParticipation)
class BidParticipationAdmin(admin.ModelAdmin):
    list_display = ['subasta', 'usuario', 'cantidad', 'fecha', 'vehiculo_info']

@admin.register(BidFormat)
class BidFormatAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'price', 'timeLimit', 'winner', 'notificated', 'created', 'estado']

@admin.register(UserLoginRecord)
class UserLoginRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'date')
    list_filter = ('date',)
    search_fields = ('user__username',)

class FCMTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at')

admin.site.register(FCMToken, FCMTokenAdmin)