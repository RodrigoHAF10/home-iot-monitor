from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 1. Área administrativa padrão
    path('admin/', admin.site.urls),
    
    # 2. O Home Page do aplicativo monitor_app no caminho raiz (/)
    # Isso permite que você acesse a página inicial em http://127.0.0.1:8000/
    path('', include('monitor_app.urls')),
    
    # 3. O aplicativo monitor_app também em /monitor/ (mantendo o que você já tinha)
    path('monitor/', include('monitor_app.urls')),
    
    # 4. (Opcional) Se você precisa que /home/ funcione
    path('home/', include('monitor_app.urls')),
]