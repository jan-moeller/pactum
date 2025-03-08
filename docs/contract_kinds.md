# Kinds Of Contracts

PyPactum knows three kinds of contract assertions:

1. **Preconditions**  
   Defined using the `@pre` function decorator, indicates that a condition must hold *before* a
   function is executed or a scope is entered.
2. **Postconditions**  
   Defined using the `@post` function decorator, indicates that a condition must hold *after* a
   function executed or a scope is left.
3. **Invariants**  
   Defined using the `@invariant` class decorator, indicates that a class must maintain a condition
   throughout the lifetime of its instances.

Along with their primary use as decorators, they can also be used as context managers.

## Preconditions

```
@pre(
   PREDICATE,
   [capture=CAPTURE],
   [clone=CLONE],
   [labels=LABELS]
)
```

1. **PREDICATE** [required]  
   A `bool`-returning callable. If the callable has parameters, then their value is determined via the
   [argument binding](/docs/argument_binding.md) rules.

   E.g. `lambda x: x > 0`, where `x` is a bound argument.

2. **CAPTURE** [optional, default=`{}`]  
   Either a `dict[str, str]` or a `set[str]`. The values are the names of variables to capture when
   the function is invoked, while the keys are the names under which their values are made available
   to the predicate.

   The arguments of the decorated function are added to the capture list implicitly.

   E.g. `{"x": "y"}` to capture `y` and make it available to the predicate as `x`, or `{"x"}` as
   shorthand for `{"x": "x"}`.

3. **CLONE** [optional, default=`{}`]  
   Either a `dict[str, str]` or a `set[str]`. The values are the names of variables to clone when
   the function is invoked, while the keys are the names under which their values are made available
   to the predicate.

   The captured variables are cloned via `copy.deepcopy` before being passed to the predicate. This
   is useful, for example, if the function modifies the captured variable, but the old value is required
   in the predicate.

   E.g. `{"x": "y"}` to clone `y` and make it available to the predicate as `x`, or `{"x"}` as
   shorthand for `{"x": "x"}`.

4. **LABELS** [optional, default=`[]`]  
   A `list` of [labels](/docs/evaluation_semantic.md) that determine the effective evaluation semantic
   of this assertion.

   E.g. `labels.expensive` to mark this precondition as expensive.

**Example**:

```python
@pre(
    lambda x, y: x > y,  # x is bound implicitly
    capture={"y": "something"},  # variable "something" is bound as "y"
)
def example(x): ...
```

## Postconditions

```
@post(
   PREDICATE,
   [capture_before=CAPTURE_BEFORE],
   [capture_after=CAPTURE_AFTER], 
   [clone_before=CLONE_BEFORE], 
   [clone_after=CLONE_AFTER], 
   [labels=LABELS], 
   [scope=SCOPE]
)
```

1. **PREDICATE** [required]  
   A `bool`-returning callable. If the callable has parameters, then their value is determined via the
   [argument binding](/docs/argument_binding.md) rules.

   E.g. `lambda r: r > 0`, where `r` is a bound argument.

2. **CAPTURE_BEFORE** [optional, default=`{}`]  
   Either a `dict[str, str]` or a `set[str]`. The values are the names of variables to capture when
   the function is invoked, while the keys are the names under which their values are made available
   to the predicate.

   E.g. `{"x": "y"}` to capture `y` and make it available to the predicate as `x`, or `{"x"}` as
   shorthand for `{"x": "x"}`.

3. **CAPTURE_AFTER** [optional, default=`{}`]  
   Either a `dict[str, str]` or a `set[str]`. The values are the names of variables to capture when
   the function returns, while the keys are the names under which their values are made available
   to the predicate.

   The first return value of the function is implicitly matched to the first predicate argument
   not explicitly bound.

   E.g. `{"x": "y"}` to capture `y` and make it available to the predicate as `x`, or `{"x"}` as
   shorthand for `{"x": "x"}`.

4. **CLONE_BEFORE** [optional, default=`{}`]  
   Either a `dict[str, str]` or a `set[str]`. The values are the names of variables to capture when
   the function is invoked, while the keys are the names under which their values are made available
   to the predicate.

   The captured variables are cloned via `copy.deepcopy` before passing them to the predicate. This
   is useful, for example, if the function modifies the captured variable, but the old value is required
   in the predicate.

   E.g. `{"x": "y"}` to clone `y` and make it available to the predicate as `x`, or `{"x"}` as
   shorthand for `{"x": "x"}`.

5. **CLONE_AFTER** [optional, default=`{}`]  
   Either a `dict[str, str]` or a `set[str]`. The values are the names of variables to capture when
   the function returns, while the keys are the names under which their values are made available
   to the predicate.

   The captured variables are cloned via `copy.deepcopy` before passing them to the predicate. This
   is useful, for example, if the function modifies the captured variable, but the old value is required
   in the predicate.

   E.g. `{"x": "y"}` to clone `y` and make it available to the predicate as `x`, or `{"x"}` as
   shorthand for `{"x": "x"}`.

6. **LABELS** [optional, default=`[]`]  
   A `list` of [labels](/docs/evaluation_semantic.md) that determine the effective evaluation semantic
   of this assertion.

   E.g. `labels.expensive` to mark this precondition as expensive.

7. **SCOPE** [optional, default=`PostconditionScope.RegularReturn`]  
   A `PostconditionScope` flagset, determining if the postcondition must hold on regular returns (the
   default), on exception returns, or both.

   E.g. `PostconditionScope.ExceptionalReturn` to apply this postcondition only when the function exits
   via an exception.

**Example**:

```python
@post(
    lambda x, old_x: len(x) > len(old_x),
    clone_before={"old_x": "x"},  # clone x before function runs
)
def example(x): ...  # function modifies x in-place
```

## Invariants

```
@invariant(
   PREDICATE,
   [capture=CAPTURE],
   [clone=CLONE],
   [labels=LABELS]
)
```

1. **PREDICATE** [required]  
   A `bool`-returning callable. If the callable has parameters, then their value is determined via the
   [argument binding](/docs/argument_binding.md) rules.

   E.g. `lambda x: x > 0`, where `x` is a bound argument.

2. **CAPTURE** [optional, default=`{}`]  
   Either a `dict[str, str]` or a `set[str]`. The values are the names of variables to capture when
   the function is invoked, while the keys are the names under which their values are made available
   to the predicate.

   The `self` argument is added to the capture list implicitly.

   E.g. `{"x": "y"}` to capture `y` and make it available to the predicate as `x`, or `{"x"}` as
   shorthand for `{"x": "x"}`.

3. **CLONE** [optional, default=`{}`]  
   Either a `dict[str, str]` or a `set[str]`. The values are the names of variables to clone when
   the function is invoked, while the keys are the names under which their values are made available
   to the predicate.

   The captured variables are cloned via `copy.deepcopy` before being passed to the predicate. This
   is useful, for example, if the function modifies the captured variable, but the old value is required
   in the predicate.

   E.g. `{"x": "y"}` to clone `y` and make it available to the predicate as `x`, or `{"x"}` as
   shorthand for `{"x": "x"}`.

4. **LABELS** [optional, default=`[]`]  
   A `list` of [labels](/docs/evaluation_semantic.md) that determine the effective evaluation semantic
   of this assertion.

   E.g. `labels.expensive` to mark this precondition as expensive.

**Example**

```python
@invariant(
    lambda self: self.x > 0,  # object must always have non-negative x
)
class Example: ...
```