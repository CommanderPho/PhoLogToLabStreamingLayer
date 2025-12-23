---
name: Move Log History to Top-Level
overview: Restructure the GUI to move the "Log History:" text pane from the Manual Log tab to the root level, making it always visible in the bottom half of the window across all tabs.
todos:
  - id: restructure-root-grid
    content: Modify root grid configuration to support two rows (notebook top, log display bottom) with equal weights
    status: completed
  - id: create-log-frame
    content: Create new top-level frame for log display area with 'Log History:' label
    status: completed
    dependencies:
      - restructure-root-grid
  - id: move-log-display
    content: Move self.log_display ScrolledText widget from manual_tab to the new top-level frame
    status: completed
    dependencies:
      - create-log-frame
  - id: move-clear-button
    content: Move 'Clear Log Display' button from manual_tab to the new log display frame
    status: completed
    dependencies:
      - create-log-frame
  - id: remove-from-manual-tab
    content: Remove log display elements (label, widget, rowconfigure) from the Manual Log tab
    status: completed
    dependencies:
      - move-log-display
      - move-clear-button
---

# Move Log History Pane to Top-Level

## Current Structure

- The "Log History:" pane (`self.log_display`) is currently inside the "Manual Log" tab (lines 686-693)
- The root window uses a single-row grid layout with the notebook taking all space
- The log display is only visible when the Manual Log tab is selected

## Changes Required

### 1. Restructure Root Grid Layout

- Modify `setup_gui()` in [`logger_app.py`](src/phologtolabstreaminglayer/logger_app.py) (lines 600-728)
- Change root grid from single row to two rows:
- Row 0: Notebook (top half, weight=1)
- Row 1: Log History pane (bottom half, weight=1)
- Update `self.root.rowconfigure()` to configure both rows with equal weight

### 2. Create Top-Level Log Display Frame

- Create a new frame at root level for the log display area
- Add "Log History:" label to this frame
- Move `self.log_display` (ScrolledText widget) from manual_tab to this frame
- Configure the frame to expand and fill the bottom half

### 3. Move Clear Log Button

- Move the "Clear Log Display" button from manual_tab (line 703) to the new log display frame
- This keeps the clear functionality accessible from any tab

### 4. Remove Log Display from Manual Tab

- Remove the "Log History:" label from manual_tab (line 687)
- Remove `self.log_display` grid placement from manual_tab (line 692)
- Remove the rowconfigure for the log display row in manual_tab (line 693)
- Keep the text entry and log button in the Manual Log tab

### 5. Update Grid Configuration

- Ensure the notebook frame only takes the top half (sticky to N, S, E, W but in row 0)
- Ensure the log display frame takes the bottom half (sticky to N, S, E, W in row 1)
- Both should have equal weight to maintain 50/50 split

## Files to Modify

- [`src/phologtolabstreaminglayer/logger_app.py`](src/phologtolabstreaminglayer/logger_app.py) - `setup_gui()` method (lines 600-728)

## Notes

- The `update_log_display()` method (line 1744) already works at the instance level, so it will continue to work without changes