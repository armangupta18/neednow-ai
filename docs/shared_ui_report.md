# Shared UI Components Report — NeedNow AI Frontend

## Summary

7 production-ready shared components created in `src/components/shared/`. All TypeScript, fully typed props, responsive, accessible.

**TypeScript check: ✅ Zero errors**

---

## Components

| Component | File | Props | Description |
|-----------|------|-------|-------------|
| **Navbar** | `Navbar.tsx` | `brand`, `items[]`, `actionLabel`, `actionHref`, `actionVariant` | Sticky navigation with active state, brand logo, configurable CTA |
| **Footer** | `Footer.tsx` | `brand`, `links[]`, `attribution` | Responsive footer with nav links and branding |
| **PageContainer** | `PageContainer.tsx` | `maxWidth`, `padded`, `className`, `children` | Centered content wrapper with 5 width variants |
| **Section** | `Section.tsx` | `title`, `subtitle`, `variant`, `centered`, `className`, `children` | Page section with optional header and 3 background variants |
| **LoadingSpinner** | `LoadingSpinner.tsx` | `size`, `color`, `label`, `showLabel`, `className` | Animated spinner with 5 sizes, 3 colors, a11y label |
| **ErrorState** | `ErrorState.tsx` | `title`, `message`, `onRetry`, `retryLabel`, `compact`, `className` | Error display with retry button, compact/full variants |
| **EmptyState** | `EmptyState.tsx` | `icon`, `title`, `description`, `actionLabel`, `onAction`, `compact` | Empty content placeholder with optional CTA |

---

## Props Detail

### Navbar
```typescript
interface NavbarProps {
  brand?: string;                        // Default: "NeedNow AI"
  items: NavItem[];                      // { label, href, icon? }
  actionLabel?: string;                  // CTA button text
  actionHref?: string;                   // CTA button link
  actionVariant?: "primary" | "danger";  // CTA color
}
```

### PageContainer
```typescript
interface PageContainerProps {
  children: ReactNode;
  maxWidth?: "sm" | "md" | "lg" | "xl" | "full";  // Default: "lg"
  padded?: boolean;                                  // Default: true
  className?: string;
}
```

### Section
```typescript
interface SectionProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  variant?: "default" | "muted" | "dark";  // Background style
  centered?: boolean;
  className?: string;
}
```

### LoadingSpinner
```typescript
interface LoadingSpinnerProps {
  size?: "xs" | "sm" | "md" | "lg" | "xl";    // Default: "md"
  color?: "default" | "primary" | "white";      // Default: "default"
  label?: string;                               // a11y label
  showLabel?: boolean;                          // Show text below
}
```

### ErrorState / EmptyState
```typescript
// Both support:
compact?: boolean;  // Inline (small) vs full-page (large) variant
```

---

## Usage Examples

```tsx
import { PageContainer, Section, LoadingSpinner, ErrorState, EmptyState } from "@/components/shared";

// Page layout
<PageContainer maxWidth="md">
  <Section title="Products" subtitle="Your recommendations" variant="muted" centered>
    {products.length === 0 ? (
      <EmptyState title="No products yet" description="Start a conversation" icon="🛒" />
    ) : (
      <ProductGrid products={products} />
    )}
  </Section>
</PageContainer>

// Loading state
<LoadingSpinner size="lg" color="primary" showLabel label="Finding products..." />

// Error state
<ErrorState message="Failed to load cart" onRetry={refetch} compact />
```

---

## Barrel Export

```typescript
// src/components/shared/index.ts
export { Navbar, Footer, PageContainer, Section, LoadingSpinner, ErrorState, EmptyState, ErrorBoundary };
```

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| `compact` prop on ErrorState/EmptyState | Reusable in both full-page and inline contexts |
| `variant` prop on Section | Eliminates need for wrapper divs with background classes |
| `maxWidth` enum on PageContainer | Prevents magic strings, ensures consistency |
| a11y `role="status"` on spinner | Screen readers announce loading state |
| `sr-only` label on spinner | Hidden text for accessibility |
| Barrel export via `index.ts` | Single import path for all shared components |
