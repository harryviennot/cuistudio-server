# CuiStudio Server

Backend API service for the CuiStudio recipe management application.

## Features

- 🔐 **Authentication** - Secure user authentication with Supabase Auth
- 📝 **Recipe Management** - Create, read, update, and delete recipes
- 🎥 **Video Processing** - Extract recipes from cooking videos
- 🖼️ **Image Processing** - Extract recipes from recipe images
- 🤖 **AI-Powered** - Uses OpenAI GPT-4 for intelligent recipe extraction
- 📚 **Cookbook Organization** - Organize recipes into cookbooks

## Tech Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **Supabase** - PostgreSQL database and authentication
- **OpenAI GPT-4** - AI-powered recipe extraction
- **Pydantic** - Data validation using Python type annotations
- **Python 3.9+** - Programming language

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Supabase account and project
- OpenAI API key

### Installation

1. **Clone the repository**

   ```bash
   cd cuistudio-server
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   ```bash
   cp env.example .env
   ```

   Edit `.env` with your credentials:

   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_PUBLISHABLE_KEY=your_supabase_anon_key
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_ORGANIZATION_ID=your_openai_org_id
   OPENAI_PROJECT_ID=your_openai_project_id
   ```

5. **Run the server**

   ```bash
   # Development mode with hot reload
   uvicorn main:app --reload --host 0.0.0.0 --port 8000

   # Or using Python directly
   python main.py
   ```

6. **Access the API documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication (`/auth`)

- `POST /auth/signup` - Register new user
- `POST /auth/login` - Authenticate user
- `POST /auth/logout` - Logout user
- `GET /auth/me` - Get current user info
- `POST /auth/refresh` - Refresh access token
- `POST /auth/password-reset` - Request password reset
- `POST /auth/password-update` - Update password
- `POST /auth/verify-token` - Verify token validity

See [Authentication Documentation](docs/AUTHENTICATION.md) for detailed API specs.

### Recipe Extraction

- `GET /extract?link={url}` - Extract recipe from URL (video/image)

### Health Check

- `GET /health` - API health status
- `GET /` - API welcome message

## Project Structure

```
cuistudio-server/
├── app/
│   ├── models/          # Pydantic data models
│   │   ├── auth.py      # Authentication models
│   │   ├── common.py    # Shared models
│   │   ├── recipe.py    # Recipe models
│   │   └── user.py      # User models
│   ├── routers/         # API route handlers
│   │   └── auth.py      # Auth endpoints
│   ├── extraction/      # Recipe extraction pipeline
│   ├── utils/           # Utility functions
│   ├── auth.py          # Auth utilities
│   ├── config.py        # Configuration
│   └── database.py      # Database client
├── docs/                # Documentation
├── main.py              # App entry point
└── requirements.txt     # Dependencies
```

See [Project Structure](docs/PROJECT_STRUCTURE.md) for detailed documentation.

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. After logging in or signing up, you'll receive an access token and refresh token.

### Using Protected Endpoints

Include the access token in the Authorization header:

```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Token Refresh

Access tokens expire after 1 hour. Use the refresh token to get a new access token:

```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

## Development

### Running Tests

```bash
python debug_test.py
```

### Code Style

The project follows PEP 8 guidelines. Format code with:

```bash
# Install formatters
pip install black isort

# Format code
black .
isort .
```

### Adding New Features

1. **Add Models** - Define data schemas in `app/models/`
2. **Create Router** - Add endpoints in `app/routers/`
3. **Register Router** - Include in `main.py`
4. **Document** - Update relevant documentation

See [Project Structure](docs/PROJECT_STRUCTURE.md) for detailed guidelines.

## Docker Deployment

### Build and Run

```bash
# Build image
docker build -t cuistudio-server .

# Run container
docker run -p 8000:8000 --env-file .env cuistudio-server
```

### Using Docker Compose

```bash
docker-compose up -d
```

## Environment Variables

| Variable                   | Description              | Required |
| -------------------------- | ------------------------ | -------- |
| `SUPABASE_URL`             | Supabase project URL     | Yes      |
| `SUPABASE_PUBLISHABLE_KEY` | Supabase anon/public key | Yes      |
| `OPENAI_API_KEY`           | OpenAI API key           | Yes      |
| `OPENAI_ORGANIZATION_ID`   | OpenAI organization ID   | Yes      |
| `OPENAI_PROJECT_ID`        | OpenAI project ID        | Yes      |
| `DEBUG`                    | Enable debug mode        | No       |

## API Examples

### Sign Up

```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### Extract Recipe

```bash
curl "http://localhost:8000/extract?link=https://youtube.com/watch?v=VIDEO_ID"
```

## Troubleshooting

### "Invalid authentication credentials"

- Check that your Supabase URL and key are correct
- Verify the token hasn't expired
- Ensure the Authorization header is properly formatted

### "Module not found" errors

- Activate the virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

### Database connection errors

- Verify `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` are set
- Check your Supabase project is active
- Ensure network connectivity

### OpenAI API errors

- Verify `OPENAI_API_KEY` is valid
- Check your OpenAI account has available credits
- Ensure organization and project IDs are correct

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions:

- Check the [documentation](docs/)
- Review [API documentation](http://localhost:8000/docs)
- Open an issue on GitHub

---

Built with ❤️ for recipe enthusiasts

