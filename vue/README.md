## VS Code Setup

### Type Support for `.vue` Imports in TS

Since TypeScript cannot handle type information for `.vue` imports, they are shimmed to be a generic Vue component type by default. In most cases this is fine if you don't really care about component prop types outside of templates.

However, if you wish to get actual prop types in `.vue` imports (for example to get props validation when using manual `h(...)` calls), you can enable ["takeover mode"](https://github.com/johnsoncodehk/volar/discussions/471) for Volar.

1. Disable built-in TypeScript extension:
   1. Run `Extensions: Show Built-in Extensions` command
   2. Find `TypeScript and JavaScript Language Features`, right click and select `Disable (Workspace)`
2. Reload VSCode
