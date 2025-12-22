def limpiar_respuesta(texto):
    """Limpia caracteres extraños y mantiene solo español/inglés."""
    import re
    
    # Eliminar caracteres no latinos (mantiene español/inglés)
    texto = re.sub(r'[^\x00-\x7FáéíóúÁÉÍÓÚñÑ¿¡üÜ\s\.\,\;\:\-\"\'\(\)\[\]\{\}]', '', texto)
    
    # Reemplazar secuencias específicas problemáticas
    sustituciones = {
        '入口': 'entrada',
        '出口': 'salida',
        '情感': 'emocional',
        '沟通': 'comunicación',
        '营养': 'nutrición'
    }
    
    for chino, espanol in sustituciones.items():
        texto = texto.replace(chino, espanol)
    
    return texto.strip()
