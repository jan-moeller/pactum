# Contract Predicates

A contract predicate is a `bool`-returning callable that encapsulates the condition that must hold
as part of a contract. In its simplest form, a predicate has no parameters. However, it is often useful
for a predicate to be able to access surrounding variables. To that end, predicates can accept arguments.

## Predicate Parameters

Predicate parameters must satisfy the following constraints:

1. they must not contain `*` or `/`, or variadic parameters.
2. their name must be in the set of [argument bindings](/docs/argument_binding.md).

## Evaluation

Whether predicates are runtime-evaluated or not is determined by the effective
[evaluation semantic](/docs/evaluation_semantic.md).
