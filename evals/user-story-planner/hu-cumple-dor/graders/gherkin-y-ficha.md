---
type: regex
flags: s
pattern: "DADO QUE.*CUANDO.*ENTONCES.*\\|\\s*Alcance\\s*\\|\\s*(Backend|Frontend|Full-stack)"
match: contains
target: last_message
---

Debe existir al menos un escenario Gherkin completo (DADO QUE / CUANDO / ENTONCES) y, más adelante, la fila `Alcance` de la Ficha técnica con un valor válido.
