# React 19 Features Research

**Research Date**: 2026-02-05
**Source**: Gemini CLI Research
**Status**: React 19 stable release (December 2024)

## Summary

React 19 (stable release December 2024) focuses on simplifying data handling, enhancing performance with Server Components, and reducing boilerplate. Key additions include **Server Actions** for seamless data mutations, a suite of new hooks (`useActionState`, `useFormStatus`, `useOptimistic`) to manage loading and optimistic states, and the **React Compiler** (experimental) to automate memoization. It also introduces declarative **document metadata** and improvements to **asset loading**, while simplifying APIs like `ref` and `Context`.

---

## 1. New Hooks

React 19 introduces hooks specifically designed to handle common async patterns in UIs, particularly for forms and data mutations.

### `useActionState` (formerly `useFormState`)

Manages the state of a form action (e.g., pending, success, error).

```jsx
import { useActionState } from "react";

async function updateName(prevState, formData) {
  const name = formData.get("name");
  if (!name) return { error: "Name is required" };
  await saveName(name); // Server action
  return { success: true, name };
}

function NameForm() {
  const [state, submitAction, isPending] = useActionState(updateName, { name: "" });

  return (
    <form action={submitAction}>
      <input name="name" defaultValue={state.name} />
      <button disabled={isPending}>Update</button>
      {state.error && <p>{state.error}</p>}
    </form>
  );
}
```

### `useFormStatus`

Provides status information (like `pending`) from the nearest parent `<form>`. Must be called from a child component of the form.

```jsx
import { useFormStatus } from "react-dom";

function SubmitButton() {
  const { pending } = useFormStatus();
  return <button disabled={pending}>{pending ? "Saving..." : "Save"}</button>;
}
```

### `useOptimistic`

Shows a different state while an async action is underway (e.g., instantly adding a comment before the server confirms).

```jsx
import { useOptimistic } from "react";

function Thread({ messages, sendMessage }) {
  const [optimisticMessages, addOptimisticMessage] = useOptimistic(
    messages,
    (state, newMessage) => [...state, newMessage]
  );

  async function formAction(formData) {
    const message = formData.get("message");
    addOptimisticMessage(message); // Instant UI update
    await sendMessage(message);    // Actual server request
  }

  return (
    <form action={formAction}>
       {/* Render optimisticMessages */}
    </form>
  );
}
```

### `use`

A new API to read resources (Promises and Context) in render. It can be conditionally called, unlike hooks.

```jsx
import { use } from "react";

function Message({ messagePromise }) {
  const message = use(messagePromise); // Suspends until resolved
  const theme = use(ThemeContext);     // Reads context
  return <div className={theme}>{message}</div>;
}
```

---

## 2. Server Components and Server Actions

### Server Components (RSC)

Components that render *only* on the server. They have direct access to backend resources (DB, file system) and do not include their code in the client bundle. They are async functions by default.

```jsx
// Server Component
import db from './db';

export default async function Page() {
  const data = await db.query('SELECT * FROM posts');
  return (
    <ul>{data.map(post => <li key={post.id}>{post.title}</li>)}</ul>
  );
}
```

### Server Actions

Functions that run on the server but can be called from client components. They are marked with `'use server'`.

```jsx
// actions.js
'use server';

export async function createPost(formData) {
  await db.post.create({ data: formData.get('title') });
}

// ClientComponent.jsx
'use client';
import { createPost } from './actions';

export default function Form() {
  return <form action={createPost}>...</form>;
}
```

---

## 3. Document Metadata Support

React 19 natively handles `<title>`, `<meta>`, and `<link>` tags. You can render them anywhere in your component tree, and React will hoist them to the `<head>`.

```jsx
function BlogPost({ title }) {
  return (
    <article>
      <title>{title}</title>
      <meta name="description" content="Blog post summary" />
      <h1>{title}</h1>
    </article>
  );
}
```

---

## 4. Asset Loading Improvements

React 19 integrates with the browser's resource loading.

- **Preloading**: APIs like `preload`, `preinit` are available (via `react-dom`) to start loading fonts, scripts, or styles early.
- **Stylesheets**: React manages the insertion and deduplication of stylesheets rendered within components, handling the loading order to prevent FOUC (Flash of Unstyled Content).
- **Async Scripts**: Scripts rendered in components are loaded efficiently and de-duplicated.

---

## 5. `ref` as a Prop

`forwardRef` is no longer needed for simple function components. `ref` is now a regular prop.

```jsx
// Before (React 18)
const Input = forwardRef((props, ref) => <input ref={ref} {...props} />);

// React 19
function Input({ ref, ...props }) {
  return <input ref={ref} {...props} />;
}
```

---

## 6. Context as a Provider

You can render `<Context>` directly instead of `<Context.Provider>`.

```jsx
const ThemeContext = createContext('');

function App() {
  return (
    <ThemeContext value="dark">
      <Page />
    </ThemeContext>
  );
}
```

---

## 7. Compiler (React Forget)

The **React Compiler** is a new build-time tool that automatically optimizes your React code. It memoizes components and values (equivalent to `React.memo`, `useMemo`, `useCallback`) automatically.

- **Goal**: To make React "default to fast" without manual performance tuning.
- **Status**: Open sourced and available (via Babel plugin), but decoupled from the React 19 core release (it's an optional tool).

---

## 8. Breaking Changes & Migration

### Removed APIs

- `ReactDOM.render`, `ReactDOM.hydrate`, and `ReactDOM.unmountComponentAtNode` are removed. Use `createRoot` and `hydrateRoot`.
- **UMD Builds**: Removed. Use ESM builds.
- **Legacy Context**: The old `contextTypes` API is removed.

### Changed Behaviors

- **Ref Cleanup**: Returning a cleanup function from a `ref` callback is now supported and expected.
- **`defaultProps`**: Deprecated for function components; use ES6 default parameters instead.

### Migration Steps

1. **Migrate to `createRoot`**: Ensure your entry point uses the new root API.
   ```jsx
   // Old
   ReactDOM.render(<App />, document.getElementById('root'));

   // New
   import { createRoot } from 'react-dom/client';
   const root = createRoot(document.getElementById('root'));
   root.render(<App />);
   ```

2. **Replace `forwardRef`**: Simplify components by accepting `ref` as a prop.

3. **Adopt Server Actions**: If using a framework like Next.js, replace API routes with Server Actions for data mutations.

4. **Update Context Usage**: Use `<Context>` directly instead of `<Context.Provider>`.

5. **Replace `defaultProps`**: Use ES6 default parameters.
   ```jsx
   // Old
   function Button(props) { }
   Button.defaultProps = { color: 'blue' };

   // New
   function Button({ color = 'blue' }) { }
   ```

---

## Recommendations

1. **Migrate to `createRoot`**: Ensure your entry point uses the new root API.
2. **Replace `forwardRef`**: Simplify components by accepting `ref` as a prop.
3. **Adopt Server Actions**: If using a framework like Next.js, replace API routes with Server Actions for data mutations.
4. **Leverage New Hooks**: Use `useActionState`, `useFormStatus`, and `useOptimistic` for better form UX.
5. **Consider React Compiler**: Evaluate the experimental compiler for automatic performance optimizations.
6. **Update Metadata**: Replace third-party libraries (like `react-helmet`) with native metadata support.

---

## Additional Resources

- [React 19 Official Blog](https://react.dev/blog/2024/12/05/react-19)
- [React 19 Upgrade Guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide)
- [React Compiler Documentation](https://react.dev/learn/react-compiler)
