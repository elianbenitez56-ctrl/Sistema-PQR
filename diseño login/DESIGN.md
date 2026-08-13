---
name: Institutional Professional
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#444650'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#757681'
  outline-variant: '#c5c6d1'
  surface-tint: '#455c99'
  primary: '#000d2f'
  on-primary: '#ffffff'
  primary-container: '#00205b'
  on-primary-container: '#738aca'
  inverse-primary: '#b2c5ff'
  secondary: '#006782'
  on-secondary: '#ffffff'
  secondary-container: '#42d0fe'
  on-secondary-container: '#00566d'
  tertiary: '#1e0a00'
  on-tertiary: '#ffffff'
  tertiary-container: '#3e1b00'
  on-tertiary-container: '#da6e01'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2ff'
  primary-fixed-dim: '#b2c5ff'
  on-primary-fixed: '#001849'
  on-primary-fixed-variant: '#2d447f'
  secondary-fixed: '#baeaff'
  secondary-fixed-dim: '#5cd4ff'
  on-secondary-fixed: '#001f29'
  on-secondary-fixed-variant: '#004d62'
  tertiary-fixed: '#ffdcc6'
  tertiary-fixed-dim: '#ffb786'
  on-tertiary-fixed: '#311300'
  on-tertiary-fixed-variant: '#723600'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  container-max: 1280px
  gutter: 1.5rem
  margin-mobile: 1rem
  margin-desktop: 2.5rem
  stack-sm: 0.5rem
  stack-md: 1rem
  stack-lg: 2rem
---

## Brand & Style

This design system is built for the INAPEL PQR (Petitions, Complaints, and Requests) system, prioritizing a **Corporate Modern** aesthetic. The goal is to project stability, institutional trust, and high-performance efficiency.

The visual narrative combines the structural reliability of enterprise software (SAP Fiori, Atlassian) with contemporary "soft" UI trends. Key characteristics include:
- **Professionalism:** High-contrast typography and a dominant deep-blue palette.
- **Modernity:** Large corner radii (20px) and glassmorphism accents for high-level navigation and modal overlays.
- **Clarity:** Generous whitespace (High-Density) to reduce cognitive load during complex administrative tasks.
- **Premium Finish:** Subtle ambient shadows and translucent layers to create a sense of depth and hierarchy.

## Colors

The palette is derived directly from the institutional logo, optimized for digital accessibility and premium feel.

### Primary Palette
- **Deep Blue (#00205B):** Used for primary actions, headers, and core brand elements. It signifies authority.
- **Bright Cyan (#00B5E2):** Used for interactive highlights, progress indicators, and secondary icons.
- **Orange Accent (#F58220):** Reserved for urgent status indicators, notifications, and "Attention" calls-to-action.

### Neutral & Backgrounds
- **Light Mode:** Uses a "Soft Gray" background (#F8FAFC) to differentiate from "Pure White" (#FFFFFF) cards, creating a layered effect.
- **Dark Mode:** A sophisticated "Midnight" scheme using #0F172A for deep backgrounds and #1E293B for elevated surfaces, maintaining high contrast for readability.

## Typography

The typography system utilizes **Inter** for its exceptional legibility in data-dense environments.

- **Headlines:** Use Bold (700) weights with slight negative letter-spacing for a modern, compact "editorial" look.
- **Body:** Standardized at 16px for optimal reading comfort. 
- **Labels:** Use Semi-Bold (600) for UI controls to ensure they are distinguishable from content.
- **Scale:** On mobile devices, large headlines scale down to prevent excessive wrapping while maintaining hierarchy.

## Layout & Spacing

This design system employs a **Fluid Grid** model based on a 12-column system for desktop and a 4-column system for mobile.

- **Spacing Rhythm:** An 8px base unit is used for all internal padding and margins.
- **Whitespace:** Elements are given significant breathing room (High Whitespace) to maintain a premium feel. Layouts should favor large vertical gaps between distinct functional sections.
- **Reflow:** On mobile, side-by-side cards (like the Login options) stack vertically. Container margins shrink from 40px (desktop) to 16px (mobile).

## Elevation & Depth

Visual hierarchy is established through a combination of **Ambient Shadows** and **Glassmorphism**.

- **Surface Tiering:** Cards use a very soft, diffused shadow (0px 10px 30px rgba(0,0,0,0.05)) to appear lifted from the soft-gray background.
- **Glassmorphism:** Navigation bars and modal backdrops utilize a "Backdrop Blur" (12px to 20px) with a semi-transparent white (80% opacity) or dark (70% opacity) fill.
- **Interactions:** Hover states on interactive cards should increase the shadow spread and slightly scale the element (1.02x) to provide tactile feedback.

## Shapes

The shape language is defined by "Extra Large" corner radii to soften the corporate tone.

- **Primary Components:** Cards, input fields, and large buttons use a **20px (1.25rem)** border radius.
- **Small Elements:** Chips, tags, and checkboxes use a smaller **8px (0.5rem)** radius for better structural definition.
- **Iconography:** Icons should feature rounded caps and corners to align with the container aesthetics.

## Components

### Buttons
- **Primary:** Deep Blue background, white text, 20px radius. High-contrast and substantial padding (16px 32px).
- **Secondary:** Transparent background with a Cyan border and Cyan text.
- **Ghost:** No background/border, used for "Cancel" or low-priority actions.

### Cards
- **Base Style:** White background (Dark Mode: #1E293B), 20px radius, soft ambient shadow.
- **Header:** Cards should include a subtle 1px border at the bottom of the header section (#E2E8F0).

### Input Fields
- **Design:** Large 20px radius, 1px border (#CBD5E1), and a subtle background tint when focused. Labels should always sit above the input field for maximum clarity.

### Chips & Tags
- **Status Tags:** Use light-tinted backgrounds of the semantic color (e.g., Light Orange background for "Pending") with dark text for accessibility.

### Glassmorphic Sidebar
- The navigation sidebar should use a semi-transparent blur effect to allow background colors to peek through, maintaining a sense of space.