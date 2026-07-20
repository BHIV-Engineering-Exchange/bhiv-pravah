# Demo Protection Rules

## A. Visible vs Hidden Flows

### Allowed Demo Flows
- **Home Page**: Main landing experience
- **Subject Selection**: Topic browsing interface  
- **Lesson View**: Content consumption flow
- **Chat Interface**: Basic conversation capability
- **Practice Tests**: Question/answer interaction

### Hidden/Disabled Elements
- **Admin Sections**: All administrative functionality
- **Teacher Tools**: Instructor-specific features
- **Parent Controls**: Guardian oversight features
- **Advanced Settings**: Complex configuration options
- **Avatar Customization**: Personalization features
- **Advanced Analytics**: Detailed performance metrics
- **Experimental Features**: Unstable functionality

### Soft-Disabled Behaviors
- **Deep Linking**: Redirect invalid routes to safe defaults
- **External Navigation**: Prevent leaving demo flow
- **Feature Discovery**: Hide non-core functionality
- **Error Paths**: Absorb failures silently

## B. Failure Presentation Rules

### What Users Must NEVER See
- Error messages or stack traces
- Loading screens that never resolve
- Blank or broken UI elements
- Console error notifications
- Failed API call details
- Network timeout warnings
- Authentication errors
- Invalid route indicators

### How Calm UI Is Preserved
- **Graceful Degradation**: Replace missing content with safe placeholders
- **Consistent Layout**: Maintain visual structure during failures
- **Silent Recovery**: Fix issues without user awareness
- **Predictable Behavior**: Same responses regardless of backend state
- **Stable Performance**: Prevent slow-downs from cascading failures

### Content Fallback Strategy
- **AI Responses**: Default to helpful, neutral messages
- **Lesson Content**: Show "Content loading..." placeholders
- **Subject Lists**: Display general topics when specific data unavailable
- **Practice Questions**: Present empty but structured interface

## C. Demo Integrity Guarantees

### Why Broken Screens Cannot Appear
- **Defensive Rendering**: All components wrapped in error boundaries
- **Default Values**: Every data access has safe fallback
- **Validation Layers**: Data checked before UI rendering
- **State Isolation**: Component failures don't affect others

### Why Errors Cannot Leak
- **Silent Absorption**: Failures caught and discarded internally
- **No User Notifications**: No error messages presented to user
- **Clean Console**: Production builds suppress internal errors
- **Resource Cleanup**: Failed operations don't leak memory

### Why Demo Feels Intentional
- **Consistent UX**: Same behavior patterns throughout
- **Controlled Flow**: Only approved navigation paths available
- **Professional Appearance**: Clean, polished interface always maintained
- **Reliable Performance**: No unexpected delays or crashes
- **Focused Experience**: Distractions and complexity removed

### Protection Mechanisms
- **API Gatekeeping**: Only approved endpoints accessed
- **State Validation**: All data verified before use
- **Component Isolation**: Individual component failures contained
- **Resource Management**: Proper cleanup of all assets
- **Navigation Control**: Prevent invalid route access

## D. Silent Operation Standards

### No Observable Failures
- Zero error dialogs or notifications
- No visible loading failures
- No broken image/video placeholders
- No crashed or frozen UI elements
- No unexpected redirects or popups

### Performance Maintenance
- Fast loading under all conditions
- Smooth animations regardless of data state
- Responsive interactions during API failures
- Stable memory usage during stress

### Professional Presentation
- Polished interface in all scenarios
- Helpful content even when data unavailable
- Natural user flow without interruptions
- Reliable behavior for investor demonstration