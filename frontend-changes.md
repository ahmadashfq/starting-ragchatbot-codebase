# Frontend Changes: Dark/Light Theme Toggle

## Summary
Added a theme toggle feature that allows users to switch between dark and light themes with smooth transitions and persistent preference storage.

## Files Modified

### 1. `frontend/index.html`
- Added theme toggle button with sun/moon SVG icons positioned at the top-right corner
- Button includes proper accessibility attributes (`aria-label`, `title`)
- Updated CSS version to v14 and JavaScript version to v13 for cache busting

**New HTML added (lines 13-29):**
```html
<button class="theme-toggle" id="themeToggle" aria-label="Toggle dark/light theme" title="Toggle theme">
    <svg class="sun-icon">...</svg>  <!-- Sun icon for dark mode -->
    <svg class="moon-icon">...</svg> <!-- Moon icon for light mode -->
</button>
```

### 2. `frontend/style.css`
**Changes made:**

#### New CSS Variables (lines 25-27, 30-49)
- Added `--code-bg`, `--scrollbar-thumb`, `--scrollbar-thumb-hover` variables to dark theme
- Created complete light theme variant with `[data-theme="light"]` selector:
  - Light background colors (`#f8fafc`, `#ffffff`)
  - Dark text for contrast (`#1e293b`, `#64748b`)
  - Adjusted surface and border colors
  - Light code background and scrollbar colors

#### Theme Toggle Button Styles (lines 686-739)
- Fixed position in top-right corner
- Circular button (44x44px) with smooth hover/focus effects
- Scale animation on hover/active states
- Icon visibility toggling based on `[data-theme="light"]` attribute

#### Smooth Transition Styles (lines 741-764)
- Applied 0.3s ease transitions to all major UI elements for:
  - `background-color`
  - `color`
  - `border-color`
  - `box-shadow`

#### Updated Existing Styles
- Changed hardcoded `rgba(0, 0, 0, 0.2)` to `var(--code-bg)` for code blocks
- Changed `var(--border-color)` to `var(--scrollbar-thumb)` for scrollbar thumbs

### 3. `frontend/script.js`
**Changes made:**

#### Added DOM Element Reference (line 8)
```javascript
let chatMessages, chatInput, sendButton, totalCourses, courseTitles, themeToggle;
```

#### Added Theme Initialization Call (line 21)
```javascript
initializeTheme();
```

#### Added Event Listener (lines 53-56)
```javascript
if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);
}
```

#### Added Theme Functions (lines 216-237)
```javascript
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

function setTheme(theme) {
    if (theme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
    } else {
        document.documentElement.removeAttribute('data-theme');
    }
    localStorage.setItem('theme', theme);
}
```

## Features
1. **Toggle Button** - Circular button in top-right with sun/moon icons
2. **Smooth Transitions** - All UI elements animate smoothly when theme changes
3. **Persistent Preference** - Theme choice saved to localStorage
4. **Accessibility** - Button is keyboard navigable with focus ring, includes aria-label
5. **Dark Theme (Default)** - Original dark color scheme
6. **Light Theme** - New light color scheme with proper contrast ratios

## Usage
- Click the toggle button (sun icon) to switch to light theme
- Click again (moon icon) to switch back to dark theme
- Preference is automatically saved and restored on page reload
