# weapon-detection API

A FastAPI backend with PostgreSQL, Docker, and auto-generated documentation.

## 🏗️ Architecture

- **Backend**: FastAPI + PostgreSQL + SQLAlchemy
- **Deployment**: Docker Compose
- **Documentation**: Auto-generated OpenAPI/Swagger docs
- **API Contract**: Auto-generated TypeScript types

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.9+ (for local development)

### Development Setup

1. **Clone and setup**
   ```bash
   git clone https://github.com/MTAI-Labs/weapon-detection.git
   cd weapon-detection
   ```

2. **Start with Docker (Recommended)**
   ```bash
   # Start with automatic migrations
   docker-compose --profile migration up --build
   
   # Or start without migrations (manual migration control)
   docker-compose up --build
   ```
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

3. **Or run locally**
   ```bash
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

## 📁 Project Structure

```
weapon-detection/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── users.py
│   │   │   └── items.py
│   │   └── routes.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── models/
│   │   ├── user.py
│   │   └── item.py
│   ├── schemas/
│   │   ├── user.py
│   │   └── item.py
│   └── main.py
├── scripts/
│   ├── generate_docs.py
│   └── generate_contract.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🔧 Environment Variables

Copy `.env.example` to `.env` and update the values:

```env
# Database
POSTGRES_USER=api_user
POSTGRES_PASSWORD=api_password
POSTGRES_DB=api_db
DATABASE_URL=postgresql://api_user:api_password@db:5432/api_db

# API
API_SECRET_KEY=your-secret-key-here
API_CORS_ORIGINS=*
API_HOST=0.0.0.0
API_PORT=8000

# Environment
ENVIRONMENT=development
```

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Generate Documentation

```bash
# Generate static HTML documentation
python scripts/generate_docs.py

# Generate TypeScript API contract
python scripts/generate_contract.py
```

## 🗃️ Database Migrations with Alembic

This project uses Alembic for database schema migrations. Alembic provides a way to manage database schema changes over time.

### Initial Setup

```bash
# Initialize the database with current schema
alembic stamp head

# Or run the initial migration
alembic upgrade head
```

### Creating New Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new field to user model"

# Create empty migration file (for data migrations)
alembic revision -m "Add default admin user"
```

### Running Migrations

```bash
# Run all pending migrations
alembic upgrade head

# Run specific migration
alembic upgrade +1  # Next migration
alembic upgrade -1  # Previous migration
alembic upgrade ae1027a6acf  # Specific revision

# Downgrade migrations
alembic downgrade -1  # Rollback one migration
alembic downgrade base  # Rollback all migrations
```

### Migration Management

```bash
# Check current migration status
alembic current

# View migration history
alembic history

# Show pending migrations
alembic show

# Generate SQL instead of running migration
alembic upgrade head --sql
```

### Docker Environment

```bash
# Option 1: Use the migration service (automatic)
docker-compose --profile migration up --build

# Option 2: Manual migration control
docker-compose up --build
docker-compose exec api alembic upgrade head

# Generate new migration in Docker
docker-compose exec api alembic revision --autogenerate -m "Description"

# Run specific migration commands
docker-compose run --rm migration alembic current
docker-compose run --rm migration alembic history
```

### Environment Variables for Migrations

Set these environment variables for different environments:

```env
# Development (default in alembic.ini)
DATABASE_URL=postgresql://api_user:api_password@localhost:5432/api_db

# Production
DATABASE_URL=postgresql://user:password@prod-db:5432/prod_db

# Testing
DATABASE_URL=postgresql://user:password@test-db:5432/test_db
```

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## 🚀 Deployment

### Production Build
```bash
docker-compose -f docker-compose.prod.yml up --build
```

### Health Checks
- **Health**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

## 📋 API Endpoints

### Users
- `GET /api/users` - List users
- `POST /api/users` - Create user
- `GET /api/users/{id}` - Get user by ID
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user

### Items
- `GET /api/items` - List items
- `POST /api/items` - Create item
- `GET /api/items/{id}` - Get item by ID
- `PUT /api/items/{id}` - Update item
- `DELETE /api/items/{id}` - Delete item

## 🔄 Development Workflow & Branching Strategy

This project follows a **feature-branch workflow** with ticket-driven development for API development and enhancements.

### Branch Structure for API Development

```
main                           # Production-ready API
├── release/v1.2.0            # API release preparation
├── feature/TICK-123-new-endpoint     # New API endpoints
├── bug/TICK-456-validation-fix       # API bug fixes  
└── enhancement/TICK-789-performance  # Performance improvements
```

### API Development Workflow

#### 1. **Create API Ticket**
- Use issue templates for API-specific work
- Include API specification requirements
- Define expected request/response formats
- Document breaking changes (if any)

#### 2. **Branch Creation for API Work**
```bash
# API-specific branch examples
git checkout -b feature/TICK-123-user-management-api
git checkout -b bug/TICK-456-auth-token-validation
git checkout -b enhancement/TICK-789-query-performance
```

#### 3. **API Development Process**
```bash
# Develop new endpoints
# Update API documentation (OpenAPI/Swagger)
# Add comprehensive tests
# Update API contracts/schemas

git commit -m "feat(api): add user management endpoints

- Add CRUD operations for user management
- Include input validation and error handling  
- Update OpenAPI specification
- Add integration tests

Closes #123"
```

#### 4. **API-Specific Code Review**

**API Development Checklist:**
- [ ] **OpenAPI Documentation**: Swagger/ReDoc updated
- [ ] **Request/Response Validation**: Pydantic schemas defined
- [ ] **Error Handling**: Proper HTTP status codes and error messages
- [ ] **Authentication**: Security requirements implemented
- [ ] **Rate Limiting**: Performance considerations addressed
- [ ] **Database Changes**: Migrations included and tested
- [ ] **API Versioning**: Version compatibility maintained
- [ ] **Integration Tests**: API endpoints thoroughly tested
- [ ] **Performance**: Query optimization and response times
- [ ] **Security**: Input sanitization and authorization
- [ ] **Backward Compatibility**: Breaking changes documented

#### 5. **API Contract Generation**
```bash
# Generate TypeScript types for frontend
python scripts/generate_contract.py

# Generate API documentation
python scripts/generate_docs.py

# Commit generated files
git add api-contract.ts docs/
git commit -m "docs: update API contract and documentation"
```

### API Release Process

```bash
# Merge API changes to release branch
git checkout release/v1.2.0
git merge feature/TICK-123-user-management-api

# Test API integration
docker-compose up --build
pytest tests/integration/

# Update version and changelog
# Deploy to staging for API testing
# Create PR to main after validation
```

### API Testing Strategy

```bash
# Unit tests for business logic
pytest tests/unit/

# Integration tests for API endpoints  
pytest tests/integration/

# Load testing for performance
pytest tests/load/

# Contract testing with frontend
pytest tests/contract/
```

## 🤝 Contributing to API Development

**API-Specific Guidelines:**
- ✅ Always update OpenAPI documentation
- ✅ Include comprehensive error handling
- ✅ Maintain backward compatibility
- ✅ Generate and commit API contracts
- ✅ Test with realistic data volumes
- ✅ Consider security implications
- ✅ Document breaking changes clearly

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, email support@MTAI-Labs.com or create an issue in this repository.