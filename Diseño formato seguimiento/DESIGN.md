---
name: Institutional Quality Standard
colors:
  surface: '#f7fafc'
  surface-dim: '#d7dadc'
  surface-bright: '#f7fafc'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f4f6'
  surface-container: '#ebeef0'
  surface-container-high: '#e5e9eb'
  surface-container-highest: '#e0e3e5'
  on-surface: '#181c1e'
  on-surface-variant: '#43474f'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eef1f3'
  outline: '#737780'
  outline-variant: '#c3c6d1'
  surface-tint: '#3a5f94'
  primary: '#001e40'
  on-primary: '#ffffff'
  primary-container: '#003366'
  on-primary-container: '#799dd6'
  inverse-primary: '#a7c8ff'
  secondary: '#175ead'
  on-secondary: '#ffffff'
  secondary-container: '#72aafe'
  on-secondary-container: '#003d79'
  tertiary: '#181f23'
  on-tertiary: '#ffffff'
  tertiary-container: '#2d3438'
  on-tertiary-container: '#959ca1'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d5e3ff'
  primary-fixed-dim: '#a7c8ff'
  on-primary-fixed: '#001b3c'
  on-primary-fixed-variant: '#1f477b'
  secondary-fixed: '#d5e3ff'
  secondary-fixed-dim: '#a8c8ff'
  on-secondary-fixed: '#001b3c'
  on-secondary-fixed-variant: '#004689'
  tertiary-fixed: '#dce3e8'
  tertiary-fixed-dim: '#c0c7cc'
  on-tertiary-fixed: '#161d20'
  on-tertiary-fixed-variant: '#41484c'
  background: '#f7fafc'
  on-background: '#181c1e'
  surface-variant: '#e0e3e5'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  section-title:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '700'
    lineHeight: 20px
  body-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-caps:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.05em
  data-mono:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  page-margin: 48px
  section-gap: 24px
  input-padding: 8px 12px
  table-cell-padding: 10px 16px
  column-gutter: 16px
---

## Brand & Style

The design system for **INAPEL** is built upon the principles of **Institutional Modernism** and **Documentary Precision**. It is specifically tailored for a Quality Management System (SGC) environment where clarity, authority, and accountability are paramount.

The brand personality is **reliable, meticulous, and professional**. It avoids decorative flourishes in favor of structural integrity and data density. The target audience includes internal quality auditors, factory managers, and corporate stakeholders who require "at-a-glance" comprehension of complex operational data. 

The aesthetic draws from **Modern Corporate** design, emphasizing:
- **Structural Rigor:** A strict adherence to alignment and information blocks.
- **Utilitarian Clarity:** High legibility and clear categorization.
- **Institutional Weight:** Use of deep blues and deliberate whitespace to signify official status.
- **A4 Optimization:** Ensuring all digital interfaces translate seamlessly to printed ISO-certified documentation.

## Colors

The palette is strictly professional, utilizing a high-contrast ratio to ensure legibility in both digital and printed formats.

- **Institutional Blue (#003366):** Used for primary headers, logos, and critical UI anchors. It represents the "official" voice of the company.
- **Medium Blue (#0055A4):** Used for interactive elements, secondary accents, and section identifiers.
- **Surface Grays (#F4F7F9, #E1E8ED):** These are the workhorses of the system. They are used for alternating table rows (zebra striping), background containers for data blocks, and subtle divisions that don't require heavy lines.
- **Pure White (#FFFFFF):** The primary background color to ensure maximum ink efficiency and clarity for A4 printing.

## Typography

The choice of **Inter** provides a highly functional, geometric neo-grotesque style that excels in small-scale data tables.

- **Hierarchy:** Use `headline-xl` for document titles (e.g., "INFORME DE GESTIÓN"). 
- **Sectioning:** Sections are marked by `section-title` in Institutional Blue, often accompanied by a vertical accent bar to the left.
- **Data Labels:** Small uppercase labels (`label-caps`) in a medium gray help distinguish field names from the actual data values without competing for attention.
- **Readability:** Body copy is set with generous line heights to accommodate long-form descriptions or investigation notes.

## Layout & Spacing

This design system uses a **Fixed Grid** model optimized for A4 vertical (8.27" x 11.69") proportions.

- **The Document Grid:** A 12-column system is used, but content is typically grouped into 2, 3, or 4 equal columns for data entry forms.
- **Rhythm:** A vertical 4px baseline grid ensures consistent spacing between labels and fields.
- **Margins:** External page margins are set at 48px to account for physical binder punching and printer "safe zones."
- **Internal Density:** Spacing is compact to maximize the information density of single-page reports.

## Elevation & Depth

To maintain a "document" feel, the system avoids depth effects like shadows or blurs. Hierarchy is instead achieved through:

- **Tonal Layering:** Containers use the `neutral` gray (#F4F7F9) to separate different data modules.
- **Low-Contrast Outlines:** Fields and tables use 1px solid borders in `#D1D9E0`. 
- **Flat Accents:** Depth is implied via color blocks—such as deep blue headers on tables—rather than physical-world metaphors.
- **Vertical Bars:** A 4px thick solid vertical line in Institutional Blue is used to lead the eye to the start of a new major section.

## Shapes

The shape language is **Soft (0.25rem)**. 

While the system is largely rectangular to reflect the "grid" nature of paper forms, a subtle corner radius is applied to data containers and input fields. This softens the industrial tone just enough to feel modern without sacrificing the "official document" gravity. Tags and status chips use the same subtle rounding; pill shapes are avoided to maintain a serious, institutional character.

## Components

### Data Tables
Tables must have a header row with a background of `primary_color_hex` (#003366) and white text. Row backgrounds should alternate between `white` and `neutral` (#F4F7F9) for readability.

### Input Fields & Blocks
Fields are represented as light gray boxes with a 1px border. Labels sit directly above the field in `label-caps`. For "View-only" documents, the field background remains white with a subtle border to maintain the form-like structure.

### Status Indicators
Small circular dots are used alongside text to indicate priority or status (e.g., Orange for "Pending", Green for "Closed"). These should be placed within a small gray container for better grouping.

### Progress & Header
The header must contain the INAPEL logo on the left and document metadata (Date of generation, ID code) on the right, separated by a horizontal rule in Institutional Blue.

### Buttons (System Actions)
Primary buttons use Institutional Blue with white text. Secondary buttons use a white background with a blue border. In a document-focused UI, these should be placed at the top-right or bottom-right, outside the main "paper" area if possible.