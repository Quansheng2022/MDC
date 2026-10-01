# Mermaid Smoke — Case A

Small post-reinstall smoke control. The Mermaid source below is copied verbatim
from Case A of `test_mermaid_triangle_v2.md`.

```mermaid
flowchart TB

    SPEC["Specification"]
    DS["DeepSeek"]
    TEST["Test System"]

    SPEC --> DS
    SPEC --> TEST
    DS --> TEST
```

End of smoke fixture.
