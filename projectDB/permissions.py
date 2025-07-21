from rest_framework import permissions

class IsAdminOrUpdatePriceOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # Cualquier usuario autenticado puede ver subastas
        if request.method in permissions.SAFE_METHODS:
            return True
        # Solo admin/staff puede crear subastas
        if request.method == 'POST':
            return request.user and request.user.is_staff
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Permitir lectura (GET)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Solo staff o superuser puede hacer PUT o DELETE
        if request.method in ['PUT', 'DELETE']:
            return request.user and request.user.is_staff

        # PATCH: todos pueden, pero solo si modifican el campo 'price'
        if request.method == 'PATCH':
            if request.user and request.user.is_staff:
                return True  # Admin puede hacer PATCH completo

            # Para usuarios normales: validar que solo modifiquen 'price'
            allowed_fields = {'price', 'estado'}
            if set(request.data.keys()).issubset(allowed_fields):
                return True
            return False

        return False