from django.urls import path
from . import views

urlpatterns = [
    path('', views.escolher_nivel, name='escolher_nivel'),
    path('jogo/', views.jogar_turno, name='jogar_turno'),
    path("novo/", views.novo_jogo, name="novo_jogo"),
    path("instrucoes/", views.instrucoes, name="instrucoes"),
    path("cancelar-nivel/", views.cancelar_nivel, name="cancelar_nivel"),

]