# Evidence: chip dialog

Date: 2026-10-24

Component `web/src/feedback/ChipDialog.tsx`, styles `web/src/feedback/feedback.css`.
Not wired into the app yet. No component tests (node test environment, no jsdom).

## Contents

- Native `<dialog>`, opened with `showModal()` and closed with `close()` when `chip` changes
  between null and a chip. Escape (`cancel` event) calls `onClose`.
- Heading is the chip label, linked by `aria-labelledby`.
- The chip's `phrases` as buttons, in the order sent. Clicking one fills the text field only.
- Labelled textarea.
- Required radio group in a `fieldset` with a `legend`: Must have, Nice to have, Would prefer not,
  Deal-breaker.
- Save (disabled until a strength is chosen), Cancel, and Remove (only when an existing answer is
  passed in). No numeric rating.
- Strength and text start from the existing answer when editing. The form is keyed by `chip_id`, so
  opening a different chip resets it.
- The element focused at open is stored and focused again after close.
- Styles are all under `.feedback-dialog`: 44px minimum targets, visible focus, reduced-motion rule,
  dark `::backdrop`.

## Commands (from `web/`)

| command             | exit | result                      |
| ------------------- | ---- | --------------------------- |
| `npm run typecheck` | 0    | clean                       |
| `npm test`          | 0    | 6 files, 160 tests passed   |
| `npm run build`     | 0    | built                       |

## Not checked

Nothing was clicked in a browser.

## By eye, later

- Dialog opens centred over a dimmed page; focus lands inside; Tab stays in the dialog.
- Escape closes it and focus returns to the chip that opened it.
- A phrase button fills the text box and leaves strength unselected; Save stays disabled.
- Choosing a strength enables Save; Save, Cancel and Remove call back as expected.
- Editing opens with the saved strength and text; Remove appears only then.
- Looks like the deck card; reads well on a narrow phone width and with reduced motion on.
