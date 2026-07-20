/**
 * Migration Script 4: Add workspace_id and channel_id to Messages
 * File: scripts/migration/004_add_workspace_to_messages.js
 * 
 * Usage:
 * mongosh --file 004_add_workspace_to_messages.js --eval "const dbName = 'boltchats_db'"
 */

const dbName = dbName || "boltchats_db";
const db = db.getSiblingDB(dbName);

console.log(`[Migration 4] Starting in database: ${dbName}`);
console.log("[Step 1] Loading room-to-channel mapping...\n");

// Load mapping from migration collection
const mapping = {};
const mappingDocs = db.migration_room_channel_map.find({}).toArray();

mappingDocs.forEach((doc) => {
  mapping[doc.old_room_id] = {
    channelId: ObjectId(doc.new_channel_id),
    workspaceId: ObjectId(doc.workspace_id),
  };
});

console.log(`✅ Loaded ${mappingDocs.length} room-to-channel mappings\n`);

// Get all messages
const messages = db.messages.find({}).toArray();
console.log(`Found ${messages.length} messages to process\n`);

let messagesUpdated = 0;
let errors = [];

messages.forEach((msg, index) => {
  try {
    // Find channel info from mapping
    const roomId = msg.room_id ? msg.room_id.toString() : null;

    if (!roomId || !mapping[roomId]) {
      throw new Error(
        `Message ${msg._id} has no matching room mapping (room_id: ${roomId})`
      );
    }

    const { channelId, workspaceId } = mapping[roomId];

    // Update message
    db.messages.updateOne(
      { _id: msg._id },
      {
        $set: {
          workspace_id: workspaceId,
          channel_id: channelId,
          dm_id: null,
          thread_id: null,
          is_thread_parent: false,
          thread_reply_count: 0,
          thread_participants: [],
          mentions: {
            user_ids: [],
            is_channel_mention: false,
            is_here_mention: false,
            is_everyone_mention: false,
          },
          attachments: [],
          reactions: {},
          edited_at: msg.edited_at || null,
          edited_by: null,
          edit_history: [],
          is_deleted: msg.deleted_at ? true : false,
          deleted_at: msg.deleted_at || null,
          deleted_by: null,
          is_pinned: false,
          pinned_at: null,
          pinned_by: null,
        },
        $rename: {
          room_id: "old_room_id",
        },
      }
    );

    messagesUpdated++;

    // Progress indicator
    if ((index + 1) % 1000 === 0) {
      console.log(
        `   ... processed ${index + 1}/${messages.length} messages (${messagesUpdated} updated)`
      );
    }
  } catch (e) {
    errors.push({
      message_id: msg._id.toString(),
      room_id: msg.room_id ? msg.room_id.toString() : "null",
      error: e.message,
    });
    console.error(
      `❌ Error updating message ${msg._id}: ${e.message}`
    );
  }
});

// ============================================================================
// STEP 2: Update Channel Message Counts
// ============================================================================

console.log("\n[Step 2] Updating channel message counts...");

const channels = db.channels.find({}).toArray();
channels.forEach((channel) => {
  const messageCount = db.messages.countDocuments({
    workspace_id: channel.workspace_id,
    channel_id: channel._id,
    is_deleted: false,
  });

  db.channels.updateOne(
    { _id: channel._id },
    {
      $set: { message_count: messageCount },
    }
  );
});

console.log(`✅ Updated message counts for ${channels.length} channels`);

// ============================================================================
// STEP 3: Verify Results
// ============================================================================

console.log("\n[Step 3] Verifying results...");

const messagesWithWorkspace = db.messages.countDocuments({
  workspace_id: { $exists: true, $ne: null },
});
const messagesWithChannel = db.messages.countDocuments({
  channel_id: { $exists: true, $ne: null },
});
const totalMessages = db.messages.countDocuments({});

console.log(`✅ Messages updated: ${messagesUpdated}`);
console.log(`✅ Messages with workspace_id: ${messagesWithWorkspace}/${totalMessages}`);
console.log(`✅ Messages with channel_id: ${messagesWithChannel}/${totalMessages}`);

if (errors.length > 0) {
  console.error(`\n❌ Errors encountered: ${errors.length}`);
  errors.slice(0, 10).forEach((err) => {
    console.error(
      `   - Message ${err.message_id} (room_id: ${err.room_id}): ${err.error}`
    );
  });
  if (errors.length > 10) {
    console.error(`   ... and ${errors.length - 10} more errors`);
  }
} else {
  console.log("\n✅ No errors! All messages updated successfully.");
}

console.log("\n✨ [Migration 4] Complete! All messages now have workspace_id and channel_id.");
console.log("\n📝 Next: Run migration 005_validate_migration.js");
