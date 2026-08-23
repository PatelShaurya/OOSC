# Run Nyaya locally

From the project directory, install dependencies with `pnpm install`, then start the development server with `pnpm dev`. The Nyaya application will be served at **http://localhost:3000**.

The complete prototype is available at the following routes:

| Route | Purpose |
|---|---|
| `/` | Describe a civic problem and enter the flow. |
| `/dashboard` | Workspace, shortcuts, and recent case activity. |
| `/assistant` | Structured case analysis with supporting sources and a clarification panel. |
| `/rights` | Progressive rights navigator with a structured result. |
| `/documents` | Document library. |
| `/documents/new` | Four-step document generation journey. |
| `/documents/:id` | Formal document preview. |

Use the theme control in the upper-right navigation to switch between the ivory light theme and the premium graphite dark theme. For visual QA, appending `?theme=dark` to any route will open the dark theme directly.
