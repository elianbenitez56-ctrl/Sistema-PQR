---
name: Inapel Corporate Logic
colors:
  surface: '#f9f9ff'
  surface-dim: '#d6dae4'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3fe'
  surface-container: '#eaeef8'
  surface-container-high: '#e5e8f2'
  surface-container-highest: '#dfe2ed'
  on-surface: '#171c23'
  on-surface-variant: '#43474f'
  inverse-surface: '#2c3138'
  inverse-on-surface: '#edf0fb'
  outline: '#737780'
  outline-variant: '#c3c6d1'
  surface-tint: '#485f84'
  primary: '#001e40'
  on-primary: '#ffffff'
  primary-container: '#003366'
  on-primary-container: '#859dc5'
  inverse-primary: '#afc8f2'
  secondary: '#1f5eac'
  on-secondary: '#ffffff'
  secondary-container: '#78acff'
  on-secondary-container: '#003f7e'
  tertiary: '#171f24'
  on-tertiary: '#ffffff'
  tertiary-container: '#2c3439'
  on-tertiary-container: '#949ca3'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d5e3ff'
  primary-fixed-dim: '#afc8f2'
  on-primary-fixed: '#001b3b'
  on-primary-fixed-variant: '#2f476b'
  secondary-fixed: '#d6e3ff'
  secondary-fixed-dim: '#a9c7ff'
  on-secondary-fixed: '#001b3d'
  on-secondary-fixed-variant: '#00468b'
  tertiary-fixed: '#dbe4ea'
  tertiary-fixed-dim: '#bfc8ce'
  on-tertiary-fixed: '#151d22'
  on-tertiary-fixed-variant: '#40484d'
  background: '#f9f9ff'
  on-background: '#171c23'
  surface-variant: '#dfe2ed'
  surface-ice: '#f8f9ff'
  status-error: '#ba1a1a'
  status-success: '#22c55e'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.4'
  title-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: '1.5'
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.6'
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1.0'
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: '1.0'
  micro-tag:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: '400'
    lineHeight: '1.0'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  xs: 4px
  base: 8px
  sm: 12px
  md: 24px
  lg: 32px
  xl: 48px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
---

## Brand & Style

The brand identity is rooted in **Corporate Modernism**, emphasizing reliability, systematic efficiency, and institutional trust. It is designed for high-utility administrative environments where clarity and data integrity are paramount.

The visual language balances a deep, authoritative navy primary with a bright, tech-forward azure secondary. The style utilizes a "Functional Layering" approach—combining Material 3 color logic with crisp, high-precision borders and subtle ambient shadows to create a workspace that feels organized and professional without being visually fatiguing.

## Colors

The palette is built on a foundation of **Deep Navy (#001E40)** to establish authority. This is complemented by an **Action Blue (#1F5EAC)** used for interactive elements and highlights. 

- **Surfaces:** We use a cold-tinted "Ice" white (#F8F9FF) for backgrounds to reduce eye strain compared to pure white, while keeping the interface feeling fresh and modern.
- **Containers:** Tonal variants of the primary and secondary colors are used to denote hierarchy. The `primary-container` acts as a bold header background, while `secondary-container` highlights active navigation states.
- **Feedback:** Standardized semantic colors (Red for errors/required, Green for positive trends) are used sparingly to maintain the professional aesthetic.

## Typography

The system exclusively uses **Inter** to ensure maximum legibility and a neutral, utilitarian tone. 

The type hierarchy relies on heavy weight shifts (700 for displays, 600 for titles) rather than large size jumps to maintain a compact, data-dense layout. All uppercase labels utilize a slight letter-spacing (0.05em) to improve readability in form contexts. For mobile devices, `display-lg` should scale down to `headline-md` (24px) to avoid awkward text wrapping in hero banners.

## Layout & Spacing

The layout follows a **Hybrid Grid System**:
- **Desktop:** A fixed 256px Sidebar is anchored to the left. The remaining content uses a fluid width with `margin-desktop (40px)` horizontal padding and a `24px` gutter between cards.
- **Grid Model:** Form sections utilize a 2-column grid on desktop that collapses to 1-column on tablet and mobile.
- **Rhythm:** An 8px linear scale (base-8) governs all padding and margins. Vertical rhythm within cards is strictly managed using `md (24px)` between sections and `base (8px)` between labels and inputs.

## Elevation & Depth

Hierarchy is established through **Tonal Layering** and **Soft Ambient Shadows**.

1.  **Level 0 (Background):** `surface-ice` (#F8F9FF).
2.  **Level 1 (Cards/Containers):** `surface-container-lowest` (#FFFFFF) with a very soft shadow: `0px 4px 20px rgba(0,0,0,0.05)`.
3.  **Level 2 (Active States/Modals):** Standard `shadow-md` or `shadow-lg` to indicate temporary interaction.
4.  **Borders:** All containers use a low-contrast outline (`outline-variant/30`) to define boundaries without adding visual weight.

## Shapes

The design uses a **Soft Geometry** approach. Standard components like inputs and buttons utilize a 0.25rem (4px) base radius. 

Cards and major hero elements use `rounded-xl` (0.75rem / 12px) to provide a modern, approachable feel. Navigation elements and profile avatars use a "Pill-shaped" full rounding to distinguish them as high-level interactive touchpoints.

## Components

- **Buttons:** Primary buttons are solid `primary` with `on-primary` text. Ghost/Outline buttons use `outline` color for borders. All buttons feature a subtle 0.2s transition and a 95% scale-down on click.
- **Input Fields:** Utilize `surface-bright` backgrounds with `outline-variant` borders. Focus states must trigger a `secondary` color border and a 4px soft glow (`rgba(31, 94, 172, 0.1)`).
- **Navigation (SideNav):** Active states use `secondary-container` with `on-secondary-container` text and a right-side rounded-full shape to create a "tab" effect.
- **Cards:** Must have a distinct header section using `surface-container-low` to separate descriptive metadata from functional form content.
- **Icons:** Material Symbols Outlined, 24px standard. For decorative use in headers, they should be encased in a 40px square `rounded-lg` container with a 10% opacity version of the brand color.