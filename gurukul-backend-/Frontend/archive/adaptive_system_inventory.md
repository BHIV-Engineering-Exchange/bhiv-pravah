# Adaptive System Inventory

## A. Signal Inventory

### User Interaction Signals
- **Avatar Drag**: onMouseDown/move/up and onTouchStart/move/end for dragging behavior [DraggableAvatar.jsx]
- **Chat Interactions**: onClick for send/close, onKeyPress for Enter key [AvatarChatbot.jsx]
- **Navigation**: onClick events for menu items and routing

### Time-Based Signals  
- **Study Timer**: 1-second interval updating total study time [App.jsx]- **Goal Timer**: 1-second interval updating countdown [App.jsx]
- **Notification Timeout**: 3-second cleanup for karma notifications [KarmaContext.jsx]
### API Signals
- **Chat Requests**: apiPost when user submits messages [AvatarChatbot.jsx]

### Passive Triggers
- **Component Effects**: useEffect for initialization across components
- **Storage Sync**: Cross-tab synchronization via 'storage' events

## B. Adaptive States

### Avatar System
- **isDragging**: Active during avatar movement, disables certain behaviors
- **isChatOpen**: Controls visibility of chat interface
- **pinMode**: Determines if avatar can be dragged

### Chat System  
- **isLoading**: Blocks input during API requests
- **messages**: Stores conversation history

### Global Systems
- **karma**: Tracks user points, persists to localStorage
- **notifications**: Temporary display of karma changes
- **Timer States**: studyTimeSeconds, timeLeft, isActive for goal tracking

## C. Visual Mutations

### Transitions & Animations
- **Drag Smoothness**: 0.3s ease transition when not dragging [DraggableAvatar.jsx]
- **UI Feedback**: Hover effects with 300ms transitions
- **Entry Animations**: fade-in-up and slide-in-right animations

### Dynamic Styling
- **Transformations**: Position, rotation, and scale changes for avatar
- **Visual States**: Active/inactive styles for navigation items

## D. JS Entry Points

### Core Components
- [App.jsx]: Global state and timers
- [DraggableAvatar.jsx]: Drag behavior and chat integration  
- [AvatarChatbot.jsx]: Messaging interface
- Context providers: Karma, Auth, Sidebar management