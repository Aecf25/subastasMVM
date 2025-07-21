from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import user_list, login, register, profile, agregar_vehiculo_por_username , user_data_view, BidViewSet, realizar_apuesta, ver_participantes_subasta, cambiar_contraseña, enviar_codigo, verificar_codigo, evaluar_subasta, cancelar_subasta, confirmar_entrega_subasta, editar_subasta, actualizar_estado_conexion, agregarNoticia, borrar_noticia, obtenerNoticias, update_last_login, report_users_by_day, report_users_by_week, report_users_by_month
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'bids', BidViewSet, basename='bid')


urlpatterns = [
    path('users/', user_list, name='user-list'),
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('profile/', profile, name='profile'),
    path('vehiculos/', agregar_vehiculo_por_username),
    path('usuario/data/', user_data_view, name='user-data'),
    path('usuario/update_last_login/', update_last_login, name='update_last_login'),
    path('report/users/day/', report_users_by_day, name='report_users_by_day'),
    path('report/users/week/', report_users_by_week, name='report_users_by_week'),
    path('report/users/month/', report_users_by_month, name='report_users_by_month'),
    path('', include(router.urls)),
    path('subasta/apostar/', realizar_apuesta, name='apostar-subasta'),
    path('subasta/<int:subasta_id>/participantes/', ver_participantes_subasta, name='participantes-subasta'),
    path('enviar-codigo/', enviar_codigo),
    path('verificar-codigo/', verificar_codigo),
    path('cambiar-contrasena/', cambiar_contraseña),
    path('subasta/<int:subasta_id>/evaluar_subasta/', evaluar_subasta),
    path('subasta/<int:subasta_id>/cancelar_subasta/', cancelar_subasta),
    path('subasta/<int:subasta_id>/confirmar_entrega_subasta/', confirmar_entrega_subasta),
    path('subasta/<int:subasta_id>/editar/', editar_subasta, name='editar-subasta'),
    path('usuario/<int:userId>/conexion/', actualizar_estado_conexion, name='estado-conexion'),
    path('noticias/agregar/', agregarNoticia, name='agregar-noticia'),
    path('noticias/', obtenerNoticias, name='listar-noticias'),
    path('noticias/eliminar/<int:id>/', borrar_noticia, name='borrar-noticia'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
