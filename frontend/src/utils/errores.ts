const GENERICOS: Record<string, string> = {
  'bad gateway': 'El servidor no responde. Revisa que el backend esté corriendo en el puerto 8000.',
  'service unavailable': 'El servidor no está disponible en este momento. Intenta de nuevo en unos segundos.',
  'gateway timeout': 'El servidor tardó demasiado en responder. Intenta de nuevo.',
  'internal server error': 'Ocurrió un error en el servidor. Intenta de nuevo o revisa los logs del backend.',
  'failed to fetch': 'No hay conexión con el servidor. Revisa tu red o que el backend esté corriendo.',
  'error de red': 'No hay conexión con el servidor. Revisa tu red o que el backend esté corriendo.',
  'not found': 'No se encontró lo que buscabas.',
}

/** Traduce los errores técnicos (HTTP o de red) a un mensaje claro. Los mensajes del backend se dejan tal cual. */
export function mensajeAmigable(e: unknown, respaldo = 'No se pudo completar la acción.'): string {
  const texto = e instanceof Error ? e.message : typeof e === 'string' ? e : ''
  if (!texto) return respaldo
  return GENERICOS[texto.trim().toLowerCase()] ?? texto
}
