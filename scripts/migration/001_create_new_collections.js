/**
 * Migration Script 1: Create New Collections & Indexes
 * File: scripts/migration/001_create_new_collections.js
 * 
 * Usage:
 * mongosh --file 001_create_new_collections.js --eval "const dbName = 'boltchats_db'"
 */

const dbName = dbName || "boltchats_db";
const db = db.getSiblingDB(dbName);

console.log(`[Migration 1] Starting in database: ${dbName}`);

// ============================================================================
// STEP 1: Create Collections (if they don't exist)
// ============================================================================

console.log("[Step 1] Creating collections...");

// Create workspaces collection
try {
  db.createCollection("workspaces");
  console.log("✅ Created 'workspaces' collection");
} catch (e) {
  if (e.codeName === "NamespaceExists") {
    console.log("ℹ️  'workspaces' collection already exists");
  } else {
    throw e;
  }
}

// Create channels collection
try {
  db.createCollection("channels");
  console.log("✅ Created 'channels' collection");
} catch (e) {
  if (e.codeName === "NamespaceExists") {
    console.log("ℹ️  'channels' collection already exists");
  } else {
    throw e;
  }
}

// Create direct_messages collection
try {
  db.createCollection("direct_messages");
  console.log("✅ Created 'direct_messages' collection");
} catch (e) {
  if (e.codeName === "NamespaceExists") {
    console.log("ℹ️  'direct_messages' collection already exists");
  } else {
    throw e;
  }
}

// Create invitations collection
try {
  db.createCollection("invitations");
  console.log("✅ Created 'invitations' collection");
} catch (e) {
  if (e.codeName === "NamespaceExists") {
    console.log("ℹ️  'invitations' collection already exists");
  } else {
    throw e;
  }
}

// ============================================================================
// STEP 2: Create Indexes
// ============================================================================

console.log("\n[Step 2] Creating indexes...");

// Workspaces indexes
db.workspaces.createIndex({ slug: 1 }, { unique: true });
console.log("✅ workspaces: index on slug (unique)");

db.workspaces.createIndex({ owner_id: 1 });
console.log("✅ workspaces: index on owner_id");

db.workspaces.createIndex({ "members.user_id": 1 });
console.log("✅ workspaces: index on members.user_id");

// Channels indexes
db.channels.createIndex({ workspace_id: 1 });
console.log("✅ channels: index on workspace_id");

db.channels.createIndex({ workspace_id: 1, name: 1 }, { unique: true });
console.log("✅ channels: unique index on (workspace_id, name)");

db.channels.createIndex({ workspace_id: 1, type: 1 });
console.log("✅ channels: index on (workspace_id, type)");

db.channels.createIndex({ workspace_id: 1, is_archived: 1 });
console.log("✅ channels: index on (workspace_id, is_archived)");

// DirectMessages indexes
db.direct_messages.createIndex({ workspace_id: 1 });
console.log("✅ direct_messages: index on workspace_id");

db.direct_messages.createIndex({ workspace_id: 1, participants: 1 });
console.log("✅ direct_messages: index on (workspace_id, participants)");

// Invitations indexes
db.invitations.createIndex({ code: 1 }, { unique: true });
console.log("✅ invitations: unique index on code");

db.invitations.createIndex({ workspace_id: 1, status: 1 });
console.log("✅ invitations: index on (workspace_id, status)");

db.invitations.createIndex({ invited_email: 1 });
console.log("✅ invitations: index on invited_email");

db.invitations.createIndex({ code_expires_at: 1 }, { expireAfterSeconds: 0 });
console.log("✅ invitations: TTL index on code_expires_at");

// Users indexes (updates)
db.users.createIndex({ email: 1 }, { unique: true });
console.log("✅ users: unique index on email");

db.users.createIndex({ "workspaces.workspace_id": 1 });
console.log("✅ users: index on workspaces.workspace_id");

// Messages indexes (updates)
db.messages.createIndex({ workspace_id: 1 });
console.log("✅ messages: index on workspace_id");

db.messages.createIndex({ workspace_id: 1, channel_id: 1, created_at: -1 });
console.log("✅ messages: index on (workspace_id, channel_id, created_at)");

db.messages.createIndex({ workspace_id: 1, dm_id: 1, created_at: -1 });
console.log("✅ messages: index on (workspace_id, dm_id, created_at)");

db.messages.createIndex({ thread_id: 1 });
console.log("✅ messages: index on thread_id");

// ============================================================================
// STEP 3: Verify Collections Exist
// ============================================================================

console.log("\n[Step 3] Verifying collections...");

const collections = db.getCollectionNames();
const requiredCollections = [
  "workspaces",
  "channels",
  "direct_messages",
  "invitations",
];

requiredCollections.forEach((col) => {
  if (collections.includes(col)) {
    console.log(`✅ ${col} exists`);
  } else {
    throw new Error(`❌ ${col} NOT found!`);
  }
});

console.log(
  "\n✨ [Migration 1] Complete! All collections and indexes created."
);
