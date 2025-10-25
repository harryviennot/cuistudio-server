# 🎯 Next Step: Create Database Tables

## Current Status

✅ Server is running successfully
✅ API endpoints are working
✅ Authentication is configured
❌ **Database tables need to be created** ← YOU ARE HERE

## The Issue

When testing the API, you're seeing this error:
```
"Could not find the table 'public.recipes' in the schema cache"
```

This means the database tables haven't been created in Supabase yet.

## Solution: Run the Database Schema

### Step 1: Go to Supabase SQL Editor

1. Open your browser
2. Go to: **https://app.supabase.com/project/ecsbjvgcefoloqrkyzta**
3. Log in to your Supabase account
4. Click **SQL Editor** in the left sidebar

### Step 2: Run the Schema

1. Click **"New query"**
2. Open this file: [`database/schema.sql`](database/schema.sql)
3. **Copy the ENTIRE contents** (all 440 lines)
4. **Paste** into the SQL Editor
5. Click **"Run"** (or press Cmd/Ctrl + Enter)

### Step 3: Verify Tables Were Created

After running the SQL, you should see a success message. To verify:

1. Click **Table Editor** in the left sidebar
2. You should now see these tables:
   - recipes
   - recipe_contributors
   - user_recipe_data
   - cookbooks
   - cookbook_folders
   - cookbook_recipes
   - folder_recipes
   - recipe_shares
   - cookbook_shares
   - featured_recipes
   - extraction_jobs

### Step 4: Create Storage Bucket (Optional - for images)

1. Click **Storage** in the left sidebar
2. Click **"New bucket"**
3. Name it: `recipe-images`
4. Set to **Public** (or configure policies later)
5. Click **"Create bucket"**

## What the Schema Creates

The schema.sql file creates:

- ✅ **11 tables** with proper relationships
- ✅ **Indexes** for fast queries
- ✅ **Full-text search** indexes
- ✅ **Row-Level Security (RLS)** policies
- ✅ **Triggers** for auto-updating timestamps
- ✅ **Foreign keys** with proper cascading

## After Creating Tables

Once you've run the schema, come back and test the API:

```bash
# Make sure server is running
python main.py

# Then run the tests
python3 /tmp/test_api.py
```

You should see:
```
✅ Signup successful!
✅ Get user successful!
✅ Recipe created!
✅ Cookbook created!
✅ Recipe forked!
... and more!
```

## If You Get Errors

### Error: "permission denied for schema auth"
**Solution**: Make sure you're using the SQL Editor in your Supabase dashboard, not a local SQL client.

### Error: "relation already exists"
**Solution**: Tables were already created. You're good to go! Just test the API.

### Error: "function uuid_generate_v4 does not exist"
**Solution**: The UUID extension didn't install. Try running just this first:
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```
Then run the full schema again.

## Quick Test After Setup

```bash
# Create account
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "you@gmail.com", "password": "password123"}'

# You should get back an access_token!
```

## Need Help?

- **Database schema**: [database/schema.sql](database/schema.sql)
- **Setup guide**: [database/README.md](database/README.md)
- **API docs**: http://localhost:8000/api/docs

---

**Ready?** Go run that schema.sql in Supabase and come back to test! 🚀
