# Studio Roadmap — Future Enhancements

> Living document tracking planned improvements to the Studio feature.
> Last updated: 2026-02-23

---

## Current State (v2.0.0)

The Studio is a full-stack visual development environment that replaced the original 5-step Builder wizard. Users describe applications in a chat interface, AI generates React files via SSE streaming with `### FILE:` marker extraction, and a Sandpack-powered preview renders the running app in real time.

### What is implemented today

| Area | Details |
|------|---------|
| **Modes** | Chat (describe and generate), Code (edit files directly), Visual (click elements to inspect/modify) |
| **Preview** | Sandpack `react` template, dark theme, console toggle, error overlay |
| **Persistence** | SQLite `studio_projects` + `studio_versions` tables, WAL journal, full CRUD |
| **Streaming** | SSE with file-marker extraction, `### DEPS:` for extra npm packages |
| **Mobile** | Responsive bottom tab bar with 5 tabs (Chat, Preview, Code, Visual, Files) |
| **Project ops** | Create, rename, delete, save version, restore version, ZIP export (frontend or fullstack) |
| **Models** | Gemini (2.5 Flash, 2.5 Pro, 3 Pro) and Claude (Haiku 4.5, Sonnet 4.6, Opus 4.6) |
| **Components** | 24 Studio components, plus shared NavBar, ThemeSwitcher, ToastContainer, ModelSelector |
| **Backend** | `routers/studio.py`, `services/studio_service.py`, `services/mock_server_manager.py`, `services/openapi_extractor.py`, `services/type_generator.py`, `templates/mock_server_template.js` |
| **Visual mode** | Element selection via `postMessage` from preview iframe, inspector sidebar, component tree, quick actions |
| **Diff viewer** | LCS-based line-by-line before/after diff for version comparison |
| **Infrastructure** | Mock server manager (Node.js from OpenAPI spec, port range 9100-9199) exists but is not yet wired to the UI |

---

## Short-Term Enhancements (v2.1)

**Goal:** Polish the editing experience so the Studio feels like a lightweight IDE rather than a chat window with a preview bolted on.

**Target: 4-6 weeks**

| Feature | Description | Priority | Complexity |
|---------|-------------|----------|------------|
| TypeScript template | Switch Sandpack template from `react` to `react-ts`; update system prompt to emit `.tsx` files when the user chooses TS | High | Low |
| Tailwind CSS in Sandpack | Add `tailwindcss` + PostCSS to Sandpack dependencies; update system prompt to allow utility classes instead of only inline styles | High | Medium |
| Undo/redo for file changes | Maintain a per-file history stack in `StudioContext`; expose `undo()` / `redo()` actions | High | Medium |
| Keyboard shortcuts | `Cmd/Ctrl+S` to save version, `Cmd/Ctrl+Z` undo, `Cmd/Ctrl+Shift+Z` redo, `Cmd/Ctrl+P` quick file open | High | Low |
| Auto-save with debounce | Debounce file edits (2 s); persist to SQLite without creating a version entry; configurable in project settings | Medium | Low |
| Better Sandpack error display | Catch parse and runtime errors from Sandpack's `useSandpack` hook; render them as inline banners with file/line links | High | Medium |
| File rename/move | Add context-menu actions in `StudioFilesPanel` to rename or move files; update all import paths via simple string replacement | Medium | Medium |
| CodeMirror standalone editor | Replace `<textarea>` in `StudioCodeEditor` with `@codemirror/view` + `@codemirror/lang-javascript`; syntax highlighting, bracket matching, line numbers | High | Medium |
| Theme sync | When the workspace theme changes (CRT, Solarized, etc.), derive a matching Sandpack theme object so the preview background and code highlight colors stay consistent | Low | Low |

### Verification Criteria

- **TypeScript template**: Creating a new project with "TypeScript" enabled generates `.tsx` files; Sandpack compiles and renders them without errors.
- **Tailwind CSS**: A prompt such as "add a blue button with rounded corners" produces `className="bg-blue-500 rounded"` instead of `style={{ background: '#3b82f6', borderRadius: '0.5rem' }}`.
- **Undo/redo**: After three edits, pressing Cmd+Z three times restores the original content; Cmd+Shift+Z re-applies each edit.
- **Keyboard shortcuts**: Each shortcut triggers the expected action from any mode; no conflicts with browser defaults.
- **Auto-save**: Switching away from Studio and returning shows unsaved edits preserved; no version entry is created until the user explicitly saves.
- **Error display**: A deliberate syntax error (e.g., missing closing bracket) shows a red banner with the file name, line number, and error message within 2 seconds.
- **File rename/move**: Renaming `Header.js` to `TopBar.js` updates the import in `App.js` automatically; preview does not break.
- **CodeMirror**: Opening a `.js` file shows syntax-colored code with line numbers; typing triggers bracket auto-close.
- **Theme sync**: Switching to CRT theme changes both the app chrome and the Sandpack preview background/text colors.

---

## Medium-Term Features (v2.2)

**Goal:** Make the Studio a credible prototyping tool where the AI generates entire project scaffolds, users manage dependencies visually, and collaboration hooks are in place.

**Target: 2-3 months after v2.1**

| Feature | Description | Priority | Complexity |
|---------|-------------|----------|------------|
| Multi-file generation | Improve system prompt and streaming parser so AI generates complete directory structures (`/components/`, `/hooks/`, `/utils/`, `/styles/`) in a single pass | High | Medium |
| Dependency management UI | Panel in project settings listing installed npm packages; add/remove/upgrade with version selector; Sandpack `customSetup.dependencies` updated live | High | Medium |
| Component library integration | Chat commands like "add shadcn/ui Button" or "use MUI DataGrid" inject the library, import statements, and a usage example | Medium | High |
| Preview device frames | Toolbar buttons for phone (375 px), tablet (768 px), and desktop (1280 px) that resize the Sandpack preview iframe | High | Low |
| Screenshot capture | "Capture" button that calls `html2canvas` on the preview iframe and downloads a PNG or copies to clipboard | Medium | Medium |
| Real-time collaboration placeholder | Add a `collaborators` field to `studio_projects`; show avatar circles in the toolbar; no live sync yet, just presence | Low | Low |
| Git-style diff view | Extend `StudioDiffView` with unified/split toggle, syntax coloring in diff hunks, and collapsible unchanged regions | Medium | Medium |
| Template marketplace | Expand the built-in template list beyond the current defaults; allow importing community templates from a JSON manifest URL | Low | High |
| AI-assisted debugging | When Sandpack reports an error, a "Fix with AI" button sends the error + relevant file to the model and streams back a corrected file | High | Medium |
| Console log viewer | Surface `console.log`, `console.warn`, `console.error` from Sandpack in a filterable, searchable panel beneath the preview | Medium | Low |

### Verification Criteria

- **Multi-file generation**: Prompt "build a todo app with header, footer, and list components" produces at least 4 files in separate directories.
- **Dependency management**: Adding `axios@^1.6` via the UI causes Sandpack to resolve and bundle axios; removing it triggers an import error in files that use it.
- **Component library**: "Add MUI TextField" results in `@mui/material` appearing in dependencies and a working `<TextField />` in the preview.
- **Device frames**: Selecting "Phone" constrains the preview to 375 px wide with a device-style border; content reflows accordingly.
- **Screenshot**: Clicking "Capture" downloads a `.png` file matching the current preview viewport.
- **Collaboration placeholder**: Two browser tabs with the same project show distinct avatar indicators; no data conflicts.
- **Diff view**: Comparing version 1 and version 3 shows added lines in green, removed in red, with line numbers from both versions.
- **Template marketplace**: Pasting a valid template URL imports files and dependencies; an invalid URL shows an error toast.
- **AI debugging**: A runtime `TypeError` displays a "Fix" button; clicking it streams a corrected file and the error disappears from the preview.
- **Console viewer**: A `console.log('hello')` in `App.js` appears in the console panel with timestamp and log-level badge.

---

## Backend Generation (v2.3)

**Goal:** Extend Studio from frontend-only generation to full-stack prototyping. The mock server infrastructure (`mock_server_manager.py`, `openapi_extractor.py`, `type_generator.py`, `mock_server_template.js`) already exists in the backend; this phase wires it to the UI and adds real backend code generation.

**Target: 2-3 months after v2.2**

| Feature | Description | Priority | Complexity |
|---------|-------------|----------|------------|
| Mock server activation | Add a "Start Mock Server" button in `StudioApiPanel`; calls `mock_server_manager.start_mock_server()` with the project's OpenAPI spec; preview fetches from `localhost:{port}` | High | Medium |
| FastAPI code generation | AI generates `main.py`, route files, and Pydantic models from a natural-language API description; validate syntax with `py_compile` before serving | High | High |
| Database schema generation | Generate SQLAlchemy / raw SQLite models from entity descriptions; output migration scripts | Medium | High |
| API contract viewer | Render the generated OpenAPI spec as an interactive Swagger-like panel using `swagger-ui-react` or a lightweight custom renderer | Medium | Medium |
| TypeScript API client | Auto-generate a typed fetch wrapper from the OpenAPI spec using `type_generator.py`; inject it into the Sandpack project so frontend code can call the mock server with full type safety | Medium | High |
| Environment variable management | UI for setting env vars (`API_URL`, `PORT`, `DB_PATH`) that the mock server reads at startup; stored in project settings JSON | Low | Low |
| Request/response logging | Mock server writes each request/response pair to a ring buffer; surface in a "Network" tab next to the console viewer | Medium | Medium |

### Verification Criteria

- **Mock server**: Clicking "Start" shows a green "Running on port 9101" badge; the preview's `fetch('/api/items')` returns mock JSON.
- **FastAPI generation**: Prompt "create an API for a bookstore with books and authors" produces valid Python files; `py_compile` passes on each.
- **Schema generation**: Entity "User with name, email, created_at" generates a `models.py` with correct SQLAlchemy column types.
- **API contract viewer**: The OpenAPI spec renders endpoints, parameters, and response schemas; clicking "Try it" sends a request to the running mock server.
- **TypeScript client**: Generated `apiClient.ts` exports typed functions like `getBooks(): Promise<Book[]>`; TypeScript compilation in Sandpack succeeds.
- **Environment variables**: Changing `API_URL` in the UI and restarting the mock server causes it to bind to the new value.
- **Request logging**: After 3 `GET /api/items` calls, the Network tab shows 3 entries with status codes, durations, and response bodies.

---

## Advanced Features (v3.0)

**Goal:** Transform Studio from a prototyping sandbox into a production-capable code generation and deployment platform.

**Target: 6+ months**

| Feature | Description | Priority | Complexity |
|---------|-------------|----------|------------|
| Deploy to Vercel/Netlify | One-click deploy via Vercel CLI or Netlify API; requires user to link an account token in settings | High | High |
| GitHub integration | Push generated project to a new or existing GitHub repo; uses `gh` CLI or GitHub REST API with a PAT | High | High |
| Docker generation | Generate `Dockerfile` + `docker-compose.yml` for full-stack apps (Node frontend + FastAPI backend + SQLite volume) | Medium | Medium |
| WebSocket mock support | Extend mock server to handle `ws://` connections for real-time app prototypes | Low | High |
| Auth scaffolding | Generate JWT login/register flow or OAuth redirect scaffolding from a chat command like "add authentication" | Medium | High |
| State management scaffolding | On request, inject Redux Toolkit, Zustand, or Jotai boilerplate with typed stores and example slices | Medium | Medium |
| Testing scaffolding | Generate Vitest unit tests for components and Playwright e2e tests for user flows | Medium | High |
| Performance profiling | Embed React DevTools Profiler data in the preview; surface component render counts and durations | Low | High |
| SEO tools | Generate `<meta>` tags, Open Graph properties, and `robots.txt` from project metadata | Low | Low |
| PWA generation | Add `manifest.json`, service worker registration, and offline fallback page to the generated project | Low | Medium |

### Verification Criteria

- **Deploy to Vercel**: After linking a token, clicking "Deploy" produces a live URL within 90 seconds; the deployed app matches the Studio preview.
- **GitHub push**: "Push to GitHub" creates a repo with the correct file structure, a `.gitignore`, and a `README.md`; subsequent pushes create new commits, not force-pushes.
- **Docker generation**: `docker compose up` from the generated files starts both frontend and backend; `curl localhost:3000` returns the app.
- **WebSocket mock**: A chat app prototype using `new WebSocket(...)` connects to the mock server and echoes messages.
- **Auth scaffolding**: "Add JWT auth" generates login/register pages, a `/api/auth/login` endpoint, and token storage in localStorage.
- **State management**: "Add Zustand store for cart" produces a typed store file, a provider wrapper, and a usage example in a component.
- **Testing scaffolding**: Generated Vitest tests for `Header.tsx` include at least a render test and a snapshot test; `npx vitest run` passes.
- **Performance profiling**: The profiler tab shows a flame graph with component names and render durations after interacting with the preview.
- **SEO tools**: Generated `<head>` tags include `title`, `description`, `og:image`, and `robots` meta; validated against an Open Graph debugger.
- **PWA generation**: The generated app passes a Lighthouse PWA audit with a score above 90.

---

## Visual Mode Enhancements (v3.1)

**Goal:** Evolve Visual Mode from an element inspector into a Figma-like visual builder where non-developers can construct interfaces by direct manipulation.

**Target: after v3.0 stabilizes**

| Feature | Description | Priority | Complexity |
|---------|-------------|----------|------------|
| Component drag-and-drop | Palette sidebar listing available components (buttons, inputs, cards, etc.); drag onto the preview canvas to insert into the React tree | High | High |
| Auto-layout and constraints | Figma-inspired constraint system (pin to top/left/right, fill container, hug content) that maps to CSS Flexbox/Grid rules | Medium | High |
| CSS Grid/Flexbox visual editor | Select a container and toggle between Grid and Flexbox; adjust `gap`, `align-items`, `justify-content` via dropdowns and sliders | High | Medium |
| Color picker | Inline color swatch next to any color style property in the inspector; opens a popover with hex/RGB/HSL inputs and a palette of theme colors | Medium | Low |
| Typography controls | Inspector fields for `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing` with live preview | Medium | Low |
| Animation builder | Timeline-based editor for CSS `transition` and `@keyframes` definitions; generates inline style objects or a `<style>` block | Low | High |
| Responsive breakpoint editor | Define breakpoints (sm, md, lg, xl); switch between them in the preview; per-breakpoint style overrides stored in the component | Medium | High |
| Component variant system | Define named variants (primary, secondary, outline) for a component; switch between them in the inspector; generates a `variants` prop | Low | High |

### Verification Criteria

- **Drag-and-drop**: Dragging a "Card" from the palette onto the preview inserts a `<Card />` component in `App.js` at the correct position; preview updates immediately.
- **Auto-layout**: Setting a container to "Fill" width and "Hug" height produces `width: '100%'` and `height: 'auto'` in the generated code.
- **Grid/Flexbox editor**: Switching a `<div>` to Grid with 3 columns produces `display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)'`.
- **Color picker**: Changing a button's background from `#0ea5e9` to `#ef4444` via the picker updates the inline style and the preview in under 500 ms.
- **Typography**: Setting `fontSize: 24` and `fontWeight: 700` on a heading updates both the inspector and the generated code.
- **Animation builder**: Defining a `fadeIn` animation produces a valid `@keyframes` block and an `animation` property on the target element.
- **Breakpoint editor**: At the "Phone" breakpoint, a 3-column grid collapses to 1 column; switching to "Desktop" restores 3 columns.
- **Variant system**: A Button with "primary" and "outline" variants generates a `variant` prop and conditional style logic.

---

## AI/ML Improvements

**Goal:** Make the AI code generation smarter, more context-aware, and capable of self-correction. These improvements are model-agnostic and apply to both Gemini and Claude backends.

**Target: ongoing, in parallel with feature releases**

| Feature | Description | Priority | Complexity |
|---------|-------------|----------|------------|
| Fine-tuned React model | Collect high-quality prompt/code pairs from Studio usage; fine-tune a smaller model for faster, cheaper generation | Low | Very High |
| Context-aware suggestions | Include all project files in the context window (not just the current file) so AI understands cross-file dependencies | High | Medium |
| AI code review | Before applying generated changes, run a review pass that checks for unused imports, missing keys, accessibility gaps, and style inconsistencies | Medium | Medium |
| Automated a11y checking | Run `axe-core` in the Sandpack preview after each generation; surface violations as warnings with AI-suggested fixes | Medium | Medium |
| AI-generated tests | "Generate tests" command produces Vitest test files for selected components, using the current project state as context | Medium | High |
| Smart refactoring | AI suggests extract-component, rename-variable, and move-to-file refactors based on code smell detection | Low | High |
| Multi-turn refinement with memory | Maintain a preference profile per project (e.g., "user prefers Tailwind", "user likes minimal UI") that persists across chat turns and sessions | Medium | Medium |
| Image-to-code | Upload a screenshot or mockup image; AI generates matching React components using multimodal models (Gemini native, Claude via base64) | Medium | High |

### Verification Criteria

- **Fine-tuned model**: The fine-tuned model generates syntactically correct React code for 95% of prompts in the evaluation set, with 2x faster response time than the base model.
- **Context-aware suggestions**: Asking "add a link to the About page" when `About.js` exists produces a correct `import` and `<Link>` without the user specifying the file path.
- **AI code review**: Generated code with an unused `useState` import triggers a warning: "Unused import: useState in Header.js line 1."
- **a11y checking**: An `<img>` without `alt` text triggers an "Images must have alt text" warning with a one-click fix button.
- **AI-generated tests**: "Generate tests for Header" produces a test file that imports `Header`, renders it, and asserts on visible text content.
- **Smart refactoring**: A component with 200+ lines triggers a suggestion: "Extract the form section (lines 45-120) into a FormSection component."
- **Multi-turn memory**: After the user says "I prefer dark backgrounds", subsequent generations default to dark color schemes without being reminded.
- **Image-to-code**: Uploading a screenshot of a login form generates a `LoginForm.tsx` with email input, password input, and submit button matching the layout.

---

## Architecture Improvements

**Goal:** Replace foundational infrastructure to unlock capabilities that Sandpack's iframe model cannot support. These are high-effort, high-reward changes that affect every other feature.

**Target: evaluated per-item; some may run in parallel with feature work**

| Feature | Description | Priority | Complexity | Rationale |
|---------|-------------|----------|------------|-----------|
| WebContainer API | Replace Sandpack with StackBlitz WebContainer for full Node.js runtime in the browser; enables `npm install`, filesystem access, and server-side code execution | Medium | Very High | Unlocks backend execution in preview, real `npm install`, and filesystem operations |
| Monaco Editor | Replace CodeMirror with Monaco (VS Code engine); provides IntelliSense, multi-cursor, minimap, and command palette out of the box | Medium | Medium | Matches developer expectations for a code editor; rich extension ecosystem |
| Language Server Protocol | Run TypeScript language server via WebContainer or web worker; provide real-time type errors, go-to-definition, and auto-imports | Low | Very High | Eliminates false positives from regex-based linting; true IDE-grade experience |
| Incremental compilation | Cache Sandpack/WebContainer compilation output; only recompile changed files; reduce preview refresh from ~1.5 s to <300 ms | High | High | Critical for Visual Mode where every drag-and-drop triggers a recompile |
| File system abstraction | Introduce a `FileSystem` interface that `StudioContext` uses; swap implementations for in-memory, SQLite, IndexedDB, or cloud (S3/GCS) | Medium | Medium | Future-proofs storage without changing any component code |
| Plugin system | Define a `StudioPlugin` interface with hooks (`onFileChange`, `onGenerate`, `onDeploy`); load plugins from a config array | Low | High | Enables community extensions (linters, formatters, custom panels) without core changes |
| Offline mode | Service worker caches the Studio shell, CodeMirror/Monaco bundles, and the most recent project; full editing works without a network connection | Low | Medium | Useful for mobile/tablet use on unreliable connections |

### Verification Criteria

- **WebContainer**: `npm install lodash` in the terminal tab installs the package; `import _ from 'lodash'` resolves in the preview; server-side `express` app runs and responds to requests.
- **Monaco Editor**: Opening a `.tsx` file shows syntax highlighting, IntelliSense popup on `.`, and red squiggles on type errors; all existing keyboard shortcuts continue to work.
- **LSP**: Hovering over a function shows its type signature; Cmd+Click on an import navigates to the definition file; renaming a symbol updates all references.
- **Incremental compilation**: Changing a single line in a 20-file project refreshes the preview in under 300 ms (measured via Performance API).
- **File system abstraction**: Switching from SQLite to IndexedDB storage requires changing one line in configuration; all 24 Studio components continue to work.
- **Plugin system**: A "Prettier on Save" plugin auto-formats files on Cmd+S; a "Dark Mode Enforcer" plugin warns if any component uses a white background.
- **Offline mode**: Disabling the network in DevTools still allows opening the last project, editing files, and previewing; changes sync when the connection returns.

---

## Prioritization Rationale

The roadmap is ordered by the following principles:

1. **Developer experience first (v2.1).** The most impactful improvements are the ones that reduce friction in daily use: syntax highlighting, undo/redo, keyboard shortcuts, and better error messages. These are low-to-medium complexity with immediately visible results.

2. **Prototyping completeness second (v2.2).** Once editing feels solid, the focus shifts to making the AI generate richer output (multi-file projects, component libraries) and giving users visual tools to inspect and debug (device frames, console viewer, diff view).

3. **Full-stack capability third (v2.3).** The mock server infrastructure already exists. Wiring it to the UI and adding backend code generation transforms Studio from a frontend tool into a full-stack prototyping platform, which is a significant differentiation point.

4. **Production readiness fourth (v3.0).** Deployment, GitHub integration, and Docker generation make Studio output usable beyond the sandbox. These features have the highest external dependency (third-party APIs, authentication flows) and are therefore scheduled later.

5. **Visual builder last (v3.1).** Drag-and-drop and visual editing are the most complex features with the highest risk of scope creep. They are intentionally placed after the code-first experience is mature, so they can build on a stable foundation.

6. **AI/ML and Architecture run in parallel.** These are continuous investments that improve every other feature. They do not gate any specific release but are prioritized based on which feature milestones they unblock.

---

## Release Timeline Summary

| Version | Milestone | Estimated Date | Feature Count | Key Dependency |
|---------|-----------|---------------|---------------|----------------|
| **v2.1** | IDE Polish | Q2 2026 | 9 features | CodeMirror package |
| **v2.2** | Prototyping | Q3-Q4 2026 | 10 features | v2.1 editor stability |
| **v2.3** | Full-Stack | Q1 2027 | 7 features | v2.2 multi-file generation |
| **v3.0** | Production | Q2-Q3 2027 | 10 features | Third-party API accounts (Vercel, GitHub) |
| **v3.1** | Visual Builder | Q4 2027+ | 8 features | v3.0 stable preview pipeline |

Dates are estimates. Each release ships when its verification criteria pass, not on a fixed calendar.

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Sandpack limitations block v2.2+ features | High | Evaluate WebContainer migration early; maintain abstraction layer |
| Model API rate limits during generation | Medium | Implement request queuing and exponential backoff; cache common scaffolds |
| Mobile performance degrades with CodeMirror/Monaco | Medium | Lazy-load editor bundles; keep textarea fallback for low-memory devices |
| Third-party API changes (Vercel, GitHub) | Low | Abstract deployment behind a provider interface; support multiple targets |
| Scope creep in Visual Mode | High | Ship v3.1 features incrementally; each must pass verification before the next begins |

---

## Contributing

When proposing a new roadmap item:

1. Add it to the appropriate version section based on complexity and dependencies.
2. Include a one-line description, priority (High/Medium/Low), and complexity (Low/Medium/High/Very High).
3. Write at least one verification criterion that can be tested without ambiguity.
4. If the feature depends on another roadmap item, note the dependency explicitly.

---

*Document maintained by the Studio development team. Review quarterly or after each minor release.*
