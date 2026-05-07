## Summary
Support report documenting the procedure to enable the Automatic Screenshot feature on the HMI of a Fresenius machine (machine number 13560). The report was authored by [Author 1] and initially created on 2026-02-19.

## Decisions
- (none recorded)

## Action items (with owner and due date where stated)
- (none recorded)

## Blockers and open questions
- Login credentials for user `gronservice2` are not included in the document and must be obtained separately ("wird bekannt gegeben" / "will be communicated").

## Implementation detail (commits, files, line counts where present)
The following steps are required to enable the Automatic Screenshot feature on the machine HMI:

**Prerequisites**
- A USB stick assigned drive letter `G:` must be connected to the machine HMI.

**Procedure**
1. Log in with user `gronservice2` and the communicated password.
2. Navigate to path `Service → Bedientabeau → Inbetriebnahme`.
3. Click button `Fernwartung`.
4. Activate button `Display access level`.
5. Activate button `Automatischer Bildschirmdruck`.

**Verification**
- Successful activation is confirmed by a status bar indicator showing that `Automatischer Bildschirmdruck` is active.

No commits, files, or line counts are present in the source artifact.

## Sources
- CS-02_Automatic_Screenshot_report (support_report), v1.0, authored by [Author 1], 2025-02-19. Customer: Fresenius, Machine Number: 13560.