class ErrorNegocio(Exception):
    """Error esperado de una regla de negocio; se traduce a una respuesta JSON con su código HTTP."""

    def __init__(self, mensaje, status=400, *, extra=None, clave="mensaje", cerrar_sesion=False):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status = status
        self.extra = extra or {}
        self.clave = clave
        self.cerrar_sesion = cerrar_sesion

    def cuerpo(self):
        if self.clave == "error":
            return {"error": self.mensaje}
        return {"ok": False, "mensaje": self.mensaje, **self.extra}
