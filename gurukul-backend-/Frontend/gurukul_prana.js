// Thin wrapper for Gurukul → unified PRANA core.
// PRANA will be initialized by PranaContext when user logs in.

import '../prana-core/prana_packet_builder.js';

// Don't auto-initialize - let PranaContext handle initialization after login
// This ensures packets are only sent when user is authenticated
console.log('[PRANA-G] PRANA core loaded (will initialize after login)');


