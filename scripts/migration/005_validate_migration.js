/**
 * Migration Script 5: Validate Migration & Rollback Plan
 * File: scripts/migration/005_validate_migration.js
 * 
 * Checks data integrity after migration
 * 
 * Usage:
 * mongosh --file 005_validate_migration.js --eval "const dbName = 'boltchats_db'"
 */

const dbName = dbName || "boltchats_db";
const db = db.getSiblingDB(dbName);

console.log(`[Migration 5] Validation Check - Database: ${dbName}\n`);

let validationErrors = [];
let warnings = [];

// ============================================================================
// CHECK 1: All Users Have Workspaces
// ============================================================================

console.log("[Check 1] Users have workspaces...");

const usersWithoutWorkspaces = db.users.countDocuments({
  $or: [{ workspaces: { $exists: false } }, { workspaces: [] }],
});

if (usersWithoutWorkspaces > 0) {
  const msg = `❌ ${usersWithoutWorkspaces} users without workspaces`;
  console.log(msg);
  validationErrors.push(msg);
} else {
  console.log("✅ All users have workspaces");
}

// CHECK 2: All Workspaces Have At Least One Member
console.log("\n[Check 2] Workspaces have members...");

const workspacesWithoutMembers = db.workspaces.countDocuments({
  $or: [{ members: { $exists: false } }, { members: [] }],
});

if (workspacesWithoutMembers > 0) {
  const msg = `⚠️  ${workspacesWithoutMembers} workspaces without members`;
  console.log(msg);
  warnings.push(msg);
} else {
  console.log("✅ All workspaces have members");
}

// CHECK 3: All Channels Have workspace_id
console.log("\n[Check 3] All channels have workspace_id...");

const channelsWithoutWorkspace = db.channels.countDocuments({
  workspace_id: { $exists: false },
});

if (channelsWithoutWorkspace > 0) {
  const msg = `❌ ${channelsWithoutWorkspace} channels without workspace_id`;
  console.log(msg);
  validationErrors.push(msg);
} else {
  console.log("✅ All channels have workspace_id");
}

// CHECK 4: All Messages Have workspace_id and channel_id
console.log("\n[Check 4] All messages have workspace_id and channel_id...");

const messagesWithoutWorkspace = db.messages.countDocuments({
  workspace_id: { $exists: false },
});

const messagesWithoutChannel = db.messages.countDocuments({
  $or: [
    { channel_id: { $exists: false }, dm_id: { $exists: false } },
  ],
});

if (messagesWithoutWorkspace > 0) {
  const msg = `❌ ${messagesWithoutWorkspace} messages without workspace_id`;
  console.log(msg);
  validationErrors.push(msg);
} else {
  console.log("✅ All messages have workspace_id");
}

if (messagesWithoutChannel > 0) {
  const msg = `⚠️  ${messagesWithoutChannel} messages without channel_id or dm_id`;
  console.log(msg);
  warnings.push(msg);
} else {
  console.log("✅ All messages have channel_id or dm_id");
}

// CHECK 5: Unique Workspace Slugs
console.log("\n[Check 5] Unique workspace slugs...");

const duplicateSlugs = db.workspaces
  .aggregate([
    { $group: { _id: "$slug", count: { $sum: 1 } } },
    { $match: { count: { $gt: 1 } } },
  ])
  .toArray();

if (duplicateSlugs.length > 0) {
  const msg = `❌ ${duplicateSlugs.length} duplicate workspace slugs`;
  console.log(msg);
  console.log(`   Duplicates: ${duplicateSlugs.map((d) => d._id).join(", ")}`);
  validationErrors.push(msg);
} else {
  console.log("✅ All workspace slugs are unique");
}

// CHECK 6: Unique Channel Names Per Workspace
console.log("\n[Check 6] Unique channel names per workspace...");

const duplicateChannelNames = db.channels
  .aggregate([
    {
      $group: {
        _id: {
          workspace_id: "$workspace_id",
          name: "$name",
        },
        count: { $sum: 1 },
      },
    },
    { $match: { count: { $gt: 1 } } },
  ])
  .toArray();

if (duplicateChannelNames.length > 0) {
  const msg = `⚠️  ${duplicateChannelNames.length} duplicate channel names within workspaces`;
  console.log(msg);
  warnings.push(msg);
} else {
  console.log("✅ All channel names are unique per workspace");
}

// CHECK 7: Data Counts Consistency
console.log("\n[Check 7] Data count consistency...");

const stats = {
  users: db.users.countDocuments({}),
  workspaces: db.workspaces.countDocuments({}),
  channels: db.channels.countDocuments({}),
  messages: db.messages.countDocuments({}),
  rooms: db.rooms.countDocuments({}),
};

console.log(`   Users: ${stats.users}`);
console.log(`   Workspaces: ${stats.workspaces}`);
console.log(`   Channels: ${stats.channels}`);
console.log(`   Messages: ${stats.messages}`);
console.log(`   Old Rooms (for reference): ${stats.rooms}`);

if (stats.channels === 0 && stats.rooms > 0) {
  const msg = `❌ No channels created but ${stats.rooms} old rooms still exist`;
  console.log(msg);
  validationErrors.push(msg);
}

// CHECK 8: Message-Channel Link Integrity
console.log("\n[Check 8] Message-channel link integrity...");

const messagesWithInvalidChannel = db.messages
  .aggregate([
    {
      $lookup: {
        from: "channels",
        localField: "channel_id",
        foreignField: "_id",
        as: "channel",
      },
    },
    {
      $match: {
        channel_id: { $exists: true, $ne: null },
        channel: { $size: 0 },
      },
    },
  ])
  .toArray();

if (messagesWithInvalidChannel.length > 0) {
  const msg = `⚠️  ${messagesWithInvalidChannel.length} messages reference non-existent channels`;
  console.log(msg);
  warnings.push(msg);
} else {
  console.log("✅ All message-channel links are valid");
}

// ============================================================================
// SUMMARY & NEXT STEPS
// ============================================================================

console.log("\n" + "=".repeat(70));
console.log("MIGRATION VALIDATION SUMMARY");
console.log("=".repeat(70));

console.log(`\n📊 Statistics:`);
console.log(`   Users with workspaces: ${db.users.countDocuments({ "workspaces.0": { $exists: true } })}`);
console.log(`   Total workspaces: ${stats.workspaces}`);
console.log(`   Total channels: ${stats.channels}`);
console.log(`   Total messages with workspace_id: ${db.messages.countDocuments({ workspace_id: { $exists: true } })}`);

if (validationErrors.length === 0 && warnings.length === 0) {
  console.log("\n✨ VALIDATION PASSED! Migration is complete and data is consistent.");
  console.log("\n📝 Next Steps:");
  console.log("   1. Deploy new API version (v2)");
  console.log("   2. Monitor for issues");
  console.log("   3. After 1 week: Deprecate v1 endpoints");
  console.log("   4. After 1 month: Delete rooms collection");
} else {
  if (validationErrors.length > 0) {
    console.log(`\n❌ CRITICAL ERRORS (${validationErrors.length}):`);
    validationErrors.forEach((err) => console.log(`   - ${err}`));
    console.log("\n   ⚠️  DO NOT PROCEED! Fix errors before deployment.");
  }

  if (warnings.length > 0) {
    console.log(`\n⚠️  WARNINGS (${warnings.length}):`);
    warnings.forEach((warn) => console.log(`   - ${warn}`));
    console.log("\n   ℹ️  Review and investigate before deployment.");
  }
}

console.log("\n" + "=".repeat(70) + "\n");

// ============================================================================
// ROLLBACK INSTRUCTIONS
// ============================================================================

console.log("📋 ROLLBACK INSTRUCTIONS (if needed):\n");

console.log("1. Delete new collections (keeps old data intact):");
console.log("   db.workspaces.drop()");
console.log("   db.channels.drop()");
console.log("   db.direct_messages.drop()");
console.log("   db.invitations.drop()");
console.log("   db.migration_room_channel_map.drop()\n");

console.log("2. Restore users to previous state:");
console.log("   db.users.updateMany({}, { $unset: { workspaces: 1 } })\n");

console.log("3. Restore messages (undo renames):");
console.log("   db.messages.updateMany(");
console.log("     { old_room_id: { $exists: true } },");
console.log("     { $rename: { old_room_id: 'room_id' }, $unset: { workspace_id: 1, channel_id: 1 } }");
console.log("   )\n");

console.log("✅ System will be back to pre-migration state.\n");
