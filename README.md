# 🛡️ PaladinsGuru Match Analyzer
<img width="909" height="995" alt="{FDA04353-81BD-4985-BC71-82C89006B66E}" src="https://github.com/user-attachments/assets/a235083b-ade7-48bc-89c3-f6b0c8469166" />
<img width="567" height="181" alt="{0F8B1E67-E09B-4960-A646-048BA12997FF}" src="https://github.com/user-attachments/assets/24d3dc76-862d-4389-968e-ddd8fa54b257" />


[
[](https://opensource.org/hields.io/img.shields.ioalizador de estadísticas profundas para Paladins Champions of the Realm**  
> Extrae y analiza datos de partidas desde PaladinsGuru, identifica compañeros problemáticos/exitosos, genera reportes detallados por campeón y mapa con exportación CSV y base SQLite.

## ⚠️ Proyecto en Fase Beta

**Este proyecto se encuentra actualmente en desarrollo beta**. Aunque es completamente funcional, pueden existir bugs menores o cambios en futuras versiones. ¡Tu feedback es muy valioso para mejorarlo!

## 🔒 Descargo de Responsabilidad

**PaladinsGuru (paladins.guru) NO me pertenece ni estoy afiliado con esta plataforma.** Este script utiliza web scraping para extraer datos públicamente disponibles en su sitio web con fines de análisis personal. El proyecto respeta los términos de uso y implementa delays apropiados para no sobrecargar sus servidores.

- 🌐 **PaladinsGuru**: Plataforma de estadísticas de terceros para Paladins
- 🎮 **Paladins**: Desarrollado por Hi-Rez Studios
- 🛠️ **Este proyecto**: Herramienta independiente de análisis de datos

## ✨ Características Principales

### 🔍 **Análisis Completo de Partidas**
- Extracción automática de historial completo de partidas
- Procesamiento de hasta 300 páginas de historial por jugador
- Análisis detallado de estadísticas K/D/A, daño, curación, créditos

### 👥 **Inteligencia de Compañeros de Equipo**
- **Detección de aliados exitosos**: Identifica con quién tienes mejor winrate
- **Alerta de jugadores problemáticos**: Detecta compañeros con historial de derrotas
- **Análisis estadístico**: Separa compañeros frecuentes vs ocasionales
- **Score de relevancia**: Combina winrate con frecuencia de juego

### 🛡️ **Estadísticas Detalladas**
- **Por campeón**: Rendimiento específico con cada personaje
- **Por mapa**: Análisis de efectividad en diferentes mapas
- **Tendencias temporales**: Seguimiento de progreso a lo largo del tiempo
- **Métricas avanzadas**: KDA, CPM, daño promedio, curación

### 📊 **Exportación Múltiple**
- **CSV detallados**: Para análisis en Excel, Google Sheets
- **Base SQLite**: Para consultas SQL avanzadas
- **Resúmenes coloridos**: Información instantánea en consola
- **Timestamps únicos**: Organización automática de reportes

## 🖥️ Instalación Completa por Sistema Operativo

### 🪟 **Windows 10/11**

#### **Método 1: Instalación Automática (Recomendado)**
```batch
# 1. Descargar e instalar Python desde python.org
# Asegúrate de marcar "Add Python to PATH" durante la instalación

# 2. Abrir PowerShell como administrador
Win + X → "Windows PowerShell (Admin)"

# 3. Verificar instalación de Python
python --version
# Debe mostrar: Python 3.8.x o superior

# 4. Clonar el repositorio
git clone https://github.com/tu-usuario/PaladinsGuru-Match-Analyzer.git
cd PaladinsGuru-Match-Analyzer

# 5. Instalar dependencias
pip install -r requirements.txt

# 6. Ejecutar primer análisis
python paladins_analyzer_standalone.py --url "https://paladins.guru/profile/725628302-katrella" --pages 10
```

#### **Método 2: Instalación Manual (Si no tienes Git)**
1. **Descargar Python**: Ve a [python.org](https://python.org) y descarga Python 3.8+
2. **Descargar proyecto**: Haz clic en "Code" → "Download ZIP" en GitHub
3. **Extraer**: Descomprime en `C:\PaladinsAnalyzer\`
4. **Abrir CMD**: `Win + R` → escribir `cmd` → Enter
5. **Navegar**: `cd C:\PaladinsAnalyzer\`
6. **Instalar**: `pip install -r requirements.txt`

### 🐧 **Linux (Ubuntu/Debian)**

```bash
# 1. Actualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar Python y Git
sudo apt install python3 python3-pip git -y

# 3. Verificar versión de Python
python3 --version
# Debe mostrar: Python 3.8.x o superior

# 4. Clonar repositorio
git clone https://github.com/tu-usuario/PaladinsGuru-Match-Analyzer.git
cd PaladinsGuru-Match-Analyzer

# 5. Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate

# 6. Instalar dependencias
pip install -r requirements.txt

# 7. Ejecutar análisis de prueba
python3 paladins_analyzer_standalone.py --url "https://paladins.guru/profile/725628302-katrella" --pages 10
```

### 🐧 **Linux (CentOS/RHEL/Fedora)**

```bash
# Para CentOS/RHEL
sudo yum install python3 python3-pip git -y

# Para Fedora
sudo dnf install python3 python3-pip git -y

# Continúa con los pasos 4-7 del apartado Ubuntu/Debian
```

### 🍎 **macOS**

```bash
# 1. Instalar Homebrew (si no lo tienes)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Instalar Python y Git
brew install python3 git

# 3. Verificar instalación
python3 --version

# 4. Clonar y configurar proyecto
git clone https://github.com/tu-usuario/PaladinsGuru-Match-Analyzer.git
cd PaladinsGuru-Match-Analyzer

# 5. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 6. Instalar dependencias
pip install -r requirements.txt

# 7. Prueba inicial
python3 paladins_analyzer_standalone.py --url "https://paladins.guru/profile/725628302-katrella" --pages 10
```

## 🚀 Guía de Uso Detallada

### 📖 **Uso Básico**

#### **Analizar cualquier jugador:**
```bash
python paladins_analyzer_standalone.py --url "https://paladins.guru/profile/PLAYER_ID-NOMBRE"
```

#### **Ejemplos con jugadores reales:**
```bash
# Análisis rápido (50 páginas)
python paladins_analyzer_standalone.py --url "https://paladins.guru/profile/725628302-katrella" --pages 50

# Análisis completo (300 páginas por defecto)
python paladins_analyzer_standalone.py --url "https://paladins.guru/profile/725628302-katrella"

# Análisis ultra-rápido para pruebas
python paladins_analyzer_standalone.py --url "https://paladins.guru/profile/725628302-katrella" --pages 10
```

### 🎛️ **Opciones de Línea de Comandos**

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| `--url` | **[REQUERIDO]** URL del perfil de PaladinsGuru | `--url "https://paladins.guru/profile/123-player"` |
| `--pages` | **[OPCIONAL]** Páginas de historial a analizar | `--pages 100` |

### 📁 **Cómo Obtener la URL del Perfil**

1. **Ve a PaladinsGuru**: Abre [paladins.guru](https://paladins.guru)
2. **Busca el jugador**: Usa la barra de búsqueda
3. **Abre el perfil**: Haz clic en el nombre del jugador
4. **Copia la URL**: Debe verse como: `https://paladins.guru/profile/123456789-PlayerName`

## 📊 Resultados Generados

### ✅ **Archivos CSV Exportados**

Cada ejecución genera archivos únicos con timestamp:

```
estadisticas_detalladas_JUGADOR_20250720_191200.csv
├── Datos completos de todas las partidas analizadas
├── Información de cada jugador en cada partida
└── Métricas: K/D/A, daño, curación, créditos, mapa, fecha

relaciones_JUGADOR_20250720_191200.csv  
├── Análisis de compañeros de equipo
├── Winrate con cada compañero
└── Frecuencia de juego conjunto

estadisticas_campeon_JUGADOR_20250720_191200.csv
├── Rendimiento específico por campeón
├── Promedios de K/D/A por personaje
└── Winrate con cada campeón

estadisticas_mapa_JUGADOR_20250720_191200.csv
├── Efectividad en diferentes mapas
├── Rendimiento promedio por ubicación  
└── Mapas más/menos exitosos
```

### ✅ **Base de Datos SQLite**

Archivo: `paladins_analisis.sqlite`

**Tablas creadas:**
- `Partidas`: Información básica de cada partida
- `EstadisticasJugadorPartida`: Métricas detalladas por jugador/partida

**Consultas SQL de ejemplo:**
```sql
-- Top 10 compañeros por winrate
SELECT PlayerName, COUNT(*) as Partidas, 
       AVG(WonMatch) as Winrate
FROM EstadisticasJugadorPartida 
WHERE MatchID IN (SELECT MatchID FROM...)
GROUP BY PlayerName 
ORDER BY Winrate DESC LIMIT 10;
```

### ✅ **Resúmenes en Consola**

**Ejemplo de salida:**
```
=== COMPAÑEROS MÁS FRECUENTES (2+ partidas) PARA KATRELLA ===
                          TotalGames  Wins  Losses  WinRate
TeammateID TeammateName                                    
725628301  FoxsSlumber            22    20       2     90.9
534829475  ProPlayer              15    12       3     80.0
193847562  GoodSupport            12    10       2     83.3

=== ESTADÍSTICAS POR CAMPEÓN PARA KATRELLA ===
           TotalGames  Wins  WinRate  AvgKills  AvgDeaths  AvgAssists
Champion                                                              
Androxus         45    32     71.1      18.2       12.4       3.8
Cassie           38    25     65.8      16.7       11.2       4.2
Kinessa          23    17     73.9      21.3        9.8       2.1

=== RESUMEN GLOBAL PARA KATRELLA ===
Total de partidas analizadas: 156
Victorias: 98 | Derrotas: 58
Winrate: 62.8%
Promedios:
  K/D/A: 17.2/11.4/4.1
  KDA Ratio: 1.88
  Daño: 89,234
  Curación: 12,456
```

## ⚙️ Configuración Avanzada

### 📝 **config.json - Personalización Completa**

```json
{
    "configuracion_general": {
        "retraso_entre_peticiones_seg": 0.5,        // Delay entre requests
        "max_paginas_historial_a_escanear": 300,    // Páginas por defecto
        "top_n_relaciones_a_mostrar": 24,           // Compañeros a mostrar
        "analizar_estadisticas_por_campeon": true,  // Análisis por campeón
        "analizar_estadisticas_por_mapa": true,     // Análisis por mapa
        "extraer_fecha_partida": true,              // Incluir timestamps
        "extraer_mapa_partida": true                // Incluir nombres de mapas
    },
    "configuracion_cache": {
        "habilitar_cache_partidas": false,          // Cache HTML (beta)
        "directorio_cache": "cache_partidas",       // Carpeta de cache
        "forzar_reanalisis_partidas_cacheadas": false
    },
    "opciones_de_salida": {
        "generar_csv_estadisticas_detalladas": true,    // CSV principal
        "generar_csv_relaciones": true,                  // CSV de compañeros
        "generar_csv_estadisticas_campeon": true,       // CSV por campeón
        "generar_csv_estadisticas_mapa": true,          // CSV por mapa
        "mostrar_resumen_consola_relaciones": true,     // Consola colorida
        "mostrar_resumen_consola_stats_campeon": true,  // Stats por campeón
        "mostrar_resumen_consola_stats_mapa": true,     // Stats por mapa  
        "mostrar_resumen_consola_stats_globales": true  // Resumen general
    },
    "base_de_datos_sqlite": {
        "habilitar_sqlite": true,                   // Base de datos
        "nombre_archivo_db": "paladins_analisis.sqlite"
    },
    "depuracion_y_logging": {
        "nivel_de_log": "INFO",                     // Verbosidad
        "mostrar_prints_depuracion_curacion": false // Debug avanzado
    }
}
```

### 🎛️ **Parámetros de Rendimiento**

| Configuración | Rápido | Balanceado | Completo |
|---------------|--------|------------|----------|
| `retraso_entre_peticiones_seg` | 0.3 | 0.5 | 1.0 |
| `max_paginas_historial_a_escanear` | 50 | 150 | 300 |
| `habilitar_cache_partidas` | false | false | true |

**⚡ Configuración rápida**: Para análisis preliminares  
**⚖️ Configuración balanceada**: Para uso general (recomendado)  
**🔍 Configuración completa**: Para análisis exhaustivos

## 🎮 Casos de Uso Específicos

### 🏆 **Para Jugadores Competitivos**
```bash
# Análisis completo antes de ranked
python paladins_analyzer_standalone.py --url "TU_PERFIL" --pages 200

# Revisión rápida de últimas partidas
python paladins_analyzer_standalone.py --url "TU_PERFIL" --pages 25
```

**Beneficios:**
- Identifica compañeros que mejoran tu winrate
- Descubre tus campeones más efectivos
- Analiza mapas donde tienes mejor rendimiento

### 📈 **Para Análisis de Datos**
```bash
# Generar datasets completos
python paladins_analyzer_standalone.py --url "PERFIL_PROFESIONAL" --pages 300
```

**Aplicaciones:**
- Análisis estadístico en R/Python
- Machine learning sobre patrones de juego
- Investigación sobre meta de Paladins

### 🕵️ **Para Detección de Toxicidad**
```bash
# Análisis de jugadores sospechosos
python paladins_analyzer_standalone.py --url "PERFIL_DUDOSO" --pages 100
```

**Detecta:**
- Jugadores con patrones de abandono
- Compañeros que consistentemente causan derrotas
- Comportamientos estadísticamente anómalos

## 🛠️ Solución de Problemas

### ❌ **Errores Comunes y Soluciones**

#### **Error: "No such file or directory"**
```bash
# Verifica que estés en el directorio correcto
pwd                  # Linux/macOS
cd                   # Windows

# Navega al directorio del proyecto
cd PaladinsGuru-Match-Analyzer
```

#### **Error: "Module not found"**
```bash
# Reinstalar dependencias
pip install -r requirements.txt --upgrade

# Verificar instalación
pip list | grep requests
pip list | grep pandas
```

#### **Error: "Invalid URL format"**
**Formato correcto de URL:**
✅ `https://paladins.guru/profile/123456789-PlayerName`
❌ `paladins.guru/profile/PlayerName`
❌ `https://paladins.guru/profile/PlayerName` (sin ID)

#### **Error: HTTP 429 (Too Many Requests)**
- **Solución**: Aumenta el `retraso_entre_peticiones_seg` en `config.json`
- **Recomendado**: Cambia de `0.3` a `1.0` segundos

#### **Error: No se encuentran partidas**
- **Verifica**: Que el perfil sea público
- **Alternativa**: Prueba con otro perfil conocido primero
- **Posible causa**: Perfil muy nuevo o sin partidas recientes

### 🐛 **Debugging Avanzado**

#### **Habilitar logs detallados:**
En `config.json`:
```json
"depuracion_y_logging": {
    "nivel_de_log": "DEBUG",
    "mostrar_prints_depuracion_curacion": true
}
```

#### **Verificar conectividad:**
```bash
# Probar conexión a PaladinsGuru
curl -I https://paladins.guru

# En Windows PowerShell:
Test-NetConnection paladins.guru -Port 443
```

## 📋 Requisitos Detallados del Sistema

### 💻 **Requisitos Mínimos**
- **SO**: Windows 7+, Linux (kernel 3.2+), macOS 10.12+
- **Python**: 3.8 o superior
- **RAM**: 512 MB disponibles
- **Almacenamiento**: 50 MB para el programa + espacio para datos
- **Red**: Conexión estable a Internet (para scraping)

### 🚀 **Requisitos Recomendados**
- **SO**: Windows 10+, Ubuntu 18.04+, macOS 11+
- **Python**: 3.10 o 3.11 (mejor rendimiento)
- **RAM**: 2 GB disponibles (análisis de 300+ páginas)
- **Almacenamiento**: 500 MB (para cache y múltiples análisis)
- **Red**: Banda ancha (análisis más rápido)

### 📦 **Dependencias de Python**
```
requests>=2.31.0      # Cliente HTTP robusto
beautifulsoup4>=4.11.2 # Parser HTML eficiente  
pandas>=2.0.3         # Análisis de datos
colorama>=0.4.6       # Colores en consola multiplataforma
```

## 🤝 Contribuir al Proyecto

### 💡 **Formas de Contribuir**
- 🐛 **Reportar bugs** via GitHub Issues
- 💡 **Sugerir características** nuevas
- 📝 **Mejorar documentación**
- 🔧 **Contribuir código** via Pull Requests
- 🌟 **Dar una estrella** al repositorio

### 🔧 **Proceso de Contribución**
1. **Fork** el repositorio
2. **Clona** tu fork: `git clone https://github.com/TU_USUARIO/PaladinsGuru-Match-Analyzer.git`
3. **Crea una rama**: `git checkout -b feature/nueva-caracteristica`
4. **Realiza cambios** y commitea: `git commit -am 'Añade nueva característica'`
5. **Push** a tu fork: `git push origin feature/nueva-caracteristica`
6. **Abre un Pull Request** con descripción detallada

### 🎯 **Ideas para Contribuir**
- **Gráficos visuales**: Integración con matplotlib/seaborn
- **Interfaz web**: Dashboard con Flask/Django
- **API oficial**: Integración con Hi-Rez API
- **Más estadísticas**: Loadouts, items, builds populares
- **Notificaciones**: Alertas cuando compañeros tóxicos están online
- **Comparación**: Herramientas para comparar múltiples jugadores

## 🚨 Limitaciones y Consideraciones

### ⚠️ **Limitaciones Técnicas**
- **Dependencia externa**: Requiere que PaladinsGuru esté disponible
- **Cambios de estructura**: Updates del sitio pueden requerir actualizaciones
- **Rate limiting**: Velocidad limitada para respetar servidores
- **Datos históricos**: Solo partidas disponibles públicamente

### 🔒 **Consideraciones Éticas**
- **Respeto al servidor**: Implementa delays apropiados
- **Datos públicos únicamente**: No accede a información privada
- **Uso personal/educativo**: No para fines comerciales sin permiso
- **Fair play**: Herramienta para mejorar, no para hacer trampas

### 📈 **Estado del Proyecto (Beta)**
- ✅ **Funcionalidad core**: Completamente operativa
- ⚠️ **Características avanzadas**: En desarrollo
- 🔄 **Updates frecuentes**: Se añaden mejoras regularmente
- 🐛 **Bug fixes**: Correcciones rápidas para problemas reportados

## 📝 Changelog Detallado

### **v1.0.0-beta (2025-07-20)**
#### ✅ **Características Implementadas:**
- 🎯 Scraping completo de perfiles PaladinsGuru
- 👥 Análisis inteligente de relaciones entre jugadores
- 🛡️ Estadísticas detalladas por campeón y mapa
- 📊 Exportación múltiple (CSV + SQLite)
- 🎨 Interfaz colorida con resúmenes detallados
- ⚙️ Sistema de configuración flexible
- 🔍 Score de relevancia estadística
- 🚨 Detección de compañeros problemáticos

#### 🔧 **Mejoras Técnicas:**
- Manejo robusto de errores HTTP
- Parsing resiliente de HTML
- Cache inteligente (opcional)
- Logging configurable
- Reintentos automáticos

#### 📋 **Próximas Características (Roadmap):**
- 📈 Gráficos de tendencias temporales
- 🌐 API REST para integraciones
- 📱 Versión web responsive
- 🤖 Integración con Discord bots
- 🎮 Soporte para API oficial de Hi-Rez

## 📄 Licencia y Uso Legal

Este proyecto está licenciado bajo la **MIT License**, lo que significa:

### ✅ **Permisos:**
- ✅ Uso comercial
- ✅ Modificación del código
- ✅ Distribución
- ✅ Uso privado

### ❗ **Condiciones:**
- ❗ Incluir aviso de copyright y licencia
- ❗ Proporcionar copia de la licencia MIT

### 🚫 **Limitaciones:**
- 🚫 Sin garantía o responsabilidad por daños
- 🚫 Sin soporte oficial garantizado

**Texto completo en**: [LICENSE](LICENSE)

## 🙏 Reconocimientos Especiales

### 🌟 **Plataformas y Servicios**
- **[PaladinsGuru](https://paladins.guru)**: Por proporcionar estadísticas detalladas y públicas
- **[Hi-Rez Studios](https://www.hirezstudios.com/)**: Creadores de Paladins Champions of the Realm
- **[GitHub](https://github.com)**: Plataforma de desarrollo colaborativo

### 🐍 **Ecosystem Python**
- **[Requests](https://docs.python-requests.org/)**: Cliente HTTP elegante
- **[Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)**: Parser HTML potente
- **[Pandas](https://pandas.pydata.org/)**: Análisis de datos profesional
- **[Colorama](https://pypi.org/project/colorama/)**: Colores multiplataforma

### 🎮 **Comunidad Gaming**
- **Comunidad de Paladins**: Por el feedback y testing
- **Reddit r/Paladins**: Por las sugerencias de características
- **Streamers y creadores de contenido**: Por popularizar herramientas de análisis


### 🚨 **Reportar Bugs**
Al reportar un problema, incluye:
1. **Sistema operativo** y versión de Python
2. **Comando exacto** que causó el error
3. **Mensaje de error completo**
4. **URL del perfil** que estabas analizando
5. **Configuración** en config.json (si es relevante)

### 💡 **Solicitar Características**
Para nuevas características, describe:
1. **Qué problema resolvería**
2. **Cómo te imaginas que funcionaría**
3. **Casos de uso específicos**
4. **Prioridad** para ti como usuario

### 🌟 **Soporte al Proyecto**
Si el proyecto te ha sido útil:
- ⭐ **Dale una estrella** en GitHub
- 🔄 **Compártelo** con otros jugadores de Paladins
- 💝 **Contribuye** con código o documentación
- 🐛 **Reporta bugs** para mejorar la calidad


  🛡️ Desarrollado con ❤️ para la comunidad de Paladins
  ⭐ Si este proyecto te ha sido útil, considera darle una estrella ⭐
  Proyecto en Beta -  Actualizaciones frecuentes -  Contribuciones bienvenidas
