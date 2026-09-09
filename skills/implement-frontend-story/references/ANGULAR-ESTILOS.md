# Guía de Estilos CSS en Angular

Esta guía define los estándares para el manejo de estilos en los proyectos Angular del monorepo (web-empresas, web-nominas).

## Tabla de Contenidos

- [Filosofía de Estilos](#filosofía-de-estilos)
- [Arquitectura en Capas](#arquitectura-en-capas)
- [Sistema de Clases @sinco/angular](#sistema-de-clases-sincoangular)
- [Clases de Espaciado](#clases-de-espaciado)
- [Clases de Layout](#clases-de-layout)
- [Sistema de Grid Responsive](#sistema-de-grid-responsive)
- [Clases de Color](#clases-de-color)
- [Clases de Tipografía](#clases-de-tipografía)
- [Sistema de Elevaciones](#sistema-de-elevaciones)
- [Clases de Display y Utilidades](#clases-de-display-y-utilidades)
- [Breakpoints Responsive](#breakpoints-responsive)
- [Mixins y Uso Avanzado](#mixins-y-uso-avanzado)
- [Patrones Comunes](#patrones-comunes)
- [Reglas Importantes](#reglas-importantes)

---

## Filosofía de Estilos

Los proyectos Angular **NO deben incluir estilos CSS personalizados** en los componentes. En su lugar, utilizamos:

1. **Sistema de clases de utilidad de @sinco/angular**
2. **Componentes de Angular Material** con estilos por defecto
3. **Sistema de diseño consistente** sin estilos custom

### Ventajas de este enfoque:

- ✅ Consistencia visual en toda la aplicación
- ✅ Mantenibilidad - Sin código CSS disperso
- ✅ Performance - CSS optimizado y compartido
- ✅ Productividad - Desarrollo más rápido
- ✅ Responsive - Sistema completo de breakpoints

---

## Arquitectura en Capas

El sistema de estilos de Bitakora está organizado en **3 capas** que se construyen una sobre otra:

```
┌─────────────────────────────────────────┐
│   @angular/material                     │
│   Material Design base                  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│   @sinco/angular (CAPA 1 - Base)       │
│   - Sistema de espaciado (p-, m-, gap-)│
│   - Sistema de layout (row, column)    │
│   - Grid responsive (12 columnas)      │
│   - Breakpoints (xs, s, m, l, xl, xxl) │
│   - Clases de utilidad (display, etc.) │
│   - Mixins compartidos                  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  @sinco/angular-bitakora (CAPA 2)      │
│   - Paletas de colores de Bitakora     │
│   - Tema Material personalizado        │
│   - Tipografía (Nunito + Roboto)       │
│   - Sistema de elevaciones (sombras)   │
│   - Componentes especializados         │
│   - Tokens de tamaño                   │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  @bitakora/angular-webkit (CAPA 3)     │
│   - Componentes locales compartidos    │
│   - Servicios del monorepo             │
│   - Estilos específicos de componentes │
└─────────────────────────────────────────┘
```

### Capa 1: @sinco/angular (Base)

**Propósito:** Sistema de diseño base con utilidades CSS y layout

**Proporciona:**

- Sistema de espaciado con unidad 0.4rem (p-_, m-_, gap-\*)
- Sistema de layout flexbox y grid
- Grid responsive de 12 columnas
- Breakpoints estandarizados
- Clases de utilidad generales
- Mixins reutilizables

### Capa 2: @sinco/angular-bitakora (Personalización)

**Propósito:** Identidad visual y tema de Bitakora

**Proporciona:**

- **Colores de marca:** Primary (#1b344c), Accent (#2d9fc5), Warn, Success, Caution
- **Tema de Material:** Configuración personalizada de Angular Material
- **Tipografía:** Nunito (headings) + Roboto (body)
- **Elevaciones:** Sistema de sombras personalizado (0-24 niveles)
- **Componentes:** Calendar, Tag, Liquidacion, Concepto, etc.

### Capa 3: @bitakora/angular-webkit (Local)

**Propósito:** Componentes y servicios específicos del monorepo

**Proporciona:**

- **Componentes:** Timeline, Loading, EmptyData, Subheader, etc.
- **Servicios:** AlertaService, LoadingService, SignalRService, etc.
- **Interceptores:** BitakoraInterceptor, BitakoraInterceptorLoading
- **Guards:** PermisosGuard, TieneDominioGuard

---

## Sistema de Clases @sinco/angular

Todas las clases de utilidad base provienen de **@sinco/angular**:

```scss
@use 'node_modules/@sinco/angular/src/lib/styles/mixins.scss' as mixins;
@use 'node_modules/@sinco/angular/src/lib/styles/tokens.scss' as tokens;
```

Las personalizaciones de color y tema vienen de **@sinco/angular-bitakora**:

```scss
@use 'node_modules/@sinco/angular-bitakora/src/lib/styles/colors.scss' as colors;
@use 'node_modules/@sinco/angular-bitakora/src/lib/styles/elevations.scss' as elevations;
```

---

## Clases de Espaciado

### Sistema de Espaciado

- **Unidad base**: `0.4rem` (4px)
- **Rango**: 0 a 20
- **Cálculo**: `p-4` = 4 × 0.4rem = 1.6rem = 16px

### Clases de Padding

```html
<!-- Padding general -->
<div class="p-0">Sin padding</div>
<div class="p-1">0.4rem (4px)</div>
<div class="p-2">0.8rem (8px)</div>
<div class="p-3">1.2rem (12px)</div>
<div class="p-4">1.6rem (16px)</div>
<div class="p-5">2rem (20px)</div>
<!-- hasta p-20 -->

<!-- Padding direccional -->
<div class="pt-4">Padding top</div>
<div class="pb-2">Padding bottom</div>
<div class="px-3">Padding horizontal (inline)</div>
<div class="py-2">Padding vertical (block)</div>
<div class="pl-2">Padding left</div>
<div class="pr-2">Padding right</div>
```

### Clases de Margin

```html
<!-- Margin general -->
<div class="m-0">Sin margin</div>
<div class="m-2">0.8rem (8px)</div>
<div class="m-4">1.6rem (16px)</div>
<!-- hasta m-20 -->

<!-- Margin direccional -->
<div class="mt-5">Margin top</div>
<div class="mb-3">Margin bottom</div>
<div class="mx-4">Margin horizontal</div>
<div class="my-2">Margin vertical</div>
<div class="ml-1">Margin left</div>
<div class="mr-1">Margin right</div>

<!-- Margin auto -->
<div class="m-auto">Margin auto (centrar)</div>
```

### Clases de Gap (Flexbox/Grid)

```html
<!-- Gap para flex/grid -->
<div class="d-flex gap-2">Gap 0.8rem entre elementos</div>
<div class="d-flex gap-4">Gap 1.6rem entre elementos</div>
<div class="d-flex gap-6">Gap 2.4rem entre elementos</div>

<!-- Gap específico para grid -->
<div class="d-grid gap-column-3">Gap entre columnas</div>
<div class="d-grid gap-row-2">Gap entre filas</div>
<div class="d-grid gap-column-12 gap-row-2">Gap columnas y filas</div>
```

### Ejemplos Reales del Proyecto

```html
<mat-card-content class="p-4 gap-2">
  <div class="column gap-4">
    <div class="row px-2">
      <div class="row align-items-center py-0 py-s-4 gap-1"></div>
    </div></div
></mat-card-content>
```

---

## Clases de Layout

### Flexbox - Dirección

```html
<!-- Dirección de flex — ya incluyen display:flex, NO agregar d-flex -->
<div class="row">Flex dirección horizontal (row)</div>
<div class="column">Flex dirección vertical (column)</div>
<div class="row-reverse">Flex horizontal reverso</div>
<div class="column-reverse">Flex vertical reverso</div>

<!-- ❌ MAL: d-flex column es redundante -->
<div class="d-flex column">...</div>
<!-- ✅ BIEN: column ya incluye display:flex -->
<div class="column">...</div>
```

### Flexbox - Display y Wrap

```html
<!-- d-flex SOLO cuando se necesita flex horizontal sin row/column -->
<div class="d-flex">Display flex con wrap automático</div>
<div class="d-flex nowrap">Flex sin wrap</div>
<div class="d-flex wrap">Flex con wrap explícito</div>
```

### Clases innecesarias

```html
<!-- ❌ MAL: m-0 y p-0 son innecesarios (ya es el valor por defecto) -->
<h5 class="m-0">Título</h5>
<div class="p-0">Contenido</div>

<!-- ✅ BIEN: sin clases redundantes -->
<h5>Título</h5>
<div>Contenido</div>

<!-- ✅ EXCEPCIÓN: p-0 es necesario con col para quitar padding de Bootstrap -->
<div class="col p-0">Columna sin padding</div>
```

### Flexbox - Justificación (eje principal)

```html
<div class="row justify-content-start">Inicio</div>
<div class="row justify-content-end">Final</div>
<div class="row justify-content-center">Centro</div>
<div class="row justify-content-between">Espacio entre</div>
<div class="row justify-content-around">Espacio alrededor</div>
<div class="row justify-content-baseline">Línea base</div>
<div class="row justify-content-stretch">Estirar</div>
```

### Flexbox - Alineación (eje cruzado)

```html
<div class="column align-items-start">Inicio</div>
<div class="column align-items-end">Final</div>
<div class="column align-items-center">Centro</div>
<div class="column align-items-baseline">Línea base</div>
<div class="column align-items-stretch">Estirar</div>
```

### Grid

```html
<!-- Display grid -->
<div class="d-grid">Display grid</div>

<!-- Grid templates (columnas automáticas) -->
<div class="d-grid grid-template-1">1 columna</div>
<div class="d-grid grid-template-2">2 columnas</div>
<div class="d-grid grid-template-3">3 columnas</div>
<div class="d-grid grid-template-4">4 columnas</div>
<!-- hasta grid-template-10 -->

<!-- Grid con gap -->
<div class="d-grid grid-template-3 gap-column-12 gap-row-2">3 columnas con espaciado</div>
```

### Ejemplos Reales del Proyecto

```html
<div class="row justify-content-between align-items-center">
  <div class="column gap-2 justify-content-center align-items-center">
    <mat-nav-list class="d-grid grid-template-3 gap-column-12 gap-row-2 p-0"></mat-nav-list>
  </div>
</div>
```

---

## Sistema de Grid Responsive

### Sistema de Columnas (12 columnas)

```html
<!-- Columnas fijas -->
<div class="col-1">8.333% (1/12)</div>
<div class="col-2">16.666% (2/12)</div>
<div class="col-3">25% (3/12)</div>
<div class="col-4">33.333% (4/12)</div>
<div class="col-6">50% (6/12)</div>
<div class="col-8">66.666% (8/12)</div>
<div class="col-12">100% (12/12)</div>

<!-- Columna flexible -->
<div class="col">Ocupa espacio disponible</div>
```

### Columnas Responsive

```html
<!-- Columnas adaptables por breakpoint -->
<div class="col-s-12 col-m-12 col-l-6 col-xl-4 col-xxl-4">
  <!-- Móvil: 100%, Tablet: 100%, Laptop: 50%, Desktop: 33.33% -->
</div>

<div class="col-s-12 col-m-6 col-l-4">
  <!-- Móvil: 100%, Tablet: 50%, Laptop: 33.33% -->
</div>

<div class="row p-0 gap-2 col-s-12 col-m-12 col-l-4 col-xl-4">
  <!-- Row que cambia de tamaño según dispositivo -->
</div>
```

### Ejemplos Reales del Proyecto

```html
<div class="row col-12 p-0 mb-5">
  <div class="col-s-12 col-m-12 col-l-6 col-xl-4 col-xxl-4">
    <!-- Contenido responsive -->
  </div>
</div>

<p class="mat-subtitle-1 col-s col-m-7 col-l-6">
  <!-- Texto que se adapta -->
</p>
```

---

## Clases de Color

### Paleta de Colores de Bitakora

Los colores provienen de **@sinco/angular-bitakora** y definen la identidad visual de Bitakora:

```scss
// Paletas principales de Bitakora
Primary: #1b344c   (Azul oscuro corporativo)
Accent:  #2d9fc5   (Azul claro - color característico)
Warn:    #d14343   (Rojo)
Success: #8fc93a   (Verde lima)
Caution: #fb8500   (Naranja)
```

### Colores de Texto

```html
<!-- Colores principales del tema Bitakora -->
<p class="color-primary">Color primario (#1b344c)</p>
<p class="color-accent">Color accent (#2d9fc5)</p>
<p class="color-warn">Color warn (#d14343)</p>

<!-- Colores de texto con opacidad (Bitakora) -->
<p class="color-text-primary">rgba(8, 21, 36, 0.87) - Texto principal</p>
<p class="color-text-secondary">rgba(8, 21, 36, 0.6) - Texto secundario</p>
<p class="color-text-disabled">rgba(8, 21, 36, 0.38) - Texto deshabilitado</p>

<!-- Colores básicos -->
<p class="color-white">Blanco (#ffffff)</p>
<p class="color-black">Negro (#000000)</p>
<p class="color-grey">Gris</p>

<!-- Colores semánticos de Bitakora -->
<p class="color-success">Color de éxito (#8fc93a)</p>
<p class="color-info">Color informativo</p>
<p class="color-warning">Color de advertencia</p>
<p class="color-caution">Color de precaución (#fb8500)</p>

<!-- Colores con tonos (50-900) -->
<p class="color-primary-500">Tono medio del primary</p>
<p class="color-primary-700">Tono oscuro del primary</p>
<p class="color-accent-300">Tono claro del accent</p>
<p class="color-accent-500">Tono medio del accent (#2d9fc5)</p>
<p class="color-success-500">Verde lima (#8fc93a)</p>
<p class="color-caution-500">Naranja (#fb8500)</p>
```

### Colores de Fondo

```html
<!-- Fondos principales -->
<div class="bg-primary">Fondo primario</div>
<div class="bg-accent">Fondo acento</div>
<div class="bg-warn">Fondo advertencia</div>

<!-- Fondos básicos -->
<div class="bg-white">Fondo blanco</div>
<div class="bg-grey">Fondo gris</div>

<!-- Fondos semánticos -->
<div class="bg-success">Fondo éxito</div>
<div class="bg-info">Fondo info</div>
<div class="bg-warning">Fondo advertencia</div>

<!-- Fondos con tonos -->
<div class="bg-accent-100">Fondo acento muy claro</div>
<div class="bg-primary-700">Fondo primario oscuro</div>

<!-- Fondos especiales -->
<div class="bg-none">Sin fondo</div>
<div class="bg-transparent">Fondo transparente</div>
```

### Ejemplos Reales del Proyecto

```html
<p class="mat-caption color-text-secondary">ID: {{ solicitud().contrato }}</p>
<p class="mat-subtitle-1 color-text-primary">{{ solicitud().nombreCompleto }}</p>
<mat-icon class="color-text-primary">chevron_right</mat-icon>
<label class="color-accent mr-1">Estado:</label>
<div class="bg-accent color-white">Contenido destacado</div>
```

---

## Clases de Tipografía

La tipografía de Bitakora está configurada en **@sinco/angular-bitakora** y utiliza dos fuentes:

- **Nunito**: Para encabezados (h3-h6, headline)
- **Roboto**: Para cuerpo de texto (body, caption, subtitle)
- **Base**: 14px (0.875rem)

### Clases de Angular Material

```html
<!-- Subtítulos (Roboto) -->
<p class="mat-subtitle-1">1.4rem (19.6px), weight 500 - Subtítulo principal</p>
<p class="mat-subtitle-2">1.3rem (18.2px), weight 500 - Subtítulo secundario</p>

<!-- Cuerpo de texto (Roboto) -->
<p class="mat-body-1">1rem (14px), weight 400 - Texto normal grande</p>
<p class="mat-body-2">0.929rem (13px), weight 400 - Texto normal</p>

<!-- Texto pequeño (Roboto) -->
<p class="mat-caption">0.786rem (11px), weight 400 - Texto pequeño para detalles</p>

<!-- Botones (Roboto) -->
<button class="mat-button">1rem (14px), weight 500, uppercase</button>
```

### Headers (fuente Nunito)

```html
<!-- Headlines (Nunito) -->
<h1 class="mat-headline-5">6.857rem (96px), weight 300</h1>
<h2 class="mat-headline-6">4.286rem (60px), weight 400</h2>

<!-- Headings (Nunito) -->
<h3>3.429rem (48px), weight 500</h3>
<h4>2.429rem (34px), weight 500</h4>
<h5>1.286rem (18px), weight 500</h5>
<h6>1.143rem (16px), weight 600</h6>
```

### Ejemplos Reales del Proyecto

```html
<p class="mat-subtitle-1 col-s col-m-7">{{ solicitud().nombreCompleto }}</p>
<p class="mat-caption color-text-secondary">ID: {{ solicitud().contrato }}</p>
<span class="mat-body-1">({{ descripcionTipoPlanilla }})</span>
<p class="mat-body-2 color-text-secondary">Valor a pagar:</p>
```

---

## Sistema de Elevaciones

Bitakora tiene un **sistema de elevaciones (sombras) personalizado** configurado en **@sinco/angular-bitakora**:

### Características

- **Niveles**: 0 a 24 (25 niveles de sombra)
- **Color de sombra**: #18274b (azul oscuro de Bitakora)
- **Tipos de sombra**: Combina umbral, prenumbral y ambient

### Clases Disponibles

```html
<!-- Elevaciones básicas -->
<div class="mat-elevation-z0">Sin sombra</div>
<div class="mat-elevation-z1">Sombra muy sutil</div>
<div class="mat-elevation-z2">Sombra sutil (raised buttons)</div>
<div class="mat-elevation-z4">Sombra media</div>
<div class="mat-elevation-z6">Sombra notable</div>
<div class="mat-elevation-z8">Sombra prominente (menus)</div>
<div class="mat-elevation-z12">Sombra elevada</div>
<div class="mat-elevation-z16">Sombra muy elevada</div>
<div class="mat-elevation-z24">Sombra máxima (dialogs)</div>
```

### Uso con Mixin en SCSS

```scss
@use 'node_modules/@sinco/angular-bitakora/src/lib/styles/elevations.scss' as elevations;

.mi-card {
  @include elevations.elevation(2);
}

.mi-modal {
  @include elevations.elevation(24);
}
```

### Elevaciones Automáticas de Material

Los componentes de Angular Material ya tienen elevaciones aplicadas automáticamente:

```scss
// Aplicadas automáticamente por @sinco/angular-bitakora
mat-raised-button     → elevation(2)
mat-menu-panel        → elevation(8)
mat-dialog-container  → elevation(24)
mat-card              → elevation(1)
```

### Elevación Responsive

```html
<!-- Elevación que cambia según el tamaño de pantalla -->
<mat-card class="mat-elevation-responsive">
  <!-- Elevation 0 en desktop, elevation 1 en móvil/tablet -->
</mat-card>
```

```scss
// Implementación de mat-elevation-responsive
.mat-elevation-responsive {
  @include elevations.elevation(0);

  @media (max-width: tokens.$breakpoint-tablet) {
    @include elevations.elevation(1);
  }
}
```

### Ejemplos del Proyecto

```html
<!-- Card sin sombra -->
<mat-card class="shadow-none">
  <mat-card-content>...</mat-card-content>
</mat-card>

<!-- Card con elevación responsive -->
<mat-card class="mat-elevation-responsive">
  <mat-card-content>...</mat-card-content>
</mat-card>

<!-- Card con elevación personalizada -->
<mat-card class="mat-elevation-z4">
  <mat-card-content>...</mat-card-content>
</mat-card>
```

---

## Clases de Display y Utilidades

### Display

```html
<div class="d-block">Display block</div>
<div class="d-none">Display none (ocultar)</div>
<div class="d-inline">Display inline</div>
<div class="d-flex">Display flex</div>
<div class="d-grid">Display grid</div>
```

### Posicionamiento

```html
<div class="fixed">Position fixed</div>
<div class="absolute">Position absolute</div>
<div class="relative">Position relative</div>
<div class="static">Position static</div>
<div class="sticky">Position sticky</div>
```

### Dimensiones

```html
<div class="full-width">Width 100%</div>
<div class="full-height">Height 100%</div>
<div class="fit-content">Width fit-content</div>
<div class="height-fit-content">Height fit-content</div>
```

### Texto

```html
<p class="text-center">Texto centrado</p>
<p class="text-left">Texto alineado izquierda</p>
<p class="text-right">Texto alineado derecha</p>
<p class="text-nowrap">Texto sin salto de línea</p>
<p class="ellipsis">Texto truncado con puntos suspensivos...</p>
```

### Cursor

```html
<div class="cursor-default">Cursor por defecto</div>
<div class="cursor-pointer">Cursor pointer (clickeable)</div>
<div class="cursor-help">Cursor de ayuda</div>
<div class="cursor-wait">Cursor de espera</div>
<div class="cursor-not-allowed">Cursor de no permitido</div>
```

### Opacidad

```html
<div class="opacity-0">Completamente transparente</div>
<div class="opacity-25">25% opacidad</div>
<div class="opacity-50">50% opacidad</div>
<div class="opacity-75">75% opacidad</div>
<div class="opacity-100">100% opacidad</div>
```

### Sombras

```html
<mat-card class="shadow-none">Sin sombra</mat-card> <mat-card class="mat-elevation-responsive">Sombra responsive</mat-card>
```

### Ejemplos Reales del Proyecto

```html
<mat-card class="shadow-none">
  <div class="column justify-content-center align-items-center">
    <span class="ellipsis list-text py-1">Texto largo truncado</span>
    <div class="cursor-pointer">Elemento clickeable</div>
  </div></mat-card
>
```

---

## Breakpoints Responsive

### Sistema de Breakpoints

```
xs   : ≤ 400px   (móvil pequeño)
s    : ≤ 525px   (móvil)
m    : 525-850px (tablet)
l    : 850-1024px (laptop pequeño)
xl   : 1024-1440px (laptop)
xxl  : ≥ 1440px (desktop grande)
```

### Uso de Sufijos Responsive

Todas las clases de espaciado, layout y display pueden tener sufijos responsive:

```html
<!-- Espaciado responsive -->
<div class="p-2 p-s-4 p-m-6">
  <!-- Desktop: padding 0.8rem, Móvil: 1.6rem, Tablet: 2.4rem -->
</div>

<div class="py-0 py-s-4 gap-1">
  <!-- Desktop: sin padding vertical, Móvil: padding 1.6rem -->
</div>

<!-- Columnas responsive -->
<div class="col-12 col-m-6 col-l-4 col-xl-3">
  <!-- Base: 100%, Tablet: 50%, Laptop: 33.33%, Desktop: 25% -->
</div>

<!-- Display responsive -->
<div class="d-block d-none-s d-none-m">
  <!-- Visible solo en laptop y desktop -->
</div>

<div class="d-none d-block-l">
  <!-- Oculto en móvil/tablet, visible desde laptop -->
</div>

<!-- Layout responsive -->
<div class="column column-reverse-xl">
  <!-- Columna normal, reversa en desktop -->
</div>

<div class="row-reverse-xl row-reverse-xxl d-none-l d-none-m d-none-s">
  <!-- Row reverso solo en desktop XL/XXL, oculto en menores -->
</div>

<!-- Alineación responsive -->
<div class="justify-content-start justify-content-end-l">
  <!-- Alineado al inicio en móvil, al final en laptop -->
</div>

<div class="justify-content-between-s justify-content-between-m">
  <!-- Espacio entre elementos en móvil y tablet -->
</div>
```

### Ejemplos Reales del Proyecto

```html
<div class="col-s-12 col-m-12 col-l-6 col-xl-4 col-xxl-4">
  <!-- 100% en móvil/tablet, 50% en laptop, 33% en desktop -->
</div>

<div class="py-0 py-s-4 gap-1">
  <!-- Sin padding vertical en desktop, con padding en móvil -->
</div>

<div class="d-none-m d-none-s d-block">
  <!-- Solo visible en laptop y desktop -->
</div>

<div class="row-reverse-xl row-reverse-xxl d-none-l d-none-m d-none-s">
  <!-- Configuración específica para desktop grande -->
</div>
```

---

## Mixins y Uso Avanzado

Cuando las clases de utilidad no son suficientes, puedes usar **mixins** de @sinco/angular en archivos .scss de componentes:

### Importar Mixins y Colores

```scss
// En tu componente.scss
@use 'sass:map';
@use 'node_modules/@sinco/angular/src/lib/styles/tokens.scss' as tokens;
@use 'node_modules/@sinco/angular/src/lib/styles/mixins.scss' as mixins;
@use 'node_modules/@sinco/angular-bitakora/src/lib/styles/colors.scss' as colors;
@use 'node_modules/@sinco/angular-bitakora/src/lib/styles/elevations.scss' as elevations;
```

### Mixin: chip()

Genera estilos para chips/badges:

```scss
@use 'node_modules/@sinco/angular/src/lib/styles/mixins.scss' as mixins;

@include mixins.chip();
```

```html
<!-- Uso en HTML -->
<mat-chip size="small" color="accent" highlighted class="stroked"> Estado </mat-chip>
```

### Mixin: elevation()

Aplica sombras de Bitakora:

```scss
@use 'node_modules/@sinco/angular-bitakora/src/lib/styles/elevations.scss' as elevations;

.mi-componente {
  @include elevations.elevation(4);

  &:hover {
    @include elevations.elevation(8);
  }
}
```

### Acceder a Paletas de Color

Usar `map.get()` para acceder a tonos específicos:

```scss
@use 'sass:map';
@use 'node_modules/@sinco/angular-bitakora/src/lib/styles/colors.scss' as colors;

.timeline-dot {
  &.primary {
    color: map.get(colors.$bitakora-primary, 500);
    border-color: map.get(colors.$bitakora-primary, 500);
  }

  &.accent {
    color: map.get(colors.$bitakora-accent, 500);
  }

  &.success {
    color: map.get(colors.$bitakora-success, 500);
  }

  &.filled {
    background-color: currentColor;
  }
}
```

### Breakpoints con Media Queries

```scss
@use 'node_modules/@sinco/angular/src/lib/styles/tokens.scss' as tokens;

.mi-componente {
  padding: 2rem;

  @media (max-width: tokens.$breakpoint-tablet) {
    padding: 1rem;
  }

  @media (max-width: tokens.$breakpoint-mobile) {
    padding: 0.5rem;
  }
}
```

### Ejemplo Completo: Timeline Component

```scss
// libs/angular-webkit/src/lib/components/timeline/timeline.component.scss
@use 'sass:map';
@use 'node_modules/@sinco/angular-bitakora/src/lib/styles/colors.scss' as colors;

.timeline-container {
  display: flex;
  flex-direction: column;
}

.timeline-item {
  display: flex;
  gap: 0.8rem;
}

.timeline-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid;
  color: colors.$text-disabled;

  &.filled {
    background-color: currentColor;
  }

  &.primary {
    color: map.get(colors.$bitakora-primary, 500);
  }

  &.accent {
    color: map.get(colors.$bitakora-accent, 500);
  }

  &.success {
    color: map.get(colors.$bitakora-success, 500);
  }
}

.timeline-connector {
  width: 2px;
  flex-grow: 1;
  background-color: colors.$text-disabled;
}
```

### Personalización de Componentes Material

```scss
// Personalizar progress bar
.mat-mdc-progress-bar {
  --mdc-linear-progress-active-indicator-color: #2d9fc5 !important;
  --mdc-linear-progress-track-color: #cdeffd !important;
  --mdc-linear-progress-active-indicator-height: 40px !important;
  --mdc-linear-progress-track-height: 40px !important;
}

.progress-container {
  border-radius: 40px;
  overflow: hidden;
}
```

### Cuándo Usar Mixins vs Clases

**✅ Usar clases de utilidad cuando:**

- Layout, espaciado, alineación estándar
- Colores del tema (color-_, bg-_)
- Responsive básico con breakpoints
- Display, posicionamiento, tipografía

**✅ Usar mixins/SCSS cuando:**

- Necesitas acceder a tonos específicos de color (500, 700, etc.)
- Aplicas transiciones o animaciones
- Personalizas componentes de Material
- Creas componentes reutilizables en angular-webkit
- Necesitas lógica condicional en estilos

---

## Patrones Comunes

### Patrón 1: Card con Contenido Responsive

```html
<mat-card class="mat-elevation-responsive">
  <mat-card-content class="row justify-content-between align-items-center py-0 py-s-4 gap-1">
    <div class="row gap-2 align-items-center col p-0">
      <p class="mat-subtitle-1 color-text-primary">Título</p>
      <p class="mat-caption color-text-secondary">Detalle</p>
    </div>
    <button mat-icon-button>
      <mat-icon class="color-text-primary">chevron_right</mat-icon>
    </button>
  </mat-card-content>
</mat-card>
```

### Patrón 2: Layout Responsive con Columnas

```html
<div class="row gap-6 align-items-center justify-content-between">
  <div class="row p-0 gap-2 col-s-12 col-m-12 col-l-4 col-xl-4">
    <div class="column gap-2">
      <h6>Título</h6>
      <p class="mat-body-2 color-text-secondary">Descripción</p>
    </div>
  </div>
  <div class="col-s-12 col-m-12 col-l-6 col-xl-4">
    <!-- Otro contenido -->
  </div>
</div>
```

### Patrón 3: Grid de Elementos

```html
<mat-nav-list class="d-grid grid-template-3 gap-column-12 gap-row-2 p-0">
  <mat-list-item class="row px-2" *ngFor="let item of items">
    <div class="row gap-2 align-items-center">
      <mat-icon class="color-text-primary">{{ item.icon }}</mat-icon>
      <span class="mat-body-1">{{ item.label }}</span>
    </div>
  </mat-list-item>
</mat-nav-list>
```

### Patrón 4: Columna Centrada Verticalmente

```html
<div class="column justify-content-center align-items-center gap-2">
  <img class="container-img" [src]="imagenUrl" />
  <h6>{{ titulo }}</h6>
  <p class="mat-body-2 color-text-secondary text-center">{{ descripcion }}</p>
  <button mat-raised-button color="primary">Acción</button>
</div>
```

### Patrón 5: Formulario Responsive

```html
<form class="row gap-4">
  <mat-form-field class="col-s-12 col-m-6 col-l-4" size="small" appearance="outline">
    <mat-label>Campo 1</mat-label>
    <input matInput />
  </mat-form-field>

  <mat-form-field class="col-s-12 col-m-6 col-l-4" size="small" appearance="outline">
    <mat-label>Campo 2</mat-label>
    <mat-select>
      <mat-option value="1">Opción 1</mat-option>
    </mat-select>
  </mat-form-field>

  <div class="row gap-2 col-12 justify-content-end">
    <button mat-button color="accent">Cancelar</button>
    <button mat-raised-button color="primary">Guardar</button>
  </div>
</form>
```

---

## Reglas Importantes

### ✅ HACER:

1. **Usar componentes de Angular Material** con sus estilos por defecto
2. **Usar clases de utilidad de @sinco/angular** para espaciado, layout y tipografía
3. **Importar `AngularWebkitModule`** en todos los componentes
4. **Combinar clases de utilidad** para lograr el diseño deseado
5. **Usar sistema de espaciado consistente** con unidades de 0.4rem (p-4, m-2, gap-3, etc.)
6. **Usar row/column** para layouts flexbox
7. **Usar grid-template-{n}** para layouts grid
8. **Usar sufijos responsive** para adaptación (-s, -m, -l, -xl, -xxl)
9. **Usar clases de color** de @sinco/angular (color-text-primary, color-accent, bg-primary)
10. **Usar clases de tipografía Material** (mat-subtitle-1, mat-body-1, mat-caption)

### ❌ NO HACER:

1. **NO crear archivos `.scss` o `.css`** para componentes individuales **a menos que** el diseño requiera más de 3 propiedades custom no cubiertas por las clases utilitarias (ver sección "Estilos personalizados de tamaño del Figma")
2. **NO usar `styles` ni `styleUrls`** en @Component **a menos que** aplique la excepción anterior
3. **NO definir estilos inline** con `[style.property]` salvo propiedades puntuales (≤3) del diseño Figma
4. **NO crear clases CSS personalizadas** para el componente
5. **NO duplicar código CSS** que ya existe en @sinco/angular
6. **NO mezclar sistemas de clases** (no inventar clases propias)
7. **NO usar valores de espaciado arbitrarios** (seguir escala 0-20 con 0.4rem)

---

## Clases Personalizadas Permitidas

Solo en **styles.scss** de la aplicación (NO en componentes) se permiten algunas clases globales específicas del proyecto.

### web-empresas/src/styles.scss

```scss
.page-content {
  width: 100%;
  max-width: 1366px;
}

.chip-normal {
  @include mixins.chip();
}

.border-outlined-05 {
  border: 0.5px solid #1b344c3b;
}

.border-radius-4 {
  border-radius: 4px;
}

.border-radius-8 {
  border-radius: 8px;
}

.width-etiqueta {
  width: 131px;
}

.seccion-height {
  min-height: calc(100vh - 56px);
}

.line-height-normal {
  line-height: normal;
}

.bottom-bar {
  position: fixed;
  bottom: 0;
  width: 100%;
}
```

### web-nominas/src/styles.scss

```scss
.texto-sin-salto {
  white-space: nowrap;
}

.hidden-control {
  display: none !important;
}

.height-pantalla-completa {
  min-height: calc(100vh - 56px);
}

.avatar {
  width: 32px;
  height: 32px;

  img {
    object-fit: cover;
    border-radius: 50%;
  }
}

.radius-1 {
  border-radius: 4px;
}

.radius-2 {
  border-radius: 8px;
}
```

**⚠️ IMPORTANTE:** Estas clases solo se permiten en el archivo styles.scss global de la aplicación. NO crear clases personalizadas en componentes individuales.

### Estilos personalizados de tamaño del Figma

Si un componente necesita tamaños específicos del diseño Figma que NO están cubiertos por las clases utilitarias (anchos fijos, alturas específicas):

- **3 o menos estilos custom** → usar atributo `style=""` directamente en el elemento HTML del template (ej: `style="width: 1110px;`)
- **Más de 3 estilos custom** → crear archivo `.scss` junto al componente con `styleUrl`
- Todo lo demás (spacing, layout, colores, tipografía) DEBE seguir usando clases utilitarias

---

## Checklist de Estilos

Antes de considerar tu componente terminado, verifica:

- [ ] El componente importa `AngularWebkitModule`
- [ ] NO existe propiedad `styles` ni `styleUrls` en @Component (salvo excepción Figma >3 custom)
- [ ] NO existen archivos `.scss` o `.css` junto al componente (salvo excepción Figma >3 custom)
- [ ] Se usan clases de espaciado de @sinco/angular (p-_, m-_, gap-\*)
- [ ] Se usan clases de layout (row, column, d-flex, d-grid)
- [ ] Se usan clases responsive cuando es necesario (-s, -m, -l, -xl, -xxl)
- [ ] Se usan clases de color de @sinco/angular (color-_, bg-_)
- [ ] Se usan clases de tipografía Material (mat-subtitle-1, mat-body-1, mat-caption)
- [ ] Se usan componentes de Angular Material sin modificaciones
- [ ] El diseño es responsive y se adapta a diferentes dispositivos
- [ ] El diseño es consistente con el resto de la aplicación

---

## Fórmula de Espaciado

```
número × 0.4rem = resultado

Ejemplos:
p-4   = 4 × 0.4rem = 1.6rem = 16px
gap-6 = 6 × 0.4rem = 2.4rem = 24px
m-10  = 10 × 0.4rem = 4rem = 40px
```

---

## Recursos

### Documentación Interna

- [Guía de Arquitectura Angular](.claude/ANGULAR-ARQUITECTURA.md)
- [Guía de Signal Store](.claude/ANGULAR-SIGNAL-STORE.md)
- [Guía del Patrón Facade](.claude/ANGULAR-FACADE.md)

### Dependencias

**Arquitectura en 3 capas:**

1. **@sinco/angular** (v5.0.6) - Sistema de diseño base
   - Clases de utilidad (spacing, layout, grid, display)
   - Breakpoints responsive (xs, s, m, l, xl, xxl)
   - Mixins reutilizables

2. **@sinco/angular-bitakora** (v5.0.7) - Personalización Bitakora
   - Paletas de colores corporativos
   - Tema de Material Design personalizado
   - Tipografía Nunito + Roboto
   - Sistema de elevaciones
   - Componentes especializados

3. **@bitakora/angular-webkit** - Librería local del monorepo
   - Componentes compartidos (Timeline, Loading, EmptyData, etc.)
   - Servicios (AlertaService, LoadingService, SignalRService, etc.)
   - Interceptores HTTP y Guards

**Otros:**

- **Angular Material** (v19.2.9): Componentes UI base
- **@angular/cdk**: Component Dev Kit

### Documentación Oficial

- [Angular Material](https://material.angular.io)
- [Angular](https://angular.dev)

---

## Conclusión

El sistema de estilos de Bitakora está construido en **3 capas** que trabajan juntas:

### Capa 1: @sinco/angular (Base)

- Sistema de espaciado modular (0-20 con unidad 0.4rem = 4px)
- Grid responsive de 12 columnas con 6 breakpoints
- Flexbox utilities completas (row, column, alineación, justificación)
- Clases de utilidad (display, cursor, posición, opacidad, etc.)
- Mixins reutilizables

### Capa 2: @sinco/angular-bitakora (Personalización)

- Paletas de colores de Bitakora (Primary #1b344c, Accent #2d9fc5, etc.)
- Tema de Material Design personalizado
- Tipografía Nunito + Roboto
- Sistema de elevaciones personalizado (25 niveles)
- Componentes especializados (Calendar, Tag, Liquidacion, etc.)

### Capa 3: @bitakora/angular-webkit (Local)

- Componentes compartidos del monorepo (Timeline, Loading, EmptyData, etc.)
- Servicios comunes (AlertaService, LoadingService, SignalRService, etc.)
- Interceptores HTTP y Guards

**Regla de oro**: Si crees que necesitas crear un estilo CSS personalizado:

1. **Primero** busca si existe una clase de utilidad de @sinco/angular
2. **Luego** verifica si existe un componente en @sinco/angular-bitakora o @bitakora/angular-webkit
3. **Finalmente** considera usar mixins y paletas de colores de @sinco/angular-bitakora
4. **Solo como último recurso** crea estilos personalizados en el styles.scss global de la aplicación

En el 99% de los casos, las clases de utilidad y componentes ya existentes son suficientes.
