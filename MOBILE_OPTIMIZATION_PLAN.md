# Mobile Responsiveness Optimization Plan

## 1. Objective
Ensure the AI Body Scan SaaS landing page is as elegant and functional on mobile devices (iOS/Android) as it is on high-end desktop monitors, while maintaining the "gig elegant" luxury feel.

## 2. Technical Targets
- **Breakpoints**: 1200px (Desktop), 1000px (Laptop/Tablet), 768px (Mobile Large), 480px (Mobile Small).
- **Typography**: Fluid scaling of the new 48px/52px headers.
- **Layout**: Transition from horizontal splits (50/50) to vertical stacks.

## 3. Implementation Strategy

### Phase 1: Global Spacing & Typography
- [ ] Reduce section horizontal padding from `120px` to `20px` on screens below 1000px.
- [ ] Implement media queries for headers:
    - Desktop: `48px` / `52px`
    - Tablet: `36px` / `40px`
    - Mobile: `28px` / `32px`
- [ ] Scale down card padding from `40px` to `24px` for mobile.

### Phase 2: Hero Section Refactoring
- [ ] Transition `.hero` from fixed `1150px` height to `auto` or `min-content` on mobile to avoid excessive white space.
- [ ] Center-align hero text and mannequin.
- [ ] Convert `heroCta` from `position: absolute` to `position: relative` on mobile. This ensures it follows the document flow and doesn't overlap section content unpredictably.

### Phase 3: Grid & Card Stacking
- [ ] Refactor `.row3` and `.row4` to use `grid-template-columns: 1fr` on mobile.
- [ ] Ensure the "Step Cards" (Capture -> Scan -> Analyze -> Act) stack vertically with consistent gaps.
- [ ] Adjust the "Wellness" section slider UI to be full-width on small screens.

### Phase 4: Navigation & Interactive Elements
- [ ] Verify the `mobileNavToggle` and ensure the drawer uses the `AppColors.darkNavy` theme.
- [ ] Increase tap targets for all buttons and links to a minimum of `44px`.
- [ ] Ensure the final "Banner" CTA is perfectly centered and legible on narrow screens.

## 4. Verification Plan
- [ ] Test on Chrome DevTools (iPhone 14, Pixel 7, iPad Air).
- [ ] Verify no horizontal scrollbars.
- [ ] Ensure all text remains readable (no clipping).
- [ ] Confirm "Gig Elegant" CTA card remains fully visible and interactive.
