from datetime import datetime
import uuid
from sqlalchemy import Column, String, Enum, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Usuario(Base):
    __tablename__ = "usuarios"

    usuario_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = Column(String(120), nullable=False)
    correo = Column(String(160), unique=True, nullable=True)
    telefono = Column(String(30), unique=True, nullable=True)
    hash_contrasena = Column(String(255), nullable=False)
    zona_horaria = Column(String(64), nullable=False, default="America/Bogota")
    rol = Column(Enum("cliente", "admin", "personal", name="rol_enum"), nullable=False, default="cliente")
    estado = Column(Enum("activo", "inactivo", "bloqueado", name="estado_enum"), nullable=False, default="activo")
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"Usuario(usuario_id={self.usuario_id}, correo={self.correo}, rol={self.rol}, estado={self.estado})"
