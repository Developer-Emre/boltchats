/**
 * Migration Script 2: Backfill User Workspaces
 * File: scripts/migration/002_backfill_user_workspaces.js
 * 
 * For each existing user, create a default workspace and add user to it
 * 
 * Usage:
 * mongosh --file 002_backfill_user_workspaces.js --eval "const dbName = 'boltchats_db'"
 */

const dbName = dbName || "boltchats_db";
const db = db.getSiblingDB(dbName);

console.log(`[Migration 2] Starting in database: ${dbName}`);
console.log("[Step 1] Backfilling user workspaces...\n");

// Get all users
const users = db.users.find({}).toArray();
console.log(`Found ${users.length} users to process`);

let workspacesCreated = 0;
let usersUpdated = 0;
let errors = [];

users.forEach((user, index) => {
  try {
    // Check if user already has workspaces
    if (user.workspaces && user.workspaces.length > 0) {
      console.log(
        `⏭️  User ${user.username} (${user.email}) already has workspaces, skipping`
      );
      return;
    }

    // Create default workspace
    const workspaceSlug = user.username
      .toLowerCase()
      .replace(/[^a-z0-9]/g, "-");
    const workspaceName = `${user.username}'s Workspace`;

    const workspace = {
      name: workspaceName,
      slug: workspaceSlug,
      description: "",
      icon_url: null,
      owner_id: user._id,
      members: [
        {
          user_id: user._id,
          role: "owner",
          joined_at: new Date(),
          is_active: true,
        },
      ],
      settings: {
        require_email_verification: true,
        allow_external_sharing: false,
        sso_enabled: false,
        message_retention_days: 90,
        file_retention_days: 365,
        max_upload_size_mb: 100,
        default_channel_visibility: "public",
        auto_join_channels: ["general"],
        guest_can_post: true,
        guest_can_download_files: false,
      },
      billing: {
        plan: "free",
        billing_email: user.email,
        billing_cycle_start: null,
        billing_cycle_end: null,
      },
      member_count: 1,
      channel_count: 0,
      message_count: 0,
      is_active: true,
      is_archived: false,
      archived_at: null,
      archived_by: null,
      created_at: new Date(),
      updated_at: new Date(),
    };

    // Insert workspace
    const result = db.workspaces.insertOne(workspace);
    const workspaceId = result.insertedId;
    workspacesCreated++;

    // Update user: add workspace to workspaces array
    db.users.updateOne(
      { _id: user._id },
      {
        $set: {
          workspaces: [
            {
              workspace_id: workspaceId,
              role: "owner",
              joined_at: new Date(),
              is_active: true,
            },
          ],
        },
      }
    );
    usersUpdated++;

    console.log(
      `✅ User ${user.username}: Created workspace '${workspaceName}' (${workspaceSlug})`
    );

    // Progress indicator
    if ((index + 1) % 10 === 0) {
      console.log(`   ... processed ${index + 1}/${users.length} users`);
    }
  } catch (e) {
    errors.push({
      user_id: user._id,
      username: user.username,
      error: e.message,
    });
    console.error(`❌ Error processing user ${user.username}: ${e.message}`);
  }
});

// ============================================================================
// STEP 2: Verify Results
// ============================================================================

console.log("\n[Step 2] Verifying results...");

const usersWithWorkspaces = db.users.countDocuments({
  workspaces: { $exists: true, $ne: [] },
});
const totalUsers = db.users.countDocuments({});

console.log(`✅ Workspaces created: ${workspacesCreated}`);
console.log(`✅ Users updated: ${usersUpdated}`);
console.log(`✅ Total workspaces in DB: ${db.workspaces.countDocuments({})}`);
console.log(`✅ Users with workspaces: ${usersWithWorkspaces}/${totalUsers}`);

if (errors.length > 0) {
  console.error(`\n❌ Errors encountered: ${errors.length}`);
  errors.forEach((err) => {
    console.error(
      `   - User ${err.username} (${err.user_id}): ${err.error}`
    );
  });
}

console.log(
  "\n✨ [Migration 2] Complete! All users now have default workspaces."
);
