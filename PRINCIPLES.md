# Single-responsibility principles

Two distinct rules travel under the name "single responsibility", and conflating them is a
common misreading. This file states both, plus the naming and structure rules the same two
source chapters make alongside them, so a module and a function each have their own test.

## 1. SRP — actor cohesion (Clean Architecture ch. 7)

A module is responsible to one, and only one, **actor** — the person or role who can demand
a change to it. Not "does one thing"; a module can do several things for the same actor and
still satisfy this rule. The violation is two actors depending on the same module, so a change
requested by one silently reaches the other.

⚠️ **DRY caveat.** Code that looks identical but serves two different actors must be allowed
to diverge. Deduplicating it is the defect — merging two actors' logic into one shared
function re-creates the coupling this rule exists to prevent, even though it reads as good
practice everywhere else.

## 2. One job per function/method (Clean Code ch. 3, "Do One Thing")

A function does one thing, at one level of abstraction, and does it well. **This is explicitly
NOT SOLID's SRP** — rule 2 is about a function's *body*, rule 1 is about a module's
*audience*. A function can satisfy rule 2 while its enclosing module still fails rule 1 (does
one thing, but for two actors), and a module can satisfy rule 1 while a function inside it
fails rule 2 (one actor, but the function does three things for that actor).

## 3. Verb naming

A function is named with a verb or verb phrase describing that exact task (`save_user`,
`validate_email`), following the target language's own convention — `snake_case` in Python,
`camelCase` in TypeScript/JavaScript.

## 4. No hidden side effects

Avoid *hidden* state mutations or *secondary* tasks. The qualifier is load-bearing:
`save_user` has a side effect by design, announced by its name, and is correct. The violation
is an effect the name does not announce — `validate_email` that also writes to a database, or
`get_total` that also mutates the cart it reads.

## 5. Classes are nouns, functions are verbs (Clean Code ch. 2)

Rule 3 is only half the naming rule. A class or type name is a noun or noun phrase —
`Customer`, `WikiPage`, `Account` — and never takes a verb name. SRP's subject is the
module/class, so a naming rule that covers only functions leaves the doc silent on its own
subject.

## 6. Command-Query Separation (Clean Code ch. 3)

A function either **does** something or **answers** something, never both. The shape to avoid
is `if (set("username", "bob"))` — a call that mutates state and also returns a value the
caller branches on. This is the decidable edge of rule 4: where "hidden side effect" can be a
judgement call, a function that is simultaneously a command and a query is not.

## 7. One level of abstraction per function (Clean Code ch. 3)

The operational test for rule 2's "does one thing": every statement in a function's body
should sit at the same level of abstraction. Mixing a high-level call like `getHtml()` with a
low-level operation like `.append("\n")` in the same body is the tell that the function is
doing more than one thing, regardless of how short it is.
