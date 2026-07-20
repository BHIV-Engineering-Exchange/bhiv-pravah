# 🚀 BlackHole Blockchain

**A high-performance, multi-token blockchain with AI-powered fraud detection, TANTRA enforcement layer, and cross-chain bridge capabilities.**

## 🎯 **Goal: List BHX Token on Cryptocurrency Exchanges**

**Current Status: 85% Complete - 70% Production Ready**

> ⚠️ **Note:** Core functionality is solid, but critical fixes needed for structured logging and test suite before full production deployment.

---

## ⚡ **Quick Start**

### **1. Start the Blockchain**
```bash
start_blockchain.bat
```

### **2. Start Web Wallet** (New Terminal)
```bash
start_wallet_web.bat
```

### **3. Start Fraud Detection** (New Terminal)
```bash
start_cybersecurity_system.bat
```

### **4. Start Token Faucet** (New Terminal)
```bash
start_integrated_faucet.bat
```

### **5. Access Services**
- **Blockchain API:** http://localhost:8080
- **Web Wallet:** http://localhost:3001
- **Token Faucet:** http://localhost:3002
- **Fraud Detection Service:** http://localhost:9090
- **Bridge Dashboard:** http://localhost:8084

### **🐳 Docker Quick Start** (Alternative)
```bash
# Start all services with Docker
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

---

## 🔥 **Key Features**

### **✅ Multi-Token Support**
- **BHX** - Native blockchain token
- **ETH** - Ethereum integration
- **USDT** - Stablecoin support
- **SOL** - Solana integration

### **✅ TANTRA Enforcement Layer** (NEW)
- **Triple-hash validation** - ExecutionAgent, ValidationAgent, ReplayAgent
- **Fraud service integration** - Real-time transaction verification
- **Hard rejection on mismatch** - HTTP 403 for failed validation
- **Truth store** - Append-only audit trail (tantra_truth.jsonl)
- **Blockchain verification** - Phase 5 on-chain validation
- **Trace ID injection** - Full transaction traceability

### **✅ AI-Powered Fraud Detection**
- Real-time transaction monitoring
- Suspicious wallet flagging
- ML-based pattern recognition
- Automatic transaction blocking
- Integration with TANTRA enforcement

### **✅ Cross-Chain Bridge**
- Ethereum ↔ BlackHole transfers
- Real-time event listening
- Secure cross-chain operations
- Multi-chain token support
- Replay protection with BoltDB
- Circuit breaker patterns

### **✅ DEX & OTC Trading**
- Decentralized exchange functionality
- OTC trade verification
- Multi-signature support
- Liquidity pool management
- Slippage protection

### **✅ Professional Web Wallet**
- Browser-based interface
- Multi-token management
- Transaction history
- Real-time balance updates
- Faucet integration

### **✅ High Performance**
- 1000+ TPS capability
- 6-second block times
- Concurrent processing
- Optimized storage (LevelDB)
- P2P networking with peer discovery

---

## 📊 **System Architecture**

```
┌─────────────────┐    ┌─────────────────────────────────────┐    ┌─────────────────┐
│   Web Wallet    │    │         Blockchain Core             │    │  Fraud Service  │
│   (Port 3001)   │    │         (Port 8080)                 │    │   (Port 9090)   │
└─────────────────┘    │                                     │    └─────────────────┘
         │             │  ┌──────────────────────────────┐  │             │
         │             │  │   TANTRA Enforcement Layer   │  │             │
         │             │  │  - ExecutionAgent            │  │             │
         │ ── TX ─────▶│  │  - ValidationAgent ──────────┼──┼─── Check ──▶
         │             │  │  - ReplayAgent               │  │             │
         │             │  │  - Hash Equality Gate        │◀─┼── Allow/Block
         │             │  │  - Truth Store               │  │             │
         │             │  └──────────────────────────────┘  │
         │◀── Result ──│                                     │
         
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Token Faucet   │    │  Cross-Chain    │    │   Bridge SDK    │    │   External      │
│   (Port 3002)   │    │     Bridge      │    │   (Port 8084)   │    │    Chains       │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         │ ── Token Requests ────▶                       │                       │
         │                       │ ── Bridge TXs ───────▶                       │
         │                       │                       │ ── Listen Events ────▶
         │                       │                       │◀── ETH/SOL Events ───│
```

---

## 🛠️ **Development**

### **Prerequisites**
- Go 1.19+
- Node.js 16+
- Git

### **Build from Source**
```bash
# Clone repository
git clone <repository-url>
cd blackhole-blockchain

# Build blockchain
cd core/relay-chain/cmd/relay
go build -o relay.exe

# Build wallet service
cd services/wallet
go build -o wallet.exe

# Build faucet service
cd services/validator-faucet
go build -o faucet.exe
```

### **Testing**
```bash
# Test transaction (goes through TANTRA enforcement)
curl -X POST http://localhost:8080/api/relay/submit \
  -H "Content-Type: application/json" \
  -d '{"type":"token_transfer","from":"alice","to":"bob","amount":100,"token_id":"BHX","nonce":1,"timestamp":1234567890}'

# Check balance
curl http://localhost:8080/api/balance/alice/BHX

# System health
curl http://localhost:8080/api/health

# Verify TANTRA transaction
curl "http://localhost:8080/api/tantra/verify?tx_hash=<transaction_id>"

# View TANTRA audit records
curl http://localhost:8080/api/tantra/records

# Bridge status
curl http://localhost:8084/bridge/status
```

---

## 📚 **Documentation**

### **Core Documentation**
- **[Complete Project Overview](PROJECT_OVERVIEW.md)** - Detailed project status
- **[System Test Report](REPORT.md)** - Comprehensive testing results
- **[API Documentation](docs/API_DOCUMENTATION.md)** - Complete API reference
- **[Production Deployment](docs/PRODUCTION_DEPLOYMENT_GUIDE.md)** - Deployment guide

### **TANTRA Enforcement**
- **[TANTRA Review Packet](REVIEW_PACKET.md)** - Complete enforcement integration
- **[AI Fraud Integration](AI_FRAUD_INTEGRATION_GUIDE.md)** - Fraud detection setup

### **Bridge & Cross-Chain**
- **[Bridge Integration Guide](bridge/INTEGRATION_GUIDE.md)** - Bridge setup
- **[Bridge SDK Documentation](bridge-sdk/docs/README.md)** - SDK usage

### **Wallet & Services**
- **[Wallet Web UI Guide](docs/WALLET_WEB_UI_GUIDE.md)** - Web wallet usage
- **[Wallet Setup Guide](WALLET_SETUP_GUIDE.md)** - Wallet configuration

---

## 🏦 **Exchange Listing Progress**

### **✅ Completed Requirements**
- [x] Multi-token blockchain (BHX, ETH, USDT, SOL)
- [x] TANTRA enforcement layer (100% complete)
- [x] AI fraud detection (integrated with TANTRA)
- [x] Cross-chain bridge (90% complete)
- [x] Professional API (REST + gRPC)
- [x] Web wallet interface
- [x] DEX & OTC trading
- [x] Performance optimization
- [x] Docker deployment
- [x] Monitoring & alerting

### **🔴 Critical Fixes Required (1-2 days)**
- [ ] **Structured logging JSON parsing** - Currently broken, blocks audit trail
- [ ] **Bridge test suite compilation** - Missing ReplayManager implementation
- [ ] **API signature updates** - Test files need updating

### **🟡 Remaining Tasks (1-2 weeks)**
- [ ] MongoDB integration for wallet service
- [ ] 1000+ TPS stress testing
- [ ] Security audit report
- [ ] Token whitepaper completion
- [ ] Exchange integration docs

**Estimated completion: 2-3 weeks (after critical fixes)**

---

## 🤝 **Team**

### **Blockchain Core (BHC)**
- **Shivam** - Token logic, approvals, event emission, core blockchain
- **Nihal** - DEX engine, OTC trading, pool health, swap mechanics
- **Sairam** - Staking core, validator logic, reward flows
- **Jay** - Wallet service, key management, validator onboarding

### **Cybercrime / AI Enforcement (AIxLaw)**
- **Prakash Yadav** - TANTRA enforcement integration (ExecutionAgent, ValidationAgent, ReplayAgent)
- **Keval** - Cybercrime smart contract lead, freeze/unfreeze logic
- **Aryan** - Event hooking, logging, multi-chain freeze logic
- **Yashika** - ML audit, violation detection, pattern recognition

### **Cross-Chain & Integration**
- **Shantanu** - Bridge SDK, cross-chain sync, relay infrastructure

### **DevOps & Quality**
- **Vinayak** - Docker, PRs, GitOps, integration testing, code review

---

## 📄 **License**

MIT License - See LICENSE file for details

---

## ⚠️ **Known Issues**

### **Critical (Must Fix Before Production)**
1. **Structured Logging Failure** - JSON parsing broken in token system tests
   - Impact: No transaction audit trail
   - Status: Requires immediate fix
   - ETA: 1-2 days

2. **Bridge Test Compilation Errors** - Missing ReplayManager in Bridge struct
   - Impact: Cannot validate replay protection
   - Status: Code incompatibility
   - ETA: 1 day

3. **API Signature Mismatches** - System test files incompatible with current codebase
   - Impact: Integration testing blocked
   - Status: Function signatures changed
   - ETA: 1 day

### **Medium Priority**
4. **Wallet Service MongoDB Dependency** - Not documented, requires manual setup
5. **Token Whitepaper Incomplete** - Exchange listing requirement
6. **Security Audit Pending** - Third-party validation needed

See [REPORT.md](REPORT.md) for detailed test results and issue analysis.

---

## 🚀 **Get Started**

1. **Run `start_blockchain.bat`** - Start the blockchain with TANTRA enforcement
2. **Run `start_wallet_web.bat`** - Start web wallet (requires MongoDB)
3. **Run `start_cybersecurity_system.bat`** - Start fraud detection service
4. **Visit http://localhost:3001** - Use the wallet
5. **Visit http://localhost:8080** - Access blockchain API
6. **Read [REVIEW_PACKET.md](REVIEW_PACKET.md)** - Understand TANTRA enforcement
7. **Read [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - Complete system overview

**85% Complete - Critical fixes needed before exchange listing!** 🎯⚠️
