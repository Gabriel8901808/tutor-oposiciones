# Práctica de Vistas Diédricas (Sistema Europeo · UPCT)

Aplicación web interactiva de un solo archivo para practicar la obtención de
**Alzado, Planta y Perfil izquierdo** en el **sistema europeo (1er diedro)**,
con piezas mecánicas generadas por niveles (Fácil / Medio / Difícil).

## Cómo ejecutarla

No necesita instalación, servidor **ni conexión a Internet**. Es un único
archivo HTML autocontenido (CSS propio y motor 3D propio en `<canvas>`, sin
Three.js ni Tailwind ni ningún CDN). Basta con abrirlo:

```bash
# desde esta carpeta
xdg-open index.html      # Linux
# o   open index.html    # macOS
# o haz doble clic en index.html
```

> Funciona también a través de visores como htmlpreview, precisamente por no
> depender de scripts externos.

## Qué incluye

### 1. Generador de piezas 3D
- Piezas no triviales por catálogo de niveles: **planos inclinados (rampas),
  vaciados (soporte en U), taladros pasantes, entalladuras, escalones y
  elementos con simetría**.
- Modelo 3D orbitable (ratón), botón **Vista isométrica estándar** y una
  **flecha amarilla "ALZADO"** que señala la cara frontal principal.

### 2. Modos de práctica
- **Opción B · Test:** la pieza 3D y 4 conjuntos de vistas diédricas; eliges el
  correcto. Los distractores reproducen errores típicos (olvidar líneas
  ocultas, dimensiones o posiciones incorrectas).
- **Opción A · Dibujar:** una cuadrícula por vista donde trazas aristas
  **vistas (continua), ocultas (discontinua) y ejes (trazo-punto)**, además de
  marcar el centro de los taladros. El botón **Comprobar** puntúa aristas
  acertadas / faltantes / sobrantes por vista.
- **Ver solución:** proyecta las tres vistas correctas, ya distribuidas en
  disposición europea (planta debajo, perfil a la derecha) con sus líneas de
  correspondencia.

### 3. Feedback y trucos
- Tras fallar o pedir la solución, botones que **iluminan en el 3D la cara que
  origina cada vista** (frontal → Alzado, superior → Planta, lateral → Perfil).
- Pestaña lateral fija con **Consejos de Normalización de la UPCT**:
  disposición del 1er diedro, correspondencia entre vistas, tipos y prioridad
  de líneas, taladros/ejes y planos inclinados.

## Notas técnicas

- La geometría se describe como un **prisma extruido en profundidad** a partir
  de un perfil frontal (el Alzado), con taladros cilíndricos pasantes. Tanto el
  modelo 3D (`THREE.ExtrudeGeometry`) como las tres vistas 2D se derivan del
  **mismo `spec` paramétrico**, garantizando coherencia.
- El proyector 2D calcula correctamente las **aristas ocultas por oclusión**
  (p. ej., el peldaño bajo de una escuadra alta o el fondo de un vaciado).
