# ESLint policy

`eslint:recommended` supplies the baseline error checks. Explicit project rules add
strict comparisons, braces, callback returns, promise-executor checks, safe language
features, immutable parameters and consistent modern JavaScript. Maintainability
limits are 150 lines/file, 60 lines/function, complexity 12, nesting depth 3 and
four parameters. Source, configuration and tests use the same quality rules.

There is no universal Fortune 500 preset. These checks suit this small JavaScript
app; React/TypeScript rules should be added if those technologies are introduced.
Lint catches certain bugs and patterns, not all security or accessibility issues.
