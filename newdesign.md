# MASTER DESIGN PROMPT — NeuroCare AI / Rootly-Inspired Premium Website

You are a principal product designer, creative director, frontend architect, and design systems engineer.

Your task is to transform the existing NeuroCare AI project into a highly polished, professional product website using the visual sophistication, page composition, product storytelling, typography, and interaction quality of https://rootly.com/ as a reference.

This must be a substantial redesign, not a color change or a small CSS refinement.

The result should have the confidence and polish of a leading modern software product website, while maintaining an original NeuroCare AI identity.

IMPORTANT: Study the current reference website directly before implementation. Do not rely solely on this prompt or screenshots from previous versions. Reproduce the general design principles and interaction patterns, not Rootly's exact branding, proprietary illustrations, logos, copy, source code, or complete page layouts.

# 1. PHASE ZERO: RESEARCH BEFORE IMPLEMENTATION

Inspect the following public reference pages:

- Homepage: https://rootly.com/
- Pricing: https://rootly.com/pricing
- Integrations: https://rootly.com/integrations
- Insights: https://rootly.com/insights
- Catalog: https://rootly.com/catalog
- Enterprise: https://rootly.com/enterprise

Use a browser or web inspection capability if available.

For each page, examine:

1. Navigation structure, dimensions, alignment, and menu behavior.
2. Content width, margins, vertical spacing, and section rhythm.
3. Heading sizes, line heights, font weights, and line breaks.
4. Body typography and muted text hierarchy.
5. Background colors, borders, card surfaces, buttons, and corner radii.
6. Hero layout, calls to action, and product visual composition.
7. How sections transition between different background colors.
8. How product interfaces are incorporated into marketing sections.
9. Hover, focus, dropdown, accordion, and responsive behaviors.
10. Footer structure and the overall length and rhythm of each page.

Do not assume every page uses identical layouts. Identify the common design system and the specific patterns appropriate to each type of content.

If a page, interaction, or visual asset cannot be inspected, record that limitation rather than inventing details.

Inspect the existing NeuroCare AI repository before making changes. Produce a concise internal implementation plan, then continue directly to implementation.

# 2. THE CORE DESIGN PHILOSOPHY

The visual direction should be:

- Minimal, but not empty.
- Editorial, but still clearly a software product.
- Elegant, but highly readable.
- Technically sophisticated, but approachable.
- Rich in visual hierarchy, not rich in decorative effects.
- Consistent without making every section look identical.

Prioritize typography, composition, whitespace, alignment, contrast, and carefully presented product visuals.

Avoid generic AI SaaS aesthetics, excessive gradients, purple glow effects, glassmorphism, random floating cards, repetitive three-card grids, stock photography, decorative blobs, and unnecessary 3D graphics.

Do not produce a generic healthcare dashboard.

# 3. VISUAL TOKENS AND DESIGN SYSTEM

Study Rootly's current appearance and define an original NeuroCare AI design system that captures the reference's visual character.

Use the following approximate starting palette as a research hypothesis, not a claim about official Rootly specifications:

- Page background: #FBFAFF
- Primary text: #100F12
- Surface: #FFFFFF
- Secondary text: #65646E
- Secondary border: #D9D3E5
- Pale lavender surface: #EBE5FF
- Muted violet accent: #8D6FDE
- Deep violet accent: #4A3E8A
- Optional soft rose accent: #F5BBC3

Verify the reference's actual current appearance in the browser, then tune the palette for NeuroCare AI rather than blindly copying every value.

Use accent colors sparingly. The website should remain predominantly light, with strong dark text, restrained accents, and clear surfaces.

Create a single source of truth for design tokens using CSS custom properties and the project's existing styling conventions.

Define tokens for:

- Colors and semantic color roles.
- Typography families, sizes, weights, and line heights.
- Content widths and page gutters.
- Section spacing.
- Border widths and colors.
- Corner radii.
- Shadows and elevation.
- Button and input heights.
- Focus indicators.
- Transition durations and easing.
- Responsive breakpoints.

Typography is especially important. Inspect the reference's headline and body typography, then choose appropriately licensed, technically compatible fonts that achieve a similar refined appearance. Do not copy or redistribute a proprietary font without permission.

Use a distinctive display face and a highly readable interface sans-serif where appropriate. Establish a clear scale from hero heading to section heading, body, labels, and metadata.

Do not rely on arbitrary font sizes and spacing values across individual pages.

# 4. NAVIGATION AND GLOBAL PAGE FRAME

Create a consistent global header and footer shared across all public pages.

The header should have:

- The existing NeuroCare AI wordmark or a refined version of its current identity.
- Simple navigation to real pages and sections.
- One clear primary call to action.
- Carefully designed hover and keyboard-focus states.
- A responsive mobile navigation.

Use a compact, deliberate layout with carefully balanced logo, navigation, and action placement.

Study Rootly's navigation information hierarchy, but do not reproduce its complete menu tree because NeuroCare AI has different needs.

There must be no sign-in, sign-up, account menu, subscription flow, or private dashboard.

The footer should contain only real links and concise project information.

# 5. HOMEPAGE: PRODUCT-LED STORYTELLING

Create a compelling homepage using the following content architecture, adapting section order and composition to the real project.

## Hero

Use a large, confident headline, concise supporting text, and two clear actions.

The content should explain that NeuroCare AI is an educational project demonstrating diabetes-related classification using an artificial neural network.

The primary action must open the actual prediction experience.

The secondary action must lead to the real model methodology or explanation.

Compose a visually distinctive hero using an original scientific diagram, an actual application screenshot, or a real visualization of the ANN architecture.

Avoid placing numerous unrelated cards beside the headline.

If using a product preview, render genuine UI components and actual project information. Never fabricate a prediction, patient, chart, model statistic, or activity feed to make the preview appear populated.

## Model introduction

Explain the actual ANN and the role of its supported input features.

Use a visually strong text-and-visual composition, taking inspiration from Rootly's product-focused storytelling sections.

Build an original diagram from the actual model architecture where the information is available.

## How the prediction works

Describe the actual user journey in a clear sequence.

Use concise steps, meaningful visual connections, and good spacing rather than repeating generic feature cards.

Do not describe functionality the application does not implement.

## Evaluation and methodology

Explain the actual dataset, preprocessing, training approach, and available evaluation metrics.

Use real saved results. Do not create sample data to fill charts or add unsupported claims about accuracy.

Provide access to further explanation without making the homepage excessively technical.

## Project identity

Explain the project's genuine educational and open-source purpose.

Use the actual repository URL and verified license information only when available.

Do not invent endorsements, customer logos, testimonials, user numbers, institutional affiliations, or scientific credentials.

## Final call to action

Finish with a clear invitation to explore the actual prediction experience, followed by a refined footer.

# 6. PRODUCT VISUALS: SHOW THE REAL APPLICATION

A key part of the reference's presentation is its use of product interfaces as visual storytelling.

Apply this principle to NeuroCare AI.

Possible visuals include:

- The actual prediction form.
- A real ANN architecture diagram generated from the model definition.
- Actual saved evaluation charts.
- The real prediction result component.
- A clear preprocessing or inference flow based on the implemented code.

Do not turn the homepage into a dashboard gallery.

Each visual should answer a question or explain a feature.

Use subtle framing, accurate proportions, crisp typography, restrained borders, and consistent spacing.

Do not insert fake users, fictional records, invented notifications, placeholder activity feeds, or hardcoded metrics.

If a real visual cannot be produced from existing project information, omit it or create a clearly illustrative technical diagram that does not pretend to show real data.

# 7. PREDICTION PAGE

Redesign the existing prediction experience so it feels like a natural extension of the marketing website.

The form must be simple, spacious, accessible, and easy to understand.

- Use the exact input schema required by the existing backend.
- Preserve valid options, data types, required fields, and feature meanings.
- Group related fields logically.
- Use concise helper text.
- Keep the form width comfortable and avoid unnecessary sidebars.
- Use a multi-step form only if it genuinely improves the experience.
- Make progress, validation, loading, submission, and error states consistent with the design system.
- Display the actual backend result.
- Provide a clear way to try again.
- Keep the educational-use disclaimer visible.

Do not remove model features merely to reduce visual complexity.

Do not imply that the result is a medical diagnosis or a clinically validated prediction.

# 8. CUSTOM INTERACTIVE COMPONENTS

Inspect existing dependencies and components. Reuse good implementations and refactor inconsistent ones.

Build a coherent shared component library, including appropriate versions of:

- SiteHeader
- SiteFooter
- Container
- Section
- SectionHeading
- Button
- TextLink
- Badge
- FeatureSection
- ProductPreview
- NeuralNetworkDiagram
- MetricDisplay
- FormField
- TextInput
- CustomSelect
- FormError
- PredictionResult
- Accordion

These are examples. Use sensible component boundaries instead of creating a component for every small wrapper.

All interactive controls must be styled components, not browser-default controls.

## Custom select

Replace the native opened dropdown with an accessible custom select using a compatible maintained primitive where appropriate.

Support keyboard navigation, Enter, Escape, arrow keys, focus management, screen readers, and touch interaction.

Style the trigger, menu, options, hover state, selected state, disabled state, and error state consistently.

## Focus states

The current application has duplicated outlines around active controls. Fix the actual conflicting styles rather than adding more overrides.

Inspect global CSS, Tailwind ring classes, outlines, shadows, and library defaults.

Implement one deliberate visible focus indicator per control. Preserve keyboard accessibility.

## Buttons and forms

Ensure shared buttons and inputs have consistent typography, dimensions, spacing, colors, transitions, and states across every page.

Avoid different styles for visually identical components.

# 9. SECONDARY PAGES

Apply the same design system to all existing public routes.

Where the existing application supports separate model, methodology, prediction, or about pages, redesign them consistently.

Do not create a pricing page because Rootly has one. NeuroCare AI has no real pricing model.

Do not create a fake integrations directory, activity dashboard, analytics product, or enterprise feature page.

Instead, adapt the reference's content organization to genuine NeuroCare AI information.

Every route must have a clear purpose and real content.

# 10. MOTION AND RESPONSIVENESS

Use subtle, high-quality transitions for navigation, dropdowns, buttons, accordions, and relevant section entrances.

Respect prefers-reduced-motion.

Use CSS and SVG for most visuals. Do not add Three.js or a large animation dependency unless it offers a real benefit.

Ensure the site works at mobile, tablet, laptop, and wide-desktop sizes.

Check content widths, typography scaling, navigation, dropdown positioning, form usability, and overflow.

# 11. TECHNICAL PRESERVATION AND REAL DATA

Keep the existing project architecture wherever possible:

- React, Vite, TypeScript, and existing styling tools.
- FastAPI and existing API contracts.
- PostgreSQL and current migrations.
- TensorFlow/Keras model and preprocessing artifacts.

Do not replace the model, retrain it unnecessarily, change API response shapes without a clear reason, or rewrite the backend for visual purposes.

Only display verified project data.

Never introduce mock records, fake metrics, fake chart series, invented patient examples, or fabricated system states into the actual application.

If data is unavailable, omit the section or show a genuine unavailable state.

Verify that prediction history cannot expose other visitors' inputs or results.

# 12. IMPLEMENTATION AND VALIDATION

Implement the complete redesign in the existing repository.

Before finishing:

- Run the available frontend lint, type-check, and production-build commands.
- Run backend tests if backend code changes.
- Test every navigation link and primary action.
- Verify the actual prediction request and response flow.
- Test custom selects, keyboard navigation, focus indicators, and form validation.
- Test responsive layouts.
- Check for console errors if browser-testing tools are available.
- Verify that every displayed metric comes from genuine project data.
- Fix discovered problems.

Do not claim that a check passed unless it was actually executed.

At completion, report the design-system changes, components created, pages redesigned, real data used, test results, and any remaining limitations.

FINAL STANDARD:

The result should demonstrate the visual discipline and product storytelling of a premium modern software website. It must feel deliberately designed rather than assembled from generic templates.

Keep NeuroCare AI's identity, use only genuine project information, preserve the working application, and prioritize visual quality, usability, accessibility, and consistency.