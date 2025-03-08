# Argument Binding

Contract predicates are typically interested in the values of variables -- most commonly, the values
of function arguments. But, more broadly, they may want to check any of these:

1. Function arguments
2. Instance variables
3. The function's return value
4. Local variables at the point of declaration (particularly useful when used as context manager)
5. Global variables

All of these can be made accessible via argument binding.

## Preference Order

When binding variables explicitly via the `capture` or `clone` family of contract assertion parameters,
the captured variable is determined via the following preference order:

1. Return value
2. Function arguments, including `self`
3. Locals
4. Globals

## Explicit vs. Implicit Binding

Some contract assertions implicitly bind variables, for example function arguments are automatically
bound for preconditions. Explicit bindings always take precedence and override the implicit ones.