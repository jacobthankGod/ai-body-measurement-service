# TODO: Replace Google Logo in Sign Up and Sign In Pages

## Task: Replace the Google logo SVG in the "continue with Google" buttons with the new logo file `Google__G__logo.svg.webp`

### Steps:
1. [x] Replace inline SVG in signup.html (btnGoogleSignUp button)
2. [x] Replace inline SVG in signin.html (btnGoogleSignIn button)
3. [x] Verify changes are complete

### Details:
- File locations:
  - signup.html: Button ID `btnGoogleSignUp`
  - signin.html: Button ID `btnGoogleSignIn`
- New logo to use: `/assets/Google__G__logo.svg.webp`

### Changes Made:
1. **signup.html**:
   - Replaced inline SVG in HTML button with `<img src="/assets/Google__G__logo.svg.webp" alt="Google" style="width:20px;height:20px;">`
   - Updated JavaScript error handlers to use new image logo

2. **signin.html**:
   - Replaced inline SVG in HTML button with `<img src="/assets/Google__G__logo.svg.webp" alt="Google" style="width:20px;height:20px;">`
   - Updated JavaScript error handlers to use new image logo
