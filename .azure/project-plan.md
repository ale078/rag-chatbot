# Plan del proyecto: RAG Chatbot

**Estado:** aprobado por el usuario el 2026-10-27  
**Fase inicial:** aplicación local; Azure queda para una fase futura

## Objetivo

Crear una aplicación web local para cargar documentos y conversar sobre su contenido. Si la recuperación no encuentra evidencia pertinente, la aplicación puede usar un LLM local como alternativa, indicando claramente que esa respuesta no está respaldada por los documentos. Las respuestas basadas en documentos deben incluir citas a las fuentes recuperadas.

## Usuarios y acceso

- MVP de uso local, sin inicio de sesión.
- El servicio debe escuchar sólo en localhost durante el desarrollo local.
- No se contempla uso multiusuario ni exposición pública en esta fase.

## Experiencia y alcance funcional

- Interfaz web de chat en español.
- Carga y administración de documentos PDF, DOCX, TXT y Markdown.
- Mostrar los documentos cargados y permitir eliminarlos.
- Dividir e indexar el texto al cargar cada documento.
- Responder preguntas con recuperación semántica y citas que identifiquen el archivo y, cuando esté disponible, la página.
- Cuando no haya fragmentos relevantes, consultar el LLM local sin atribuir la respuesta a los documentos e indicarlo visiblemente en la respuesta.
- Mostrar errores accionables cuando Ollama no esté disponible, falle una carga o un formato no sea compatible.
- El historial del chat será temporal en la sesión del navegador; no se requiere persistencia de conversaciones para el MVP.

## Arquitectura y tecnologías

- **Frontend:** React, TypeScript y Vite.
- **Backend:** Python con FastAPI.
- **LLM:** Ollama ejecutándose localmente; modelo configurable por variable de entorno, sin acoplar la aplicación a un modelo específico.
- **Embeddings:** modelo local servido por Ollama, configurable de forma independiente al modelo generativo.
- **Recuperación vectorial:** Chroma con persistencia local.
- **Archivos fuente:** sistema de archivos local, bajo un directorio de datos configurable que no se versiona.
- **Procesamiento:** extracción de texto para PDF, DOCX, TXT y Markdown; fragmentación con metadatos de documento y página cuando aplique.
- **Comunicación:** API HTTP local entre el frontend y FastAPI.
- No se requieren servicios Azure ni credenciales cloud para ejecutar el MVP.

## Flujos principales

1. El usuario inicia Ollama y la aplicación local.
2. Carga un documento compatible; la API valida el formato, lo guarda, extrae y fragmenta el texto y persiste sus embeddings en Chroma.
3. La interfaz muestra el documento y su estado de indexación.
4. El usuario envía una pregunta. La API busca fragmentos pertinentes en Chroma.
5. Si hay evidencia suficiente, el LLM responde con base en los fragmentos y la API devuelve sus citas. Si no la hay, el LLM local responde usando su conocimiento general y la interfaz advierte que no encontró respaldo en los documentos.
6. Al eliminar un documento, se eliminan sus archivos y fragmentos indexados.

## API inicial propuesta

- `GET /api/health`: estado de la API y disponibilidad de dependencias locales.
- `GET /api/documents`: listar documentos y su estado.
- `POST /api/documents`: cargar e indexar un documento.
- `DELETE /api/documents/{document_id}`: eliminar un documento y sus fragmentos.
- `POST /api/chat`: recibir una pregunta y devolver respuesta, tipo de respaldo y citas.

Los nombres y esquemas finales se pueden ajustar durante la implementación si el contrato sigue cubriendo estos flujos.

## Datos, privacidad y seguridad

- Los documentos, el índice Chroma y cualquier configuración local se almacenan en directorios de datos ignorados por Git.
- El contenido no se envía a proveedores de modelos en la nube.
- Validar extensiones y tamaño de carga; generar nombres internos seguros para evitar traversal y colisiones.
- No renderizar contenido de documentos como HTML confiable.
- Configurar CORS para el origen local del frontend y no exponer la API fuera de localhost en el modo local.
- No persistir historial de chat ni solicitar credenciales en el MVP.

## Configuración y ejecución

- Documentar prerrequisitos locales: Python, Node.js y Ollama, además de los modelos Ollama necesarios.
- Proveer archivos de ejemplo para variables de entorno sin secretos y comandos claros para instalar dependencias, iniciar API y frontend, y ejecutar pruebas.
- Hacer configurables las rutas de datos, el endpoint de Ollama y los identificadores de modelos.
- Informar claramente si falta un modelo o si Ollama no está iniciado; no simular respuestas exitosas.

## Pruebas y criterios de aceptación

- Pruebas unitarias de extracción, fragmentación, metadatos y validación de formatos.
- Pruebas de API para carga/listado/eliminación y chat, incluyendo errores de dependencias.
- Prueba de recuperación que compruebe que una respuesta respaldada incluye citas del documento correcto.
- Prueba de fallback sin evidencia que compruebe que la respuesta queda marcada como no respaldada y no inventa citas.
- Verificación manual del flujo de carga, conversación y eliminación en la interfaz.
- El proyecto debe poder iniciarse localmente siguiendo la documentación, sin Azure y sin claves de API externas.

## Fuera del alcance del MVP

- Despliegue en Azure, aprovisionamiento de infraestructura y costos cloud.
- Azure Blob Storage, Azure AI Search, autenticación, colaboración multiusuario y persistencia de conversaciones.
- OCR para documentos escaneados, crawling web, sincronización automática de fuentes y evaluación avanzada de calidad.

## Evolución futura a Azure

Mantener el almacenamiento de archivos y la recuperación detrás de componentes reemplazables, de manera que una fase posterior pueda migrar el almacenamiento local a Azure Blob Storage y Chroma a Azure AI Search. Esa migración requerirá un plan separado que confirme autenticación, cuotas, región, configuración de seguridad y presupuesto antes de aprovisionar recursos.
