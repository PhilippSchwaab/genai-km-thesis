## Summary
Support report describing the procedure to enable the automatic screenshot feature ("Automatischer Bildschirmdruck") on a Fresenius machine (machine number 13560) via the HMI. Authored by [Author 1], version 1.0, dated 2025-02-19.

## Decisions
- (none recorded)

## Action items (with owner and due date where stated)
- (none recorded)

## Blockers and open questions
- Login password for user `gronservice2` is not documented in the report; it is communicated separately ("wird bekannt gegeben").

## Implementation detail (commits, files, line counts where present)
Activation procedure (performed directly on the machine HMI):
1. Connect a USB stick assigned drive letter `G:` to the machine HMI.
2. Log in with user `gronservice2` and the separately communicated password.
3. Navigate to path `Service → Bedientabeau → Inbetriebnahme`.
4. Click button `Fernwartung`.
5. Activate button `Display access level`.
6. Activate button `Automatischer Bildschirmdruck`.
7. Confirm activation via the status bar, which indicates that automatic screenshot capture is active.

No commits, files, or line counts are present in the source artifact.

## Sources
- CS-02_Automatic_Screenshot_report (support_report), v1.0, 2025-02-19, [Author 1].