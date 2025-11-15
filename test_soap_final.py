from zeep import Client

print("=" * 60)
print("🧪 PRUEBA FINAL DE SOAP - Reserva-Canchas")
print("=" * 60)

# Test Auth Service
print("\n1️⃣ Probando Auth Service...")
try:
    client = Client('http://localhost:8000/soap/auth')
    
    print("   ✅ WSDL cargado correctamente")
    print("   📋 Operaciones disponibles:", [op for op in dir(client.service) if not op.startswith('_')])
    
    # Llamar al servicio
    print("\n   🔐 Probando Login...")
    response = client.service.Login(Username='testuser', Password='test123')
    
    print(f"   ✅ ¡LOGIN EXITOSO!")
    print(f"      Token: {response.Token[:40]}...")
    print(f"      Success: {response.Success}")
    print(f"      Message: {response.Message}")
    print(f"      Expires: {response.ExpiresAt}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test Booking Service  
print("\n2️⃣ Probando Booking Service...")
try:
    client = Client('http://localhost:8000/soap/booking')
    print("   ✅ WSDL cargado correctamente")
    
    response = client.service.ConsultarDisponibilidad(
        idSede=1,
        idCancha=2,
        fecha='2025-11-15'
    )
    
    print(f"   ✅ ¡CONSULTA EXITOSA!")
    print(f"      Mensaje: {response.mensaje}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test Billing Service
print("\n3️⃣ Probando Billing Service...")
try:
    client = Client('http://localhost:8000/soap/billing')
    print("   ✅ WSDL cargado correctamente")
    print("   📋 Servicio billing disponible")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("🎉 ¡PRUEBAS COMPLETADAS!")
print("=" * 60)
print("\n💡 Próximos pasos:")
print("   - Integrar con tus services existentes")
print("   - Agregar más operaciones SOAP")
print("   - Crear tests con pytest")