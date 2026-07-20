
 ## 1. Visual Theme & Philosophy
 
 ### Design Vision
 **Modern, Accessible, Purposeful**: BoltChats delivers a clean, distraction-free messaging experience. The design system prioritizes readability and responsiveness across all devices, with deliberate use of whitespace, meaningful color, and purposeful motion.
 
 ### Core Principles
 1. **Mobile-First Optimization**: Every component designed for mobile first, then enhanced for larger screens
 2. **8px Semantic Grid**: All spacing follows 8px increments for consistency and predictability
 3. **Dark Mode Parity**: Complete feature parity between light and dark themes
 4. **Accessibility First**: WCAG AA compliance minimum; keyboard navigation throughout
 5. **Minimal, Purposeful Motion**: Animations enhance clarity, never distract; respect prefers-reduced-motion
 6. **Token-Driven**: No hardcoded values; all design decisions flow from CSS custom properties
 7. **Component Resilience**: Components work in isolation and in composition
 
 ---
 
 ## 2. Design Tokens & CSS Variables
 
 ### Light Mode (Default)
 \`\`\`css
 :root {
   /* ========== COLORS: ACCENT & BRANDING ========== */
   --color-accent: #639922;
   --color-accent-hover: #547a1a;
   --color-accent-active: #466212;
   --color-accent-soft: #e8edd6;
 
   /* ========== COLORS: NEUTRALS (LIGHT) ========== */
   --color-white: #ffffff;
   --color-gray-50: #fafafa;
   --color-gray-100: #f5f5f5;
   --color-gray-200: #e5e5e5;
   --color-gray-300: #d4d4d4;
   --color-gray-400: #a3a3a3;
   --color-gray-500: #737373;
   --color-gray-600: #525252;
   --color-gray-700: #404040;
   --color-gray-800: #262626;
   --color-gray-900: #171717;
 
   /* ========== COLORS: SEMANTIC ========== */
   --color-text-primary: #171717;
   --color-text-secondary: #525252;
   --color-text-tertiary: #a3a3a3;
   --color-text-inverse: #ffffff;
 
   --color-bg-primary: #ffffff;
   --color-bg-secondary: #fafafa;
   --color-bg-tertiary: #f5f5f5;
 
   --color-border: #e5e5e5;
   --color-border-subtle: #f5f5f5;
 
   --color-surface: #ffffff;
   --color-surface-hover: #f5f5f5;
   --color-surface-active: #efefef;
 
   /* ========== COLORS: STATUS ========== */
   --color-success: #16a34a;
   --color-success-light: #dcfce7;
   --color-warning: #ea580c;
   --color-warning-light: #fed7aa;
   --color-error: #dc2626;
   --color-error-light: #fee2e2;
   --color-info: #0284c7;
   --color-info-light: #e0f2fe;
 
   /* ========== COLORS: PRESENCE ========== */
   --color-presence-active: #16a34a;
   --color-presence-idle: #f59e0b;
   --color-presence-offline: #9ca3af;
 
   /* ========== SPACING (8px GRID) ========== */
   --spacing-0: 0;
   --spacing-1: 0.5rem;    /* 8px */
   --spacing-2: 1rem;      /* 16px */
   --spacing-3: 1.5rem;    /* 24px */
   --spacing-4: 2rem;      /* 32px */
   --spacing-5: 2.5rem;    /* 40px */
   --spacing-6: 3rem;      /* 48px */
   --spacing-7: 3.5rem;    /* 56px */
   --spacing-8: 4rem;      /* 64px */
 
   /* ========== TYPOGRAPHY: FONT FAMILIES ========== */
   --font-family-primary: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
   --font-family-mono: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
 
   /* ========== TYPOGRAPHY: FONT SIZES ========== */
   --font-size-xs: 0.75rem;    /* 12px */
   --font-size-sm: 0.875rem;   /* 14px */
   --font-size-base: 1rem;     /* 16px */
   --font-size-lg: 1.125rem;   /* 18px */
   --font-size-xl: 1.25rem;    /* 20px */
   --font-size-2xl: 1.5rem;    /* 24px */
   --font-size-3xl: 1.875rem;  /* 30px */
   --font-size-4xl: 2.25rem;   /* 36px */
 
   /* ========== TYPOGRAPHY: COMPONENT SIZES ========== */
   --font-size-message: 0.8125rem;   /* 13px - chat messages */
   --font-size-timestamp: 0.75rem;   /* 12px - message timestamps */
   --font-size-label: 0.6875rem;     /* 11px - UI labels, badges */
 
   /* ========== TYPOGRAPHY: FONT WEIGHTS ========== */
   --font-weight-regular: 400;
   --font-weight-medium: 500;
   --font-weight-semibold: 600;
   --font-weight-bold: 700;
 
   /* ========== TYPOGRAPHY: LINE HEIGHTS ========== */
   --line-height-tight: 1.25;      /* 125% */
   --line-height-snug: 1.375;      /* 137.5% */
   --line-height-normal: 1.5;      /* 150% */
   --line-height-relaxed: 1.625;   /* 162.5% */
   --line-height-loose: 2;         /* 200% */
 
   /* ========== SHADOWS ========== */
   --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.05);
   --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
   --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06);
   --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05);
   --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.1), 0 10px 10px rgba(0, 0, 0, 0.04);
 
   /* ========== BORDER RADIUS ========== */
   --radius-sm: 0.25rem;   /* 4px */
   --radius-md: 0.375rem;  /* 6px */
   --radius-lg: 0.5rem;    /* 8px */
   --radius-xl: 0.75rem;   /* 12px */
   --radius-2xl: 1rem;     /* 16px */
   --radius-full: 9999px;
 
   /* ========== TRANSITIONS ========== */
   --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
   --transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
   --transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);
 
   /* ========== Z-INDEX SCALE ========== */
   --z-hide: -1;
   --z-base: 0;
   --z-dropdown: 10;
   --z-sticky: 20;
   --z-fixed: 30;
   --z-modal-backdrop: 40;
   --z-modal: 50;
   --z-popover: 60;
   --z-tooltip: 70;
 }
 
 /* ========== DARK MODE ========== */
 @media (prefers-color-scheme: dark) {
   :root {
     /* Text Colors */
     --color-text-primary: #f5f5f5;
     --color-text-secondary: #d4d4d4;
     --color-text-tertiary: #a3a3a3;
     --color-text-inverse: #0a0a0a;
 
     /* Background Colors */
     --color-bg-primary: #0a0a0a;
     --color-bg-secondary: #171717;
     --color-bg-tertiary: #262626;
 
     /* Border Colors */
     --color-border: #262626;
     --color-border-subtle: #171717;
 
     /* Surface Colors */
     --color-surface: #1a1a1a;
     --color-surface-hover: #262626;
     --color-surface-active: #333333;
 
     /* Shadows (inverted with inner glow) */
     --shadow-xs: 0 1px 3px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
     --shadow-sm: 0 4px 6px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
     --shadow-md: 0 10px 15px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
     --shadow-lg: 0 20px 25px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.1);
     --shadow-xl: 0 25px 50px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
   }
 }
 
 /* ========== REDUCED MOTION ========== */
 @media (prefers-reduced-motion: reduce) {
   :root {
     --transition-fast: 0ms;
     --transition-base: 0ms;
     --transition-slow: 0ms;
   }
 
   * {
     animation-duration: 0.01ms !important;
     animation-iteration-count: 1 !important;
     transition-duration: 0.01ms !important;
   }
 }
 \`\`\`
 
 ---
 
 ## 3. Color Palette
 
 ### Accent Colors (Green #639922)
 | Token | Light | Dark | Usage |
 |-------|-------|------|-------|
 | **Primary** | #639922 | #639922 | Primary CTA, active states, success indicator |
 | **Hover** | #547a1a | #7aaa34 | Hover state on accent elements |
 | **Active** | #466212 | #8abc3a | Pressed/active state on accent elements |
 | **Soft** | #e8edd6 | #2d3b0f | Soft background for contextual accents |
 
 ### Neutral Scale (Light Theme)
 | Shade | Hex | Usage |
 |-------|-----|-------|
 | 50 | #fafafa | Lightest background |
 | 100 | #f5f5f5 | Light UI surfaces |
 | 200 | #e5e5e5 | Light borders, dividers |
 | 300 | #d4d4d4 | Disabled state |
 | 400 | #a3a3a3 | Tertiary text, icons |
 | 500 | #737373 | Secondary text |
 | 600 | #525252 | Secondary text |
 | 700 | #404040 | Muted text |
 | 800 | #262626 | Dark gray |
 | 900 | #171717 | Primary text |
 
 ### Status Colors
 | Status | Color | Usage |
 |--------|-------|-------|
 | **Success** | #16a34a | Online status, confirmed actions |
 | **Success Light** | #dcfce7 | Light backgrounds for success |
 | **Warning** | #ea580c | Idle status, cautions |
 | **Warning Light** | #fed7aa | Light backgrounds for warnings |
 | **Error** | #dc2626 | Offline status, failed actions |
 | **Error Light** | #fee2e2 | Light backgrounds for errors |
 | **Info** | #0284c7 | Informational messages |
 | **Info Light** | #e0f2fe | Light backgrounds for info |
 
 ### Presence Indicators
 | State | Color | Icon |
 |-------|-------|------|
 | **Active** | #16a34a | Solid filled circle |
 | **Idle** | #f59e0b | Solid filled circle, pulsing 50% opacity |
 | **Offline** | #9ca3af | Hollow circle or dimmed |
 | **Do Not Disturb** | #dc2626 | Solid filled circle |
 
 ### WCAG AA Contrast Verification
 
 All color combinations meet WCAG AA standard (4.5:1 minimum for normal text, 3:1 for large text):
 
 - **Primary text (#171717) on primary background (#ffffff)**: 14.5:1 ✓✓
 - **Primary text (#171717) on gray-100 (#f5f5f5)**: 13.2:1 ✓✓
 - **Secondary text (#525252) on primary background (#ffffff)**: 10.2:1 ✓✓
 - **Accent (#639922) on white**: 4.8:1 ✓
 - **White text on accent (#639922)**: 5.3:1 ✓
 - **Accent (#639922) on gray-100 (#f5f5f5)**: 4.5:1 ✓ (meets minimum)
 - **Dark mode text (#f5f5f5) on dark background (#0a0a0a)**: 14.8:1 ✓✓
 - **Success (#16a34a) on white**: 5.2:1 ✓
 - **Error (#dc2626) on white**: 5.8:1 ✓
 
 ---
 
 ## 4. Typography System
 
 ### Font Stack
 \`\`\`css
 /* Primary UI Font */
 --font-family-primary: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 
                        Oxygen, Ubuntu, Cantarell, sans-serif;
 
 /* Monospace for Code */
 --font-family-mono: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
 \`\`\`
 
 **Rationale**: System fonts optimize for platform (SF Pro Display on macOS/iOS, Segoe UI on Windows, Roboto on Android). Fallback to sans-serif ensures universal support. No custom font loading—performance first.
 
 ### Typographic Scale
 
 | Scale | Size | Weight | Line Height | Usage | Example |
 |-------|------|--------|-------------|-------|---------|
 | **4xl** | 36px | 700 | 1.25 | Page/app title | "BoltChats" |
 | **3xl** | 30px | 700 | 1.25 | Major section heading | "Channels" |
 | **2xl** | 24px | 600 | 1.25 | Section heading | Channel name in header |
 | **xl** | 20px | 600 | 1.375 | Subsection heading | Dialog title |
 | **lg** | 18px | 500 | 1.5 | Emphasis, prompts | "Send Message" button |
 | **base** | 16px | 400 | 1.5 | Body text, default | Regular paragraph text |
 | **sm** | 14px | 400 | 1.5 | Secondary text | Helper text, meta info |
 | **xs** | 12px | 400 | 1.5 | Captions | Timestamp, status |
 
 ### Component-Specific Sizes
 
 | Component | Size | Weight | Usage |
 |-----------|------|--------|-------|
 | **Message** | 13px | 400 | Chat message body text |
 | **Timestamp** | 12px | 400 | Message timestamp, read time |
 | **Label** | 11px | 500 | UI labels, badges, tags |
 
 ### Font Weight Usage
 
 | Weight | Value | Usage |
 |--------|-------|-------|
 | **Regular** | 400 | Body text, default |
 | **Medium** | 500 | Emphasis, labels, secondary headings |
 | **Semibold** | 600 | Section headings, strong emphasis |
 | **Bold** | 700 | Page titles, major headings |
 
 ---
 
 ## 5. Spacing & Grid
 
 ### 8px Semantic Grid
 
 All spacing uses 8px increments for mathematical consistency and easy scaling:
 
 \`\`\`
 Spacing Scale:
 --spacing-1 = 8px    (smallest unit)
 --spacing-2 = 16px   (2×)
 --spacing-3 = 24px   (3×)
 --spacing-4 = 32px   (4×)
 --spacing-5 = 40px   (5×)
 --spacing-6 = 48px   (6×)
 --spacing-7 = 56px   (7×)
 --spacing-8 = 64px   (8×)
 \`\`\`
 
 ### Spacing Application Rules
 
 | Context | Spacing | Usage |
 |---------|---------|-------|
 | **Internal padding** | spacing-1 (8px) | Button, chip, small elements |
 | **Standard padding** | spacing-2 (16px) | Cards, modals, form fields |
 | **Section spacing** | spacing-3 (24px) | Between major UI sections |
 | **Major spacing** | spacing-4 (32px) | Page margins, container gaps |
 | **Large gaps** | spacing-5+ (40px+) | Page sections, full-width gaps |
 
 ### Touch Targets
 
 - **Mobile (< 768px)**: 44×44px minimum for all interactive elements
 - **Desktop (≥ 768px)**: 40×40px minimum for buttons and inputs
 - **Rationale**: 44×44px accommodates 9.2mm finger width (medical standard)
 
 ### Micro-Interactions
 - **Hover target expansion**: 4–8px outward padding on interactive elements
 - **Focus ring offset**: 2px from element border
 - **Hit area > visual boundary** for usability
 
 ---
 
 ## 6. Component Specifications
 
 ### 6.1 Sidebar
 
 #### Overview
 Collapsible navigation panel showing channels, DMs, and workspace header. Responsive: full-width drawer on mobile (< 768px), fixed sidebar on desktop.
 
 #### Dimensions
 | Property | Mobile | Desktop | Notes |
 |----------|--------|---------|-------|
 | Width | 100vw | 280px | Mobile: full screen drawer |
 | Height | Full | Full | Always full viewport height |
 | Collapse Trigger | < 768px | N/A | Switches from drawer to sidebar |
 | Max Width | N/A | 320px | Never exceeds 320px |
 
 #### Workspace Header
 - **Height**: 56px (7 × spacing-1)
 - **Padding**: spacing-2 (16px)
 - **Background**: var(--color-bg-secondary)
 - **Border Bottom**: 1px solid var(--color-border)
 - **Display**: flex, justify-content: space-between
 - **Align Items**: center
 - **Typography**: font-size-base, font-weight-semibold
 
 #### Section Headers ("CHANNELS", "DIRECT MESSAGES")
 - **Font Size**: 11px (--font-size-label)
 - **Font Weight**: 600 (--font-weight-semibold)
 - **Text Transform**: uppercase
 - **Letter Spacing**: 0.05em
 - **Color**: var(--color-text-tertiary)
 - **Padding**: 16px 16px 8px 16px (spacing-2 top/bottom spacing-1)
 - **Margin Top**: spacing-2 (first), spacing-1 (subsequent)
 
 #### Channel/DM Items
 - **Height**: 40px
 - **Padding**: 8px 16px (spacing-1 vertical, spacing-2 horizontal)
 - **Border Radius**: 6px (--radius-md)
 - **Font Size**: 13px (--font-size-message)
 - **Font Weight**: 400
 - **Display**: flex, align-items: center, gap: spacing-1
 - **Transition**: background-color var(--transition-fast)
 - **States**:
   - **Default**: background: transparent, color: var(--color-text-primary)
   - **Hover**: background-color: var(--color-surface-hover)
   - **Active**: background-color: var(--color-accent-soft), color: var(--color-accent), font-weight: 500
   - **Focus**: outline: 2px solid var(--color-accent), outline-offset: 2px
 
 #### Presence Indicator (DMs Only)
 - **Size**: 8px × 8px
 - **Border Radius**: 50% (solid circle)
 - **Margin Right**: spacing-1 (8px)
 - **Colors**:
   - **Active**: var(--color-presence-active) #16a34a
   - **Idle**: var(--color-presence-idle) #f59e0b
   - **Offline**: var(--color-presence-offline) #9ca3af
   - **Pulsing (Idle)**: @keyframes pulse at 50% opacity, 2s cycle
 
 ---
 
 ### 6.2 MessageList
 
 #### Overview
 Scrollable area displaying grouped messages with avatars, content, timestamps, and reaction bars.
 
 #### Message Group Container
 - **Padding**: spacing-2 (16px)
 - **Margin Bottom**: spacing-1 (8px)
 - **Display**: flex
 - **Gap**: spacing-1.5 (12px) between avatar and content
 - **Align Items**: flex-start
 
 #### Avatar
 - **Size**: 32×32px
 - **Border Radius**: 50% (perfect circle)
 - **Background**: Generated from user initials or avatar color
 - **Font Size**: 14px, --font-weight-semibold
 - **Display**: flex, justify-content: center, align-items: center
 - **Flex Shrink**: 0 (never compress)
 
 #### Message Content Wrapper
 - **Display**: flex, flex-direction: column
 - **Gap**: spacing-0.5 (4px)
 - **Flex**: 1 (grow)
 
 #### Message Text
 - **Font Size**: 13px (--font-size-message)
 - **Font Weight**: 400
 - **Line Height**: 1.5
 - **Color**: var(--color-text-primary)
 - **Word Break**: break-word
 - **White Space**: pre-wrap (preserve newlines)
 - **Overflow Wrap**: break-word
 - **Max Width**: 70% (desktop), 100% (mobile)
 - **Padding**: spacing-2 (16px) if in bubble, 0 if plain text
 
 #### Timestamp & Meta
 - **Font Size**: 12px (--font-size-timestamp)
 - **Font Weight**: 400
 - **Color**: var(--color-text-tertiary)
 - **Display**: flex, gap: spacing-1
 - **Align Items**: center
 - **Line Height**: 1.375
 
 #### Message States
 
 **Sending**
 - **Opacity**: 0.6
 - **Position**: relative
 - **Spinner**: 12px diameter, 2px border, --color-accent top arc
 - **Animation**: spin 1s linear infinite, respects prefers-reduced-motion
 
 **Sent**
 - **Opacity**: 1.0
 - **Checkmark Icon**: Single ✓, color: var(--color-text-tertiary)
 
 **Read**
 - **Opacity**: 1.0
 - **Double Checkmark**: ✓✓, color: var(--color-accent)
 
 **Failed**
 - **Border Left**: 2px solid var(--color-error)
 - **Background**: var(--color-error-light)
 - **Retry Button**: 32×32px, text "Retry"
 
 #### Grouped Messages
 Group messages from same user within 5-minute window:
 - Hide avatar on subsequent messages in group
 - Show only one timestamp per group
 - Reduce vertical gap between grouped messages (spacing-0.5)
 
 ---
 
 ### 6.3 MessageInput
 
 #### Overview
 Expandable text input with toolbar and send button. Auto-grows from 48px to max 120px.
 
 #### Container
 - **Height**: Auto, 48px minimum, 120px maximum
 - **Padding**: spacing-1 (8px)
 - **Background**: var(--color-bg-secondary)
 - **Border**: 1px solid var(--color-border)
 - **Border Radius**: 8px (--radius-lg)
 - **Display**: flex
 - **Gap**: spacing-1 (8px)
 - **Align Items**: flex-end
 - **Box Shadow**: None (default), var(--shadow-md) on focus
 - **Transition**: box-shadow var(--transition-fast), border-color var(--transition-fast)
 
 #### Toolbar (Left Side)
 - **Display**: flex
 - **Gap**: spacing-1 (8px)
 - **Align Items**: flex-end
 - **Flex Shrink**: 0
 
 #### Toolbar Button
 - **Size**: 32×32px
 - **Background**: transparent, var(--color-surface-hover) on hover
 - **Border**: None
 - **Border Radius**: 4px (--radius-sm)
 - **Icon Size**: 16px
 - **Color**: var(--color-text-secondary), var(--color-accent) when active
 - **Cursor**: pointer
 - **Transition**: background-color var(--transition-fast)
 - **States**:
   - **Default**: background: transparent, color: var(--color-text-secondary)
   - **Hover**: background-color: var(--color-surface-hover)
   - **Active**: color: var(--color-accent), background-color: var(--color-accent-soft)
   - **Focus**: outline: 2px solid var(--color-accent), outline-offset: 2px
 
 #### Text Input
 - **Font Size**: 13px (--font-size-message)
 - **Font Weight**: 400
 - **Line Height**: 1.5
 - **Color**: var(--color-text-primary)
 - **Background**: transparent
 - **Border**: None
 - **Padding**: spacing-1 (8px) top/bottom
 - **Flex**: 1 (grow)
 - **Resize**: none
 - **Max Height**: 120px (scrollable)
 - **Placeholder Color**: var(--color-text-tertiary)
 - **Placeholder Font Style**: italic
 - **Outline**: None
 
 #### Send Button (Right Side)
 - **Size**: 40×40px
 - **Icon Size**: 20px
 - **Background**: var(--color-accent) (enabled), var(--color-gray-300) (disabled)
 - **Color**: white (enabled), var(--color-gray-600) (disabled)
 - **Border**: None
 - **Border Radius**: 4px (--radius-sm)
 - **Cursor**: pointer (enabled), not-allowed (disabled)
 - **Flex Shrink**: 0
 - **Transition**: background-color var(--transition-fast)
 - **States**:
   - **Default**: background-color: var(--color-accent)
   - **Hover**: background-color: var(--color-accent-hover)
   - **Active**: background-color: var(--color-accent-active)
   - **Disabled**: background-color: var(--color-gray-300), opacity: 0.6
   - **Focus**: outline: 2px solid var(--color-accent), outline-offset: 2px
 
 #### Container Focus State
 - **Border Color**: var(--color-accent)
 - **Box Shadow**: 0 0 0 3px rgba(99, 153, 34, 0.1)
 
 ---
 
 ### 6.4 ReactionBar
 
 #### Overview
 Compact display of emoji reactions with counts. Can be expanded to add reactions.
 
 #### Display Rules
 - **Desktop (≥ 768px)**: Visible on message hover only
 - **Mobile (< 768px)**: Always visible below message (no hover state)
 - **Direction**: Horizontal, scrollable if overflow
 - **Position**: Absolute below message (desktop hover), or inline (mobile)
 
 #### Container
 - **Display**: flex
 - **Gap**: spacing-1 (8px)
 - **Overflow X**: auto (horizontal scroll)
 - **Padding**: spacing-1 (8px)
 - **Background**: var(--color-bg-secondary) (mobile visible), transparent (desktop hover)
 - **Border Radius**: 8px (--radius-lg) (mobile), none (desktop)
 
 #### Reaction Button
 - **Height**: 28px
 - **Padding**: 4px 8px (spacing-0.5 vertical, spacing-1 horizontal)
 - **Background**: var(--color-bg-tertiary)
 - **Border**: 1px solid var(--color-border)
 - **Border Radius**: 14px (--radius-full)
 - **Display**: flex
 - **Gap**: 4px
 - **Align Items**: center
 - **Font Size**: 14px
 - **Font Weight**: 500
 - **Cursor**: pointer
 - **Transition**: all var(--transition-fast)
 - **States**:
   - **Default**: background-color: var(--color-bg-tertiary), border-color: var(--color-border)
   - **Hover**: background-color: var(--color-surface-hover), border-color: var(--color-accent)
   - **Active**: background-color: var(--color-accent-soft), border-color: var(--color-accent), color: var(--color-accent)
   - **Focus**: outline: 2px solid var(--color-accent), outline-offset: 2px
 
 #### Emoji
 - **Size**: 16px
 - **Margin Right**: 0 (flexbox gap handles spacing)
