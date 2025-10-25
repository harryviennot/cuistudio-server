# Quick Start Guide

Get your Recipe App Backend up and running in minutes!

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Supabase account (free tier works)
- OpenAI API key

## 5-Minute Setup

### 1. Install System Dependencies

**macOS:**
```bash
brew install ffmpeg tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg tesseract-ocr
```

**Windows:**
- Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
- Download Tesseract from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### 2. Set Up Python Environment

```bash
# Navigate to project directory
cd new-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Supabase

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Wait for project provisioning (2-3 minutes)
3. Go to **SQL Editor** in your project dashboard
4. Copy the entire contents of `database/schema.sql`
5. Paste and click **Run**
6. Go to **Storage** and create a bucket named `recipe-images`
7. Make the bucket public or configure appropriate policies

### 4. Set Up Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

Fill in your credentials:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=your_publishable_key_here
SUPABASE_SECRET_KEY=your_secret_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

**Where to find Supabase keys:**
- Go to your project settings
- Click "API" in the sidebar
- Copy "URL", "publishable" key, and "secret" key (you may need to create new API keys in the new format)

**Where to get OpenAI API key:**
- Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- Create a new API key

### 5. Run the Application

```bash
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 6. Test the API

Open your browser and go to:
- **API Docs**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

You should see the Swagger UI with all available endpoints!

## Your First API Call

### 1. Create an Account

```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "your-secure-password"
  }'
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "email": "your-email@example.com"
  }
}
```

Save your `access_token` - you'll need it for authenticated requests!

### 2. Create Your First Recipe (Manual)

```bash
curl -X POST http://localhost:8000/api/v1/recipes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Simple Pasta",
    "description": "A quick and easy pasta recipe",
    "source_type": "paste",
    "ingredients": [
      {
        "name": "pasta",
        "quantity": 200,
        "unit": "g"
      },
      {
        "name": "olive oil",
        "quantity": 2,
        "unit": "tbsp"
      }
    ],
    "instructions": [
      {
        "step_number": 1,
        "text": "Boil water in a large pot"
      },
      {
        "step_number": 2,
        "text": "Add pasta and cook for 10 minutes",
        "timer_minutes": 10
      }
    ],
    "servings": 2,
    "difficulty": "easy",
    "tags": ["quick", "italian"],
    "categories": ["dinner"],
    "timings": {
      "prep_time_minutes": 5,
      "cook_time_minutes": 10,
      "total_time_minutes": 15
    }
  }'
```

### 3. Extract Recipe from Smart Paste

```bash
curl -X POST http://localhost:8000/api/v1/extraction/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "source_type": "paste",
    "text_content": "Chocolate Chip Cookies\n\nIngredients:\n- 2 cups flour\n- 1 cup sugar\n- 1/2 cup butter\n- 2 eggs\n- 1 cup chocolate chips\n\nInstructions:\n1. Mix dry ingredients\n2. Add wet ingredients\n3. Fold in chocolate chips\n4. Bake at 350F for 12 minutes"
  }'
```

This returns a job ID. Check the status:

```bash
curl http://localhost:8000/api/v1/extraction/jobs/JOB_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

When `status` is `"completed"`, you'll have a `recipe_id`!

### 4. Search for Recipes

```bash
curl -X POST http://localhost:8000/api/v1/recipes/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "query": "quick pasta recipes under 20 minutes",
    "limit": 5
  }'
```

## Next Steps

### Explore More Features

1. **Fork a Recipe**: `POST /api/v1/recipes/{recipe_id}/fork`
2. **Create Cookbooks**: `POST /api/v1/cookbooks`
3. **Add to Cookbook**: `POST /api/v1/cookbooks/{id}/recipes`
4. **Rate Recipes**: `POST /api/v1/recipes/{id}/user-data`
5. **Extract from Video**: `POST /api/v1/extraction/submit` with `source_type: "video"`

### Using the Interactive Docs

1. Go to http://localhost:8000/api/docs
2. Click **Authorize** button
3. Enter your token: `Bearer YOUR_ACCESS_TOKEN`
4. Click **Authorize**
5. Now you can test all endpoints interactively!

### Create a Cookbook

```bash
curl -X POST http://localhost:8000/api/v1/cookbooks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "My Favorite Recipes",
    "subtitle": "A collection of my go-to meals",
    "description": "These are the recipes I cook most often",
    "is_public": false
  }'
```

### Add Recipe to Cookbook

```bash
curl -X POST http://localhost:8000/api/v1/cookbooks/COOKBOOK_ID/recipes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "recipe_id": "RECIPE_ID"
  }'
```

## Common Issues

### Issue: "Module not found" error

**Solution**: Make sure you activated your virtual environment
```bash
source venv/bin/activate  # macOS/Linux
```

### Issue: "Connection refused" to Supabase

**Solution**: Check your `SUPABASE_URL` in `.env` - make sure it includes `https://`

### Issue: OpenAI rate limit error

**Solution**:
- You may need to add credits to your OpenAI account
- Or use a lower-tier model (edit `app/services/openai_service.py`)

### Issue: FFmpeg or Tesseract not found

**Solution**: Install system dependencies (see step 1)

### Issue: "Row level security" error

**Solution**: Make sure you ran the complete `database/schema.sql` in Supabase SQL Editor

## Development Mode

### Enable Auto-Reload

The app already runs with auto-reload by default when using `python main.py`

### View Logs

Logs are printed to console. To adjust log level:

```env
# In .env
LOG_LEVEL=DEBUG  # or INFO, WARNING, ERROR
```

### Debug Mode

```env
# In .env
DEBUG=true
```

## Production Deployment

For production deployment, see the main [README.md](README.md#deployment) file.

## Getting Help

- **Documentation**: Check [README.md](README.md), [ARCHITECTURE.md](docs/ARCHITECTURE.md), and [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)
- **API Reference**: http://localhost:8000/api/docs
- **Database Setup**: See [database/README.md](database/README.md)

## What's Next?

Now that you have the backend running, you can:

1. **Build a frontend**: Connect your React/Vue/Next.js app to this API
2. **Customize extractors**: Add support for new recipe sources
3. **Extend features**: Add meal planning, grocery lists, etc.
4. **Deploy**: Host on your preferred cloud platform

Happy cooking! 🍳
