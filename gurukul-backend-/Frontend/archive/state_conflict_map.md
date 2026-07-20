# State Conflict Map

## A. Concurrent Triggers

### High-Risk Combinations
- **Drag + Click**: Mouse move and release during rapid interactions can confuse drag vs click detection
- **Multiple API Calls**: Rapid chat messages may cause request race conditions
- **Timer Overlaps**: Study and goal timers both updating every second

### Navigation Conflicts
- **Component Mounting**: Effects may run inconsistently during route changes
- **Cleanup Issues**: Event listeners may not properly remove during navigation

## B. State Collisions

| States                  | Conflict | Result                                     |
|-------------------------|----------|--------------------------------------------|
| isDragging × isChatOpen | YES      | Chat window doesn't follow avatar movement |
| Multiple notifications  | YES      | Visual stacking of alerts                  |
| Timer states            | YES      | Independent updates may seem inconsistent  |

## C. Race Conditions

### Critical Issues
- **Rapid Clicks**: Multiple avatar clicks may open several chat windows
- **Storage Sync**: Cross-tab updates may conflict with local changes
- **Effect Loops**: Avatar settings may trigger repeated updates

### Cleanup Problems
- **Event Listeners**: Drag handlers may persist after component unmount
- **Intervals**: Timers may continue after component destruction
- **Timeouts**: Notification timers may cause memory leaks

## D. Failure Scenarios

### User Behaviors
- **Rapid clicking**: Could cause UI confusion with multiple chat windows
- **Fast navigation**: May leave orphaned event handlers or intervals
- **Network timeouts**: Loading states may lock UI if API fails
- **Multi-tab usage**: Avatar settings may conflict between tabs

### System Failures
- **Timer drift**: Multiple intervals may become unsynchronized
- **Message ordering**: Rapid API calls may arrive out of sequence
- **Authentication expiry**: Long idle periods may break API interactions