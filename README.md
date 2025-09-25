# FastAPI Senior-User Matching Platform

A comprehensive FastAPI application that connects users with senior citizens for various job opportunities, featuring real-time chat, file uploads, and semantic skill matching.

## 🚀 Features

### Core Functionality
- **User & Senior User Management** - Dual user types with different profiles and capabilities
- **Job Posting & Matching** - Post jobs and find suitable senior workers
- **Semantic Search** - AI-powered skill matching using sentence transformers
- **Real-time Chat System** - WebSocket-based messaging with typing indicators
- **File Upload System** - Support for documents and profile images
- **Location Tracking** - Real-time location updates with Redis
- **JWT Authentication** - Secure token-based authentication

### Advanced Features
- **Vector Similarity Search** - Using pgvector for efficient skill matching
- **Profile Image Management** - Automatic image optimization and resizing
- **WebSocket Chat** - Real-time messaging with online status
- **Geographic Search** - Location-based job discovery
- **File Management** - Organized file storage with metadata

## 🏗️ Architecture

### Backend Stack
- **FastAPI** - Modern, fast web framework for building APIs
- **PostgreSQL** - Primary database with pgvector extension
- **Redis** - Real-time data and presence tracking
- **SQLAlchemy 2.0** - Modern ORM with async support
- **Pydantic** - Data validation and serialization
- **Sentence Transformers** - AI-powered text embeddings

### Database Models
- **Users** & **UserProfiles** - Regular user accounts
- **SeniorUsers** & **SeniorProfiles** - Senior citizen workers
- **Jobs** - Job postings and opportunities
- **ChatRooms** & **ChatMessages** - Real-time messaging
- **Files** - File storage and metadata

## 📦 Installation

### Prerequisites
- Python 3.13+
- PostgreSQL with pgvector extension
- Redis server
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd first_fastapi
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

4. **Environment Configuration**
   Create a `.env` file in the root directory:
   ```env
   # Database Configuration
   PG_HOST=localhost
   PG_PORT=5432
   PG_USER=your_db_user
   PG_PASSWORD=your_db_password
   PG_DBNAME=your_db_name
   
   # Redis Configuration
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   REDIS_PASSWORD=your_redis_password
   PRESENCE_TTL_SECONDS=60
   
   # AI Model Configuration
   MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
   
   # JWT Configuration
   JWT_SECRET=your-super-secret-key-change-in-production
   JWT_ALGORITHM=HS256
   JWT_EXPIRES_MINUTES=43200
   JWT_ISSUER=waiwan-app
   ```

5. **Database Setup**
   ```bash
   # Install PostgreSQL and pgvector extension
   # Create database and user
   # Run migrations (handled automatically on startup)
   ```

6. **Create upload directories**
   ```bash
   mkdir -p uploads/{images,documents,profiles,temp}
   ```

## 🚀 Running the Application

### Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Chat Test Page**: http://localhost:8000/chat-test
- **File Upload Test**: http://localhost:8000/file-test

## 📚 API Endpoints

### Authentication
- `POST /auth/request-otp` - Request OTP for phone verification
- `POST /auth/verify-otp` - Verify OTP and create/login user
- `POST /auth/login` - Simple login for testing (testuser/testpass)

### Users
- `GET /users/me` - Get current user profile
- `GET /users/seniors/{senior_id}` - Get senior user details
- `GET /users/locations` - Get user locations
- `POST /users/heartbeat` - Update user location

### Search & Jobs
- `POST /search` - Semantic search for jobs/seniors
- `GET /jobs` - List jobs
- `POST /jobs` - Create/update job
- `DELETE /jobs/{job_id}` - Delete job

### Real-time Chat
- `GET /chat/rooms` - Get user's chat rooms
- `GET /chat/rooms/{room_id}` - Get chat room with messages
- `POST /chat/rooms/{room_id}/messages` - Send message
- `WS /chat/ws/{room_id}` - WebSocket connection for real-time chat

### File Management
- `POST /files/upload` - Upload file (with profile image option)
- `GET /files/{file_id}` - Get file information
- `GET /files/user/my-files` - List user's files
- `DELETE /files/{file_id}` - Delete file
- `GET /files/{category}/{filename}` - Download/serve file

## 🔧 Configuration

### Environment Variables
The application uses environment variables for configuration. See `.env.example` for all available options.

### File Upload Settings
- **Max file size**: 10MB
- **Supported image formats**: JPEG, PNG, GIF, WebP
- **Supported documents**: PDF, DOC, DOCX, TXT
- **Automatic image optimization**: Resize and compress images
- **Profile image support**: Link files to user profiles

### WebSocket Features
- **Real-time messaging**: Instant message delivery
- **Typing indicators**: Show when users are typing
- **Online status**: Track user presence
- **Message read status**: Mark messages as read
- **Connection management**: Handle reconnections gracefully

## 🧪 Testing

### Interactive Test Pages
1. **Chat System Testing**
   - Visit: http://localhost:8000/chat-test
   - Test WebSocket connections, messaging, and real-time features

2. **File Upload Testing**
   - Visit: http://localhost:8000/file-test
   - Test file uploads, profile images, and file management

### API Testing
Use the interactive API documentation at http://localhost:8000/docs to test all endpoints.

## 🗂️ Project Structure

```
first_fastapi/
├── app/
│   ├── database/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── db.py           # Database configuration
│   │   └── redis.py        # Redis operations
│   ├── routes/             # API route handlers
│   │   ├── auth_router.py  # Authentication endpoints
│   │   ├── user_router.py  # User management
│   │   ├── search_router.py # Search functionality
│   │   ├── job_router.py   # Job management
│   │   ├── chat_router.py  # Chat and WebSocket
│   │   └── file_router.py  # File operations
│   ├── utils/              # Utility modules
│   │   ├── config.py       # Configuration
│   │   ├── deps.py         # Dependencies
│   │   ├── jwt.py          # JWT operations
│   │   ├── schemas.py      # Pydantic models
│   │   ├── embedder.py     # AI embeddings
│   │   ├── file_upload.py  # File processing
│   │   ├── websocket.py    # WebSocket management
│   │   └── score.py        # Scoring algorithms
│   ├── services/           # Business logic
│   └── main.py            # FastAPI application
├── uploads/               # File storage
├── venv/                 # Virtual environment
├── websocket_test.html   # WebSocket test page
├── file_upload_test.html # File upload test page
└── README.md            # This file
```

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Role-based Access**: Different permissions for users and seniors
- **File Validation**: Strict file type and size validation
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **CORS Configuration**: Configurable cross-origin resource sharing
- **Input Validation**: Pydantic models validate all inputs

## 🌐 WebSocket Events

### Chat Events
```json
// Send message
{
  "type": "message",
  "message": "Hello world",
  "user_id": "123"
}

// Typing indicator
{
  "type": "typing",
  "is_typing": true,
  "user_id": "123"
}

// Mark as read
{
  "type": "mark_read",
  "user_id": "123"
}
```

## 📈 Performance Features

- **Vector Database**: Fast similarity search with pgvector
- **Redis Caching**: Real-time data caching
- **Image Optimization**: Automatic image compression
- **Database Indexing**: Optimized database queries
- **Connection Pooling**: Efficient database connections
- **Async Operations**: Non-blocking I/O operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- PostgreSQL and pgvector for vector similarity search
- Sentence Transformers for AI-powered embeddings
- Redis for real-time data management
- All contributors and the open-source community

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Use the interactive test pages for debugging

---

**Happy coding! 🚀**