/**
 * Migration Script 3: Migrate Rooms to Channels
 * File: scripts/migration/003_migrate_rooms_to_channels.js
 * 
 * For each room, create a corresponding channel in the owner's workspace
 * 
 * Usage:
 * mongosh --file 003_migrate_rooms_to_channels.js --eval "const dbName = 'boltchats_db'"
 */

const dbName = dbName || "boltchats_db";
const db = db.getSiblingDB(dbName);

console.log(`[Migration 3] Starting in database: ${dbName}`);
console.log("[Step 1] Creating channel mapping...\n");

// Helper function: Get user's default workspace
function getUserWorkspaceId(userId) {
  const user = db.users.findOne({
    _id: ObjectId(userId),
    "workspaces.role": "owner",
  });

  if (!user || !user.workspaces || user.workspaces.length === 0) {
    throw new Error(
      `User ${userId} has no workspace! Run migration 002 first.`
    );
  }

  // Return owner's workspace
  const ownerWorkspace = user.workspaces.find((ws) => ws.role === "owner");
  if (!ownerWorkspace) {
    throw new Error(`User ${userId} is not owner of any workspace!`);
  }

  return ownerWorkspace.workspace_id;
}

// Get all rooms
const rooms = db.rooms.find({}).toArray();
console.log(`Found ${rooms.length} rooms to migrate\n`);

let channelsCreated = 0;
let errors = [];
const roomToChannelMap = {}; // For message migration

rooms.forEach((room, index) => {
  try {
    // Get owner's workspace
    const workspaceId = getUserWorkspaceId(room.owner_id);

    // Create channel
    const channel = {
      workspace_id: ObjectId(workspaceId),
      name: room.name,
      display_name: room.name,
      description: room.description || "",
      type: room.is_private ? "private" : "public",
      topic: "",
      purpose: "",
      owner_id: ObjectId(room.owner_id),
      members: room.member_ids.map((id) => ObjectId(id)),
      settings: {
        can_post: ["member"],
        can_invite: ["admin"],
        thread_replies_allowed: true,
        auto_join_new_members: true,
        posting_restrictions: "none",
      },
      is_archived: false,
      archived_at: null,
      archived_by: null,
      is_default: false,
      message_count: 0, // Will be updated later
      member_count: room.member_ids.length,
      last_message_at: null,
      shared_workspaces: [],
      created_at: room.created_at,
      updated_at: room.updated_at,
    };

    // Insert channel
    const result = db.channels.insertOne(channel);
    const channelId = result.insertedId;
    channelsCreated++;

    // Store mapping for message migration
    roomToChannelMap[room._id.toString()] = {
      channelId: channelId.toString(),
      workspaceId: workspaceId.toString(),
    };

    console.log(
      `✅ Room '${room.name}' → Channel (${room.is_private ? "private" : "public"})`
    );

    // Progress indicator
    if ((index + 1) % 10 === 0) {
      console.log(
        `   ... processed ${index + 1}/${rooms.length} rooms (${channelsCreated} created)`
      );
    }
  } catch (e) {
    errors.push({
      room_id: room._id.toString(),
      room_name: room.name,
      error: e.message,
    });
    console.error(`❌ Error migrating room '${room.name}': ${e.message}`);
  }
});

// ============================================================================
// STEP 2: Create Mapping File (for use in next migration)
// ============================================================================

console.log("\n[Step 2] Saving room-to-channel mapping...");

// Store mapping in a temporary collection
db.migration_room_channel_map.deleteMany({});
Object.entries(roomToChannelMap).forEach(([roomId, mapping]) => {
  db.migration_room_channel_map.insertOne({
    old_room_id: roomId,
    new_channel_id: mapping.channelId,
    workspace_id: mapping.workspaceId,
  });
});

console.log(`✅ Mapping stored in migration_room_channel_map collection`);

// ============================================================================
// STEP 3: Verify Results
// ============================================================================

console.log("\n[Step 3] Verifying results...");

const totalChannels = db.channels.countDocuments({});
console.log(`✅ Channels created: ${channelsCreated}`);
console.log(`✅ Total channels in DB: ${totalChannels}`);
console.log(`✅ Mapping entries: ${db.migration_room_channel_map.countDocuments({})}`);

if (errors.length > 0) {
  console.error(`\n❌ Errors encountered: ${errors.length}`);
  errors.forEach((err) => {
    console.error(
      `   - Room '${err.room_name}' (${err.room_id}): ${err.error}`
    );
  });
} else {
  console.log("\n✅ No errors! All rooms migrated successfully.");
}

console.log(
  "\n✨ [Migration 3] Complete! All rooms migrated to channels."
);
console.log("\n📝 Next: Run migration 004_add_workspace_to_messages.js");
